# Getting Started Guide

## Overview

This guide helps you start using KiCad PCB Generator for audio-focused PCB design and validation.  It covers basic workflow steps—project creation, board generation, validation, and export. The system provides comprehensive features for signal integrity analysis, template management, and manufacturing preparation.

## Installation

1. Ensure you have Python 3.8+ installed
2. Install KiCad 9
3. Install the package:
```bash
pip install kicad-pcb-generator
```

## Basic Usage

### Creating a New Project

```python
from kicad_pcb_generator import PCBGenerator

# Initialize the generator
generator = PCBGenerator()

# Create a new project
project = generator.create_project("MyAudioProject")
```

### Using Templates

```python
from kicad_pcb_generator.core.templates import TemplateManager

# Initialize template manager
template_manager = TemplateManager()

# List available templates
templates = template_manager.list_templates(category="audio")

# Create project from template
project = generator.create_from_template(templates[0].id)
```

## Signal Integrity Analysis

### Basic Analysis

```python
from kicad_pcb_generator.core.signal_integrity import SignalIntegrityAnalyzer

# Initialize analyzer
analyzer = SignalIntegrityAnalyzer(board)

# Analyze impedance
impedance_results = analyzer.analyze_impedance("net1")
print(f"Impedance: {impedance_results['impedance']} ohms")

# Analyze reflections
reflection_results = analyzer.analyze_reflections("net1")
```

### Crosstalk Analysis

```python
from kicad_pcb_generator.core.signal_integrity import CrosstalkAnalyzer

# Initialize analyzer
analyzer = CrosstalkAnalyzer(board)

# Analyze crosstalk
crosstalk_results = analyzer.analyze_crosstalk("net1")
print(f"Maximum crosstalk: {crosstalk_results['max_crosstalk']}")
```

## Manufacturing Features

### Thermal Management

```python
from kicad_pcb_generator.core.manufacturing import ThermalManagement

# Initialize thermal management
thermal = ThermalManagement(board)

# Create thermal zone
thermal.create_thermal_zone(
    name="zone1",
    position=(10.0, 10.0),
    size=(20.0, 20.0)
)

# Validate thermal design
errors = thermal.validate_thermal_design()
```

### Routing Management

```python
from kicad_pcb_generator.core.manufacturing import RoutingManagement

# Initialize routing management
routing = RoutingManagement(board)

# Create differential pair
routing.create_differential_pair(
    name="pair1",
    net1="net1",
    net2="net2",
    width=0.2,
    gap=0.1
)
```

### 3D Model Generation

```python
from kicad_pcb_generator.core.manufacturing import ModelManagement

# Initialize model management
models = ModelManagement(board)

# Generate 3D model
models.generate_3D_model("output.step")
```

## Best Practices

1. **Project Organization**
   - Use templates for common designs
   - Maintain consistent naming conventions
   - Document design decisions
   - Use version control

2. **Signal Integrity**
   - Analyze impedance early in design
   - Check for reflections
   - Monitor crosstalk
   - Use appropriate termination

3. **Manufacturing**
   - Consider thermal requirements
   - Plan routing carefully
   - Validate design rules
   - Generate 3D models for review

4. **Template Management**
   - Use version control for templates
   - Document template changes
   - Test templates before use
   - Maintain template library

## Next Steps

1. Review the [Audio Design Guide](audio_design_guide.md) for audio-specific considerations
2. Check the [API Documentation](../api/) for detailed information
3. Explore the [Examples](../examples/) directory for sample projects
4. Join the community for support and updates

## Troubleshooting

Common issues and solutions:

1. **Installation Issues**
   - Ensure Python 3.8+ is installed
   - Verify KiCad 9 installation
   - Check system dependencies

2. **Template Issues**
   - Verify template compatibility
   - Check template version
   - Validate template format

3. **Analysis Issues**
   - Verify board connectivity
   - Check component models
   - Validate analysis parameters

4. **Manufacturing Issues**
   - Verify design rules
   - Check layer stackup
   - Validate component placement

## Support

For additional support:
- Check the [documentation](../)
- Join the community forum
- Submit issues on GitHub
- Contact the development team

# Getting Started: Falstad to PCB in 60 Seconds

This quick-start walks you through converting a Falstad circuit into a production-ready KiCad PCB using **kicad-pcb-generator**.

```bash
# 1.  Export your Falstad schematic as JSON (File ▸ Export ▸ Circuit (.json))
#     Save it as circuit.json

# 2.  Create a project & generate PCB directly from the Falstad file
kicad-pcb-gen falstad2pcb circuit.json my_audio_amp --export gerber bom step

# 3.  Output
#    - projects/my_audio_amp/output/pcb/my_audio_amp.kicad_pcb
#    - Gerber/Drill/BOM/STEP files inside projects/my_audio_amp/output/exports/
```

The command pipeline:
Falstad JSON → Netlist → Placement (LayoutOptimizer) → Routing (AudioRouter) → Validation → Exports.

For advanced options (`--config`, custom stack-up, API usage), see the full documentation. 