# Audio PCB Design Examples

This directory contains example designs that demonstrate how to use the audio PCB design tools. Each example shows different aspects of audio PCB design and can be used as a starting point for your own designs.

## Available Examples

### Audio Amplifier (`audio_amplifier.py`)

A high-quality audio amplifier design that demonstrates:
- Component placement for optimal audio performance
- Power supply filtering and stability
- EMI/EMC considerations
- Signal routing best practices

To run the example:
```bash
python audio_amplifier.py
```

This will create a KiCad PCB file named `audio_amplifier.kicad_pcb` in the current directory.

## Features Demonstrated

### Component Placement
- Opamps placed in the center for short signal paths
- Input connectors on the left edge
- Output connectors on the right edge
- Power components at the top
- Passive components near their associated opamps

### Stability Components
- Ferrite beads for power filtering
- EMC filters for input/output protection
- Power supply filtering capacitors
- Audio signal filters

### Design Rules
- Custom trace widths for different signal types
- Proper clearance between traces
- Thick power and ground planes
- Audio-specific routing rules

## Customizing Examples

You can modify the examples to suit your needs:

1. Adjust component values and types
2. Modify design rules for your specific requirements
3. Add or remove stability components
4. Change the board dimensions and layout

## Best Practices

When using these examples as a starting point:

1. Always verify component values and ratings
2. Check power supply requirements
3. Consider your specific EMI/EMC requirements
4. Test the design with your actual components
5. Verify signal integrity with your specific requirements

## Testing

Each example has corresponding tests in the `tests/examples` directory. Run the tests to verify the functionality:

```bash
pytest tests/examples/
```

## Contributing

Feel free to contribute new examples or improvements to existing ones. When adding new examples:

1. Follow the existing code style
2. Add appropriate tests
3. Update this README with documentation
4. Include comments explaining design decisions 
