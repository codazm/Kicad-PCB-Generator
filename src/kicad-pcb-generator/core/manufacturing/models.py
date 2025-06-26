"""3D model management using KiCad's native functionality."""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pcbnew
from kicad.core.manufacturing.model_generator import ModelGenerator
from ..base.base_config import BaseConfig
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigFormat

@dataclass
class ModelConfigItem:
    """Configuration item for 3D models."""
    format: str = "STEP"  # Output format (STEP, IGES, etc.)
    resolution: int = 100  # Model resolution
    include_components: bool = True  # Whether to include components
    include_tracks: bool = True  # Whether to include tracks
    include_vias: bool = True  # Whether to include vias
    include_zones: bool = True  # Whether to include zones
    include_silkscreen: bool = True  # Whether to include silkscreen
    include_soldermask: bool = True  # Whether to include soldermask
    include_paste: bool = True  # Whether to include paste
    include_courtyard: bool = True  # Whether to include courtyard
    include_fabrication: bool = True  # Whether to include fabrication
    include_other: bool = True  # Whether to include other layers

class ModelConfig(BaseConfig[ModelConfigItem]):
    """Configuration manager for 3D models."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize model configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = logging.getLogger(__name__)
        
    def _validate_config(self, config: ModelConfigItem) -> ConfigResult:
        """Validate model configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate format
            valid_formats = ["STEP", "IGES", "STL", "OBJ", "PLY"]
            if config.format not in valid_formats:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message=f"Format must be one of: {', '.join(valid_formats)}",
                    data=config
                )
            
            # Validate resolution
            if config.resolution < 10 or config.resolution > 1000:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Resolution must be between 10 and 1000",
                    data=config
                )
            
            # Validate boolean flags
            if not isinstance(config.include_components, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include components must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_tracks, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include tracks must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_vias, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include vias must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_zones, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include zones must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_silkscreen, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include silkscreen must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_soldermask, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include soldermask must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_paste, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include paste must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_courtyard, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include courtyard must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_fabrication, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include fabrication must be a boolean",
                    data=config
                )
            
            if not isinstance(config.include_other, bool):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Include other must be a boolean",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Model configuration validated successfully",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Error validating model configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Configuration validation failed: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ModelConfigItem:
        """Parse configuration data into ModelConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            ModelConfigItem instance
        """
        try:
            return ModelConfigItem(
                format=config_data.get('format', 'STEP'),
                resolution=config_data.get('resolution', 100),
                include_components=config_data.get('include_components', True),
                include_tracks=config_data.get('include_tracks', True),
                include_vias=config_data.get('include_vias', True),
                include_zones=config_data.get('include_zones', True),
                include_silkscreen=config_data.get('include_silkscreen', True),
                include_soldermask=config_data.get('include_soldermask', True),
                include_paste=config_data.get('include_paste', True),
                include_courtyard=config_data.get('include_courtyard', True),
                include_fabrication=config_data.get('include_fabrication', True),
                include_other=config_data.get('include_other', True)
            )
        except Exception as e:
            self.logger.error(f"Error parsing model configuration: {e}")
            raise ValueError(f"Invalid model configuration data: {e}")
    
    def _prepare_config_data(self, config: ModelConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'format': config.format,
            'resolution': config.resolution,
            'include_components': config.include_components,
            'include_tracks': config.include_tracks,
            'include_vias': config.include_vias,
            'include_zones': config.include_zones,
            'include_silkscreen': config.include_silkscreen,
            'include_soldermask': config.include_soldermask,
            'include_paste': config.include_paste,
            'include_courtyard': config.include_courtyard,
            'include_fabrication': config.include_fabrication,
            'include_other': config.include_other
        }

class ModelManagement:
    """Manages 3D models using KiCad's native functionality."""
    
    def __init__(self, board: Optional[pcbnew.BOARD] = None, logger: Optional[logging.Logger] = None):
        """Initialize model management.
        
        Args:
            board: Optional KiCad board object
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.board = board
        self.model_generator = ModelGenerator()
        self.config = ModelConfig()
    
    def set_board(self, board: pcbnew.BOARD) -> None:
        """Set the board to manage.
        
        Args:
            board: KiCad board object
        """
        self.board = board
        self.logger.info("Set board for model management")
    
    def generate_3d_model(self, output_path: str) -> str:
        """Generate 3D model.
        
        Args:
            output_path: Output file path
            
        Returns:
            Path to generated model
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        # Configure model generation
        config = {
            "format": self.config.format,
            "resolution": self.config.resolution,
            "include_components": self.config.include_components,
            "include_tracks": self.config.include_tracks,
            "include_vias": self.config.include_vias,
            "include_zones": self.config.include_zones,
            "include_silkscreen": self.config.include_silkscreen,
            "include_soldermask": self.config.include_soldermask,
            "include_paste": self.config.include_paste,
            "include_courtyard": self.config.include_courtyard,
            "include_fabrication": self.config.include_fabrication,
            "include_other": self.config.include_other
        }
        
        # Generate model using KiCad's model generator
        model_path = self.model_generator.generate_3d_model(
            self.board,
            output_path,
            config
        )
        
        self.logger.info(f"Generated 3D model: {model_path}")
        return model_path
    
    def validate_3d_model(self, model_path: str) -> List[str]:
        """Validate 3D model.
        
        Args:
            model_path: Path to model file
            
        Returns:
            List of validation errors
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        errors = []
        
        # Use KiCad's native model validation
        validator = pcbnew.MODEL_VALIDATOR()
        validator.SetBoard(self.board)
        
        # Check model format
        if not validator.ValidateFormat(model_path):
            errors.append(f"Invalid model format: {model_path}")
        
        # Check model structure
        if not validator.ValidateStructure(model_path):
            errors.append(f"Invalid model structure: {model_path}")
        
        # Check model components
        if self.config.include_components:
            if not validator.ValidateComponents(model_path):
                errors.append(f"Invalid model components: {model_path}")
        
        # Log validation results
        if errors:
            self.logger.warning("3D model validation found issues:")
            for error in errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info("3D model validation passed")
        
        return errors
    
    def update_model_config(self, **kwargs) -> None:
        """Update model configuration.
        
        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.logger.info("Updated model configuration") 