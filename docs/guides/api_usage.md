# API Usage Guide

## Overview
This guide provides detailed information about using the KiCad PCB Generator API for programmatic control and automation of PCB design tasks. It covers core functionality, audio-specific features, UI integration, and best practices.

## Core Components

### Board Management
```python
from kicad_pcb_generator.core.board import Board
from kicad_pcb_generator.core.exceptions import BoardError

try:
    # Create a new board
    board = Board()
    
    # Configure board settings
    board.settings.update({
        'board_size': (100, 100),  # mm
        'layers': ['F.Cu', 'B.Cu', 'F.SilkS', 'B.SilkS'],
        'design_rules': {
            'min_trace_width': 0.3,
            'min_clearance': 0.3,
            'min_via_diameter': 0.4
        }
    })
    
    # Load existing board
    board = Board.load("path/to/board.kicad_pcb")
    
    # Save board
    board.save("path/to/output.kicad_pcb")
    
except BoardError as e:
    print(f"Board operation failed: {e.message}")
    print(f"Error code: {e.code}")
    print(f"Details: {e.details}")
```

### Component Management
```python
from kicad_pcb_generator.audio.components import ComponentManager, ComponentError

try:
    # Create component manager
    manager = ComponentManager()
    
    # Add component to board
    component = manager.create_component(
        name="Resistor",
        value="10k",
        footprint="R_0805_2012Metric",
        properties={
            'tolerance': '1%',
            'power': '0.25W',
            'manufacturer': 'Vishay'
        }
    )
    board.add_component(component)
    
    # Get component by reference
    resistor = board.get_component("R1")
    
    # Update component properties
    resistor.set_value("20k")
    resistor.set_footprint("R_1206_3216Metric")
    resistor.set_property('tolerance', '0.1%')
    
    # Get component properties
    properties = resistor.get_properties()
    print(f"Component properties: {properties}")
    
    # Remove component
    board.remove_component("R1")
    
except ComponentError as e:
    print(f"Component operation failed: {e.message}")
    print(f"Component: {e.component_ref}")
    print(f"Details: {e.details}")
```

### Net Management
```python
from kicad_pcb_generator.core.net import Net, NetError

try:
    # Create new net
    net = Net("VCC")
    net.set_property('voltage', '5V')
    net.set_property('current', '1A')
    board.add_net(net)
    
    # Connect components
    board.connect_components("R1", "R2", net)
    
    # Get net by name
    vcc_net = board.get_net("VCC")
    
    # Get connected components
    connected = vcc_net.get_connected_components()
    print(f"Connected components: {connected}")
    
    # Get net properties
    properties = vcc_net.get_properties()
    print(f"Net properties: {properties}")
    
    # Remove net
    board.remove_net("VCC")
    
except NetError as e:
    print(f"Net operation failed: {e.message}")
    print(f"Net: {e.net_name}")
    print(f"Details: {e.details}")
```

## Audio-Specific Features

### Circuit Generation
```python
from kicad_pcb_generator.audio.circuits import (
    CircuitGenerator,
    CircuitError,
    CircuitType
)

try:
    # Create circuit generator
    generator = CircuitGenerator(board)
    
    # Generate basic circuit
    generator.generate_basic_circuit(
        circuit_type=CircuitType.OPAMP,
        components={
            "R1": "10k",  # Input resistor
            "R2": "100k", # Feedback resistor
            "C1": "100n"  # Decoupling capacitor
        },
        options={
            'gain': 10,
            'input_impedance': '10k',
            'output_impedance': '100'
        }
    )
    
    # Generate complex circuit
    generator.generate_complex_circuit(
        circuit_type=CircuitType.VCA,
        options={
            'power_supply': 'dual',
            'input_impedance': '10k',
            'output_impedance': '100',
            'control_voltage': '0-5V',
            'response': 'linear'
        }
    )
    
except CircuitError as e:
    print(f"Circuit generation failed: {e.message}")
    print(f"Circuit type: {e.circuit_type}")
    print(f"Details: {e.details}")
```

