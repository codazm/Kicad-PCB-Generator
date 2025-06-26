# Falstad Schematic Import

This document describes the Falstad schematic import feature for the KiCad PCB Generator.

## Overview

The Falstad import feature allows users to convert Falstad circuit schematics into KiCad format. This enables users to leverage Falstad's intuitive circuit simulation environment for initial design and then seamlessly transfer their designs to KiCad for PCB layout.

## Features

- Import Falstad JSON schematics
- Automatic component mapping
- Schematic validation
- Interactive preview
- Progress tracking
- Detailed error reporting
- Support for common audio components
- Automatic netlist generation
- Design rule checking

## Usage

### GUI Interface

The GUI provides a user-friendly interface for importing Falstad schematics:

1. Open the "Import" tab
2. Select your Falstad schematic file
3. Choose an output directory
4. Configure import options:
   - Strict validation mode
   - Preview enabled/disabled
   - Auto-validation on load
5. Click "Import" to start the process

The interface provides:
- Real-time preview of the schematic
- Zoom controls for the preview
- Validation results display
- Progress tracking
- Detailed error reporting

### Command Line Interface

The CLI provides several options for importing Falstad schematics:

```bash
# Basic import
kicad-pcb-generator import-falstad schematic.json output_dir

# Validate only
kicad-pcb-generator import-falstad schematic.json output_dir --validate-only

# Output validation results to file
kicad-pcb-generator import-falstad schematic.json output_dir --output-file validation.txt

# JSON output format
kicad-pcb-generator import-falstad schematic.json output_dir --output-format json

# Disable strict validation
kicad-pcb-generator import-falstad schematic.json output_dir --no-strict

# Verbose output
kicad-pcb-generator import-falstad schematic.json output_dir -v
```

## Component Support

The importer supports the following Falstad components:

### Basic Components
- Resistors
- Capacitors
- Inductors
- Diodes
- Transistors (BJT, MOSFET)
- Operational Amplifiers
- Voltage Sources
- Current Sources
- Ground

### Audio-Specific Components
- Audio Input/Output
- Potentiometers
- Switches
- Relays
- Transformers
- Speakers
- Microphones

## Validation Rules

The importer performs several validation checks:

### Schematic Structure
- Valid JSON format
- Required fields present
- Component connections
- Net connectivity

### Component Validation
- Supported component types
- Valid component values
- Component placement
- Connection points

### Design Rules
- Minimum component spacing
- Maximum net length
- Power supply requirements
- Ground connections
- Signal path integrity

## Error Handling

The importer provides detailed error reporting:

### Error Types
- Validation errors
- Component mapping errors
- Connection errors
- Design rule violations

### Error Format
```json
{
    "severity": "error|warning",
    "message": "Error description",
    "location": "Component or net identifier"
}
```

## Output Files

The importer generates the following files:

- `schematic.kicad_sch`: KiCad schematic file
- `schematic.kicad_pcb`: KiCad PCB file
- `schematic.net`: Netlist file
- `validation_report.txt`: Validation results (if enabled)

## Limitations

- Complex Falstad components may not be fully supported
- Some advanced Falstad features are not converted
- Custom component libraries require additional configuration
- Large schematics may require more processing time

## Best Practices

1. Keep schematics simple and well-organized
2. Use standard component values
3. Label important nets and components
4. Verify component connections
5. Run validation before import
6. Check the preview before final import
7. Review the generated files in KiCad

## Troubleshooting

### Common Issues

1. **Component Not Found**
   - Check component type is supported
   - Verify component parameters
   - Use standard component values

2. **Connection Errors**
   - Verify net connections
   - Check for floating components
   - Ensure proper ground connections

3. **Validation Failures**
   - Review validation report
   - Fix identified issues
   - Consider using non-strict mode for warnings

4. **Import Failures**
   - Check file permissions
   - Verify JSON format
   - Ensure sufficient disk space

### Getting Help

- Check the validation report
- Review the error messages
- Consult the documentation
- Submit an issue on GitHub

## Future Improvements

Planned enhancements:

1. Additional component support
2. Enhanced validation rules
3. Custom component mapping
4. Batch import support
5. Improved error reporting
6. Performance optimizations
7. Additional output formats

## Contributing

Contributions are welcome! Please see the [Contributing Guide](CONTRIBUTING.md) for details.

## License

This feature is part of the KiCad PCB Generator project and is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 