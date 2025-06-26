# Effect Inventory System

The Effect Inventory System is a comprehensive framework for managing and validating audio effects in the KiCad PCB Generator. It provides a structured way to define, validate, and manage different types of audio effects, including guitar effects, modular synthesizer modules, and more.

## Features

- **Effect Categories**: Organized categorization of effects (distortion, delay, modulation, etc.)
- **Parameter Validation**: Built-in validation rules for effect parameters
- **Metadata Management**: Comprehensive metadata for each effect
- **Configuration Persistence**: Save and load effect configurations
- **Dependency Management**: Track and validate effect dependencies
- **Documentation Integration**: Links to effect documentation
- **Extensible Design**: Easy to add new effects and validation rules

## Effect Categories

The system supports the following categories of effects:

### Time-based Effects
- Delay
- Reverb
- Echo

### Modulation Effects
- Modulation
- Chorus
- Flanger
- Phaser
- Tremolo

### Distortion Effects
- Distortion
- Overdrive
- Fuzz
- Bitcrusher

### Filter Effects
- Filter
- EQ
- Wah
- Resonator

### Dynamics Effects
- Dynamics
- Compressor
- Limiter
- Gate

### Synth Effects
- Synth
- Oscillator
- Envelope
- LFO

### Utility Effects
- Utility
- Buffer
- Mixer
- Splitter

### Specialized Effects
- Guitar
- Bass
- Vocal
- Drum

## Effect Metadata

Each effect is defined with the following metadata:

```python
@dataclass
class EffectMetadata:
    name: str
    description: str
    categories: Set[EffectCategory]
    tags: Set[str]
    config_class: Optional[Type]
    validator_class: Optional[Type]
    parameters: Dict[str, Any]
    version: str
    author: str
    dependencies: Set[str]
    documentation_url: Optional[str]
    validation_rules: List[ValidationRule]
```

## Validation Rules

Effects can have custom validation rules defined using the `ValidationRule` class:

```python
@dataclass
class ValidationRule:
    name: str
    description: str
    validator: Callable[[Any], bool]
    error_message: str
```

Example validation rule for a distortion effect:

```python
ValidationRule(
    name="gain_range",
    description="Gain must be within valid range",
    validator=lambda x: 0 <= x <= 100,
    error_message="Gain must be between 0 and 100"
)
```

## Usage Examples

### Creating an Effect Inventory

```python
from kicad_pcb_generator.core.validation.effect_inventory import EffectInventory

# Create a new inventory
inventory = EffectInventory()

# Create with configuration file
inventory = EffectInventory(Path("effects.json"))
```

### Registering a New Effect

```python
from kicad_pcb_generator.core.validation.effect_inventory import EffectMetadata, EffectCategory, ValidationRule

# Define effect metadata
metadata = EffectMetadata(
    name="Custom Distortion",
    description="A custom distortion effect",
    categories={EffectCategory.DISTORTION, EffectCategory.GUITAR},
    tags={"guitar", "distortion", "custom"},
    parameters={
        "gain": {"min": 0, "max": 100, "default": 50},
        "tone": {"min": 0, "max": 100, "default": 50}
    },
    validation_rules=[
        ValidationRule(
            name="gain_range",
            description="Gain must be within range",
            validator=lambda x: 0 <= x <= 100,
            error_message="Gain must be between 0 and 100"
        )
    ]
)

# Register the effect
inventory.register_effect("custom_distortion", metadata)
```

### Validating Effect Parameters

```python
# Validate parameters
is_valid, errors = inventory.validate_effect_parameters(
    "distortion",
    {"gain": 50, "tone": 75}
)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

### Finding Effects

```python
# Get effect by ID
effect = inventory.get_effect("distortion")

# Get effects by category
distortion_effects = inventory.get_effects_by_category(EffectCategory.DISTORTION)

# Get effects by tag
guitar_effects = inventory.get_effects_by_tag("guitar")
```

### Saving and Loading Configuration

```python
# Save configuration
inventory.save_config(Path("effects.json"))

# Load configuration
inventory = EffectInventory(Path("effects.json"))
```

## Built-in Effects

The system comes with several built-in effects:

### Guitar Effects
- Distortion
- Delay
- Chorus
- Phaser
- Compressor
- Wah

### Modular Synth Effects
- VCO (Voltage Controlled Oscillator)
- VCF (Voltage Controlled Filter)
- VCA (Voltage Controlled Amplifier)

Each built-in effect comes with:
- Predefined parameters with valid ranges
- Validation rules
- Documentation
- Configuration classes
- Validator classes

## Extending the System

### Adding a New Effect

1. Define the effect's metadata
2. Create configuration and validator classes
3. Register the effect with the inventory
4. Add validation rules
5. Update documentation

### Adding Validation Rules

1. Create a new `ValidationRule` instance
2. Define the validation function
3. Add the rule to the effect's metadata

### Creating Custom Categories

1. Add new categories to the `EffectCategory` enum
2. Update documentation
3. Add new effects using the categories

## Best Practices

1. **Parameter Validation**
   - Always define min/max values for numeric parameters
   - Use validation rules for complex constraints
   - Provide meaningful error messages

2. **Effect Organization**
   - Use appropriate categories
   - Add relevant tags
   - Keep descriptions clear and concise

3. **Documentation**
   - Maintain up-to-date documentation
   - Include parameter descriptions
   - Document validation rules

4. **Error Handling**
   - Validate parameters before use
   - Handle missing dependencies
   - Provide clear error messages

5. **Configuration Management**
   - Save configurations regularly
   - Validate loaded configurations
   - Handle version changes

## Contributing

When contributing new effects or features:

1. Follow the existing code structure
2. Add comprehensive tests
3. Update documentation
4. Include validation rules
5. Add example usage

## License

This system is part of the KiCad PCB Generator project and is subject to its license terms. 