### Optimization
```python
from kicad_pcb_generator.audio.optimization import (
    AdvancedCircuitOptimizer,
    OptimizationError,
    OptimizationType
)

try:
    # Create optimizer
    optimizer = AdvancedCircuitOptimizer(board)
    
    # Configure optimization settings
    optimizer.settings.update({
        'signal_path': {
            'min_trace_width': 0.3,
            'max_trace_width': 5.0,
            'min_clearance': 0.3,
            'max_clearance': 10.0,
            'impedance_target': 50.0,
            'max_length': 100.0,
            'preferred_layer': "F.Cu"
        },
        'power_distribution': {
            'min_trace_width': 0.5,
            'max_trace_width': 5.0,
            'min_clearance': 0.5,
            'max_clearance': 10.0,
            'max_voltage_drop': 0.1,
            'decoupling_cap_distance': 2.0,
            'star_topology': True
        },
        'ground_plane': {
            'min_area': 1000.0,
            'min_width': 2.0,
            'split_planes': True,
            'analog_ground': True,
            'digital_ground': True,
            'star_ground': True
        }
    })
    
    # Run optimizations
    results = optimizer.optimize([
        OptimizationType.SIGNAL_PATH,
        OptimizationType.POWER_DISTRIBUTION,
        OptimizationType.GROUND_PLANE
    ])
    
    # Process results
    for result in results:
        print(f"Optimization type: {result.type}")
        print(f"Success: {result.success}")
        print(f"Improvements: {result.improvements}")
        print(f"Warnings: {result.warnings}")
        
except OptimizationError as e:
    print(f"Optimization failed: {e.message}")
    print(f"Optimization type: {e.optimization_type}")
    print(f"Details: {e.details}")
```

### Validation
```python
from kicad_pcb_generator.audio.validation import (
    ValidationManager,
    ValidationError,
    ValidationType
)

try:
    # Create validation manager
    validator = ValidationManager()
    
    # Configure validation settings
    validator.settings.update({
        'real_time': True,
        'cache_results': True,
        'max_issues': 100,
        'min_severity': "warning",
        'signal_integrity': {
            'max_trace_length': 100.0,
            'min_clearance': 0.3,
            'max_crosstalk': -60,
            'impedance_tolerance': 10,
            'max_rise_time': 1.0
        },
        'power_supply': {
            'max_voltage_drop': 0.1,
            'min_decoupling_cap_distance': 2.0,
            'max_ripple': 0.01,
            'min_cap_value': 100,
            'star_topology': True
        },
        'emi_emc': {
            'max_loop_area': 100.0,
            'min_clearance': 0.5,
            'max_radiation': -40,
            'shielding': True,
            'ground_plane': True
        }
    })
    
    # Run validation
    results = validator.validate_board(
        board,
        types=[
            ValidationType.SIGNAL_INTEGRITY,
            ValidationType.POWER_SUPPLY,
            ValidationType.EMI_EMC
        ]
    )
    
    # Process results
    for result in results:
        print(f"Validation type: {result.type}")
        print(f"Severity: {result.severity}")
        print(f"Message: {result.message}")
        if result.suggestion:
            print(f"Suggestion: {result.suggestion}")
        if result.affected_components:
            print(f"Affected components: {result.affected_components}")
        if result.affected_nets:
            print(f"Affected nets: {result.affected_nets}")
            
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Validation type: {e.validation_type}")
    print(f"Details: {e.details}")
```

## UI Integration

### Custom Views
```python
from kicad_pcb_generator.ui.views import (
    PCBVisualizationView,
    ViewError
)

try:
    # Create visualization view
    view = PCBVisualizationView(parent)
    
    # Configure view options
    view.options.update({
        'show_tracks': True,
        'show_vias': True,
        'show_pads': True,
        'show_zones': True,
        'show_3d': True,
        'layer_visibility': {
            'F.Cu': True,
            'B.Cu': True,
            'F.SilkS': True,
            'B.SilkS': True
        },
        'layer_order': [
            'F.Cu',
            'F.SilkS',
            'F.Mask',
            'B.Mask',
            'B.SilkS',
            'B.Cu'
        ]
    })
    
    # Update visualization
    view.update_visualization()
    
    # Handle view events
    view.on_component_selected = lambda comp: print(f"Selected: {comp}")
    view.on_net_selected = lambda net: print(f"Selected: {net}")
    view.on_layer_changed = lambda layer: print(f"Layer: {layer}")
    
except ViewError as e:
    print(f"View operation failed: {e.message}")
    print(f"View type: {e.view_type}")
    print(f"Details: {e.details}")
```

### Theme Management
```python
from kicad_pcb_generator.ui.widgets import (
    ThemeManager,
    ThemeError
)

try:
    # Create theme manager
    theme_manager = ThemeManager()
    
    # Apply theme
    theme_manager.apply_theme(window)
    
    # Create custom theme
    custom_theme = {
        'background': wx.Colour(40, 40, 40),
        'foreground': wx.Colour(255, 255, 255),
        'panel': wx.Colour(60, 60, 60),
        'border': wx.Colour(80, 80, 80),
        'highlight': wx.Colour(0, 120, 215),
        'warning': wx.Colour(255, 165, 0),
        'error': wx.Colour(255, 0, 0),
        'success': wx.Colour(0, 128, 0)
    }
    theme_manager.set_custom_theme(custom_theme)
    
    # Save theme
    theme_manager.save_theme("custom_theme.json")
    
    # Load theme
    theme_manager.load_theme("custom_theme.json")
    
except ThemeError as e:
    print(f"Theme operation failed: {e.message}")
    print(f"Theme: {e.theme_name}")
    print(f"Details: {e.details}")
```

