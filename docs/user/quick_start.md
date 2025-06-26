# Quick Start Guide for Home Users

This guide will help you get started with the KiCad PCB Generator for your audio projects. We'll walk through the basic installation and create a simple audio circuit.

## Installation

### Windows Users

1. **Install Python**
   - Download Python 3.8 or later from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation by opening Command Prompt and typing:
     ```bash
     python --version
     ```

2. **Install KiCad**
   - Download KiCad 9 from [kicad.org](https://www.kicad.org/download/)
   - Run the installer and follow the prompts
   - Make sure to install the Python API during installation

3. **Install PCB Generator**
   - Open Command Prompt as Administrator
   - Run:
     ```bash
     pip install kicad-pcb-generator
     ```

### macOS Users

1. **Install Python**
   - Download Python 3.8 or later from [python.org](https://www.python.org/downloads/)
   - Run the installer package
   - Verify installation by opening Terminal and typing:
     ```bash
     python3 --version
     ```

2. **Install KiCad**
   - Download KiCad 9 from [kicad.org](https://www.kicad.org/download/)
   - Open the .dmg file and drag KiCad to Applications
   - Run KiCad once to complete setup

3. **Install PCB Generator**
   - Open Terminal
   - Run:
     ```bash
     pip3 install kicad-pcb-generator
     ```

### Linux Users

1. **Install Python**
   - Open Terminal
   - Run:
     ```bash
     sudo apt update
     sudo apt install python3 python3-pip
     ```

2. **Install KiCad**
   - Run:
     ```bash
     sudo apt install kicad
     ```

3. **Install PCB Generator**
   - Run:
     ```bash
     pip3 install kicad-pcb-generator
     ```

## Your First Project

Let's create a simple audio amplifier project.

### 1. Start the Generator

Open Terminal (macOS/Linux) or Command Prompt (Windows) and run:
```bash
kicad-pcb-generator
```

### 2. Create New Project

1. Click "New Project" in the main window
2. Enter project name (e.g., "MyFirstAmp")
3. Select "Audio Amplifier" template
4. Click "Create"

### 3. Add Components

The template will add basic components. You can modify them:

1. Click "Add Component"
2. Select from common audio components:
   - Op-amps (NE5532, TL072)
   - Resistors (10k, 100k)
   - Capacitors (100nF, 10µF)
   - Connectors (3.5mm jacks)

### 4. Generate PCB

1. Click "Generate PCB"
2. The generator will:
   - Place components
   - Route traces
   - Add ground plane
   - Validate design

### 5. Review and Export

1. Check the validation results
2. Review the PCB layout
3. Click "Export" to save:
   - Gerber files
   - Drill files
   - BOM (Bill of Materials)

## Common Issues and Solutions

### Installation Problems

1. **Python not found**
   - Make sure Python is in your PATH
   - Try using `python3` instead of `python`

2. **KiCad not found**
   - Verify KiCad installation
   - Make sure Python API is installed

3. **Package installation fails**
   - Try updating pip:
     ```bash
     pip install --upgrade pip
     ```
   - Install with verbose output:
     ```bash
     pip install -v kicad-pcb-generator
     ```

### Generation Problems

1. **Component placement fails**
   - Check component footprints
   - Verify component values
   - Try manual placement

2. **Routing fails**
   - Check net connections
   - Verify component pins
   - Try different routing strategy

3. **Validation errors**
   - Read error messages
   - Check component spacing
   - Verify power connections

## Next Steps

1. **Learn More**
   - Read the [User Guide](user_guide.md)
   - Check [Examples](examples.md)
   - Join the [Community](community.md)

2. **Try Templates**
   - Guitar pedal
   - Headphone amplifier
   - Mixer

3. **Customize**
   - Add your own components
   - Modify templates
   - Create custom rules

## Getting Help

- Check the [FAQ](faq.md)
- Join our [Discord](https://discord.gg/kicad-pcb-generator)
- Submit [Issues](https://github.com/yourusername/kicad-pcb-generator/issues)

## Tips for Success

1. **Start Simple**
   - Begin with basic circuits
   - Use provided templates
   - Follow examples

2. **Validate Often**
   - Check design rules
   - Verify connections
   - Test before manufacturing

3. **Save Regularly**
   - Use version control
   - Keep backups
   - Document changes 