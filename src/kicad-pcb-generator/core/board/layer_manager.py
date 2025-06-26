"""Layer management using KiCad 9's native functionality."""
import logging
import pcbnew
from typing import Dict, List, Optional, Any, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import json
import math

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus

if TYPE_CHECKING:
    from ..base.results.analysis_result import AnalysisResult

class LayerType(Enum):
    """Types of PCB layers."""
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"
    MIXED = "mixed"
    MECHANICAL = "mechanical"
    USER = "user"
    AUDIO_SIGNAL = "audio_signal"  # Special layer type for audio signals
    AUDIO_GROUND = "audio_ground"  # Special layer type for audio ground
    AUDIO_POWER = "audio_power"    # Special layer type for audio power

@dataclass
class LayerProperties:
    """Properties of a PCB layer."""
    name: str
    type: LayerType
    copper_weight: float  # oz/ft²
    dielectric_constant: float
    loss_tangent: float
    thickness: float  # mm
    min_trace_width: float  # mm
    min_clearance: float  # mm
    is_enabled: bool = True
    is_visible: bool = True

    def __post_init__(self):
        """Initialize and validate layer properties."""
        self.validate()

    def validate(self) -> None:
        """Validate layer properties.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.name:
            raise ValueError("Layer name is required")
        
        if not isinstance(self.type, LayerType):
            raise ValueError("Layer type must be a LayerType enum value")
        
        # Validate numeric properties
        if self.copper_weight <= 0:
            raise ValueError("Copper weight must be positive")
        if self.dielectric_constant <= 0:
            raise ValueError("Dielectric constant must be positive")
        if self.loss_tangent < 0:
            raise ValueError("Loss tangent must be non-negative")
        if self.thickness <= 0:
            raise ValueError("Layer thickness must be positive")
        if self.min_trace_width <= 0:
            raise ValueError("Minimum trace width must be positive")
        if self.min_clearance <= 0:
            raise ValueError("Minimum clearance must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "copper_weight": self.copper_weight,
            "dielectric_constant": self.dielectric_constant,
            "loss_tangent": self.loss_tangent,
            "thickness": self.thickness,
            "min_trace_width": self.min_trace_width,
            "min_clearance": self.min_clearance,
            "is_enabled": self.is_enabled,
            "is_visible": self.is_visible
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayerProperties":
        """Create from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            LayerProperties instance
        """
        return cls(
            name=data["name"],
            type=LayerType(data["type"]),
            copper_weight=data["copper_weight"],
            dielectric_constant=data["dielectric_constant"],
            loss_tangent=data["loss_tangent"],
            thickness=data["thickness"],
            min_trace_width=data["min_trace_width"],
            min_clearance=data["min_clearance"],
            is_enabled=data.get("is_enabled", True),
            is_visible=data.get("is_visible", True)
        )

    def to_json(self) -> str:
        """Convert to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "LayerProperties":
        """Create from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            LayerProperties instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def update(self, **kwargs) -> None:
        """Update layer properties.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.validate()

    def get_impedance(self, trace_width: float) -> float:
        """Calculate characteristic impedance for a trace.
        
        Args:
            trace_width: Trace width in mm
            
        Returns:
            Characteristic impedance in ohms
        """
        # Simple microstrip impedance calculation
        # This is a simplified model and may need to be adjusted
        # based on specific requirements
        h = self.thickness  # Substrate height
        w = trace_width  # Trace width
        er = self.dielectric_constant  # Relative permittivity
        t = self.copper_weight * 0.035  # Trace thickness in mm (1oz = 0.035mm)
        
        # Calculate effective width
        weff = w + 0.398 * h * (1 + math.log(2 * h / w))
        
        # Calculate impedance
        z0 = (87 / math.sqrt(er + 1.41)) * math.log(5.98 * h / (0.8 * w + t))
        
        return z0

    def get_propagation_delay(self) -> float:
        """Calculate signal propagation delay.
        
        Returns:
            Propagation delay in ps/mm
        """
        # Calculate effective dielectric constant
        er_eff = (self.dielectric_constant + 1) / 2
        
        # Calculate propagation delay
        delay = 3.33 * math.sqrt(er_eff)  # ps/mm
        
        return delay

