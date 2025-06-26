# Extended Component Support

The KiCad PCB Generator now supports a comprehensive range of audio and music circuit components, making it easy to import and design complex audio circuits from Falstad simulations.

## Supported Component Types

### Basic Passive Components
- **Resistors**: Axial through-hole, SMD variants (0805, 1206)
- **Capacitors**: Electrolytic, ceramic, film, tantalum
- **Inductors**: Radial through-hole, SMD variants
- **Diodes**: Through-hole, SMD with proper anode/cathode mapping
- **LEDs**: Through-hole, SMD with proper anode/cathode mapping

### Active Components
- **Transistors**: BJT, JFET, MOSFET with proper pin mapping
  - BJT: Emitter, Base, Collector
  - JFET: Source, Gate, Drain
  - MOSFET: Source, Gate, Drain
- **Op-amps**: Single, dual, quad with proper pin assignments
- **Comparators**: Standard pin configurations
- **Specialized ICs**: VCO, VCF, VCA, DAC, ADC, timers

### Audio-Specific Components
- **Potentiometers**: 9mm, 16mm, 24mm Alps-style
- **Audio Connectors**: 3.5mm, 6.35mm jacks, XLR connectors
- **Switches**: SPST, DPDT, toggle switches
- **Speakers**: Audio output devices
- **Ferrite Beads**: EMI filtering components

### Power and Ground
- **Voltage Sources**: VCC, VEE, custom voltage levels
- **Ground**: Standard ground connections
- **Regulators**: Linear and switching regulators

### Logic and Digital
- **Logic ICs**: Standard logic families
- **Flip-flops**: D-type, JK-type
- **Counters**: Binary, decade counters
- **Shift Registers**: Serial/parallel shift registers

### Specialized Audio Components
- **Crystals**: HC49, SMD variants
- **Oscillators**: Crystal oscillators
- **Relays**: SPDT, DPDT with proper pin mapping
- **Transformers**: Audio transformers with primary/secondary mapping

### Vacuum Tubes
- **Tubes**: Triode, pentode with proper socket mapping
- **Tube Sockets**: 9-pin, octal sockets

### Mechanical
- **Mounting Holes**: Standard M3, M4 mounting holes
- **Standoffs**: PCB standoffs

## Pin Mapping

The system automatically maps pins for common components:

### Transistors
```json
{
  "bjt": {"1": "E", "2": "B", "3": "C"},
  "jfet": {"1": "S", "2": "G", "3": "D"},
  "mosfet": {"1": "S", "2": "G", "3": "D"}
}
```

### Op-amps
```json
{
  "8": {"1": "OUT", "2": "IN-", "3": "IN+", "4": "V-", "8": "V+"},
  "14": {"1": "OUT1", "2": "IN1-", "3": "IN1+", "4": "V-", "7": "OUT2", "11": "V+"}
}
```

### Audio Connectors
```json
{
  "3.5mm": {"1": "TIP", "2": "RING", "3": "SLEEVE"},
  "6.35mm": {"1": "TIP", "2": "RING", "3": "SLEEVE"},
  "xlr": {"1": "GND", "2": "HOT", "3": "COLD"}
}
```

### Potentiometers
```json
{
  "3": {"1": "1", "2": "W", "3": "3"}
}
```

## Reference Prefixes

Components are automatically assigned appropriate reference prefixes:

- **R**: Resistors
- **C**: Capacitors
- **L**: Inductors
- **D**: Diodes
- **LED**: Light Emitting Diodes
- **Q**: Transistors (BJT, JFET, MOSFET)
- **U**: ICs, Op-amps, Logic
- **RV**: Potentiometers
- **SW**: Switches
- **J**: Jacks, Connectors
- **XLR**: XLR Connectors
- **SPK**: Speakers
- **FB**: Ferrite Beads
- **XTAL**: Crystals
- **OSC**: Oscillators
- **RLY**: Relays
- **T**: Transformers
- **V**: Vacuum Tubes
- **REG**: Regulators

## Usage Examples

