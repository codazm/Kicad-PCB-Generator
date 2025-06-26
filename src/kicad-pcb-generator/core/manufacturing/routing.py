"""Routing management using KiCad's native functionality."""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pcbnew
from ..base.base_config import BaseConfig
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigFormat
from ..utils.logger import Logger

@dataclass
class RoutingConfigItem:
    """Configuration item for routing."""
    min_trace_width: float = 0.1  # Minimum trace width in mm
    min_clearance: float = 0.1  # Minimum clearance in mm
    min_via_diameter: float = 0.4  # Minimum via diameter in mm
    min_via_hole: float = 0.2  # Minimum via hole diameter in mm
    differential_pair_spacing: float = 0.2  # Differential pair spacing in mm
    differential_pair_width: float = 0.2  # Differential pair trace width in mm
    max_length_mismatch: float = 0.1  # Maximum length mismatch in mm
    use_length_matching: bool = True  # Whether to use length matching
    use_differential_pairs: bool = True  # Whether to use differential pairs

class RoutingConfig(BaseConfig[RoutingConfigItem]):
    """Configuration manager for routing."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize routing configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: RoutingConfigItem) -> ConfigResult:
        """Validate routing configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate minimum trace width
            if config.min_trace_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum trace width must be positive",
                    data=config
                )
            
            # Validate minimum clearance
            if config.min_clearance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum clearance must be positive",
                    data=config
                )
            
            # Validate minimum via diameter
            if config.min_via_diameter <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum via diameter must be positive",
                    data=config
                )
            
            # Validate minimum via hole
            if config.min_via_hole <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum via hole must be positive",
                    data=config
                )
            
            # Validate via hole vs diameter relationship
            if config.min_via_hole >= config.min_via_diameter:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Via hole diameter must be less than via diameter",
                    data=config
                )
            
            # Validate differential pair spacing
            if config.differential_pair_spacing <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Differential pair spacing must be positive",
                    data=config
                )
            
            # Validate differential pair width
            if config.differential_pair_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Differential pair width must be positive",
                    data=config
                )
            
            # Validate maximum length mismatch
            if config.max_length_mismatch <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum length mismatch must be positive",
                    data=config
                )
            
            # Validate trace width vs differential pair width relationship
            if config.differential_pair_width < config.min_trace_width:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Differential pair width cannot be less than minimum trace width",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Routing configuration validated successfully",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Error validating routing configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Configuration validation failed: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> RoutingConfigItem:
        """Parse configuration data into RoutingConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            RoutingConfigItem instance
        """
        try:
            return RoutingConfigItem(
                min_trace_width=config_data.get('min_trace_width', 0.1),
                min_clearance=config_data.get('min_clearance', 0.1),
                min_via_diameter=config_data.get('min_via_diameter', 0.4),
                min_via_hole=config_data.get('min_via_hole', 0.2),
                differential_pair_spacing=config_data.get('differential_pair_spacing', 0.2),
                differential_pair_width=config_data.get('differential_pair_width', 0.2),
                max_length_mismatch=config_data.get('max_length_mismatch', 0.1),
                use_length_matching=config_data.get('use_length_matching', True),
                use_differential_pairs=config_data.get('use_differential_pairs', True)
            )
        except Exception as e:
            self.logger.error(f"Error parsing routing configuration: {e}")
            raise ValueError(f"Invalid routing configuration data: {e}")
    
    def _prepare_config_data(self, config: RoutingConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'min_trace_width': config.min_trace_width,
            'min_clearance': config.min_clearance,
            'min_via_diameter': config.min_via_diameter,
            'min_via_hole': config.min_via_hole,
            'differential_pair_spacing': config.differential_pair_spacing,
            'differential_pair_width': config.differential_pair_width,
            'max_length_mismatch': config.max_length_mismatch,
            'use_length_matching': config.use_length_matching,
            'use_differential_pairs': config.use_differential_pairs
        }
    
    def create_config(
        self,
        min_trace_width: float = 0.1,
        min_clearance: float = 0.1,
        min_via_diameter: float = 0.4,
        min_via_hole: float = 0.2,
        differential_pair_spacing: float = 0.2,
        differential_pair_width: float = 0.2,
        max_length_mismatch: float = 0.1,
        use_length_matching: bool = True,
        use_differential_pairs: bool = True
    ) -> ConfigResult:
        """Create a new routing configuration.
        
        Args:
            min_trace_width: Minimum trace width in mm
            min_clearance: Minimum clearance in mm
            min_via_diameter: Minimum via diameter in mm
            min_via_hole: Minimum via hole diameter in mm
            differential_pair_spacing: Differential pair spacing in mm
            differential_pair_width: Differential pair trace width in mm
            max_length_mismatch: Maximum length mismatch in mm
            use_length_matching: Whether to use length matching
            use_differential_pairs: Whether to use differential pairs
            
        Returns:
            ConfigResult with the created configuration
        """
        try:
            config = RoutingConfigItem(
                min_trace_width=min_trace_width,
                min_clearance=min_clearance,
                min_via_diameter=min_via_diameter,
                min_via_hole=min_via_hole,
                differential_pair_spacing=differential_pair_spacing,
                differential_pair_width=differential_pair_width,
                max_length_mismatch=max_length_mismatch,
                use_length_matching=use_length_matching,
                use_differential_pairs=use_differential_pairs
            )
            
            # Validate the configuration
            validation_result = self._validate_config(config)
            if validation_result.status != ConfigStatus.SUCCESS:
                return validation_result
            
            # Store the configuration
            self._config_data = self._prepare_config_data(config)
            
            self.logger.info("Routing configuration created successfully")
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Routing configuration created successfully",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Error creating routing configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Failed to create routing configuration: {e}",
                data=None
            )

