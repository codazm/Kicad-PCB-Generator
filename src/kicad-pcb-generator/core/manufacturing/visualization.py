"""
Visualization manager for KiCad PCB Generator.
Handles board visualization using PcbDraw integration.
"""

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

import pcbnew

from ..base.base_manager import BaseManager
from ..base.base_config import BaseConfig
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigFormat
from ..base.results.manager_result import ManagerResult

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

@dataclass
class VisualizationConfigItem:
    """Configuration item for board visualization."""
    style: str = "default"  # PcbDraw style
    resolution: int = 300  # DPI
    transparent: bool = False
    highlight_nets: List[str] = field(default_factory=list)
    highlight_components: List[str] = field(default_factory=list)
    highlight_pads: bool = False
    highlight_tracks: bool = False
    highlight_zones: bool = False
    highlight_vias: bool = False
    highlight_holes: bool = False
    highlight_silkscreen: bool = True
    highlight_soldermask: bool = True
    highlight_courtyard: bool = True
    highlight_fabrication: bool = True
    highlight_other: bool = True

class VisualizationConfig(BaseConfig[VisualizationConfigItem]):
    """Configuration manager for board visualization."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize visualization configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = logging.getLogger(__name__)
        
    def _validate_config(self, config: VisualizationConfigItem) -> ConfigResult:
        """Validate visualization configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate style
            if not config.style or not isinstance(config.style, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Style must be a non-empty string",
                    data=config
                )
            
            # Validate resolution
            if config.resolution < 72 or config.resolution > 1200:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Resolution must be between 72 and 1200 DPI",
                    data=config
                )
            
            # Validate highlight lists
            if config.highlight_nets and not isinstance(config.highlight_nets, list):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight nets must be a list",
                    data=config
                )
            
            if config.highlight_components and not isinstance(config.highlight_components, list):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight components must be a list",
                    data=config
                )
            
            # Validate boolean flags
            if not isinstance(config.transparent, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Transparent must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_pads, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight pads must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_tracks, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight tracks must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_zones, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight zones must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_vias, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight vias must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_holes, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight holes must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_silkscreen, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight silkscreen must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_soldermask, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight soldermask must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_courtyard, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight courtyard must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_fabrication, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight fabrication must be a boolean",
                    data=config
                )
            
            if not isinstance(config.highlight_other, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Highlight other must be a boolean",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Visualization configuration validated successfully",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Error validating visualization configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Configuration validation failed: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> VisualizationConfigItem:
        """Parse configuration data into VisualizationConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            VisualizationConfigItem instance
        """
        try:
            return VisualizationConfigItem(
                style=config_data.get('style', 'default'),
                resolution=config_data.get('resolution', 300),
                transparent=config_data.get('transparent', False),
                highlight_nets=config_data.get('highlight_nets', []),
                highlight_components=config_data.get('highlight_components', []),
                highlight_pads=config_data.get('highlight_pads', False),
                highlight_tracks=config_data.get('highlight_tracks', False),
                highlight_zones=config_data.get('highlight_zones', False),
                highlight_vias=config_data.get('highlight_vias', False),
                highlight_holes=config_data.get('highlight_holes', False),
                highlight_silkscreen=config_data.get('highlight_silkscreen', True),
                highlight_soldermask=config_data.get('highlight_soldermask', True),
                highlight_courtyard=config_data.get('highlight_courtyard', True),
                highlight_fabrication=config_data.get('highlight_fabrication', True),
                highlight_other=config_data.get('highlight_other', True)
            )
        except Exception as e:
            self.logger.error(f"Error parsing visualization configuration: {e}")
            raise ValueError(f"Invalid visualization configuration data: {e}")
    
    def _prepare_config_data(self, config: VisualizationConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'style': config.style,
            'resolution': config.resolution,
            'transparent': config.transparent,
            'highlight_nets': config.highlight_nets,
            'highlight_components': config.highlight_components,
            'highlight_pads': config.highlight_pads,
            'highlight_tracks': config.highlight_tracks,
            'highlight_zones': config.highlight_zones,
            'highlight_vias': config.highlight_vias,
            'highlight_holes': config.highlight_holes,
            'highlight_silkscreen': config.highlight_silkscreen,
            'highlight_soldermask': config.highlight_soldermask,
            'highlight_courtyard': config.highlight_courtyard,
            'highlight_fabrication': config.highlight_fabrication,
            'highlight_other': config.highlight_other
        }

@dataclass
class VisualizationItem:
    """Data structure for visualization items."""
    id: str
    input_file: str
    output_file: str
    config: VisualizationConfigItem
    status: str = "pending"  # pending, processing, completed, failed
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = None

class VisualizationManager(BaseManager[VisualizationItem]):
    """Manages board visualization using PcbDraw."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the visualization manager."""
        super().__init__(logger=logger or logging.getLogger(__name__))
        self._validate_pcbdraw_installation()
    
    def _validate_data(self, item: VisualizationItem) -> bool:
        """Validate visualization item data."""
        if not item.id or not isinstance(item.id, str):
            self.logger.error("Visualization item must have a valid string ID")
            return False
        
        if not item.input_file or not isinstance(item.input_file, str):
            self.logger.error("Visualization item must have a valid input file path")
            return False
        
        if not Path(item.input_file).exists():
            self.logger.error(f"Input file does not exist: {item.input_file}")
            return False
        
        if not item.output_file or not isinstance(item.output_file, str):
            self.logger.error("Visualization item must have a valid output file path")
            return False
        
        if not item.config or not isinstance(item.config, VisualizationConfigItem):
            self.logger.error("Visualization item must have a valid VisualizationConfigItem")
            return False
        
        # Validate config values
        if not item.config.style or not isinstance(item.config.style, str):
            self.logger.error("Visualization config must have a valid style")
            return False
        
        if item.config.resolution < 72 or item.config.resolution > 1200:
            self.logger.error("Visualization config must have resolution between 72 and 1200 DPI")
            return False
        
        return True
    
    def _cleanup_item(self, item: VisualizationItem) -> None:
        """Clean up visualization item resources."""
        try:
            # Clean up output file if needed
            if item.output_file and Path(item.output_file).exists():
                Path(item.output_file).unlink()
                self.logger.debug(f"Cleaned up visualization output file: {item.output_file}")
        except Exception as e:
            self.logger.warning(f"Error during visualization item cleanup: {str(e)}")
    
    def _clear_cache(self) -> None:
        """Clear visualization manager cache."""
        try:
            # Clear any cached board objects or temporary files
            self.logger.debug("Cleared visualization manager cache")
        except Exception as e:
            self.logger.warning(f"Error clearing visualization manager cache: {str(e)}")
    
    def create_visualization_job(self, 
                                input_file: str, 
                                output_file: str, 
                                config: VisualizationConfigItem) -> ManagerResult[VisualizationItem]:
        """Create a new visualization job."""
        try:
            visualization_id = f"visualization_{len(self._items) + 1}"
            visualization_item = VisualizationItem(
                id=visualization_id,
                input_file=input_file,
                output_file=output_file,
                config=config,
                status="pending",
                validation_errors=[]
            )
            
            result = self.create(visualization_item)
            if result.success:
                self.logger.info(f"Created visualization job: {visualization_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating visualization job: {str(e)}")
            return ManagerResult[VisualizationItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def generate_visualization(self, 
                             input_file: str, 
                             output_file: str, 
                             config: VisualizationConfigItem) -> bool:
        """
        Generate board visualization using PcbDraw.
        
        Args:
            input_file: Path to input KiCad board file
            output_file: Path to output visualization file
            config: Visualization configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input file
            if not Path(input_file).exists():
                self.logger.error(f"Input file not found: {input_file}")
                return False
            
            # Construct PcbDraw command
            cmd = [
                "pcbdraw",
                "--style", config.style,
                "--resolution", str(config.resolution),
                input_file,
                output_file
            ]
            
            # Add transparency if enabled
            if config.transparent:
                cmd.append("--transparent")
            
            # Add highlighting options
            if config.highlight_nets:
                cmd.extend(["--highlight-nets", ",".join(config.highlight_nets)])
            
            if config.highlight_components:
                cmd.extend(["--highlight-components", ",".join(config.highlight_components)])
            
            if config.highlight_pads:
                cmd.append("--highlight-pads")
            
            if config.highlight_tracks:
                cmd.append("--highlight-tracks")
            
            if config.highlight_zones:
                cmd.append("--highlight-zones")
            
            if config.highlight_vias:
                cmd.append("--highlight-vias")
            
            if config.highlight_holes:
                cmd.append("--highlight-holes")
            
            if not config.highlight_silkscreen:
                cmd.append("--no-silkscreen")
            
            if not config.highlight_soldermask:
                cmd.append("--no-soldermask")
            
            if not config.highlight_courtyard:
                cmd.append("--no-courtyard")
            
            if not config.highlight_fabrication:
                cmd.append("--no-fabrication")
            
            if not config.highlight_other:
                cmd.append("--no-other")
            
            # Run PcbDraw
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"PcbDraw visualization failed: {result.stderr}")
                return False
            
            self.logger.info("Board visualization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during visualization: {str(e)}")
            return False
    
    def process_visualization_job(self, visualization_id: str) -> ManagerResult[VisualizationItem]:
        """Process a visualization job."""
        try:
            # Get the visualization item
            result = self.get(visualization_id)
            if not result.success or not result.data:
                return ManagerResult[VisualizationItem](
                    success=False,
                    error_message=f"Visualization job not found: {visualization_id}",
                    data=None
                )
            
            visualization_item = result.data
            
            # Update status to processing
            visualization_item.status = "processing"
            self.update(visualization_item)
            
            # Validate visualization configuration
            validation_errors = self.validate_visualization_config(visualization_item.config)
            if validation_errors:
                visualization_item.status = "failed"
                visualization_item.error_message = "Visualization configuration validation failed"
                visualization_item.validation_errors = validation_errors
                self.update(visualization_item)
                return ManagerResult[VisualizationItem](
                    success=False,
                    error_message="Visualization configuration validation failed",
                    data=visualization_item
                )
            
            # Perform visualization
            success = self.generate_visualization(
                visualization_item.input_file,
                visualization_item.output_file,
                visualization_item.config
            )
            
            # Update visualization item with results
            visualization_item.status = "completed" if success else "failed"
            if not success:
                visualization_item.error_message = "Visualization process failed"
            
            # Update the item
            update_result = self.update(visualization_item)
            if update_result.success:
                self.logger.info(f"Processed visualization job: {visualization_id}")
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"Error processing visualization job {visualization_id}: {str(e)}")
            return ManagerResult[VisualizationItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def validate_visualization_config(self, config: VisualizationConfigItem) -> List[str]:
        """Validate visualization configuration."""
        errors = []
        
        # Validate style
        if not config.style or not isinstance(config.style, str):
            errors.append("Style must be a valid string")
        
        # Validate resolution
        if config.resolution < 72 or config.resolution > 1200:
            errors.append("Resolution must be between 72 and 1200 DPI")
        
        # Validate highlight lists
        if config.highlight_nets and not isinstance(config.highlight_nets, list):
            errors.append("Highlight nets must be a list")
        
        if config.highlight_components and not isinstance(config.highlight_components, list):
            errors.append("Highlight components must be a list")
        
        return errors
    
    def validate_visualization(self, 
                             board: pcbnew.BOARD, 
                             config: VisualizationConfigItem) -> List[str]:
        """
        Validate visualization configuration against board.
        
        Args:
            board: KiCad board object
            config: Visualization configuration
            
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        
        # Validate highlighted nets
        if config.highlight_nets:
            for net in config.highlight_nets:
                if not board.FindNet(net):
                    errors.append(f"Net not found: {net}")
        
        # Validate highlighted components
        if config.highlight_components:
            for ref in config.highlight_components:
                if not board.FindFootprintByReference(ref):
                    errors.append(f"Component not found: {ref}")
        
        # Validate resolution
        if config.resolution < 72 or config.resolution > 1200:
            errors.append("Resolution must be between 72 and 1200 DPI")
        
        return errors
    
    def _validate_pcbdraw_installation(self) -> bool:
        """Validate PcbDraw installation."""
        try:
            result = subprocess.run(["pcbdraw", "--version"], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode != 0:
                self.logger.error("PcbDraw is not properly installed")
                return False
            self.logger.info(f"PcbDraw version: {result.stdout.strip()}")
            return True
        except Exception as e:
            self.logger.error(f"Error validating PcbDraw installation: {str(e)}")
            return False 