### Basic Audio Amplifier
```python
from kicad_pcb_generator.core.falstad_importer import FalstadImporter

importer = FalstadImporter()

# Audio amplifier circuit data
circuit_data = {
    "elements": [
        {"type": "jack", "value": "Input", "properties": {"connector_type": "3.5mm"}},
        {"type": "resistor", "value": "10k"},
        {"type": "opamp", "value": "NE5532", "properties": {"pins": "8"}},
        {"type": "transistor", "value": "2N3904", "properties": {"transistor_type": "bjt"}},
        {"type": "potentiometer", "value": "10k", "properties": {"package": "16mm"}},
        {"type": "jack", "value": "Output", "properties": {"connector_type": "6.35mm"}},
    ],
    "wires": []
}

# Convert to netlist
netlist = importer.to_netlist(circuit_data)
```

### Synthesizer Module
```python
# VCO, VCF, VCA synthesizer module
synth_data = {
    "elements": [
        {"type": "vco", "value": "CEM3340", "properties": {"pins": "16"}},
        {"type": "vcf", "value": "Moog Ladder", "properties": {"pins": "16"}},
        {"type": "vca", "value": "THAT2180", "properties": {"pins": "8"}},
        {"type": "potentiometer", "value": "100k", "properties": {"package": "24mm"}},
        {"type": "jack", "value": "CV In", "properties": {"connector_type": "3.5mm"}},
        {"type": "jack", "value": "Audio Out", "properties": {"connector_type": "3.5mm"}},
    ],
    "wires": []
}

netlist = importer.to_netlist(synth_data)
```

### Guitar Effects Pedal
```python
# Guitar effects pedal with JFET input
pedal_data = {
    "elements": [
        {"type": "jack", "value": "Input", "properties": {"connector_type": "6.35mm"}},
        {"type": "jfet", "value": "J201", "properties": {"transistor_type": "jfet"}},
        {"type": "opamp", "value": "TL072", "properties": {"pins": "8"}},
        {"type": "diode", "value": "1N4148"},
        {"type": "potentiometer", "value": "100k", "properties": {"package": "16mm"}},
        {"type": "switch", "value": "Bypass"},
        {"type": "jack", "value": "Output", "properties": {"connector_type": "6.35mm"}},
    ],
    "wires": []
}

netlist = importer.to_netlist(pedal_data)
```

## Footprint Selection

The system automatically selects appropriate footprints based on component type and properties:

### Through-Hole (Audio-Optimized)
- Resistors: Axial 9mm
- Capacitors: Radial 16mm
- Transistors: TO-92, TO-220
- Op-amps: DIP-8, DIP-14
- Potentiometers: Alps RK09K, RK16K, RK24K

### SMD (Space-Constrained)
- Resistors: 0603, 0805, 1206
- Capacitors: 0603, 0805, 1206
- Transistors: SOT-23, SOT-223
- Op-amps: SOIC-8, SOIC-14

## Configuration

### Audio-Specific Overrides
The system loads audio-specific footprint overrides from `config/footprint_overrides.json`:

```json
{
  "audio_component_overrides": {
    "resistor": "Device:R_Axial_L9.0mm_D3.0mm_P10.16mm_Horizontal",
    "capacitor": "Device:CP_Radial_D16.0mm_P7.50mm",
    "opamp": "Package_DIP:DIP-8_W7.62mm",
    "transistor": "Package_TO_SOT_THT:TO-92_Inline"
  }
}
```

### Package Variants
Specify package variants in component properties:

```python
{
    "type": "transistor",
    "value": "2N3904",
    "properties": {
        "transistor_type": "bjt",
        "package": "to92"  # or "to220", "sot23"
    }
}
```

## Testing

Run the component support test:

```bash
python examples/test_extended_components.py
```

This will test:
1. Footprint registry functionality
2. Falstad importer with various circuit types
3. Audio amplifier, synthesizer, and effects pedal circuits
4. Component reference assignment and pin mapping

## Best Practices

1. **Use Through-Hole for Audio**: Prefer through-hole components for audio circuits to minimize noise
2. **Proper Grounding**: Use the audio-specific ground rules for star grounding
3. **Component Placement**: Follow audio layout guidelines for low-noise design
4. **EMI Filtering**: Include ferrite beads and proper filtering capacitors
5. **Power Supply**: Use proper power supply filtering and regulation

## Future Enhancements

- Support for more specialized audio ICs
- Automatic component value optimization
- Integration with audio analysis tools
- Support for tube amplifier circuits
- Advanced pin mapping for complex ICs 