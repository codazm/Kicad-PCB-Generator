#!/usr/bin/env python3
"""
Advanced command-line interface for the KiCad PCB Generator.
Provides sophisticated features for experienced users.
"""

import argparse
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedCLI:
    def __init__(self):
        self.config: Dict = {}
        self.project_path: Optional[Path] = None

    def load_config(self, config_path: Union[str, Path]) -> None:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, PermissionError) as e:
            logger.error("File access error loading config: %s", e)
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in config file: %s", e)
            sys.exit(1)
        except Exception as e:
            logger.error("Unexpected error loading config: %s", e)
            sys.exit(1)

    def create_project(self, args) -> None:
        """Create a new project with advanced options."""
        try:
            self.project_path = Path(args.name)
            if self.project_path.exists():
                raise ValueError(f"Project directory '{args.name}' already exists")

            # Create project structure
            self.project_path.mkdir(parents=True)
            (self.project_path / "schematics").mkdir()
            (self.project_path / "pcb").mkdir()
            (self.project_path / "config").mkdir()

            # Create configuration files
            config = {
                "project": {
                    "name": args.name,
                    "template": args.template,
                    "version": "1.0.0"
                },
                "validation": {
                    "rules": args.validation_rules,
                    "strict_mode": args.strict,
                    "custom_rules": args.custom_rules
                },
                "generation": {
                    "auto_route": args.auto_route,
                    "optimize": args.optimize,
                    "parallel": args.parallel
                }
            }

            with open(self.project_path / "config" / "project.json", 'w') as f:
                json.dump(config, f, indent=4)

            logger.info(f"Created project '{args.name}' with advanced configuration")
        except (ValueError, OSError, PermissionError) as e:
            logger.error("Error creating project: %s", e)
            sys.exit(1)
        except Exception as e:
            logger.error("Unexpected error creating project: %s", e)
            sys.exit(1)

    def generate_pcb(self, args) -> None:
        """Generate PCB with advanced options."""
        try:
            project_path = Path(args.project)
            if not project_path.exists():
                raise ValueError(f"Project directory '{args.project}' not found")

            # Load project configuration
            with open(project_path / "config" / "project.json", 'r') as f:
                config = json.load(f)

            # Apply generation options
            if args.override_config:
                config["generation"].update(args.override_config)

            logger.info(f"Generating PCB for project '{args.project}' with advanced options:")
            logger.info(f"- Auto-route: {config['generation']['auto_route']}")
            logger.info(f"- Optimization: {config['generation']['optimize']}")
            logger.info(f"- Parallel processing: {config['generation']['parallel']}")

        except (ValueError, FileNotFoundError, PermissionError) as e:
            logger.error("Error generating PCB: %s", e)
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error("Invalid project configuration: %s", e)
            sys.exit(1)
        except Exception as e:
            logger.error("Unexpected error generating PCB: %s", e)
            sys.exit(1)

    def export_files(self, args) -> None:
        """Export files with advanced options."""
        try:
            project_path = Path(args.project)
            if not project_path.exists():
                raise ValueError(f"Project directory '{args.project}' not found")

            # Load project configuration
            with open(project_path / "config" / "project.json", 'r') as f:
                config = json.load(f)

            # Apply export options
            export_config = {
                "formats": args.formats,
                "output_dir": args.output_dir,
                "include_3d": args.include_3d,
                "include_docs": args.include_docs
            }

            logger.info(f"Exporting files for project '{args.project}' with options:")
            logger.info(f"- Formats: {', '.join(export_config['formats'])}")
            logger.info(f"- Output directory: {export_config['output_dir']}")
            logger.info(f"- Include 3D models: {export_config['include_3d']}")
            logger.info(f"- Include documentation: {export_config['include_docs']}")

        except (ValueError, FileNotFoundError, PermissionError) as e:
            logger.error("Error exporting files: %s", e)
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error("Invalid project configuration: %s", e)
            sys.exit(1)
        except Exception as e:
            logger.error("Unexpected error exporting files: %s", e)
            sys.exit(1)

def main():
    """Main entry point for the advanced CLI."""
    parser = argparse.ArgumentParser(
        description="KiCad PCB Generator Advanced CLI - For experienced users"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create project command
    create_parser = subparsers.add_parser("create", help="Create a new project with advanced options")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument(
        "--template",
        default="basic_audio_amp",
        help="Project template to use (default: basic_audio_amp)",
    )
    create_parser.add_argument(
        "--validation-rules",
        nargs="+",
        default=["signal_integrity", "power_ground", "emi_emc"],
        help="Validation rules to enable",
    )
    create_parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation mode",
    )
    create_parser.add_argument(
        "--custom-rules",
        type=str,
        help="Path to custom validation rules file",
    )
    create_parser.add_argument(
        "--auto-route",
        action="store_true",
        help="Enable automatic routing",
    )
    create_parser.add_argument(
        "--optimize",
        action="store_true",
        help="Enable layout optimization",
    )
    create_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing",
    )

    # Generate PCB command
    generate_parser = subparsers.add_parser("generate", help="Generate PCB with advanced options")
    generate_parser.add_argument(
        "project",
        help="Path to project directory or project name",
    )
    generate_parser.add_argument(
        "--override-config",
        type=json.loads,
        help="Override generation configuration (JSON string)",
    )

    # Export files command
    export_parser = subparsers.add_parser("export", help="Export files with advanced options")
    export_parser.add_argument(
        "project",
        help="Path to project directory or project name",
    )
    export_parser.add_argument(
        "--formats",
        nargs="+",
        default=["gerber", "drill", "bom"],
        help="Export formats",
    )
    export_parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for exported files",
    )
    export_parser.add_argument(
        "--include-3d",
        action="store_true",
        help="Include 3D models in export",
    )
    export_parser.add_argument(
        "--include-docs",
        action="store_true",
        help="Include documentation in export",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    cli = AdvancedCLI()
    if args.command == "create":
        cli.create_project(args)
    elif args.command == "generate":
        cli.generate_pcb(args)
    elif args.command == "export":
        cli.export_files(args)

if __name__ == "__main__":
    main() 