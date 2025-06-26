# Frequently Asked Questions

## Installation

### Q: How do I install the PCB Generator?
A: Follow these steps:
1. Install Python 3.8 or higher
2. Install KiCad 9 or higher
3. Run: `pip install kicad-pcb-generator`

### Q: I get an error about missing KiCad Python API
A: Make sure you:
1. Installed KiCad with Python API support
2. Have KiCad in your system PATH
3. Are using a compatible Python version

### Q: The GUI doesn't start
A: Try these solutions:
1. Install wxPython: `pip install wxPython`
2. Check if you have X11 installed (Linux)
3. Run from terminal to see error messages

## Usage

### Q: How do I create my first project?
A: See the [Quick Start Guide](quick_start.md) for step-by-step instructions.

### Q: Can I import existing KiCad projects?
A: Yes! Use File > Import > KiCad Project to import existing designs.

### Q: How do I add custom components?
A: You can:
1. Use the Component Editor
2. Import from KiCad libraries
3. Create custom footprints

## Components

### Q: Where can I find component libraries?
A: We provide:
1. Built-in libraries
2. KiCad standard libraries
3. Community libraries

### Q: How do I create custom footprints?
A: Use the Footprint Editor:
1. Open Component Editor
2. Click "New Footprint"
3. Design your footprint
4. Save to library

## PCB Design

### Q: What are the minimum trace widths?
A: Default rules:
- Signal traces: 0.2mm
- Power traces: 0.5mm
- High current: 1.0mm

### Q: How many layers can I use?
A: The generator supports:
- 2 layers (default)
- 4 layers
- 6 layers
- Custom configurations

### Q: How do I check my design?
A: Use:
1. Design Rules Check (DRC)
2. Electrical Rules Check (ERC)
3. 3D Preview

## Manufacturing

### Q: What files do I need for manufacturing?
A: Essential files:
1. Gerber files
2. Drill files
3. Pick and place
4. Bill of Materials

### Q: How do I export for manufacturing?
A: Use File > Export > Manufacturing Files to generate all required files.

### Q: Which manufacturers are supported?
A: The generator creates standard files compatible with:
1. JLCPCB
2. PCBWay
3. OSH Park
4. Most other manufacturers

## Troubleshooting

### Q: The auto-router fails
A: Try:
1. Check design rules
2. Verify component placement
3. Adjust routing parameters
4. Use manual routing

### Q: Components are missing
A: Check:
1. Library paths
2. Component references
3. Footprint assignments
4. Update libraries

### Q: Design validation fails
A: Common issues:
1. Clearance violations
2. Missing connections
3. Invalid component values
4. Design rule conflicts

## Support

### Q: Where can I get help?
A: Multiple options:
1. Check the [Documentation](https://kicad-pcb-generator.readthedocs.io/)
2. Join our [Discord](https://discord.gg/kicad-pcb-generator)
3. Submit [Issues](https://github.com/kicad-pcb-generator/kicad-pcb-generator/issues)

### Q: How do I report bugs?
A: Please:
1. Check if it's already reported
2. Include steps to reproduce
3. Attach error messages
4. Share relevant files

### Q: Can I contribute?
A: Yes! We welcome:
1. Code contributions
2. Documentation improvements
3. Bug reports
4. Feature requests

## Advanced Topics

### Q: How do I use custom design rules?
A: You can:
1. Edit the rules file
2. Use the Rules Editor
3. Import from KiCad

### Q: Can I automate the design process?
A: Yes! Use:
1. Command line interface
2. Python API
3. Custom scripts

### Q: How do I optimize for manufacturing?
A: Consider:
1. Panelization
2. Test points
3. Fiducials
4. Assembly requirements 