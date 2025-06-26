"""
Output manager for KiCad PCB Generator.
Handles manufacturing output generation and 3D visualization.
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

import pcbnew

from ..base.base_manager import BaseManager
from ..base.base_config import BaseConfig
from ..base.results.manager_result import ManagerResult
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigSection

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

@dataclass
class OutputConfigItem:
    """Data structure for output configuration items."""
    id: str
    output_dir: str
    gerber_format: str = "RS274X"  # RS274X or RS274D
    drill_format: str = "EXCELLON"  # EXCELLON or GERBER
    include_3d_models: bool = True
    generate_3d_visualization: bool = True
    generate_pdf: bool = True
    generate_bom: bool = True
    generate_pick_and_place: bool = True
    generate_drill_files: bool = True
    generate_gerber_files: bool = True
    generate_3d_step: bool = True
    generate_3d_gltf: bool = True
    generate_3d_obj: bool = True
    generate_3d_stl: bool = True
    generate_3d_wrl: bool = True
    generate_3d_x3d: bool = True
    generate_3d_x3dv: bool = True
    generate_3d_x3db: bool = True
    generate_3d_x3dz: bool = True
    generate_3d_x3dvz: bool = True
    generate_3d_x3dbz: bool = True
    generate_3d_x3dzip: bool = True
    generate_3d_x3dvzip: bool = True
    generate_3d_x3dbzip: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class OutputConfig(BaseConfig[OutputConfigItem]):
    """Configuration for manufacturing output generation.
    
    Now inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "OutputConfig", config_path: Optional[str] = None):
        """Initialize output configuration.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        self.set_default("output_dir", "./output")
        self.set_default("gerber_format", "RS274X")
        self.set_default("drill_format", "EXCELLON")
        self.set_default("include_3d_models", True)
        self.set_default("generate_3d_visualization", True)
        self.set_default("generate_pdf", True)
        self.set_default("generate_bom", True)
        self.set_default("generate_pick_and_place", True)
        self.set_default("generate_drill_files", True)
        self.set_default("generate_gerber_files", True)
        self.set_default("generate_3d_step", True)
        self.set_default("generate_3d_gltf", True)
        self.set_default("generate_3d_obj", True)
        self.set_default("generate_3d_stl", True)
        self.set_default("generate_3d_wrl", True)
        self.set_default("generate_3d_x3d", True)
        self.set_default("generate_3d_x3dv", True)
        self.set_default("generate_3d_x3db", True)
        self.set_default("generate_3d_x3dz", True)
        self.set_default("generate_3d_x3dvz", True)
        self.set_default("generate_3d_x3dbz", True)
        self.set_default("generate_3d_x3dzip", True)
        self.set_default("generate_3d_x3dvzip", True)
        self.set_default("generate_3d_x3dbzip", True)
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        self.add_validation_rule("output_dir", {
            "type": "str",
            "required": True,
            "min_length": 1
        })
        self.add_validation_rule("gerber_format", {
            "type": "str",
            "required": True,
            "allowed_values": ["RS274X", "RS274D"]
        })
        self.add_validation_rule("drill_format", {
            "type": "str",
            "required": True,
            "allowed_values": ["EXCELLON", "GERBER"]
        })
        self.add_validation_rule("include_3d_models", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("generate_3d_visualization", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("generate_pdf", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("generate_bom", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("generate_pick_and_place", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("generate_drill_files", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("generate_gerber_files", {
            "type": "bool",
            "required": True
        })
        # Add validation rules for all 3D generation options
        for field in ["generate_3d_step", "generate_3d_gltf", "generate_3d_obj", 
                     "generate_3d_stl", "generate_3d_wrl", "generate_3d_x3d",
                     "generate_3d_x3dv", "generate_3d_x3db", "generate_3d_x3dz",
                     "generate_3d_x3dvz", "generate_3d_x3dbz", "generate_3d_x3dzip",
                     "generate_3d_x3dvzip", "generate_3d_x3dbzip"]:
            self.add_validation_rule(field, {
                "type": "bool",
                "required": True
            })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate output configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "output_dir", "gerber_format", "drill_format", "include_3d_models",
                "generate_3d_visualization", "generate_pdf", "generate_bom",
                "generate_pick_and_place", "generate_drill_files", "generate_gerber_files"
            ]
            
            # Add 3D generation fields
            for field in ["generate_3d_step", "generate_3d_gltf", "generate_3d_obj", 
                         "generate_3d_stl", "generate_3d_wrl", "generate_3d_x3d",
                         "generate_3d_x3dv", "generate_3d_x3db", "generate_3d_x3dz",
                         "generate_3d_x3dvz", "generate_3d_x3dbz", "generate_3d_x3dzip",
                         "generate_3d_x3dvzip", "generate_3d_x3dbzip"]:
                required_fields.append(field)
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "str" and not isinstance(value, str):
                    errors.append(f"Field {field} must be a string")
                elif rule.get("type") == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                
                # String validation
                if rule.get("type") == "str":
                    if rule.get("min_length") and len(value) < rule["min_length"]:
                        errors.append(f"Field {field} must have minimum length {rule['min_length']}")
                    if rule.get("allowed_values") and value not in rule["allowed_values"]:
                        errors.append(f"Field {field} must be one of {rule['allowed_values']}")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="Output configuration validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="Output configuration is valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating output configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse output configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create output config item
            output_item = OutputConfigItem(
                id=config_data.get("id", "output_config"),
                output_dir=config_data.get("output_dir", "./output"),
                gerber_format=config_data.get("gerber_format", "RS274X"),
                drill_format=config_data.get("drill_format", "EXCELLON"),
                include_3d_models=config_data.get("include_3d_models", True),
                generate_3d_visualization=config_data.get("generate_3d_visualization", True),
                generate_pdf=config_data.get("generate_pdf", True),
                generate_bom=config_data.get("generate_bom", True),
                generate_pick_and_place=config_data.get("generate_pick_and_place", True),
                generate_drill_files=config_data.get("generate_drill_files", True),
                generate_gerber_files=config_data.get("generate_gerber_files", True),
                generate_3d_step=config_data.get("generate_3d_step", True),
                generate_3d_gltf=config_data.get("generate_3d_gltf", True),
                generate_3d_obj=config_data.get("generate_3d_obj", True),
                generate_3d_stl=config_data.get("generate_3d_stl", True),
                generate_3d_wrl=config_data.get("generate_3d_wrl", True),
                generate_3d_x3d=config_data.get("generate_3d_x3d", True),
                generate_3d_x3dv=config_data.get("generate_3d_x3dv", True),
                generate_3d_x3db=config_data.get("generate_3d_x3db", True),
                generate_3d_x3dz=config_data.get("generate_3d_x3dz", True),
                generate_3d_x3dvz=config_data.get("generate_3d_x3dvz", True),
                generate_3d_x3dbz=config_data.get("generate_3d_x3dbz", True),
                generate_3d_x3dzip=config_data.get("generate_3d_x3dzip", True),
                generate_3d_x3dvzip=config_data.get("generate_3d_x3dvzip", True),
                generate_3d_x3dbzip=config_data.get("generate_3d_x3dbzip", True)
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="output_settings",
                data=config_data,
                description="Manufacturing output configuration settings"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="Output configuration parsed successfully",
                data=output_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing output configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare output configuration data for saving.
        
        Returns:
            Configuration data
        """
        output_section = self.get_section("output_settings")
        if output_section:
            return output_section.data
        
        # Return default configuration
        return {
            "id": "output_config",
            "output_dir": self.get_default("output_dir"),
            "gerber_format": self.get_default("gerber_format"),
            "drill_format": self.get_default("drill_format"),
            "include_3d_models": self.get_default("include_3d_models"),
            "generate_3d_visualization": self.get_default("generate_3d_visualization"),
            "generate_pdf": self.get_default("generate_pdf"),
            "generate_bom": self.get_default("generate_bom"),
            "generate_pick_and_place": self.get_default("generate_pick_and_place"),
            "generate_drill_files": self.get_default("generate_drill_files"),
            "generate_gerber_files": self.get_default("generate_gerber_files"),
            "generate_3d_step": self.get_default("generate_3d_step"),
            "generate_3d_gltf": self.get_default("generate_3d_gltf"),
            "generate_3d_obj": self.get_default("generate_3d_obj"),
            "generate_3d_stl": self.get_default("generate_3d_stl"),
            "generate_3d_wrl": self.get_default("generate_3d_wrl"),
            "generate_3d_x3d": self.get_default("generate_3d_x3d"),
            "generate_3d_x3dv": self.get_default("generate_3d_x3dv"),
            "generate_3d_x3db": self.get_default("generate_3d_x3db"),
            "generate_3d_x3dz": self.get_default("generate_3d_x3dz"),
            "generate_3d_x3dvz": self.get_default("generate_3d_x3dvz"),
            "generate_3d_x3dbz": self.get_default("generate_3d_x3dbz"),
            "generate_3d_x3dzip": self.get_default("generate_3d_x3dzip"),
            "generate_3d_x3dvzip": self.get_default("generate_3d_x3dvzip"),
            "generate_3d_x3dbzip": self.get_default("generate_3d_x3dbzip")
        }
    
    def create_output_config(self, 
                            output_dir: str = "./output",
                            gerber_format: str = "RS274X",
                            drill_format: str = "EXCELLON",
                            include_3d_models: bool = True,
                            generate_3d_visualization: bool = True,
                            generate_pdf: bool = True,
                            generate_bom: bool = True,
                            generate_pick_and_place: bool = True,
                            generate_drill_files: bool = True,
                            generate_gerber_files: bool = True,
                            **kwargs) -> ConfigResult[OutputConfigItem]:
        """Create a new output configuration.
        
        Args:
            output_dir: Output directory path
            gerber_format: Gerber format (RS274X or RS274D)
            drill_format: Drill format (EXCELLON or GERBER)
            include_3d_models: Whether to include 3D models
            generate_3d_visualization: Whether to generate 3D visualization
            generate_pdf: Whether to generate PDF
            generate_bom: Whether to generate BOM
            generate_pick_and_place: Whether to generate pick and place
            generate_drill_files: Whether to generate drill files
            generate_gerber_files: Whether to generate Gerber files
            **kwargs: Additional 3D generation options
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"output_config_{len(self._config_history) + 1}",
                "output_dir": output_dir,
                "gerber_format": gerber_format,
                "drill_format": drill_format,
                "include_3d_models": include_3d_models,
                "generate_3d_visualization": generate_3d_visualization,
                "generate_pdf": generate_pdf,
                "generate_bom": generate_bom,
                "generate_pick_and_place": generate_pick_and_place,
                "generate_drill_files": generate_drill_files,
                "generate_gerber_files": generate_gerber_files
            }
            
            # Add 3D generation options from kwargs or defaults
            for field in ["generate_3d_step", "generate_3d_gltf", "generate_3d_obj", 
                         "generate_3d_stl", "generate_3d_wrl", "generate_3d_x3d",
                         "generate_3d_x3dv", "generate_3d_x3db", "generate_3d_x3dz",
                         "generate_3d_x3dvz", "generate_3d_x3dbz", "generate_3d_x3dzip",
                         "generate_3d_x3dvzip", "generate_3d_x3dbzip"]:
                config_data[field] = kwargs.get(field, self.get_default(field))
            
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
                message=f"Error creating output configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )

@dataclass
class OutputItem:
    """Data structure for output items."""
    id: str
    input_file: str
    config: OutputConfig
    output_files: Dict[str, str]
    status: str = "pending"  # pending, processing, completed, failed
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

class OutputManager(BaseManager[OutputItem]):
    """Manages manufacturing output generation and 3D visualization."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the output manager."""
        super().__init__(logger=logger or logging.getLogger(__name__))
        self._validate_gerber2blend_installation()
    
    def _validate_data(self, item: OutputItem) -> bool:
        """Validate output item data."""
        if not item.id or not isinstance(item.id, str):
            self.logger.error("Output item must have a valid string ID")
            return False
        
        if not item.input_file or not isinstance(item.input_file, str):
            self.logger.error("Output item must have a valid input file path")
            return False
        
        if not Path(item.input_file).exists():
            self.logger.error(f"Input file does not exist: {item.input_file}")
            return False
        
        if not item.config or not isinstance(item.config, OutputConfig):
            self.logger.error("Output item must have a valid OutputConfig")
            return False
        
        if not item.config.output_dir or not isinstance(item.config.output_dir, str):
            self.logger.error("OutputConfig must have a valid output directory")
            return False
        
        return True
    
    def _cleanup_item(self, item: OutputItem) -> None:
        """Clean up output item resources."""
        try:
            # Clean up generated files if needed
            if item.output_files:
                for file_path in item.output_files.values():
                    if Path(file_path).exists():
                        Path(file_path).unlink()
                        self.logger.debug(f"Cleaned up output file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Error during output item cleanup: {str(e)}")
    
    def _clear_cache(self) -> None:
        """Clear output manager cache."""
        try:
            # Clear any cached board objects or temporary files
            self.logger.debug("Cleared output manager cache")
        except Exception as e:
            self.logger.warning(f"Error clearing output manager cache: {str(e)}")
    
    def create_output_job(self, 
                         input_file: str, 
                         config: OutputConfig) -> ManagerResult[OutputItem]:
        """Create a new output generation job."""
        try:
            output_id = f"output_{len(self._items) + 1}"
            output_item = OutputItem(
                id=output_id,
                input_file=input_file,
                config=config,
                output_files={},
                status="pending"
            )
            
            result = self.create(output_item)
            if result.success:
                self.logger.info(f"Created output job: {output_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating output job: {str(e)}")
            return ManagerResult[OutputItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def generate_output(self, 
                       input_file: str, 
                       config: OutputConfig) -> Dict[str, str]:
        """
        Generate manufacturing output files.
        
        Args:
            input_file: Path to input KiCad board file
            config: Output configuration
            
        Returns:
            Dict[str, str]: Dictionary of generated output files
        """
        try:
            # Validate input file
            if not Path(input_file).exists():
                self.logger.error(f"Input file not found: {input_file}")
                return {}
            
            output_files = {}
            
            # Generate Gerber files
            if config.generate_gerber_files:
                gerber_files = self._generate_gerber_files(input_file, config)
                output_files.update(gerber_files)
            
            # Generate drill files
            if config.generate_drill_files:
                drill_files = self._generate_drill_files(input_file, config)
                output_files.update(drill_files)
            
            # Generate 3D visualization
            if config.generate_3d_visualization:
                visualization_files = self._generate_3d_visualization(input_file, config)
                output_files.update(visualization_files)
            
            # Generate PDF
            if config.generate_pdf:
                pdf_file = self._generate_pdf(input_file, config)
                if pdf_file:
                    output_files["pdf"] = pdf_file
            
            # Generate BOM
            if config.generate_bom:
                bom_file = self._generate_bom(input_file, config)
                if bom_file:
                    output_files["bom"] = bom_file
            
            # Generate pick and place
            if config.generate_pick_and_place:
                pick_and_place_file = self._generate_pick_and_place(input_file, config)
                if pick_and_place_file:
                    output_files["pick_and_place"] = pick_and_place_file
            
            return output_files
            
        except Exception as e:
            self.logger.error(f"Error during output generation: {str(e)}")
            return {}
    
    def process_output_job(self, output_id: str) -> ManagerResult[OutputItem]:
        """Process an output generation job."""
        try:
            # Get the output item
            result = self.get(output_id)
            if not result.success or not result.data:
                return ManagerResult[OutputItem](
                    success=False,
                    error_message=f"Output job not found: {output_id}",
                    data=None
                )
            
            output_item = result.data
            
            # Update status to processing
            output_item.status = "processing"
            self.update(output_item)
            
            # Generate output files
            output_files = self.generate_output(output_item.input_file, output_item.config)
            
            # Update output item with results
            output_item.output_files = output_files
            output_item.status = "completed" if output_files else "failed"
            if not output_files:
                output_item.error_message = "No output files were generated"
            
            # Update the item
            update_result = self.update(output_item)
            if update_result.success:
                self.logger.info(f"Processed output job: {output_id}")
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"Error processing output job {output_id}: {str(e)}")
            return ManagerResult[OutputItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def get_output_files(self, output_id: str) -> ManagerResult[Dict[str, str]]:
        """Get output files for a specific job."""
        try:
            result = self.get(output_id)
            if not result.success or not result.data:
                return ManagerResult[Dict[str, str]](
                    success=False,
                    error_message=f"Output job not found: {output_id}",
                    data=None
                )
            
            return ManagerResult[Dict[str, str]](
                success=True,
                data=result.data.output_files
            )
            
        except Exception as e:
            self.logger.error(f"Error getting output files for {output_id}: {str(e)}")
            return ManagerResult[Dict[str, str]](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def _validate_gerber2blend_installation(self) -> bool:
        """Validate gerber2blend installation."""
        try:
            result = subprocess.run(["gerber2blend", "--version"], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode != 0:
                self.logger.error("gerber2blend is not properly installed")
                return False
            self.logger.info(f"gerber2blend version: {result.stdout.strip()}")
            return True
        except Exception as e:
            self.logger.error(f"Error validating gerber2blend installation: {str(e)}")
            return False
    
    def _generate_gerber_files(self, 
                             input_file: str, 
                             config: OutputConfig) -> Dict[str, str]:
        """Generate Gerber files."""
        try:
            # Load board
            board = pcbnew.LoadBoard(input_file)
            
            # Set up plot controller
            plot_controller = pcbnew.PLOT_CONTROLLER(board)
            plot_options = plot_controller.GetPlotOptions()
            
            # Configure plot options
            plot_options.SetOutputDirectory(config.output_dir)
            plot_options.SetFormat(pcbnew.PLOT_FORMAT_GERBER)
            plot_options.SetGerberPrecision(6)  # 6 decimal places
            plot_options.SetGerberFormat(config.gerber_format)
            plot_options.SetIncludeGerberNetlistInfo(True)
            plot_options.SetIncludeGerberAttributes(True)
            plot_options.SetIncludeGerberX2Attributes(True)
            plot_options.SetIncludeGerberX2NetAttributes(True)
            plot_options.SetIncludeGerberX2ComponentAttributes(True)
            plot_options.SetIncludeGerberX2PadAttributes(True)
            plot_options.SetIncludeGerberX2ViaAttributes(True)
            plot_options.SetIncludeGerberX2TrackAttributes(True)
            plot_options.SetIncludeGerberX2ZoneAttributes(True)
            plot_options.SetIncludeGerberX2TextAttributes(True)
            plot_options.SetIncludeGerberX2GraphicAttributes(True)
            plot_options.SetIncludeGerberX2DimensionAttributes(True)
            plot_options.SetIncludeGerberX2TargetAttributes(True)
            plot_options.SetIncludeGerberX2ReferenceAttributes(True)
            plot_options.SetIncludeGerberX2ValueAttributes(True)
            plot_options.SetIncludeGerberX2FootprintAttributes(True)
            plot_options.SetIncludeGerberX2NetAttributes(True)
            plot_options.SetIncludeGerberX2ComponentAttributes(True)
            plot_options.SetIncludeGerberX2PadAttributes(True)
            plot_options.SetIncludeGerberX2ViaAttributes(True)
            plot_options.SetIncludeGerberX2TrackAttributes(True)
            plot_options.SetIncludeGerberX2ZoneAttributes(True)
            plot_options.SetIncludeGerberX2TextAttributes(True)
            plot_options.SetIncludeGerberX2GraphicAttributes(True)
            plot_options.SetIncludeGerberX2DimensionAttributes(True)
            plot_options.SetIncludeGerberX2TargetAttributes(True)
            plot_options.SetIncludeGerberX2ReferenceAttributes(True)
            plot_options.SetIncludeGerberX2ValueAttributes(True)
            plot_options.SetIncludeGerberX2FootprintAttributes(True)
            
            # Generate Gerber files for each layer
            output_files = {}
            for layer in pcbnew.LSET.AllCuMask().Seq():
                layer_name = pcbnew.BOARD_GetStandardLayerName(layer)
                plot_controller.SetLayer(layer)
                plot_controller.OpenPlotfile(layer_name, pcbnew.PLOT_FORMAT_GERBER, layer_name)
                plot_controller.PlotLayer()
                output_files[layer_name] = str(Path(config.output_dir) / f"{layer_name}.gbr")
            
            return output_files
            
        except Exception as e:
            self.logger.error(f"Error generating Gerber files: {str(e)}")
            return {}
    
    def _generate_drill_files(self, 
                            input_file: str, 
                            config: OutputConfig) -> Dict[str, str]:
        """Generate drill files."""
        try:
            # Load board
            board = pcbnew.LoadBoard(input_file)
            
            # Set up drill writer
            drill_writer = pcbnew.EXCELLON_WRITER(board)
            drill_writer.SetMapFileFormat(pcbnew.PLOT_FORMAT_GERBER)
            
            # Generate drill files
            drill_writer.CreateDrillandMapFilesSet(config.output_dir, True, False)
            
            return {
                "drill": str(Path(config.output_dir) / "drill.drl"),
                "drill_map": str(Path(config.output_dir) / "drill_map.gbr")
            }
            
        except Exception as e:
            self.logger.error(f"Error generating drill files: {str(e)}")
            return {}
    
    def _generate_3d_visualization(self, 
                                 input_file: str, 
                                 config: OutputConfig) -> Dict[str, str]:
        """Generate 3D visualization files."""
        try:
            output_files = {}
            
            # Generate STEP file
            if config.generate_3d_step:
                step_file = str(Path(config.output_dir) / "board.step")
                cmd = ["gerber2blend", "--step", input_file, step_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    output_files["step"] = step_file
            
            # Generate glTF file
            if config.generate_3d_gltf:
                gltf_file = str(Path(config.output_dir) / "board.gltf")
                cmd = ["gerber2blend", "--gltf", input_file, gltf_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    output_files["gltf"] = gltf_file
            
            # Generate OBJ file
            if config.generate_3d_obj:
                obj_file = str(Path(config.output_dir) / "board.obj")
                cmd = ["gerber2blend", "--obj", input_file, obj_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    output_files["obj"] = obj_file
            
            # Generate STL file
            if config.generate_3d_stl:
                stl_file = str(Path(config.output_dir) / "board.stl")
                cmd = ["gerber2blend", "--stl", input_file, stl_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    output_files["stl"] = stl_file
            
            return output_files
            
        except Exception as e:
            self.logger.error(f"Error generating 3D visualization: {str(e)}")
            return {}
    
    def _generate_pdf(self, 
                     input_file: str, 
                     config: OutputConfig) -> Optional[str]:
        """Generate PDF file."""
        try:
            # Load board
            board = pcbnew.LoadBoard(input_file)
            
            # Set up plot controller
            plot_controller = pcbnew.PLOT_CONTROLLER(board)
            plot_options = plot_controller.GetPlotOptions()
            
            # Configure plot options
            plot_options.SetOutputDirectory(config.output_dir)
            plot_options.SetFormat(pcbnew.PLOT_FORMAT_PDF)
            plot_options.SetScale(1.0)
            plot_options.SetMirror(False)
            plot_options.SetUseGerberAttributes(False)
            plot_options.SetUseGerberX2Attributes(False)
            plot_options.SetUseGerberX2NetAttributes(False)
            plot_options.SetUseGerberX2ComponentAttributes(False)
            plot_options.SetUseGerberX2PadAttributes(False)
            plot_options.SetUseGerberX2ViaAttributes(False)
            plot_options.SetUseGerberX2TrackAttributes(False)
            plot_options.SetUseGerberX2ZoneAttributes(False)
            plot_options.SetUseGerberX2TextAttributes(False)
            plot_options.SetUseGerberX2GraphicAttributes(False)
            plot_options.SetUseGerberX2DimensionAttributes(False)
            plot_options.SetUseGerberX2TargetAttributes(False)
            plot_options.SetUseGerberX2ReferenceAttributes(False)
            plot_options.SetUseGerberX2ValueAttributes(False)
            plot_options.SetUseGerberX2FootprintAttributes(False)
            
            # Generate PDF
            pdf_file = str(Path(config.output_dir) / "board.pdf")
            plot_controller.OpenPlotfile("board", pcbnew.PLOT_FORMAT_PDF, "board")
            plot_controller.PlotLayer()
            
            return pdf_file
            
        except Exception as e:
            self.logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def _generate_bom(self, 
                     input_file: str, 
                     config: OutputConfig) -> Optional[str]:
        """Generate BOM file."""
        try:
            # Load board
            board = pcbnew.LoadBoard(input_file)
            
            # Generate BOM
            bom_file = str(Path(config.output_dir) / "bom.csv")
            with open(bom_file, "w") as f:
                f.write("Reference,Value,Footprint,Quantity\n")
                components = {}
                for footprint in board.GetFootprints():
                    ref = footprint.GetReference()
                    value = footprint.GetValue()
                    fp = footprint.GetFPID().GetLibItemName()
                    if (value, fp) in components:
                        components[(value, fp)] += 1
                    else:
                        components[(value, fp)] = 1
                for (value, fp), quantity in components.items():
                    f.write(f"{ref},{value},{fp},{quantity}\n")
            
            return bom_file
            
        except Exception as e:
            self.logger.error(f"Error generating BOM: {str(e)}")
            return None
    
    def _generate_pick_and_place(self, 
                               input_file: str, 
                               config: OutputConfig) -> Optional[str]:
        """Generate pick and place file."""
        try:
            # Load board
            board = pcbnew.LoadBoard(input_file)
            
            # Generate pick and place file
            pick_and_place_file = str(Path(config.output_dir) / "pick_and_place.csv")
            with open(pick_and_place_file, "w") as f:
                f.write("Reference,Value,Footprint,X,Y,Rotation,Side\n")
                for footprint in board.GetFootprints():
                    ref = footprint.GetReference()
                    value = footprint.GetValue()
                    fp = footprint.GetFPID().GetLibItemName()
                    pos = footprint.GetPosition()
                    rot = footprint.GetOrientationDegrees()
                    side = "top" if footprint.IsFlipped() else "bottom"
                    f.write(f"{ref},{value},{fp},{pos.x/1e6},{pos.y/1e6},{rot},{side}\n")
            
            return pick_and_place_file
            
        except Exception as e:
            self.logger.error(f"Error generating pick and place file: {str(e)}")
            return None 