## Error Handling

### Custom Exceptions
```python
from kicad_pcb_generator.utils.exceptions import (
    ValidationError,
    OptimizationError,
    ComponentError,
    NetError,
    CircuitError,
    ViewError,
    ThemeError
)

def handle_operation():
    try:
        # Attempt operation
        board.validate()
    except ValidationError as e:
        print(f"Validation failed: {e.message}")
        print(f"Severity: {e.severity}")
        print(f"Suggestion: {e.suggestion}")
    except OptimizationError as e:
        print(f"Optimization failed: {e.message}")
        print(f"Failed step: {e.step}")
    except ComponentError as e:
        print(f"Component error: {e.message}")
        print(f"Component: {e.component_ref}")
    except NetError as e:
        print(f"Net error: {e.message}")
        print(f"Net: {e.net_name}")
    except CircuitError as e:
        print(f"Circuit error: {e.message}")
        print(f"Circuit type: {e.circuit_type}")
    except ViewError as e:
        print(f"View error: {e.message}")
        print(f"View type: {e.view_type}")
    except ThemeError as e:
        print(f"Theme error: {e.message}")
        print(f"Theme: {e.theme_name}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
```

## Performance Optimization

### Caching
```python
from kicad_pcb_generator.utils.cache import (
    CacheManager,
    CacheError
)

try:
    # Create cache manager
    cache = CacheManager()
    
    # Enable caching
    cache.enable()
    
    # Configure cache settings
    cache.settings.update({
        'max_size': 1000,  # MB
        'ttl': 3600,  # seconds
        'compression': True,
        'persistence': True,
        'location': 'cache/'
    })
    
    # Use cache
    result = cache.get_or_compute(
        "key",
        compute_function,
        ttl=1800  # Override TTL for this operation
    )
    
    # Clear cache
    cache.clear()
    
    # Get cache statistics
    stats = cache.get_statistics()
    print(f"Cache hits: {stats.hits}")
    print(f"Cache misses: {stats.misses}")
    print(f"Cache size: {stats.size} MB")
    
except CacheError as e:
    print(f"Cache operation failed: {e.message}")
    print(f"Operation: {e.operation}")
    print(f"Details: {e.details}")
```

## Best Practices

### 1. Error Handling
- Always use try-except blocks for operations that might fail
- Handle specific exceptions rather than catching all
- Provide meaningful error messages
- Log errors with appropriate context
- Use custom exceptions for domain-specific errors

### 2. Resource Management
- Use context managers for file operations
- Clean up resources properly
- Monitor memory usage
- Implement proper cleanup in destructors
- Use weak references where appropriate

### 3. Performance
- Use caching for expensive operations
- Optimize validation checks
- Minimize UI updates
- Use background processing for long operations
- Profile critical sections

### 4. Code Organization
- Follow the project's modular structure
- Use type hints
- Document all functions
- Write unit tests
- Use design patterns where appropriate

## Examples

### Complete Circuit Generation
```python
from kicad_pcb_generator.core.board import Board
from kicad_pcb_generator.audio.circuits import CircuitGenerator
from kicad_pcb_generator.audio.optimization import AdvancedCircuitOptimizer
from kicad_pcb_generator.audio.validation import ValidationManager

def generate_audio_circuit():
    try:
        # Create board
        board = Board()
        
        # Generate circuit
        generator = CircuitGenerator(board)
        generator.generate_complex_circuit(
            circuit_type="instrumentation_amp",
            options={
                "gain": 10,
                "input_impedance": "10k",
                "cmrr": 80
            }
        )
        
        # Optimize
        optimizer = AdvancedCircuitOptimizer(board)
        optimizer.optimize_signal_paths()
        optimizer.optimize_power_distribution()
        optimizer.optimize_ground_plane()
        
        # Validate
        validator = ValidationManager()
        results = validator.validate_board(board)
        
        # Save if valid
        if not any(r.severity == "error" for r in results):
            board.save("audio_circuit.kicad_pcb")
            return True, "Circuit generated successfully"
        else:
            return False, "Validation failed"
            
    except Exception as e:
        return False, f"Error: {str(e)}"
```

## Support
For additional help:
- Check the [API Documentation](../api/validation.md)
- Join the [Discord Community](https://discord.gg/your-server)
- Submit [GitHub Issues](https://github.com/yourusername/kicad-pcb-generator/issues)
- Email: support@kicad-pcb-generator.com 
