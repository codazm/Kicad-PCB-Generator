"""
Core functionality for KiCad Audio Designer.
"""

from .compatibility.kicad9 import KiCad9Compatibility
from .components.manager import ComponentManager
from .templates.base import TemplateBase
from .pcb import PCBGenerator, PCBGenerationConfig, PCBGenerationResult
from .project_manager import ProjectManager, ProjectConfig

__all__ = [
    "KiCad9Compatibility",
    "ComponentManager",
    "TemplateBase",
    "PCBGenerator",
    "PCBGenerationConfig",
    "PCBGenerationResult",
    "ProjectManager",
    "ProjectConfig"
] 