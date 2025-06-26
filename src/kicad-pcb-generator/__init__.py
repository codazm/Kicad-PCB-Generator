"""
KiCad Audio Designer - A specialized PCB design tool for audio circuits.

This package provides a comprehensive framework for designing high-quality audio PCB circuits
using KiCad 9's native functionality. It includes specialized tools for audio circuit analysis,
validation, and optimization with a focus on signal integrity and audio performance.

Key Features:
- Advanced audio circuit analysis (THD+N, frequency response, microphonic coupling)
- Real-time validation with audio-specific rules
- Thermal and EMI analysis for audio designs
- Manufacturing optimization for audio PCBs
- Template system for common audio circuits
- Express workflow for rapid Falstad to PCB conversion
- Board preset system for standard audio PCB sizes
- Integration with KiCad 9's native DRC engine

Example Usage:
    from kicad_pcb_generator import PCBGenerator, AudioCircuitTemplate
    
    # Create a new audio circuit
    generator = PCBGenerator()
    template = AudioCircuitTemplate("preamplifier")
    
    # Generate PCB with audio optimization
    result = generator.generate_pcb(
        template=template,
        optimize_audio=True,
        validate_signal_integrity=True
    )

For more information, see the documentation at:
https://github.com/yourusername/kicad-pcb-generator
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"
__description__ = "A specialized PCB design tool for audio circuits with express workflow capabilities"

# Core functionality imports
from .core.compatibility.kicad9 import KiCad9Compatibility
from .core.components.manager import ComponentManager
from .core.templates.base import TemplateBase
from .core.pcb import PCBGenerator, PCBGenerationConfig, PCBGenerationResult
from .core.project_manager import ProjectManager, ProjectConfig

# Audio circuit templates
from .audio.circuits.templates import (
    AudioCircuitTemplate,
    PreamplifierTemplate,
    PowerAmplifierTemplate,
    EffectsPedalTemplate,
    AudioInterfaceTemplate,
    MixingConsoleTemplate
)

# Public API exports
__all__ = [
    # Core components
    "KiCad9Compatibility",
    "ComponentManager", 
    "TemplateBase",
    "PCBGenerator",
    "PCBGenerationConfig",
    "PCBGenerationResult",
    "ProjectManager",
    "ProjectConfig",
    
    # Audio circuit templates
    "AudioCircuitTemplate",
    "PreamplifierTemplate",
    "PowerAmplifierTemplate", 
    "EffectsPedalTemplate",
    "AudioInterfaceTemplate",
    "MixingConsoleTemplate"
]

# Load optional footprint overrides for audio components
from pathlib import Path
from .core.components.footprint_registry import FootprintRegistry

_override_path = Path(__file__).parent / "config" / "footprint_overrides.json"
if _override_path.exists():
    FootprintRegistry.load_from_file(_override_path) 