@dataclass
class LayerItem:
    """Represents a layer item managed by LayerManager."""
    id: str
    layer_id: int
    properties: LayerProperties
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class LayerManager(BaseManager[LayerItem]):
    """Manages PCB layers using KiCad 9's native functionality."""
    
    def __init__(self, board: pcbnew.BOARD, logger: Optional[logging.Logger] = None):
        """Initialize the layer manager.
        
        Args:
            board: KiCad board object
            logger: Optional logger instance
        """
        super().__init__()
        self.board = board
        self.logger = logger or logging.getLogger(__name__)
        self._validate_kicad_version()
        
        # Cache for layer properties
        self._layer_properties: Dict[int, LayerProperties] = {}
        self._layer_cache: Dict[str, Any] = {}
        self._enabled_layers: Set[int] = set()
        self._visible_layers: Set[int] = set()
        
        # Initialize layer properties
        self._initialize_layer_properties()
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        version = pcbnew.Version()
        if not version.startswith('9'):
            raise RuntimeError(f"This module requires KiCad 9.x, but found version {version}")
        self.logger.info(f"Running with KiCad version: {version}")
    
    def _initialize_layer_properties(self) -> None:
        """Initialize layer properties using KiCad's native functionality."""
        try:
            # Get layer manager
            layer_manager = self.board.GetLayerManager()
            
            # Initialize properties for each layer
            for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT):
                if not self.board.IsLayerEnabled(layer_id):
                    continue
                
                # Cache enabled and visible states
                self._enabled_layers.add(layer_id)
                if self.board.IsLayerVisible(layer_id):
                    self._visible_layers.add(layer_id)
                
                # Get native layer properties
                layer_name = self.board.GetLayerName(layer_id)
                layer_type = layer_manager.GetLayerType(layer_id)
                
                # Convert layer type to our enum
                type_enum = self._get_layer_type_enum(layer_type)
                
                # Get layer properties from board settings
                settings = self.board.GetDesignSettings()
                min_trace_width = settings.GetTrackWidth() / 1e6  # Convert to mm
                min_clearance = settings.GetMinClearance() / 1e6
                
                # Create layer properties
                layer_props = LayerProperties(
                    name=layer_name,
                    type=type_enum,
                    copper_weight=1.0,  # Default value
                    dielectric_constant=4.5,  # Default value
                    loss_tangent=0.02,  # Default value
                    thickness=0.035,  # Default value
                    min_trace_width=min_trace_width,
                    min_clearance=min_clearance,
                    is_enabled=True,
                    is_visible=layer_id in self._visible_layers
                )
                
                # Store in internal cache
                self._layer_properties[layer_id] = layer_props
                
                # Create layer item for BaseManager
                layer_item = LayerItem(
                    id=f"layer_{layer_id}",
                    layer_id=layer_id,
                    properties=layer_props
                )
                self.create(f"layer_{layer_id}", layer_item)
                
        except Exception as e:
            self.logger.error(f"Error initializing layer properties: {str(e)}")
            raise
    
    @staticmethod
    def _get_layer_type_enum(layer_type: int) -> LayerType:
        """Convert KiCad layer type to our enum.
        
        Args:
            layer_type: KiCad layer type
            
        Returns:
            LayerType enum value
        """
        if layer_type == pcbnew.LT_SIGNAL:
            return LayerType.SIGNAL
        elif layer_type == pcbnew.LT_POWER:
            return LayerType.POWER
        elif layer_type == pcbnew.LT_GROUND:
            return LayerType.GROUND
        elif layer_type == pcbnew.LT_MIXED:
            return LayerType.MIXED
        elif layer_type == pcbnew.LT_MECHANICAL:
            return LayerType.MECHANICAL
        else:
            return LayerType.USER
    
    @lru_cache(maxsize=128)
    def get_layer_properties(self, layer_id: int) -> Optional[LayerProperties]:
        """Get properties for a specific layer.
        
        Args:
            layer_id: Layer ID
            
        Returns:
            Layer properties or None if layer doesn't exist
        """
        return self._layer_properties.get(layer_id)
    
    def set_layer_properties(self, layer_id: int, properties: LayerProperties) -> None:
        """Set properties for a specific layer.
        
        Args:
            layer_id: Layer ID
            properties: New layer properties
        """
        try:
            # Update native layer properties
            self.board.SetLayerName(layer_id, properties.name)
            
            # Update layer visibility
            if properties.is_visible != (layer_id in self._visible_layers):
                self.board.SetLayerVisible(layer_id, properties.is_visible)
                if properties.is_visible:
                    self._visible_layers.add(layer_id)
                else:
                    self._visible_layers.discard(layer_id)
            
            # Update layer enabled state
            if properties.is_enabled != (layer_id in self._enabled_layers):
                self.board.SetLayerEnabled(layer_id, properties.is_enabled)
                if properties.is_enabled:
                    self._enabled_layers.add(layer_id)
                else:
                    self._enabled_layers.discard(layer_id)
            
            # Update design rules
            settings = self.board.GetDesignSettings()
            settings.SetTrackWidth(int(properties.min_trace_width * 1e6))  # Convert to nm
            settings.SetMinClearance(int(properties.min_clearance * 1e6))  # Convert to nm
            
            # Store properties in internal cache
            self._layer_properties[layer_id] = properties
            
            # Update layer item in BaseManager
            layer_item = LayerItem(
                id=f"layer_{layer_id}",
                layer_id=layer_id,
                properties=properties
            )
            self.update(f"layer_{layer_id}", layer_item)
            
            # Clear cache for this layer
            self.get_layer_properties.cache_clear()
            
        except Exception as e:
            self.logger.error(f"Error setting layer properties: {str(e)}")
            raise
    
    @lru_cache(maxsize=32)
    def get_audio_layer_stackup(self) -> List[Tuple[int, LayerProperties]]:
        """Get recommended layer stackup for audio designs.
        
        Returns:
            List of (layer_id, properties) tuples
        """
        try:
            # Get all layers
            layers = []
            for layer_id, props in self._layer_properties.items():
                if props.type in [
                    LayerType.SIGNAL,
                    LayerType.GROUND,
                    LayerType.POWER,
                    LayerType.AUDIO_SIGNAL,
                    LayerType.AUDIO_GROUND,
                    LayerType.AUDIO_POWER
                ]:
                    layers.append((layer_id, props))
            
            # Sort layers by type (audio layers first, then signal layers)
            layers.sort(key=lambda x: (
                x[1].type not in [LayerType.AUDIO_SIGNAL, LayerType.AUDIO_GROUND, LayerType.AUDIO_POWER],
                x[1].type != LayerType.SIGNAL,
                x[0]
            ))
            
            return layers
            
        except Exception as e:
            self.logger.error(f"Error getting audio layer stackup: {str(e)}")
            raise
    
    def optimize_for_audio(self) -> None:
        """Optimize layer properties for audio design."""
        try:
            # Get audio layer stackup
            layers = self.get_audio_layer_stackup()
            
            # Optimize each layer
            for layer_id, props in layers:
                if props.type in [LayerType.SIGNAL, LayerType.AUDIO_SIGNAL]:
                    # Optimize signal layers
                    props.min_trace_width = max(props.min_trace_width, 0.3)  # Minimum 0.3mm for audio
                    props.min_clearance = max(props.min_clearance, 0.3)  # Minimum 0.3mm clearance
                    props.copper_weight = max(props.copper_weight, 1.0)  # Minimum 1oz copper
                    props.dielectric_constant = min(props.dielectric_constant, 4.5)  # Maximum 4.5 for audio
                    props.loss_tangent = min(props.loss_tangent, 0.02)  # Maximum 0.02 for audio
                    
                    # Additional optimizations for audio signal layers
                    if props.type == LayerType.AUDIO_SIGNAL:
                        props.min_trace_width = max(props.min_trace_width, 0.4)  # Minimum 0.4mm for audio signals
                        props.min_clearance = max(props.min_clearance, 0.4)  # Minimum 0.4mm clearance for audio
                        props.copper_weight = max(props.copper_weight, 2.0)  # Minimum 2oz copper for audio
                        props.dielectric_constant = min(props.dielectric_constant, 4.0)  # Maximum 4.0 for audio signals
                        props.loss_tangent = min(props.loss_tangent, 0.01)  # Maximum 0.01 for audio signals
                
                elif props.type in [LayerType.GROUND, LayerType.AUDIO_GROUND]:
                    # Optimize ground layers
                    props.min_trace_width = max(props.min_trace_width, 0.5)  # Minimum 0.5mm for ground
                    props.min_clearance = max(props.min_clearance, 0.2)  # Minimum 0.2mm clearance
                    props.copper_weight = max(props.copper_weight, 2.0)  # Minimum 2oz copper
                    
                    # Additional optimizations for audio ground layers
                    if props.type == LayerType.AUDIO_GROUND:
                        props.min_trace_width = max(props.min_trace_width, 0.6)  # Minimum 0.6mm for audio ground
                        props.min_clearance = max(props.min_clearance, 0.3)  # Minimum 0.3mm clearance for audio
                        props.copper_weight = max(props.copper_weight, 3.0)  # Minimum 3oz copper for audio
                        props.dielectric_constant = min(props.dielectric_constant, 4.0)  # Maximum 4.0 for audio ground
                        props.loss_tangent = min(props.loss_tangent, 0.01)  # Maximum 0.01 for audio ground
                
                elif props.type in [LayerType.POWER, LayerType.AUDIO_POWER]:
                    # Optimize power layers
                    props.min_trace_width = max(props.min_trace_width, 0.4)  # Minimum 0.4mm for power
                    props.min_clearance = max(props.min_clearance, 0.3)  # Minimum 0.3mm clearance
                    props.copper_weight = max(props.copper_weight, 2.0)  # Minimum 2oz copper
                    
                    # Additional optimizations for audio power layers
                    if props.type == LayerType.AUDIO_POWER:
                        props.min_trace_width = max(props.min_trace_width, 0.5)  # Minimum 0.5mm for audio power
                        props.min_clearance = max(props.min_clearance, 0.4)  # Minimum 0.4mm clearance for audio
                        props.copper_weight = max(props.copper_weight, 3.0)  # Minimum 3oz copper for audio
                        props.dielectric_constant = min(props.dielectric_constant, 4.0)  # Maximum 4.0 for audio power
                        props.loss_tangent = min(props.loss_tangent, 0.01)  # Maximum 0.01 for audio power
                
                # Apply optimized properties
                self.set_layer_properties(layer_id, props)
            
            # Clear cache after optimization
            self.get_audio_layer_stackup.cache_clear()
            
        except Exception as e:
            self.logger.error(f"Error optimizing for audio: {str(e)}")
            raise
    
    @lru_cache(maxsize=32)
    def validate_layer_stackup(self) -> List[str]:
        """Validate the layer stackup configuration.
        
        Returns:
            List of validation messages
        """
        messages = []
        
        try:
            # Check minimum number of layers
            if len(self._layer_properties) < 2:
                messages.append("At least 2 layers are required")
            
            # Check for ground layer
            has_ground = any(props.type in [LayerType.GROUND, LayerType.AUDIO_GROUND] 
                           for props in self._layer_properties.values())
            if not has_ground:
                messages.append("No ground layer found")
            
            # Check for power layer
            has_power = any(props.type in [LayerType.POWER, LayerType.AUDIO_POWER] 
                          for props in self._layer_properties.values())
            if not has_power:
                messages.append("No power layer found")
            
            # Check for audio-specific layers
            has_audio_signal = any(props.type == LayerType.AUDIO_SIGNAL 
                                 for props in self._layer_properties.values())
            has_audio_ground = any(props.type == LayerType.AUDIO_GROUND 
                                 for props in self._layer_properties.values())
            has_audio_power = any(props.type == LayerType.AUDIO_POWER 
                                for props in self._layer_properties.values())
            
            if not has_audio_signal:
                messages.append("No dedicated audio signal layer found")
            if not has_audio_ground:
                messages.append("No dedicated audio ground layer found")
            if not has_audio_power:
                messages.append("No dedicated audio power layer found")
            
            # Check layer spacing
            signal_layers = [props for props in self._layer_properties.values() 
                           if props.type in [LayerType.SIGNAL, LayerType.AUDIO_SIGNAL]]
            if len(signal_layers) > 1:
                for i in range(len(signal_layers) - 1):
                    if signal_layers[i].thickness + signal_layers[i + 1].thickness < 0.1:
                        messages.append(f"Signal layers {i} and {i + 1} are too close")
            
            # Check audio-specific requirements
            for layer_id, props in self._layer_properties.items():
                if props.type == LayerType.AUDIO_SIGNAL:
                    if props.dielectric_constant > 4.0:
                        messages.append(f"Audio signal layer {layer_id} has high dielectric constant")
                    if props.loss_tangent > 0.01:
                        messages.append(f"Audio signal layer {layer_id} has high loss tangent")
                    if props.copper_weight < 2.0:
                        messages.append(f"Audio signal layer {layer_id} has insufficient copper weight")
                
                elif props.type == LayerType.AUDIO_GROUND:
                    if props.copper_weight < 3.0:
                        messages.append(f"Audio ground layer {layer_id} has insufficient copper weight")
                    if props.min_trace_width < 0.6:
                        messages.append(f"Audio ground layer {layer_id} has insufficient trace width")
                
                elif props.type == LayerType.AUDIO_POWER:
                    if props.copper_weight < 3.0:
                        messages.append(f"Audio power layer {layer_id} has insufficient copper weight")
                    if props.min_trace_width < 0.5:
                        messages.append(f"Audio power layer {layer_id} has insufficient trace width")
            
        except Exception as e:
            self.logger.error(f"Error validating layer stackup: {str(e)}")
            messages.append(f"Error validating layer stackup: {str(e)}")
        
        return messages
    
    def _validate_data(self, data: LayerItem) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.id:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Layer item ID is required",
                    errors=["Layer item ID cannot be empty"]
                )
            
            if not data.properties:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Layer properties are required",
                    errors=["Layer properties cannot be empty"]
                )
            
            # Validate layer properties
            try:
                data.properties.validate()
            except ValueError as e:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message=f"Layer properties validation failed: {e}",
                    errors=[str(e)]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Layer item validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Layer item validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a layer item.
        
        Args:
            key: Layer item ID to clean up
        """
        # Clear cache for this layer
        self.get_layer_properties.cache_clear()
        self.get_audio_layer_stackup.cache_clear()
        self.validate_layer_stackup.cache_clear()
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache and all function caches
        super()._clear_cache()
        self.get_layer_properties.cache_clear()
        self.get_audio_layer_stackup.cache_clear()
        self.validate_layer_stackup.cache_clear() 