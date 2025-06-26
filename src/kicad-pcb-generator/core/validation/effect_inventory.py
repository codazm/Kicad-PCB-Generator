"""Effect inventory system for managing different types of audio effects."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Type, Any, Tuple, Callable
from pathlib import Path
import json
import logging
from .guitar_effect_validator import (
    GuitarEffectValidator,
    DistortionConfig,
    DelayConfig,
    ModulationConfig
)
from .modular_synth_validator import (
    ModularSynthValidator,
    VCOConfig,
    VCFConfig,
    VCAConfig
)

logger = logging.getLogger(__name__)

class EffectCategory(Enum):
    """Categories of audio effects."""
    # Time-based effects
    DELAY = auto()
    REVERB = auto()
    ECHO = auto()
    
    # Modulation effects
    MODULATION = auto()
    CHORUS = auto()
    FLANGER = auto()
    PHASER = auto()
    TREMOLO = auto()
    
    # Distortion effects
    DISTORTION = auto()
    OVERDRIVE = auto()
    FUZZ = auto()
    BITCRUSHER = auto()
    
    # Filter effects
    FILTER = auto()
    EQ = auto()
    WAH = auto()
    RESONATOR = auto()
    
    # Dynamics effects
    DYNAMICS = auto()
    COMPRESSOR = auto()
    LIMITER = auto()
    GATE = auto()
    
    # Synth effects
    SYNTH = auto()
    OSCILLATOR = auto()
    ENVELOPE = auto()
    LFO = auto()
    
    # Utility effects
    UTILITY = auto()
    BUFFER = auto()
    MIXER = auto()
    SPLITTER = auto()
    
    # Specialized effects
    GUITAR = auto()
    BASS = auto()
    VOCAL = auto()
    DRUM = auto()

@dataclass
class ValidationRule:
    """Rule for validating effect parameters."""
    name: str
    description: str
    validator: Callable[[Any], bool]
    error_message: str

@dataclass
class EffectMetadata:
    """Metadata for an audio effect."""
    name: str
    description: str
    categories: Set[EffectCategory]
    tags: Set[str] = field(default_factory=set)
    config_class: Optional[Type] = None
    validator_class: Optional[Type] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    author: str = "Unknown"
    dependencies: Set[str] = field(default_factory=set)
    documentation_url: Optional[str] = None
    validation_rules: List[ValidationRule] = field(default_factory=list)

class EffectInventory:
    """Inventory system for managing audio effects."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the effect inventory.
        
        Args:
            config_path: Optional path to a JSON configuration file
        """
        self._effects: Dict[str, EffectMetadata] = {}
        self._config_path = config_path
        self._initialize_default_effects()
        if config_path and config_path.exists():
            self._load_config()
    
    def _initialize_default_effects(self):
        """Initialize the default set of effects."""
        # Guitar Effects
        self.register_effect(
            "distortion",
            EffectMetadata(
                name="Distortion",
                description="Classic guitar distortion effect",
                categories={EffectCategory.DISTORTION, EffectCategory.GUITAR},
                tags={"guitar", "overdrive", "fuzz", "distortion"},
                config_class=DistortionConfig,
                validator_class=GuitarEffectValidator,
                parameters={
                    "gain": {"min": 0, "max": 100, "default": 50},
                    "tone": {"min": 0, "max": 100, "default": 50},
                    "volume": {"min": 0, "max": 100, "default": 50}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/distortion",
                validation_rules=[
                    ValidationRule(
                        name="gain_range",
                        description="Gain must be within valid range",
                        validator=lambda x: 0 <= x <= 100,
                        error_message="Gain must be between 0 and 100"
                    )
                ]
            )
        )
        
        self.register_effect(
            "delay",
            EffectMetadata(
                name="Delay",
                description="Time-based delay effect",
                categories={EffectCategory.DELAY, EffectCategory.GUITAR},
                tags={"guitar", "time", "echo", "delay"},
                config_class=DelayConfig,
                validator_class=GuitarEffectValidator,
                parameters={
                    "time": {"min": 0, "max": 2000, "default": 500},
                    "feedback": {"min": 0, "max": 100, "default": 30},
                    "mix": {"min": 0, "max": 100, "default": 50}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/delay",
                validation_rules=[
                    ValidationRule(
                        name="feedback_limit",
                        description="Feedback must not cause infinite loop",
                        validator=lambda x: x < 100,
                        error_message="Feedback must be less than 100% to prevent infinite loop"
                    )
                ]
            )
        )
        
        self.register_effect(
            "chorus",
            EffectMetadata(
                name="Chorus",
                description="Modulation effect for rich, shimmering sounds",
                categories={EffectCategory.MODULATION, EffectCategory.CHORUS, EffectCategory.GUITAR},
                tags={"guitar", "modulation", "stereo", "chorus"},
                config_class=ModulationConfig,
                validator_class=GuitarEffectValidator,
                parameters={
                    "rate": {"min": 0.1, "max": 10, "default": 2},
                    "depth": {"min": 0, "max": 100, "default": 50},
                    "mix": {"min": 0, "max": 100, "default": 50}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/chorus",
                validation_rules=[
                    ValidationRule(
                        name="rate_range",
                        description="Rate must be within valid range",
                        validator=lambda x: 0.1 <= x <= 10,
                        error_message="Rate must be between 0.1 and 10 Hz"
                    )
                ]
            )
        )
        
        # Modular Synth Effects
        self.register_effect(
            "vco",
            EffectMetadata(
                name="Voltage Controlled Oscillator",
                description="Core oscillator module for modular synthesis",
                categories={EffectCategory.SYNTH, EffectCategory.OSCILLATOR},
                tags={"modular", "oscillator", "vco", "synth"},
                config_class=VCOConfig,
                validator_class=ModularSynthValidator,
                parameters={
                    "frequency": {"min": 20, "max": 20000, "default": 440},
                    "waveform": {"options": ["sine", "square", "saw", "triangle"], "default": "sine"},
                    "octave": {"min": -4, "max": 4, "default": 0}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/vco",
                validation_rules=[
                    ValidationRule(
                        name="frequency_range",
                        description="Frequency must be within audible range",
                        validator=lambda x: 20 <= x <= 20000,
                        error_message="Frequency must be between 20 Hz and 20 kHz"
                    )
                ]
            )
        )
        
        self.register_effect(
            "vcf",
            EffectMetadata(
                name="Voltage Controlled Filter",
                description="Filter module for modular synthesis",
                categories={EffectCategory.FILTER, EffectCategory.SYNTH},
                tags={"modular", "filter", "vcf", "synth"},
                config_class=VCFConfig,
                validator_class=ModularSynthValidator,
                parameters={
                    "cutoff": {"min": 20, "max": 20000, "default": 1000},
                    "resonance": {"min": 0, "max": 100, "default": 50},
                    "type": {"options": ["lowpass", "highpass", "bandpass"], "default": "lowpass"}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/vcf",
                validation_rules=[
                    ValidationRule(
                        name="resonance_limit",
                        description="Resonance must not cause self-oscillation",
                        validator=lambda x: x < 90,
                        error_message="Resonance must be less than 90% to prevent self-oscillation"
                    )
                ]
            )
        )
        
        self.register_effect(
            "vca",
            EffectMetadata(
                name="Voltage Controlled Amplifier",
                description="Amplifier module for modular synthesis",
                categories={EffectCategory.DYNAMICS, EffectCategory.SYNTH},
                tags={"modular", "amplifier", "vca", "synth"},
                config_class=VCAConfig,
                validator_class=ModularSynthValidator,
                parameters={
                    "gain": {"min": 0, "max": 100, "default": 50},
                    "response": {"options": ["linear", "exponential"], "default": "linear"},
                    "bias": {"min": 0, "max": 100, "default": 0}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/vca",
                validation_rules=[
                    ValidationRule(
                        name="gain_limit",
                        description="Gain must not cause clipping",
                        validator=lambda x: x <= 100,
                        error_message="Gain must not exceed 100% to prevent clipping"
                    )
                ]
            )
        )
        
        # Additional Effects
        self.register_effect(
            "reverb",
            EffectMetadata(
                name="Reverb",
                description="Space simulation effect",
                categories={EffectCategory.REVERB, EffectCategory.GUITAR},
                tags={"guitar", "space", "ambience", "reverb"},
                config_class=ModulationConfig,  # Using ModulationConfig as base
                validator_class=GuitarEffectValidator,
                parameters={
                    "decay": {"min": 0.1, "max": 10, "default": 2},
                    "damping": {"min": 0, "max": 100, "default": 50},
                    "mix": {"min": 0, "max": 100, "default": 50}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/reverb",
                validation_rules=[
                    ValidationRule(
                        name="decay_range",
                        description="Decay time must be reasonable",
                        validator=lambda x: 0.1 <= x <= 10,
                        error_message="Decay time must be between 0.1 and 10 seconds"
                    )
                ]
            )
        )
        
        self.register_effect(
            "phaser",
            EffectMetadata(
                name="Phaser",
                description="Phase-shifting modulation effect",
                categories={EffectCategory.MODULATION, EffectCategory.PHASER, EffectCategory.GUITAR},
                tags={"guitar", "modulation", "phaser", "sweep"},
                config_class=ModulationConfig,
                validator_class=GuitarEffectValidator,
                parameters={
                    "rate": {"min": 0.1, "max": 10, "default": 1},
                    "depth": {"min": 0, "max": 100, "default": 50},
                    "stages": {"min": 2, "max": 12, "default": 4},
                    "mix": {"min": 0, "max": 100, "default": 50}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/phaser",
                validation_rules=[
                    ValidationRule(
                        name="stages_even",
                        description="Number of stages must be even",
                        validator=lambda x: x % 2 == 0,
                        error_message="Number of stages must be even"
                    )
                ]
            )
        )
        
        self.register_effect(
            "compressor",
            EffectMetadata(
                name="Compressor",
                description="Dynamic range compression effect",
                categories={EffectCategory.DYNAMICS, EffectCategory.COMPRESSOR, EffectCategory.GUITAR},
                tags={"guitar", "dynamics", "compression", "leveling"},
                config_class=ModulationConfig,
                validator_class=GuitarEffectValidator,
                parameters={
                    "threshold": {"min": -60, "max": 0, "default": -20},
                    "ratio": {"min": 1, "max": 20, "default": 4},
                    "attack": {"min": 0.1, "max": 100, "default": 10},
                    "release": {"min": 10, "max": 1000, "default": 100}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/compressor",
                validation_rules=[
                    ValidationRule(
                        name="ratio_range",
                        description="Compression ratio must be valid",
                        validator=lambda x: 1 <= x <= 20,
                        error_message="Compression ratio must be between 1:1 and 20:1"
                    )
                ]
            )
        )
        
        self.register_effect(
            "wah",
            EffectMetadata(
                name="Wah",
                description="Filter sweep effect",
                categories={EffectCategory.FILTER, EffectCategory.WAH, EffectCategory.GUITAR},
                tags={"guitar", "filter", "wah", "sweep"},
                config_class=ModulationConfig,
                validator_class=GuitarEffectValidator,
                parameters={
                    "frequency": {"min": 200, "max": 2000, "default": 1000},
                    "resonance": {"min": 0, "max": 100, "default": 50},
                    "sweep": {"min": 0, "max": 100, "default": 50}
                },
                version="1.0.0",
                author="System",
                documentation_url="https://docs.example.com/effects/wah",
                validation_rules=[
                    ValidationRule(
                        name="frequency_range",
                        description="Wah frequency must be in vocal range",
                        validator=lambda x: 200 <= x <= 2000,
                        error_message="Wah frequency must be between 200 Hz and 2 kHz"
                    )
                ]
            )
        )
    
    def _load_config(self) -> None:
        """Load effect configurations from JSON file."""
        try:
            with open(self._config_path, 'r') as f:
                config = json.load(f)
                
            for effect_id, effect_data in config.items():
                # Convert categories back to enum values
                categories = set()
                for cat_name in effect_data.get('categories', []):
                    try:
                        categories.add(EffectCategory[cat_name])
                    except KeyError:
                        logger.warning(f"Unknown category '{cat_name}' for effect '{effect_id}'")
                
                # Create metadata object
                metadata = EffectMetadata(
                    name=effect_data['name'],
                    description=effect_data['description'],
                    categories=categories,
                    tags=set(effect_data.get('tags', [])),
                    parameters=effect_data.get('parameters', {}),
                    version=effect_data.get('version', '1.0.0'),
                    author=effect_data.get('author', 'Unknown'),
                    dependencies=set(effect_data.get('dependencies', [])),
                    documentation_url=effect_data.get('documentation_url'),
                    validation_rules=[]  # Validation rules would need special handling
                )
                
                self.register_effect(effect_id, metadata)
                
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Data processing error loading effect configuration: {e}")
            raise
        except (OSError, IOError) as e:
            logger.error(f"I/O error loading effect configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading effect configuration: {e}")
            raise
    
    def save_config(self, path: Optional[Path] = None) -> None:
        """Save current effect configurations to JSON file.
        
        Args:
            path: Optional path to save configuration to. If not provided,
                 uses the path specified during initialization.
        """
        save_path = path or self._config_path
        if not save_path:
            raise ValueError("No configuration path specified")
            
        config = {}
        for effect_id, metadata in self._effects.items():
            config[effect_id] = {
                'name': metadata.name,
                'description': metadata.description,
                'categories': [cat.name for cat in metadata.categories],
                'tags': list(metadata.tags),
                'parameters': metadata.parameters,
                'version': metadata.version,
                'author': metadata.author,
                'dependencies': list(metadata.dependencies),
                'documentation_url': metadata.documentation_url,
                'validation_rules': [
                    {
                        'name': rule.name,
                        'description': rule.description,
                        'validator': rule.validator.__name__,
                        'error_message': rule.error_message
                    }
                    for rule in metadata.validation_rules
                ]
            }
            
        try:
            with open(save_path, 'w') as f:
                json.dump(config, f, indent=2)
        except (json.JSONEncodeError, TypeError) as e:
            logger.error(f"Data serialization error saving effect configuration: {e}")
            raise
        except (OSError, IOError) as e:
            logger.error(f"I/O error saving effect configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving effect configuration: {e}")
            raise
    
    def register_effect(self, effect_id: str, metadata: EffectMetadata) -> None:
        """Register a new effect in the inventory.
        
        Args:
            effect_id: Unique identifier for the effect
            metadata: Effect metadata including name, description, and configuration
        """
        if effect_id in self._effects:
            raise ValueError(f"Effect with ID '{effect_id}' already exists")
            
        # Validate dependencies
        for dep in metadata.dependencies:
            if dep not in self._effects:
                raise ValueError(f"Dependency '{dep}' not found")
                
        self._effects[effect_id] = metadata
        logger.info(f"Registered effect: {effect_id}")
    
    def unregister_effect(self, effect_id: str) -> None:
        """Remove an effect from the inventory.
        
        Args:
            effect_id: ID of the effect to remove
        """
        if effect_id not in self._effects:
            raise ValueError(f"Effect with ID '{effect_id}' not found")
            
        # Check if other effects depend on this one
        for other_id, other_metadata in self._effects.items():
            if effect_id in other_metadata.dependencies:
                raise ValueError(
                    f"Cannot remove effect '{effect_id}' as it is required by '{other_id}'"
                )
                
        del self._effects[effect_id]
        logger.info(f"Unregistered effect: {effect_id}")
    
    def get_effect(self, effect_id: str) -> EffectMetadata:
        """Get metadata for a specific effect.
        
        Args:
            effect_id: ID of the effect to retrieve
            
        Returns:
            EffectMetadata for the requested effect
        """
        if effect_id not in self._effects:
            raise ValueError(f"Effect with ID '{effect_id}' not found")
        return self._effects[effect_id]
    
    def get_effects_by_category(self, category: EffectCategory) -> List[EffectMetadata]:
        """Get all effects in a specific category.
        
        Args:
            category: Category to filter effects by
            
        Returns:
            List of EffectMetadata for effects in the specified category
        """
        return [
            metadata for metadata in self._effects.values()
            if category in metadata.categories
        ]
    
    def get_effects_by_tag(self, tag: str) -> List[EffectMetadata]:
        """Get all effects with a specific tag.
        
        Args:
            tag: Tag to filter effects by
            
        Returns:
            List of EffectMetadata for effects with the specified tag
        """
        return [
            metadata for metadata in self._effects.values()
            if tag in metadata.tags
        ]
    
    def get_effects_by_author(self, author: str) -> List[EffectMetadata]:
        """Get all effects by a specific author.
        
        Args:
            author: Author name to filter effects by
            
        Returns:
            List of EffectMetadata for effects by the specified author
        """
        return [
            metadata for metadata in self._effects.values()
            if metadata.author == author
        ]
    
    def get_effects_by_version(self, version: str) -> List[EffectMetadata]:
        """Get all effects with a specific version.
        
        Args:
            version: Version string to filter effects by
            
        Returns:
            List of EffectMetadata for effects with the specified version
        """
        return [
            metadata for metadata in self._effects.values()
            if metadata.version == version
        ]
    
    def list_effects(self) -> List[str]:
        """Get a list of all registered effect IDs.
        
        Returns:
            List of effect IDs
        """
        return list(self._effects.keys())
    
    def get_validator(self, effect_id: str) -> Optional[Type]:
        """Get the validator class for a specific effect.
        
        Args:
            effect_id: ID of the effect
            
        Returns:
            Validator class for the effect, or None if not specified
        """
        metadata = self.get_effect(effect_id)
        return metadata.validator_class
    
    def get_config_class(self, effect_id: str) -> Optional[Type]:
        """Get the configuration class for a specific effect.
        
        Args:
            effect_id: ID of the effect
            
        Returns:
            Configuration class for the effect, or None if not specified
        """
        metadata = self.get_effect(effect_id)
        return metadata.config_class
    
    def get_effect_parameters(self, effect_id: str) -> Dict[str, Any]:
        """Get the parameters for a specific effect.
        
        Args:
            effect_id: ID of the effect
            
        Returns:
            Dictionary of parameter definitions
        """
        metadata = self.get_effect(effect_id)
        return metadata.parameters
    
    def get_effect_dependencies(self, effect_id: str) -> Set[str]:
        """Get the dependencies for a specific effect.
        
        Args:
            effect_id: ID of the effect
            
        Returns:
            Set of effect IDs that this effect depends on
        """
        metadata = self.get_effect(effect_id)
        return metadata.dependencies
    
    def validate_effect_dependencies(self, effect_id: str) -> Tuple[bool, List[str]]:
        """Validate that all dependencies for an effect are satisfied.
        
        Args:
            effect_id: ID of the effect to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_dependencies)
        """
        metadata = self.get_effect(effect_id)
        missing = []
        
        for dep in metadata.dependencies:
            if dep not in self._effects:
                missing.append(dep)
                
        return len(missing) == 0, missing
    
    def validate_effect_parameters(self, effect_id: str, parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate effect parameters against rules.
        
        Args:
            effect_id: ID of the effect
            parameters: Dictionary of parameter values to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        metadata = self.get_effect(effect_id)
        errors = []
        
        # Check parameter ranges
        for param_name, value in parameters.items():
            if param_name in metadata.parameters:
                param_def = metadata.parameters[param_name]
                if "min" in param_def and value < param_def["min"]:
                    errors.append(f"{param_name} value {value} is below minimum {param_def['min']}")
                if "max" in param_def and value > param_def["max"]:
                    errors.append(f"{param_name} value {value} is above maximum {param_def['max']}")
                if "options" in param_def and value not in param_def["options"]:
                    errors.append(f"{param_name} value {value} is not in allowed options {param_def['options']}")
        
        # Check validation rules
        for rule in metadata.validation_rules:
            if not rule.validator(parameters.get(rule.name)):
                errors.append(rule.error_message)
        
        return len(errors) == 0, errors
    
    def get_effect_validation_rules(self, effect_id: str) -> List[ValidationRule]:
        """Get validation rules for a specific effect.
        
        Args:
            effect_id: ID of the effect
            
        Returns:
            List of validation rules
        """
        metadata = self.get_effect(effect_id)
        return metadata.validation_rules 