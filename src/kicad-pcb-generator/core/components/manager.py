"""
Component management system for KiCad Audio Designer.
Adapted from the existing KiCad codebase with improvements for audio-specific needs.
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union, TYPE_CHECKING
from enum import Enum

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from ..compatibility.kicad9 import KiCad9Compatibility

if TYPE_CHECKING:
    from .audio_components import AudioComponentData

logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """Types of components."""
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    TRANSISTOR = "transistor"
    IC = "ic"
    CONNECTOR = "connector"
    MECHANICAL = "mechanical"
    OTHER = "other"

@dataclass
class ComponentData:
    """Component data structure."""
    id: str
    type: str
    value: str
    footprint: str
    position: Optional[tuple[float, float]] = None
    orientation: Optional[float] = None
    layer: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize default values and validate."""
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
        self.validate()

    def validate(self) -> None:
        """Validate component data.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.id:
            raise ValueError("Component ID is required")
        if not self.type:
            raise ValueError("Component type is required")
        if not self.value:
            raise ValueError("Component value is required")
        if not self.footprint:
            raise ValueError("Component footprint is required")
        
        # Validate position if provided
        if self.position is not None:
            if not isinstance(self.position, tuple) or len(self.position) != 2:
                raise ValueError("Position must be a tuple of (x, y) coordinates")
            if not all(isinstance(x, (int, float)) for x in self.position):
                raise ValueError("Position coordinates must be numeric")
        
        # Validate orientation if provided
        if self.orientation is not None:
            if not isinstance(self.orientation, (int, float)):
                raise ValueError("Orientation must be numeric")
            if not 0 <= self.orientation <= 360:
                raise ValueError("Orientation must be between 0 and 360 degrees")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "type": self.type,
            "value": self.value,
            "footprint": self.footprint,
            "position": self.position,
            "orientation": self.orientation,
            "layer": self.layer,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentData":
        """Create from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            ComponentData instance
        """
        return cls(
            id=data["id"],
            type=data["type"],
            value=data["value"],
            footprint=data["footprint"],
            position=data.get("position"),
            orientation=data.get("orientation"),
            layer=data.get("layer"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

    def update(self, **kwargs) -> None:
        """Update component data.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
        self.validate()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def to_json(self) -> str:
        """Convert to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ComponentData":
        """Create from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            ComponentData instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

class ComponentManager(BaseManager[Union[ComponentData, "AudioComponentData"]]):
    """Component management system.
    
    Adapted from the existing KiCad codebase with improvements for audio-specific needs.
    Now inherits from BaseManager for standardized CRUD operations.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize component manager.
        
        Args:
            base_path: Base path for component data
            logger: Optional logger instance
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.base_path = Path(base_path)
        self.kicad = KiCad9Compatibility(logger=self.logger)
        
        # Create necessary directories
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Load components
        self._load_components()
    
    def _load_components(self) -> None:
        """Load components from storage."""
        try:
            components_file = self.base_path / "components.json"
            if components_file.exists():
                with open(components_file, "r") as f:
                    data = json.load(f)
                    for component_data in data:
                        if "audio_type" in component_data:
                            # Import locally to avoid circular imports
                            from .audio_components import AudioComponentData
                            component = AudioComponentData.from_dict(component_data)
                        else:
                            component = ComponentData.from_dict(component_data)
                        # Use BaseManager's create method
                        self.create(component.id, component)
        except Exception as e:
            self.logger.error(f"Error loading components: {e}")
    
    def _save_components(self) -> None:
        """Save components to storage."""
        try:
            components_file = self.base_path / "components.json"
            with open(components_file, "w") as f:
                json.dump([c.to_dict() for c in self._items.values()], f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving components: {e}")
    
    def add_component(self, component: Union[ComponentData, "AudioComponentData"]) -> bool:
        """Add a component.
        
        Args:
            component: Component to add
            
        Returns:
            True if successful
        """
        result = self.create(component.id, component)
        if result.success:
            self._save_components()
        return result.success
    
    def update_component(self, component_id: str, **kwargs) -> bool:
        """Update a component.
        
        Args:
            component_id: Component ID
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        # Get existing component
        read_result = self.read(component_id)
        if not read_result.success:
            return False
        
        # Update component
        component = read_result.data
        component.update(**kwargs)
        
        # Save using BaseManager
        result = self.update(component_id, component)
        if result.success:
            self._save_components()
        return result.success
    
    def remove_component(self, component_id: str) -> bool:
        """Remove a component.
        
        Args:
            component_id: Component ID
            
        Returns:
            True if successful
        """
        result = self.delete(component_id)
        if result.success:
            self._save_components()
        return result.success
    
    def get_component(self, component_id: str) -> Optional[Union[ComponentData, "AudioComponentData"]]:
        """Get a component.
        
        Args:
            component_id: Component ID
            
        Returns:
            Component if found
        """
        result = self.read(component_id)
        return result.data if result.success else None
    
    def get_components(self) -> Dict[str, Union[ComponentData, "AudioComponentData"]]:
        """Get all components.
        
        Returns:
            Dictionary of components
        """
        result = self.list_all()
        if result.success:
            return {comp.id: comp for comp in result.data}
        return {}
    
    def _validate_data(self, data: Union[ComponentData, "AudioComponentData"]) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            data.validate()
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Component validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Component validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a component.
        
        Args:
            key: Component ID to clean up
        """
        # Placeholder for future component cleanup (e.g., temp files).
        self.logger.debug("ComponentManager cleanup hook called for component '%s'", key)
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache and save to disk
        super()._clear_cache()
        self._save_components() 