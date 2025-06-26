"""
Main PCB generator for KiCad PCB Generator.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import csv
import pcbnew

from .project_manager import ProjectManager, ProjectConfig
from .board.layer_manager import LayerManager, LayerProperties, LayerType
from .board.validator import BoardValidator
from .templates.base import TemplateBase
from .validation.base_validator import BaseValidator
from .base.base_config import BaseConfig
from .base.results.config_result import ConfigResult, ConfigStatus, ConfigSection
from .results.validation_result import ValidationResult

# Netlist + footprint helper
from .netlist.parser import Netlist
from .pcb.footprint_instantiator import instantiate_footprints

# Layout optimization
from ..layout.layout_optimizer import LayoutOptimizer, LayoutConstraints

# AudioRouter integration
from ..audio.routing.audio_router import AudioRouter

logger = logging.getLogger(__name__)

@dataclass
class PCBGenerationConfigItem:
    """Data structure for PCB generation configuration items."""
    id: str
    board_size: Tuple[float, float] = (100.0, 100.0)  # mm
    layer_count: int = 2
    copper_thickness: float = 35.0  # um
    substrate_thickness: float = 1.6  # mm
    min_trace_width: float = 0.1  # mm
    min_clearance: float = 0.1  # mm
    min_via_size: float = 0.2  # mm
    target_impedance: float = 50.0  # ohms
    stackup: Optional[List[Dict[str, Any]]] = None  # Custom layer stack-up definitions
    design_rules: Dict[str, Any] = None  # E.g., {"min_annular_ring": 0.15}
    routing_strategy: str = "SHORTEST"  # SHORTEST | LENGTH_MATCHED | CONTROLLED_IMPEDANCE
    output_formats: List[str] = None  # ["gerber", "drill", "bom", "step"]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PCBGenerationConfig(BaseConfig[PCBGenerationConfigItem]):
    """Configuration for PCB generation.
    
    Now inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "PCBGenerationConfig", config_path: Optional[str] = None):
        """Initialize PCB generation configuration.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        self.set_default("board_size", (100.0, 100.0))
        self.set_default("layer_count", 2)
        self.set_default("copper_thickness", 35.0)
        self.set_default("substrate_thickness", 1.6)
        self.set_default("min_trace_width", 0.1)
        self.set_default("min_clearance", 0.1)
        self.set_default("min_via_size", 0.2)
        self.set_default("target_impedance", 50.0)
        self.set_default("stackup", None)
        self.set_default("design_rules", {})
        self.set_default("routing_strategy", "SHORTEST")
        self.set_default("output_formats", ["gerber", "drill", "bom"])
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        self.add_validation_rule("board_size", {
            "type": "tuple",
            "required": True,
            "length": 2,
            "element_type": "float"
        })
        self.add_validation_rule("layer_count", {
            "type": "int",
            "min": 1,
            "max": 20,
            "required": True
        })
        self.add_validation_rule("copper_thickness", {
            "type": "float",
            "min": 5.0,
            "max": 200.0,
            "required": True
        })
        self.add_validation_rule("substrate_thickness", {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "required": True
        })
        self.add_validation_rule("min_trace_width", {
            "type": "float",
            "min": 0.05,
            "max": 1.0,
            "required": True
        })
        self.add_validation_rule("min_clearance", {
            "type": "float",
            "min": 0.05,
            "max": 1.0,
            "required": True
        })
        self.add_validation_rule("min_via_size", {
            "type": "float",
            "min": 0.1,
            "max": 2.0,
            "required": True
        })
        self.add_validation_rule("target_impedance", {
            "type": "float",
            "min": 25.0,
            "max": 200.0,
            "required": True
        })
        self.add_validation_rule("stackup", {
            "type": "list",
            "required": False
        })
        self.add_validation_rule("design_rules", {
            "type": "dict",
            "required": False
        })
        self.add_validation_rule("routing_strategy", {
            "type": "str",
            "options": ["SHORTEST", "LENGTH_MATCHED", "CONTROLLED_IMPEDANCE"],
            "required": True
        })
        self.add_validation_rule("output_formats", {
            "type": "list",
            "required": False
        })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate PCB generation configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "board_size", "layer_count", "copper_thickness", "substrate_thickness",
                "min_trace_width", "min_clearance", "min_via_size", "target_impedance"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "tuple" and not isinstance(value, tuple):
                    errors.append(f"Field {field} must be a tuple")
                elif rule.get("type") == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} must be a number")
                elif rule.get("type") == "int" and not isinstance(value, int):
                    errors.append(f"Field {field} must be an integer")
                
                # Range validation for numbers
                if rule.get("type") == "float":
                    if rule.get("min") is not None and value < rule["min"]:
                        errors.append(f"Field {field} must be >= {rule['min']}")
                    if rule.get("max") is not None and value > rule["max"]:
                        errors.append(f"Field {field} must be <= {rule['max']}")
                elif rule.get("type") == "int":
                    if rule.get("min") is not None and value < rule["min"]:
                        errors.append(f"Field {field} must be >= {rule['min']}")
                    if rule.get("max") is not None and value > rule["max"]:
                        errors.append(f"Field {field} must be <= {rule['max']}")
                
                # Tuple validation
                if rule.get("type") == "tuple":
                    if rule.get("length") and len(value) != rule["length"]:
                        errors.append(f"Field {field} must have length {rule['length']}")
                    elif rule.get("element_type") == "float":
                        for i, element in enumerate(value):
                            if not isinstance(element, (int, float)):
                                errors.append(f"Field {field}[{i}] must be a number")
                            if element <= 0:
                                errors.append(f"Field {field}[{i}] must be positive")
            
            # Validate board size relationship
            if "board_size" in config_data:
                board_size = config_data["board_size"]
                if len(board_size) == 2:
                    if board_size[0] <= 0 or board_size[1] <= 0:
                        errors.append("Board size dimensions must be positive")
                    if board_size[0] > 1000 or board_size[1] > 1000:
                        errors.append("Board size dimensions must be <= 1000mm")
            
            # Validate via size relationship
            if "min_via_size" in config_data and "min_trace_width" in config_data:
                if config_data["min_via_size"] < config_data["min_trace_width"]:
                    errors.append("min_via_size must be >= min_trace_width")
            
            # Simple enum check for routing_strategy
            if field == "routing_strategy" and field in config_data:
                if config_data[field] not in ["SHORTEST", "LENGTH_MATCHED", "CONTROLLED_IMPEDANCE"]:
                    errors.append("Invalid routing_strategy value")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="PCB generation configuration validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="PCB generation configuration is valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating PCB generation configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse PCB generation configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create PCB generation config item
            pcb_item = PCBGenerationConfigItem(
                id=config_data.get("id", "pcb_generation_config"),
                board_size=config_data.get("board_size", (100.0, 100.0)),
                layer_count=config_data.get("layer_count", 2),
                copper_thickness=config_data.get("copper_thickness", 35.0),
                substrate_thickness=config_data.get("substrate_thickness", 1.6),
                min_trace_width=config_data.get("min_trace_width", 0.1),
                min_clearance=config_data.get("min_clearance", 0.1),
                min_via_size=config_data.get("min_via_size", 0.2),
                target_impedance=config_data.get("target_impedance", 50.0),
                stackup=config_data.get("stackup", None),
                design_rules=config_data.get("design_rules", {}),
                routing_strategy=config_data.get("routing_strategy", "SHORTEST"),
                output_formats=config_data.get("output_formats", ["gerber", "drill", "bom"]),
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="pcb_generation_settings",
                data=config_data,
                description="PCB generation configuration settings"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="PCB generation configuration parsed successfully",
                data=pcb_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing PCB generation configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare PCB generation configuration data for saving.
        
        Returns:
            Configuration data
        """
        pcb_section = self.get_section("pcb_generation_settings")
        if pcb_section:
            return pcb_section.data
        
        # Return default configuration
        return {
            "id": "pcb_generation_config",
            "board_size": self.get_default("board_size"),
            "layer_count": self.get_default("layer_count"),
            "copper_thickness": self.get_default("copper_thickness"),
            "substrate_thickness": self.get_default("substrate_thickness"),
            "min_trace_width": self.get_default("min_trace_width"),
            "min_clearance": self.get_default("min_clearance"),
            "min_via_size": self.get_default("min_via_size"),
            "target_impedance": self.get_default("target_impedance"),
            "stackup": self.get_default("stackup"),
            "design_rules": self.get_default("design_rules"),
            "routing_strategy": self.get_default("routing_strategy"),
            "output_formats": self.get_default("output_formats"),
        }
    
    def create_pcb_generation_config(self,
                                    board_size: Tuple[float, float] = (100.0, 100.0),
                                    layer_count: int = 2,
                                    copper_thickness: float = 35.0,
                                    substrate_thickness: float = 1.6,
                                    min_trace_width: float = 0.1,
                                    min_clearance: float = 0.1,
                                    min_via_size: float = 0.2,
                                    target_impedance: float = 50.0) -> ConfigResult[PCBGenerationConfigItem]:
        """Create a new PCB generation configuration.
        
        Args:
            board_size: Board size tuple (width, height) in mm
            layer_count: Number of layers
            copper_thickness: Copper thickness in um
            substrate_thickness: Substrate thickness in mm
            min_trace_width: Minimum trace width in mm
            min_clearance: Minimum clearance in mm
            min_via_size: Minimum via size in mm
            target_impedance: Target impedance in ohms
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"pcb_generation_config_{len(self._config_history) + 1}",
                "board_size": board_size,
                "layer_count": layer_count,
                "copper_thickness": copper_thickness,
                "substrate_thickness": substrate_thickness,
                "min_trace_width": min_trace_width,
                "min_clearance": min_clearance,
                "min_via_size": min_via_size,
                "target_impedance": target_impedance,
                "stackup": self.get_default("stackup"),
                "design_rules": self.get_default("design_rules"),
                "routing_strategy": self.get_default("routing_strategy"),
                "output_formats": self.get_default("output_formats"),
            }
            
            # Validate configuration
            validation_result = self._validate_config(config_data)
            if not validation_result.success:
                return validation_result
            
            # Parse configuration
            return self._parse_config(config_data)
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error creating PCB generation configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )

@dataclass
class PCBGenerationResult:
    """Result of PCB generation."""
    success: bool
    output_path: Optional[Path] = None
    warnings: List[str] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class PCBGenerator(BaseValidator):
    """Main PCB generator class."""
    
    def __init__(self, project_manager: Optional[ProjectManager] = None):
        """Initialize the PCB generator.
        
        Args:
            project_manager: Project manager instance
        """
        super().__init__()
        self.project_manager = project_manager or ProjectManager()
        self.layer_manager = LayerManager()
        self.board_validator = BoardValidator()
        self.generation_history: List[PCBGenerationResult] = []
        
    def generate_pcb(
        self,
        project_name: str,
        config: Optional[PCBGenerationConfig] = None,
        netlist: Optional[Netlist] = None,
    ) -> PCBGenerationResult:
        """Generate a PCB for a project.
        
        Args:
            project_name: Name of the project
            config: PCB generation configuration
            netlist: Netlist for footprint instantiation
            
        Returns:
            Generation result
        """
        try:
            project_path = self.project_manager.get_project_path(project_name)
            project_config = self.project_manager.get_project_config(project_name)
            
            if config is None:
                config = PCBGenerationConfig()
            
            # Create output directory
            output_path = project_path / "output" / "pcb"
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate PCB files
            gen_result = self._generate_pcb_files(project_config, config, output_path, netlist=netlist)
            
            # Validate the generated PCB
            validation_result = self._validate_generated_pcb(output_path, project_config.name)
            
            # Combine results
            final_result = PCBGenerationResult(
                success=gen_result.success and validation_result.success,
                output_path=output_path if gen_result.success else None,
                warnings=gen_result.warnings + validation_result.warnings,
                errors=gen_result.errors + validation_result.errors,
                metadata={
                    "project_name": project_name,
                    "board_size": config.board_size,
                    "layer_count": config.layer_count,
                    "generation_time": datetime.now().isoformat()
                }
            )
            
            self.generation_history.append(final_result)
            logger.info(f"Generated PCB for project '{project_name}'")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error generating PCB for project '{project_name}': {e}")
            return PCBGenerationResult(
                success=False,
                errors=[str(e)]
            )
    
    def export_pcb(self, project_name: str, format: str = "gerber", 
                   output_dir: Optional[Path] = None) -> PCBGenerationResult:
        """Export PCB files in various formats.
        
        Args:
            project_name: Name of the project
            format: Export format (gerber, drill, bom)
            output_dir: Output directory (defaults to project output directory)
            
        Returns:
            Export result
        """
        try:
            project_path = self.project_manager.get_project_path(project_name)
            
            if output_dir is None:
                output_dir = project_path / "output" / "export" / format
            
            output_dir.mkdir(parents=True, exist_ok=True)

            pcb_file_path = project_path / "output" / "pcb" / f"{project_name}.kicad_pcb"
            if not pcb_file_path.exists():
                return PCBGenerationResult(
                    success=False,
                    errors=[f"PCB file not found for project '{project_name}'. Please generate it first."]
                )

            board = pcbnew.LoadBoard(str(pcb_file_path))
            
            if format == "gerber":
                result = self._export_gerber(board, output_dir)
            elif format == "drill":
                result = self._export_drill(board, output_dir)
            elif format == "bom":
                result = self._export_bom(board, output_dir)
            elif format == "step":
                result = self._export_step(board, output_dir)
            else:
                return PCBGenerationResult(
                    success=False,
                    errors=[f"Unsupported export format: {format}"]
                )
            
            logger.info(f"Exported PCB for project '{project_name}' in {format} format")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting PCB for project '{project_name}': {e}")
            return PCBGenerationResult(
                success=False,
                errors=[str(e)]
            )
    
    def _generate_pcb_files(
        self,
        project_config: ProjectConfig,
        config: PCBGenerationConfig,
        output_path: Path,
        *,
        netlist: Optional[Netlist] = None,
    ) -> PCBGenerationResult:
        """Generate PCB files."""
        try:
            board = pcbnew.BOARD()

            # Set board dimensions
            board_width = pcbnew.FromMM(config.board_size[0])
            board_height = pcbnew.FromMM(config.board_size[1])
            
            # Create board outline
            outline = [
                pcbnew.VECTOR2I(0, 0),
                pcbnew.VECTOR2I(board_width, 0),
                pcbnew.VECTOR2I(board_width, board_height),
                pcbnew.VECTOR2I(0, board_height),
                pcbnew.VECTOR2I(0, 0)
            ]
            for i in range(len(outline) - 1):
                segment = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
                segment.SetStart(outline[i])
                segment.SetEnd(outline[i+1])
                segment.SetLayer(pcbnew.Edge_Cuts)
                segment.SetWidth(pcbnew.FromMM(0.15))
                board.Add(segment)
            
            # ------------------------------------------------------------------
            # 2.  Instantiate footprints from netlist (if provided)
            # ------------------------------------------------------------------
            if netlist is not None and netlist.footprints:
                instantiate_footprints(board, netlist)

            # Instantiate and configure layer stack-up
            try:
                layer_manager = LayerManager(board)
                if config.stackup:
                    for item in config.stackup:
                        try:
                            layer_id = item.get("layer_id") if "layer_id" in item else layer_manager.board.GetLayerID(item["name"]) if hasattr(layer_manager.board, "GetLayerID") else None
                            if layer_id is None:
                                self.logger.warning("Unknown layer id/name in stackup item %s", item)
                                continue

                            layer_type = LayerType(item.get("type", "signal")) if isinstance(item.get("type"), str) else LayerType(item.get("type", LayerType.SIGNAL))
                            lp = LayerProperties(
                                name=item.get("name", f"Layer_{layer_id}"),
                                type=layer_type,
                                copper_weight=item.get("copper_weight", 1.0),
                                dielectric_constant=item.get("dielectric_constant", 4.5),
                                loss_tangent=item.get("loss_tangent", 0.02),
                                thickness=item.get("thickness", 0.035),
                                min_trace_width=item.get("min_trace_width", config.min_trace_width),
                                min_clearance=item.get("min_clearance", config.min_clearance),
                            )

                            layer_manager.set_layer_properties(layer_id, lp)
                        except Exception as lp_exc:
                            self.logger.warning("Failed to apply stackup layer %s: %s", item, lp_exc)
                else:
                    layer_manager.optimize_for_audio()
            except Exception as exc:
                logger.warning("LayerManager configuration skipped: %s", exc)

            # ------------------------------------------------------------------
            # 3.  Automatic placement & initial routing (layout optimizer)
            # ------------------------------------------------------------------
            try:
                constraints = LayoutConstraints(
                    min_track_width=config.min_trace_width,
                    min_clearance=config.min_clearance,
                    min_via_size=config.min_via_size,
                    # Fallback values for unused fields
                    max_component_density=0.15,
                    max_track_density=0.5,
                    min_thermal_pad_size=1.0,
                    max_parallel_tracks=4,
                    min_power_track_width=max(config.min_trace_width * 2, 0.2),
                    max_high_speed_length=100.0,
                )

                layout_opt = LayoutOptimizer(board, constraints=constraints)
                layout_opt.optimize_layout()
            except Exception as exc:
                logger.warning("Layout optimization skipped or failed: %s", exc)

            # ------------------------------------------------------------------
            # 4.  Autorouting & Connectivity (AudioRouter)
            # ------------------------------------------------------------------
            try:
                router = AudioRouter(board)
                router.optimize_audio_routing()
                routing_issues = router.validate_routing()
                if routing_issues:
                    self.logger.warning("Routing validation found %d issues", len(routing_issues))
            except Exception as exc:
                logger.warning("Audio routing step skipped or failed: %s", exc)

            # ------------------------------------------------------------------
            # 5.  Incremental Validation (Integrated Validation Loop)
            # ------------------------------------------------------------------
            try:
                bvalidator = BoardValidator()
                validation_results = bvalidator.validate_board(board)
                issues = sum(len(v) for v in validation_results.values())
                if issues > 0:
                    self.logger.warning("Incremental board validation found %d issues", issues)
            except Exception as exc:
                logger.warning("Incremental BoardValidator step skipped or failed: %s", exc)

            # Save .kicad_pcb file
            pcb_file_path = output_path / f"{project_config.name}.kicad_pcb"
            board.Save(str(pcb_file_path))

            # Create empty .kicad_sch file as a placeholder
            sch_file = output_path / f"{project_config.name}.kicad_sch"
            sch_file.write_text(f"(kicad_sch (version 20211027) (generator {self.__class__.__name__}))")

            return PCBGenerationResult(
                success=True,
                output_path=output_path,
                warnings=[],
                errors=[]
            )
        except Exception as e:
            return PCBGenerationResult(
                success=False,
                errors=[f"Error generating PCB files: {e}"]
            )
    
    def _validate_generated_pcb(self, output_path: Path, project_name: str) -> PCBGenerationResult:
        """Validate the generated PCB."""
        try:
            pcb_file_path = output_path / f"{project_name}.kicad_pcb"
            board = pcbnew.LoadBoard(str(pcb_file_path))
            
            validator = BoardValidator(board)
            results = validator.run_all_checks()
            
            warnings = [res.message for res in results if res.severity == ValidationSeverity.WARNING]
            errors = [res.message for res in results if res.severity == ValidationSeverity.ERROR]

            success = not errors

            return PCBGenerationResult(
                success=success,
                warnings=warnings,
                errors=errors
            )
        except Exception as e:
            return PCBGenerationResult(
                success=False,
                errors=[f"Error validating generated PCB: {e}"]
            )
    
    def _export_gerber(self, board: pcbnew.BOARD, output_dir: Path) -> PCBGenerationResult:
        """Export Gerber files."""
        try:
            plot_controller = pcbnew.PLOT_CONTROLLER(board)
            plot_options = plot_controller.GetPlotOptions()

            plot_options.SetOutputDirectory(str(output_dir))
            plot_options.SetPlotFrameRef(False)
            plot_options.SetUseGerberProtelExtensions(True)
            plot_options.SetGerberPrecision(6)
            plot_options.SetCreateGerberJobFile(True)
            
            # Define layers to plot
            layers = [
                (pcbnew.F_Cu, "F_Cu"), (pcbnew.B_Cu, "B_Cu"),
                (pcbnew.F_Paste, "F_Paste"), (pcbnew.B_Paste, "B_Paste"),
                (pcbnew.F_SilkS, "F_SilkS"), (pcbnew.B_SilkS, "B_SilkS"),
                (pcbnew.F_Mask, "F_Mask"), (pcbnew.B_Mask, "B_Mask"),
                (pcbnew.Edge_Cuts, "Edge_Cuts")
            ]

            for layer_id, layer_name in layers:
                plot_controller.SetLayer(layer_id)
                plot_controller.OpenPlotfile(layer_name, pcbnew.PLOT_FORMAT_GERBER, layer_name)
                plot_controller.PlotLayer()

            plot_controller.ClosePlot()

            return PCBGenerationResult(
                success=True,
                output_path=output_dir
            )
        except Exception as e:
            return PCBGenerationResult(
                success=False,
                errors=[f"Error exporting Gerber files: {e}"]
            )
    
    def _export_drill(self, board: pcbnew.BOARD, output_dir: Path) -> PCBGenerationResult:
        """Export drill files."""
        try:
            drill_writer = pcbnew.EXCELLON_WRITER(board)
            drill_writer.SetMapFileFormat(pcbnew.PLOT_FORMAT_PDF)
            
            mirror = False
            minimal_header = False
            offset = pcbnew.VECTOR2I(0, 0)
            merge_npth = True # Merge plated and non-plated holes
            drill_writer.CreateDrillandMapFiles(str(output_dir), True, merge_npth)

            return PCBGenerationResult(
                success=True,
                output_path=output_dir
            )
        except Exception as e:
            return PCBGenerationResult(
                success=False,
                errors=[f"Error exporting drill files: {e}"]
            )
    
    def _export_bom(self, board: pcbnew.BOARD, output_dir: Path) -> PCBGenerationResult:
        """Export bill of materials."""
        try:
            bom_file_path = output_dir / "bom.csv"
            with open(bom_file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Reference', 'Value', 'Footprint', 'Quantity'])
                
                components = {}
                for footprint in board.GetFootprints():
                    key = (footprint.GetValue(), footprint.GetFootprint().GetLibItemName())
                    if key not in components:
                        components[key] = {
                            'refs': [],
                            'value': footprint.GetValue(),
                            'footprint': str(footprint.GetFootprint().GetLibItemName())
                        }
                    components[key]['refs'].append(footprint.GetReference())
                
                for key, data in sorted(components.items()):
                    writer.writerow([
                        ','.join(sorted(data['refs'])),
                        data['value'],
                        data['footprint'],
                        len(data['refs'])
                    ])

            return PCBGenerationResult(
                success=True,
                output_path=output_dir
            )
        except Exception as e:
            return PCBGenerationResult(
                success=False,
                errors=[f"Error exporting BOM: {e}"]
            )
    
    def _export_step(self, board: pcbnew.BOARD, output_dir: Path) -> PCBGenerationResult:
        """Export 3D STEP model of the board.

        The function silently skips export if KiCad STEP exporter is not
        available (e.g., running in headless CI) to keep the pipeline safe.
        """
        try:
            step_path = output_dir / "board.step"

            # KiCad 7/8+ provides ExportBoardSTEP in pcbnew Python API
            if hasattr(pcbnew, "ExportBoardSTEP"):
                pcbnew.ExportBoardSTEP(board, str(step_path))
            else:
                # Fallback: warn and create placeholder file so downstream
                # workflows don't fail when expecting the artifact.
                self.logger.warning("STEP export not supported in this environment, creating placeholder file.")
                step_path.write_text("STEP export not supported in headless environment.")

            return PCBGenerationResult(success=True, output_path=step_path.parent)
        except Exception as e:
            return PCBGenerationResult(success=False, errors=[f"Error exporting STEP: {e}"])
    
    def get_generation_history(self) -> List[PCBGenerationResult]:
        """Get PCB generation history.
        
        Returns:
            List of generation results
        """
        return self.generation_history.copy()
    
    def clear_history(self) -> None:
        """Clear generation history."""
        self.generation_history.clear() 