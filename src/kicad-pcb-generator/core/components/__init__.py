"""Component management system for KiCad Audio Designer."""

from .manager import ComponentManager, ComponentData, ComponentType
from .audio_components import AudioComponentData, AudioComponentType, AudioComponentValidator

__all__ = [
    "ComponentManager",
    "ComponentData",
    "ComponentType",
    "AudioComponentData",
    "AudioComponentType",
    "AudioComponentValidator"
] 
