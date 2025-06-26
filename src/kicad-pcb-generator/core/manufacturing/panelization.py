"""
Panelization manager for KiCad PCB Generator.
Handles board panelization using KiKit integration.
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
class PanelizationConfigItem:
    """Data structure for panelization configuration items."""
    id: str
    rows: int = 2
    cols: int = 2
    spacing: float = 5.0  # mm
    frame_width: float = 5.0  # mm
    frame_clearance: float = 2.0  # mm
    mouse_bites: bool = True
    mouse_bite_diameter: float = 0.5  # mm
    mouse_bite_spacing: float = 1.0  # mm
    mouse_bite_offset: float = 0.0  # mm
    vcuts: bool = True
    vcut_width: float = 0.1  # mm
    tooling_holes: bool = True
    tooling_hole_diameter: float = 3.0  # mm
    fiducials: bool = True
    fiducial_diameter: float = 1.0  # mm
    fiducial_clearance: float = 2.0  # mm
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PanelizationConfig(BaseConfig[PanelizationConfigItem]):
    """Configuration for board panelization.
    
    Now inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "PanelizationConfig", config_path: Optional[str] = None):
        """Initialize panelization configuration.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        self.set_default("rows", 2)
        self.set_default("cols", 2)
        self.set_default("spacing", 5.0)
        self.set_default("frame_width", 5.0)
        self.set_default("frame_clearance", 2.0)
        self.set_default("mouse_bites", True)
        self.set_default("mouse_bite_diameter", 0.5)
        self.set_default("mouse_bite_spacing", 1.0)
        self.set_default("mouse_bite_offset", 0.0)
        self.set_default("vcuts", True)
        self.set_default("vcut_width", 0.1)
        self.set_default("tooling_holes", True)
        self.set_default("tooling_hole_diameter", 3.0)
        self.set_default("fiducials", True)
        self.set_default("fiducial_diameter", 1.0)
        self.set_default("fiducial_clearance", 2.0)
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        self.add_validation_rule("rows", {
            "type": "int",
            "min": 1,
            "max": 20,
            "required": True
        })
        self.add_validation_rule("cols", {
            "type": "int",
            "min": 1,
            "max": 20,
            "required": True
        })
        self.add_validation_rule("spacing", {
            "type": "float",
            "min": 0.0,
            "max": 50.0,
            "required": True
        })
        self.add_validation_rule("frame_width", {
            "type": "float",
            "min": 0.0,
            "max": 20.0,
            "required": True
        })
        self.add_validation_rule("frame_clearance", {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "required": True
        })
        self.add_validation_rule("mouse_bites", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("mouse_bite_diameter", {
            "type": "float",
            "min": 0.1,
            "max": 2.0,
            "required": True
        })
        self.add_validation_rule("mouse_bite_spacing", {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "required": True
        })
        self.add_validation_rule("mouse_bite_offset", {
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "required": True
        })
        self.add_validation_rule("vcuts", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("vcut_width", {
            "type": "float",
            "min": 0.05,
            "max": 1.0,
            "required": True
        })
        self.add_validation_rule("tooling_holes", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("tooling_hole_diameter", {
            "type": "float",
            "min": 1.0,
            "max": 10.0,
            "required": True
        })
        self.add_validation_rule("fiducials", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("fiducial_diameter", {
            "type": "float",
            "min": 0.5,
            "max": 5.0,
            "required": True
        })
        self.add_validation_rule("fiducial_clearance", {
            "type": "float",
            "min": 0.5,
            "max": 10.0,
            "required": True
        })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate panelization configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "rows", "cols", "spacing", "frame_width", "frame_clearance",
                "mouse_bites", "mouse_bite_diameter", "mouse_bite_spacing", "mouse_bite_offset",
                "vcuts", "vcut_width", "tooling_holes", "tooling_hole_diameter",
                "fiducials", "fiducial_diameter", "fiducial_clearance"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} must be a number")
                elif rule.get("type") == "int" and not isinstance(value, int):
                    errors.append(f"Field {field} must be an integer")
                elif rule.get("type") == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                
                # Range validation
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
            
            # Validate panel size relationship
            if "rows" in config_data and "cols" in config_data:
                total_panels = config_data["rows"] * config_data["cols"]
                if total_panels > 100:
                    errors.append("Total panels (rows * cols) must be <= 100")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="Panelization configuration validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="Panelization configuration is valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating panelization configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse panelization configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create panelization config item
            panel_item = PanelizationConfigItem(
                id=config_data.get("id", "panelization_config"),
                rows=config_data.get("rows", 2),
                cols=config_data.get("cols", 2),
                spacing=config_data.get("spacing", 5.0),
                frame_width=config_data.get("frame_width", 5.0),
                frame_clearance=config_data.get("frame_clearance", 2.0),
                mouse_bites=config_data.get("mouse_bites", True),
                mouse_bite_diameter=config_data.get("mouse_bite_diameter", 0.5),
                mouse_bite_spacing=config_data.get("mouse_bite_spacing", 1.0),
                mouse_bite_offset=config_data.get("mouse_bite_offset", 0.0),
                vcuts=config_data.get("vcuts", True),
                vcut_width=config_data.get("vcut_width", 0.1),
                tooling_holes=config_data.get("tooling_holes", True),
                tooling_hole_diameter=config_data.get("tooling_hole_diameter", 3.0),
                fiducials=config_data.get("fiducials", True),
                fiducial_diameter=config_data.get("fiducial_diameter", 1.0),
                fiducial_clearance=config_data.get("fiducial_clearance", 2.0)
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="panelization_settings",
                data=config_data,
                description="Board panelization configuration settings"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="Panelization configuration parsed successfully",
                data=panel_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing panelization configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare panelization configuration data for saving.
        
        Returns:
            Configuration data
        """
        panel_section = self.get_section("panelization_settings")
        if panel_section:
            return panel_section.data
        
        # Return default configuration
        return {
            "id": "panelization_config",
            "rows": self.get_default("rows"),
            "cols": self.get_default("cols"),
            "spacing": self.get_default("spacing"),
            "frame_width": self.get_default("frame_width"),
            "frame_clearance": self.get_default("frame_clearance"),
            "mouse_bites": self.get_default("mouse_bites"),
            "mouse_bite_diameter": self.get_default("mouse_bite_diameter"),
            "mouse_bite_spacing": self.get_default("mouse_bite_spacing"),
            "mouse_bite_offset": self.get_default("mouse_bite_offset"),
            "vcuts": self.get_default("vcuts"),
            "vcut_width": self.get_default("vcut_width"),
            "tooling_holes": self.get_default("tooling_holes"),
            "tooling_hole_diameter": self.get_default("tooling_hole_diameter"),
            "fiducials": self.get_default("fiducials"),
            "fiducial_diameter": self.get_default("fiducial_diameter"),
            "fiducial_clearance": self.get_default("fiducial_clearance")
        }
    
    def create_panelization_config(self,
                                   rows: int = 2,
                                   cols: int = 2,
                                   spacing: float = 5.0,
                                   frame_width: float = 5.0,
                                   frame_clearance: float = 2.0,
                                   mouse_bites: bool = True,
                                   mouse_bite_diameter: float = 0.5,
                                   mouse_bite_spacing: float = 1.0,
                                   mouse_bite_offset: float = 0.0,
                                   vcuts: bool = True,
                                   vcut_width: float = 0.1,
                                   tooling_holes: bool = True,
                                   tooling_hole_diameter: float = 3.0,
                                   fiducials: bool = True,
                                   fiducial_diameter: float = 1.0,
                                   fiducial_clearance: float = 2.0) -> ConfigResult[PanelizationConfigItem]:
        """Create a new panelization configuration.
        
        Args:
            rows: Number of rows in panel
            cols: Number of columns in panel
            spacing: Spacing between boards in mm
            frame_width: Frame width in mm
            frame_clearance: Frame clearance in mm
            mouse_bites: Whether to add mouse bites
            mouse_bite_diameter: Mouse bite diameter in mm
            mouse_bite_spacing: Mouse bite spacing in mm
            mouse_bite_offset: Mouse bite offset in mm
            vcuts: Whether to add V-cuts
            vcut_width: V-cut width in mm
            tooling_holes: Whether to add tooling holes
            tooling_hole_diameter: Tooling hole diameter in mm
            fiducials: Whether to add fiducials
            fiducial_diameter: Fiducial diameter in mm
            fiducial_clearance: Fiducial clearance in mm
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"panelization_config_{len(self._config_history) + 1}",
                "rows": rows,
                "cols": cols,
                "spacing": spacing,
                "frame_width": frame_width,
                "frame_clearance": frame_clearance,
                "mouse_bites": mouse_bites,
                "mouse_bite_diameter": mouse_bite_diameter,
                "mouse_bite_spacing": mouse_bite_spacing,
                "mouse_bite_offset": mouse_bite_offset,
                "vcuts": vcuts,
                "vcut_width": vcut_width,
                "tooling_holes": tooling_holes,
                "tooling_hole_diameter": tooling_hole_diameter,
                "fiducials": fiducials,
                "fiducial_diameter": fiducial_diameter,
                "fiducial_clearance": fiducial_clearance
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
                message=f"Error creating panelization configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )

@dataclass
class PanelizationItem:
    """Data structure for panelization items."""
    id: str
    input_file: str
    output_file: str
    config: PanelizationConfig
    status: str = "pending"  # pending, processing, completed, failed
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = None

class PanelizationManager(BaseManager[PanelizationItem]):
    """Manages board panelization using KiKit."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the panelization manager."""
        super().__init__(logger=logger or logging.getLogger(__name__))
        self._validate_kikit_installation()
    
    def _validate_data(self, item: PanelizationItem) -> bool:
        """Validate panelization item data."""
        if not item.id or not isinstance(item.id, str):
            self.logger.error("Panelization item must have a valid string ID")
            return False
        
        if not item.input_file or not isinstance(item.input_file, str):
            self.logger.error("Panelization item must have a valid input file path")
            return False
        
        if not Path(item.input_file).exists():
            self.logger.error(f"Input file does not exist: {item.input_file}")
            return False
        
        if not item.output_file or not isinstance(item.output_file, str):
            self.logger.error("Panelization item must have a valid output file path")
            return False
        
        if not item.config or not isinstance(item.config, PanelizationConfig):
            self.logger.error("Panelization item must have a valid PanelizationConfig")
            return False
        
        # Validate config values
        if item.config.rows <= 0 or item.config.cols <= 0:
            self.logger.error("Panelization config must have positive rows and columns")
            return False
        
        if item.config.spacing < 0 or item.config.frame_width < 0:
            self.logger.error("Panelization config must have non-negative spacing and frame width")
            return False
        
        return True
    
    def _cleanup_item(self, item: PanelizationItem) -> None:
        """Clean up panelization item resources."""
        try:
            # Clean up output file if needed
            if item.output_file and Path(item.output_file).exists():
                Path(item.output_file).unlink()
                self.logger.debug(f"Cleaned up panelization output file: {item.output_file}")
        except Exception as e:
            self.logger.warning(f"Error during panelization item cleanup: {str(e)}")
    
    def _clear_cache(self) -> None:
        """Clear panelization manager cache."""
        try:
            # Clear any cached board objects or temporary files
            self.logger.debug("Cleared panelization manager cache")
        except Exception as e:
            self.logger.warning(f"Error clearing panelization manager cache: {str(e)}")
    
    def create_panelization_job(self, 
                               input_file: str, 
                               output_file: str, 
                               config: PanelizationConfig) -> ManagerResult[PanelizationItem]:
        """Create a new panelization job."""
        try:
            panelization_id = f"panelization_{len(self._items) + 1}"
            panelization_item = PanelizationItem(
                id=panelization_id,
                input_file=input_file,
                output_file=output_file,
                config=config,
                status="pending",
                validation_errors=[]
            )
            
            result = self.create(panelization_item)
            if result.success:
                self.logger.info(f"Created panelization job: {panelization_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating panelization job: {str(e)}")
            return ManagerResult[PanelizationItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def panelize_board(self, 
                      input_file: str, 
                      output_file: str, 
                      config: PanelizationConfig) -> bool:
        """
        Panelize a board using KiKit.
        
        Args:
            input_file: Path to input KiCad board file
            output_file: Path to output panelized board file
            config: Panelization configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input file
            if not Path(input_file).exists():
                self.logger.error(f"Input file not found: {input_file}")
                return False
            
            # Construct KiKit command
            cmd = [
                "kikit", "panelize",
                "--rows", str(config.rows),
                "--cols", str(config.cols),
                "--space", str(config.spacing),
                "--frame-width", str(config.frame_width),
                "--frame-clearance", str(config.frame_clearance),
                input_file,
                output_file
            ]
            
            # Add mouse bites if enabled
            if config.mouse_bites:
                cmd.extend([
                    "--mousebites",
                    "--mousebites-diameter", str(config.mouse_bite_diameter),
                    "--mousebites-spacing", str(config.mouse_bite_spacing),
                    "--mousebites-offset", str(config.mouse_bite_offset)
                ])
            
            # Add V-cuts if enabled
            if config.vcuts:
                cmd.extend([
                    "--vcuts",
                    "--vcuts-width", str(config.vcut_width)
                ])
            
            # Add tooling holes if enabled
            if config.tooling_holes:
                cmd.extend([
                    "--tooling",
                    "--tooling-diameter", str(config.tooling_hole_diameter)
                ])
            
            # Add fiducials if enabled
            if config.fiducials:
                cmd.extend([
                    "--fiducials",
                    "--fiducial-diameter", str(config.fiducial_diameter),
                    "--fiducial-clearance", str(config.fiducial_clearance)
                ])
            
            # Run KiKit
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"KiKit panelization failed: {result.stderr}")
                return False
            
            self.logger.info("Board panelization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during panelization: {str(e)}")
            return False
    
    def process_panelization_job(self, panelization_id: str) -> ManagerResult[PanelizationItem]:
        """Process a panelization job."""
        try:
            # Get the panelization item
            result = self.get(panelization_id)
            if not result.success or not result.data:
                return ManagerResult[PanelizationItem](
                    success=False,
                    error_message=f"Panelization job not found: {panelization_id}",
                    data=None
                )
            
            panelization_item = result.data
            
            # Update status to processing
            panelization_item.status = "processing"
            self.update(panelization_item)
            
            # Validate panelization configuration
            validation_errors = self.validate_panelization_config(panelization_item.config)
            if validation_errors:
                panelization_item.status = "failed"
                panelization_item.error_message = "Panelization configuration validation failed"
                panelization_item.validation_errors = validation_errors
                self.update(panelization_item)
                return ManagerResult[PanelizationItem](
                    success=False,
                    error_message="Panelization configuration validation failed",
                    data=panelization_item
                )
            
            # Perform panelization
            success = self.panelize_board(
                panelization_item.input_file,
                panelization_item.output_file,
                panelization_item.config
            )
            
            # Update panelization item with results
            panelization_item.status = "completed" if success else "failed"
            if not success:
                panelization_item.error_message = "Panelization process failed"
            
            # Update the item
            update_result = self.update(panelization_item)
            if update_result.success:
                self.logger.info(f"Processed panelization job: {panelization_id}")
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"Error processing panelization job {panelization_id}: {str(e)}")
            return ManagerResult[PanelizationItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def validate_panelization_config(self, config: PanelizationConfig) -> List[str]:
        """Validate panelization configuration."""
        errors = []
        
        # Validate basic parameters
        if config.rows <= 0:
            errors.append("Rows must be greater than 0")
        
        if config.cols <= 0:
            errors.append("Columns must be greater than 0")
        
        if config.spacing < 2.0:  # Minimum spacing for manufacturing
            errors.append("Panel spacing is too small for manufacturing (minimum 2.0mm)")
        
        if config.frame_width < 5.0:  # Minimum frame width for manufacturing
            errors.append("Frame width is too small for manufacturing (minimum 5.0mm)")
        
        if config.mouse_bite_diameter <= 0:
            errors.append("Mouse bite diameter must be greater than 0")
        
        if config.mouse_bite_spacing <= 0:
            errors.append("Mouse bite spacing must be greater than 0")
        
        if config.vcut_width <= 0:
            errors.append("V-cut width must be greater than 0")
        
        if config.tooling_hole_diameter <= 0:
            errors.append("Tooling hole diameter must be greater than 0")
        
        if config.fiducial_diameter <= 0:
            errors.append("Fiducial diameter must be greater than 0")
        
        return errors
    
    def validate_panelization(self, 
                            board: pcbnew.BOARD, 
                            config: PanelizationConfig) -> List[str]:
        """
        Validate panelization configuration against board.
        
        Args:
            board: KiCad board object
            config: Panelization configuration
            
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        
        # Validate board dimensions
        board_width = board.GetBoardEdgesBoundingBox().GetWidth() / 1e6  # Convert to mm
        board_height = board.GetBoardEdgesBoundingBox().GetHeight() / 1e6  # Convert to mm
        
        # Calculate panel dimensions
        panel_width = (board_width * config.cols + 
                      config.spacing * (config.cols - 1) + 
                      config.frame_width * 2)
        panel_height = (board_height * config.rows + 
                       config.spacing * (config.rows - 1) + 
                       config.frame_width * 2)
        
        # Check if panel dimensions are within manufacturing limits
        if panel_width > 500 or panel_height > 500:  # Standard panel size limit
            errors.append("Panel dimensions exceed manufacturing limits")
        
        # Validate spacing
        if config.spacing < 2.0:  # Minimum spacing for manufacturing
            errors.append("Panel spacing is too small for manufacturing")
        
        # Validate frame width
        if config.frame_width < 5.0:  # Minimum frame width for manufacturing
            errors.append("Frame width is too small for manufacturing")
        
        return errors
    
    def _validate_kikit_installation(self) -> bool:
        """Validate KiKit installation."""
        try:
            result = subprocess.run(["kikit", "--version"], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode != 0:
                self.logger.error("KiKit is not properly installed")
                return False
            self.logger.info(f"KiKit version: {result.stdout.strip()}")
            return True
        except Exception as e:
            self.logger.error(f"Error validating KiKit installation: {str(e)}")
            return False 