class RoutingManagement:
    """Manages PCB routing using KiCad's native functionality."""
    
    def __init__(self, board: Optional[pcbnew.BOARD] = None, logger: Optional[logging.Logger] = None):
        """Initialize routing management.
        
        Args:
            board: Optional KiCad board object
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.board = board
        self.config = RoutingConfig()
    
    def set_board(self, board: pcbnew.BOARD) -> None:
        """Set the board to manage.
        
        Args:
            board: KiCad board object
        """
        self.board = board
        self.logger.info("Set board for routing management")
    
    def create_differential_pair(self, net_p: str, net_n: str, 
                               start_pos: Tuple[float, float],
                               end_pos: Tuple[float, float]) -> None:
        """Create a differential pair.
        
        Args:
            net_p: Positive net name
            net_n: Negative net name
            start_pos: Start position (x, y) in mm
            end_pos: End position (x, y) in mm
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        if not self.config.use_differential_pairs:
            raise RuntimeError("Differential pairs not enabled")
        
        # Convert positions to KiCad units
        start = pcbnew.wxPoint(
            int(start_pos[0] * pcbnew.IU_PER_MM),
            int(start_pos[1] * pcbnew.IU_PER_MM)
        )
        end = pcbnew.wxPoint(
            int(end_pos[0] * pcbnew.IU_PER_MM),
            int(end_pos[1] * pcbnew.IU_PER_MM)
        )
        
        # Create differential pair using KiCad's native routing
        router = pcbnew.ROUTER()
        router.SetBoard(self.board)
        
        # Set differential pair parameters
        router.SetDifferentialPairSpacing(int(self.config.differential_pair_spacing * pcbnew.IU_PER_MM))
        router.SetDifferentialPairWidth(int(self.config.differential_pair_width * pcbnew.IU_PER_MM))
        
        # Route differential pair
        router.RouteDifferentialPair(net_p, net_n, start, end)
        
        self.logger.info(f"Created differential pair: {net_p}/{net_n}")
    
    def match_trace_lengths(self, net_group: List[str], target_length: float) -> None:
        """Match trace lengths for a group of nets.
        
        Args:
            net_group: List of net names
            target_length: Target length in mm
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        if not self.config.use_length_matching:
            raise RuntimeError("Length matching not enabled")
        
        # Convert target length to KiCad units
        target = int(target_length * pcbnew.IU_PER_MM)
        
        # Use KiCad's native length matching
        router = pcbnew.ROUTER()
        router.SetBoard(self.board)
        
        # Set length matching parameters
        router.SetMaxLengthMismatch(int(self.config.max_length_mismatch * pcbnew.IU_PER_MM))
        
        # Match lengths
        router.MatchTraceLengths(net_group, target)
        
        self.logger.info(f"Matched trace lengths for nets: {net_group}")
    
    def validate_routing(self) -> List[str]:
        """Validate routing.
        
        Returns:
            List of validation errors
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        errors = []
        
        # Use KiCad's native DRC for routing validation
        drc = pcbnew.DRC_ENGINE()
        drc.SetBoard(self.board)
        
        # Check trace widths
        for track in self.board.GetTracks():
            width = track.GetWidth() / pcbnew.IU_PER_MM
            if width < self.config.min_trace_width:
                errors.append(
                    f"Trace width {width:.2f}mm below minimum {self.config.min_trace_width}mm"
                )
        
        # Check clearances
        drc.SetMinClearance(int(self.config.min_clearance * pcbnew.IU_PER_MM))
        clearance_errors = drc.CheckClearance()
        errors.extend(clearance_errors)
        
        # Check vias
        for via in self.board.GetVias():
            diameter = via.GetWidth() / pcbnew.IU_PER_MM
            hole = via.GetDrill() / pcbnew.IU_PER_MM
            if diameter < self.config.min_via_diameter:
                errors.append(
                    f"Via diameter {diameter:.2f}mm below minimum {self.config.min_via_diameter}mm"
                )
            if hole < self.config.min_via_hole:
                errors.append(
                    f"Via hole {hole:.2f}mm below minimum {self.config.min_via_hole}mm"
                )
        
        # Log validation results
        if errors:
            self.logger.warning("Routing validation found issues:")
            for error in errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info("Routing validation passed")
        
        return errors
    
    def update_routing_config(self, **kwargs) -> None:
        """Update routing configuration.
        
        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.logger.info("Updated routing configuration") 