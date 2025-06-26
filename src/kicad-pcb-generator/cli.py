#!/usr/bin/env python3
"""
Command-line interface for the KiCad PCB Generator.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
import json

from .core.project_manager import ProjectManager
from .core.pcb import PCBGenerator, PCBGenerationConfig
from .core.netlist.parser import parse_schematic, parse_json_netlist, Netlist
from .core.falstad_importer import FalstadImporter, FalstadImportError
from .core.templates.board_presets import board_preset_registry, BoardProfile
from .design_library import list_designs, filter_designs_by_tag, get_design, ensure_placeholders

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_project(args):
    """Create a new project from a template."""
    try:
        project_manager = ProjectManager()
        
        # Validate board preset if specified
        board_config = None
        if args.board_preset:
            preset = board_preset_registry.get_preset_by_name(args.board_preset)
            if not preset:
                logger.error(f"Board preset '{args.board_preset}' not found")
                logger.info("Use 'kicadpcb board-presets' to list available presets")
                sys.exit(1)
            board_config = {
                "board_profile": preset.name.lower().replace(" ", "_"),
                "board_width_mm": preset.width_mm,
                "board_height_mm": preset.height_mm
            }
        
        config = project_manager.create_project(
            name=args.name,
            template=args.template,
            description=f"Project created from template {args.template}",
            author="KiCad PCB Generator",
            board_config=board_config
        )
        logger.info(f"Successfully created project '{args.name}' from template '{args.template}'")
        if board_config:
            logger.info(f"Board size: {board_config['board_width_mm']}mm x {board_config['board_height_mm']}mm ({args.board_preset})")
        logger.info(f"Project location: {project_manager.get_project_path(args.name)}")
    except (ValueError, OSError, PermissionError) as e:
        logger.error(f"Error creating project: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error creating project: {e}")
        sys.exit(1)

def generate_pcb(args):
    """Generate PCB from project files."""
    try:
        project_manager = ProjectManager()
        pcb_generator = PCBGenerator(project_manager)
        
        # Check if project exists
        if not project_manager.get_project_path(args.project).exists():
            logger.error(f"Project '{args.project}' not found")
            sys.exit(1)
        
        # Load optional config
        config_obj: PCBGenerationConfig | None = None
        if args.config:
            config_obj = PCBGenerationConfig()
            config_result = config_obj.load(args.config)
            if not config_result.success:
                logger.error("Invalid PCB generation config: %s", config_result.errors)
                sys.exit(1)
        
        # Apply board preset if specified
        if args.board_preset:
            preset = board_preset_registry.get_preset_by_name(args.board_preset)
            if not preset:
                logger.error(f"Board preset '{args.board_preset}' not found")
                logger.info("Use 'kicadpcb board-presets' to list available presets")
                sys.exit(1)
            
            # Create or update config with board preset
            if config_obj is None:
                config_obj = PCBGenerationConfig()
            
            # Update board size in config
            config_obj.board_size = (preset.width_mm, preset.height_mm)
            logger.info(f"Applied board preset: {preset.name} ({preset.width_mm}mm x {preset.height_mm}mm)")

        # Load optional netlist from schematic
        netlist: Netlist | None = None
        if args.schematic:
            schem_path = Path(args.schematic)
            if not schem_path.exists():
                logger.error("Schematic file '%s' not found", schem_path)
                sys.exit(1)
            if schem_path.suffix.lower() in {".kicad_sch", ".sch"}:
                netlist = parse_schematic(schem_path)
            else:
                netlist = parse_json_netlist(schem_path)

        # Generate PCB
        result = pcb_generator.generate_pcb(args.project, config=config_obj, netlist=netlist)
        
        if result.success:
            logger.info(f"Successfully generated PCB for project '{args.project}'")
            if result.output_path:
                logger.info(f"Output location: {result.output_path}")
            if result.warnings:
                for warning in result.warnings:
                    logger.warning(f"Warning: {warning}")

            # Optional export immediately after generation
            if args.export:
                for fmt in args.export:
                    exp_result = pcb_generator.export_pcb(args.project, format=fmt, output_dir=result.output_path)
                    if exp_result.success:
                        logger.info("Exported %s files to %s", fmt, exp_result.output_path)
                    else:
                        logger.error("Export %s failed: %s", fmt, exp_result.errors)
                        sys.exit(1)
        else:
            logger.error(f"Failed to generate PCB for project '{args.project}'")
            for error in result.errors:
                logger.error(f"Error: {error}")
            sys.exit(1)
            
    except (ValueError, OSError, PermissionError) as e:
        logger.error(f"Error generating PCB: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error generating PCB: {e}")
        sys.exit(1)

def export_files(args):
    """Export project files."""
    try:
        project_manager = ProjectManager()
        pcb_generator = PCBGenerator(project_manager)
        
        # Check if project exists
        if not project_manager.get_project_path(args.project).exists():
            logger.error(f"Project '{args.project}' not found")
            sys.exit(1)
        
        # Export files
        result = pcb_generator.export_pcb(args.project, format=args.format)
        
        if result.success:
            logger.info(f"Successfully exported {args.format} files for project '{args.project}'")
            if result.output_path:
                logger.info(f"Export location: {result.output_path}")
            if result.warnings:
                for warning in result.warnings:
                    logger.warning(f"Warning: {warning}")
        else:
            logger.error(f"Failed to export {args.format} files for project '{args.project}'")
            for error in result.errors:
                logger.error(f"Error: {error}")
            sys.exit(1)
            
    except (ValueError, OSError, PermissionError) as e:
        logger.error(f"Error exporting files: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error exporting files: {e}")
        sys.exit(1)

def falstad2pcb(args):
    """Convert Falstad JSON to PCB directly."""
    try:
        importer = FalstadImporter()
        netlist = importer.to_netlist(json.loads(Path(args.falstad).read_text()))

        project_manager = ProjectManager()
        pcb_generator = PCBGenerator(project_manager)

        cfg = None
        if args.config:
            cfg = PCBGenerationConfig()
            res = cfg.load(args.config)
            if not res.success:
                logger.error("Config invalid: %s", res.errors)
                sys.exit(1)

        result = pcb_generator.generate_pcb(args.project, config=cfg, netlist=netlist)
        if not result.success:
            logger.error("PCB generation failed: %s", result.errors)
            sys.exit(1)

        # optional export
        if args.export:
            for fmt in args.export:
                exp_res = pcb_generator.export_pcb(args.project, format=fmt, output_dir=result.output_path)
                if not exp_res.success:
                    logger.error("Export %s failed: %s", fmt, exp_res.errors)
                    sys.exit(1)
    except FalstadImportError as exc:
        logger.error("Falstad import error: %s", exc)
        sys.exit(1)
    except (ValueError, OSError, PermissionError) as exc:
        logger.error("Error: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        sys.exit(1)

def list_library(args):
    """List available reference designs or show details for a single design.

    Usage examples::

        kicadpcb library --list
        kicadpcb library --id vco_basic_v1
        kicadpcb library --tags eurorack vco
    """
    try:
        if args.list:
            records = filter_designs_by_tag(*args.tags) if args.tags else [get_design(d) for d in list_designs()]
            for rec in records:
                logger.info(f"{rec['id']}: {rec['title']}")
            if not records:
                logger.info("No designs match given criteria.")
            return
        if args.id:
            rec = get_design(args.id)
            logger.info(json.dumps(rec, indent=2))
            return
        if args.make_placeholders:
            if args.id:
                ensure_placeholders(args.id)
                logger.info(f"Placeholder created for {args.id}")
            elif args.list or args.tags:
                targets = [rec["id"] for rec in filter_designs_by_tag(*args.tags)] if args.tags else list_designs()
                ensure_placeholders(*targets)
                logger.info(f"Placeholders ensured for {len(targets)} design(s)")
                return
            else:
                ensure_placeholders()
                logger.info("Placeholders ensured for all designs.")
                return
        # default case – nothing specified
        logger.info("Specify --list or --id <design_id>. Use --help for details.")
    except KeyError as exc:
        logger.error("Design not found: %s", exc)
        sys.exit(1)
    except (ValueError, OSError, PermissionError) as exc:
        logger.error("Error accessing design library: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        sys.exit(1)

def list_board_presets(args):
    """List available board size presets or show details for a specific preset."""
    try:
        if args.preset:
            # Show details for specific preset
            preset = board_preset_registry.get_preset_by_name(args.preset)
            if preset:
                logger.info(f"Board Preset: {preset.name}")
                logger.info(f"Description: {preset.description}")
                logger.info(f"Dimensions: {preset.width_mm}mm x {preset.height_mm}mm")
                logger.info(f"Max Thickness: {preset.max_thickness_mm}mm")
                logger.info(f"Min Track Width: {preset.min_track_width_mm}mm")
                logger.info(f"Min Via Diameter: {preset.min_via_diameter_mm}mm")
                logger.info(f"Min Clearance: {preset.min_clearance_mm}mm")
                logger.info(f"Max Component Height: {preset.max_component_height_mm}mm")
                logger.info(f"Edge Clearance: {preset.edge_clearance_mm}mm")
                if preset.mounting_holes:
                    logger.info(f"Mounting Holes: {preset.mounting_holes}")
                if preset.manufacturing_constraints:
                    logger.info("Manufacturing Constraints:")
                    for key, value in preset.manufacturing_constraints.items():
                        logger.info(f"  {key}: {value}")
            else:
                logger.error(f"Preset '{args.preset}' not found")
                sys.exit(1)
        else:
            # List all presets
            presets = board_preset_registry.list_presets()
            logger.info("Available Board Size Presets:")
            logger.info("-" * 50)
            for profile, preset in presets.items():
                logger.info(f"{profile.value:20} - {preset.name}")
                logger.info(f"{'':20}   {preset.description}")
                logger.info(f"{'':20}   {preset.width_mm}mm x {preset.height_mm}mm")
                logger.info("")
    except (ValueError, KeyError) as e:
        logger.error(f"Error listing board presets: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error listing board presets: {e}")
        sys.exit(1)

def main():
    """Main entry point for the KiCad PCB Generator CLI.
    
    This function sets up the command-line interface with the following commands:
    
    Commands:
        create         - Create a new project from a template
        generate       - Generate PCB from project files
        export         - Export project files in various formats
        falstad2pcb    - Convert Falstad JSON directly to PCB
        library        - Query built-in reference design library
        board-presets  - List available board size presets
    
    Examples:
        # Create a new audio amplifier project with Eurorack 3U board
        kicadpcb create my_amp --template basic_audio_amp --board-preset "Eurorack 3U"
        
        # Generate PCB from project with specific board size
        kicadpcb generate my_amp --schematic circuit.kicad_sch --board-preset "Standard Guitar Pedal"
        
        # List available board presets
        kicadpcb board-presets
        
        # Show details for a specific preset
        kicadpcb board-presets --preset "Eurorack 3U"
        
        # Export Gerber files
        kicadpcb export my_amp --format gerber
        
        # Convert Falstad circuit to PCB
        kicadpcb falstad2pcb circuit.json my_project
        
        # List available reference designs
        kicadpcb library --list --tags eurorack
    """
    parser = argparse.ArgumentParser(
        description="KiCad PCB Generator - A specialized tool for audio PCB design automation and validation",
        epilog="For more information, visit: https://github.com/yourusername/kicad-pcb-generator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create project command
    create_parser = subparsers.add_parser(
        "create", 
        help="Create a new project from a template",
        description="Create a new PCB project using one of the available templates"
    )
    create_parser.add_argument("name", help="Project name (must be unique)")
    create_parser.add_argument(
        "--template",
        default="basic_audio_amp",
        choices=["basic_audio_amp", "preamplifier", "power_amp", "effects_pedal"],
        help="Project template to use (default: basic_audio_amp)"
    )
    create_parser.add_argument(
        "--board-preset",
        help="Board size preset to use (e.g., 'Eurorack 3U', 'Standard Guitar Pedal')"
    )
    create_parser.set_defaults(func=create_project)

    # Generate PCB command
    generate_parser = subparsers.add_parser(
        "generate", 
        help="Generate PCB from project files",
        description="Generate a PCB design from project files with optional schematic/netlist input"
    )
    generate_parser.add_argument("project", help="Path to project directory or project name")
    generate_parser.add_argument(
        "--schematic", 
        help="Path to KiCad schematic (.kicad_sch) or JSON netlist file"
    )
    generate_parser.add_argument(
        "--config", 
        help="PCB generation configuration file (JSON/YAML format)"
    )
    generate_parser.add_argument(
        "--board-preset",
        help="Board size preset to apply (e.g., 'Eurorack 3U', 'Standard Guitar Pedal')"
    )
    generate_parser.add_argument(
        "--export", 
        nargs="*", 
        choices=["gerber", "drill", "bom", "step"], 
        help="Export formats to generate after PCB creation"
    )
    generate_parser.set_defaults(func=generate_pcb)

    # Export files command
    export_parser = subparsers.add_parser(
        "export", 
        help="Export project files in various formats",
        description="Export PCB project files for manufacturing or documentation"
    )
    export_parser.add_argument("project", help="Path to project directory or project name")
    export_parser.add_argument(
        "--format",
        choices=["gerber", "drill", "bom", "step"],
        default="gerber",
        help="Export format (default: gerber)"
    )
    export_parser.set_defaults(func=export_files)

    # Falstad2PCB command
    falstad_parser = subparsers.add_parser(
        "falstad2pcb", 
        help="Convert Falstad JSON directly to PCB",
        description="Convert a Falstad circuit simulator JSON file directly to a PCB project"
    )
    falstad_parser.add_argument("falstad", help="Path to Falstad JSON schematic file")
    falstad_parser.add_argument("project", help="Target project name")
    falstad_parser.add_argument("--config", help="PCB generation configuration file")
    falstad_parser.add_argument(
        "--export", 
        nargs="*", 
        choices=["gerber", "drill", "bom", "step"], 
        help="Export formats to generate after PCB creation"
    )
    falstad_parser.set_defaults(func=falstad2pcb)

    # Design library command
    lib_parser = subparsers.add_parser(
        "library", 
        help="Query built-in reference design library",
        description="Browse and manage the built-in library of reference audio circuit designs"
    )
    lib_parser.add_argument(
        "--list", 
        action="store_true", 
        help="List all available design IDs (optionally filtered by --tags)"
    )
    lib_parser.add_argument(
        "--id", 
        help="Show complete metadata for a specific design ID"
    )
    lib_parser.add_argument(
        "--tags", 
        nargs="*", 
        default=[], 
        help="Filter designs by tag(s) (e.g., eurorack, vco, filter)"
    )
    lib_parser.add_argument(
        "--make-placeholders", 
        action="store_true", 
        help="Create schematic placeholders for selected designs"
    )
    lib_parser.set_defaults(func=list_library)

    # Board presets command
    board_presets_parser = subparsers.add_parser(
        "board-presets", 
        help="List available board size presets",
        description="Browse available board size presets for common audio PCB standards"
    )
    board_presets_parser.add_argument(
        "--preset", 
        help="Show detailed information for a specific preset"
    )
    board_presets_parser.set_defaults(func=list_board_presets)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main() 