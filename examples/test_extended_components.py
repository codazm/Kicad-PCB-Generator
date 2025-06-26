#!/usr/bin/env python3
"""
Test script to demonstrate extended component support in the Falstad importer.
This script creates example Falstad JSON data for various audio and music circuit components.
"""

import json
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kicad_pcb_generator.core.falstad_importer import FalstadImporter
from kicad_pcb_generator.core.components.footprint_registry import FootprintRegistry

def create_audio_amplifier_circuit():
    """Create a simple audio amplifier circuit with various components."""
    return {
        "elements": [
            # Input stage
            {"type": "jack", "value": "Input", "properties": {"connector_type": "3.5mm"}},
            {"type": "resistor", "value": "10k"},
            {"type": "capacitor", "value": "100n", "properties": {"package": "electrolytic"}},
            
            # Op-amp stage
            {"type": "opamp", "value": "NE5532", "properties": {"pins": "8"}},
            {"type": "resistor", "value": "100k"},
            {"type": "resistor", "value": "1k"},
            {"type": "capacitor", "value": "1u", "properties": {"package": "film"}},
            
            # Output stage
            {"type": "transistor", "value": "2N3904", "properties": {"transistor_type": "bjt"}},
            {"type": "transistor", "value": "2N3906", "properties": {"transistor_type": "bjt"}},
            {"type": "resistor", "value": "4.7k"},
            {"type": "resistor", "value": "4.7k"},
            
            # Power supply
            {"type": "voltage", "value": "+15V"},
            {"type": "voltage", "value": "-15V"},
            {"type": "ground", "value": "GND"},
            
            # Output
            {"type": "jack", "value": "Output", "properties": {"connector_type": "6.35mm"}},
            {"type": "speaker", "value": "8Ω"},
            
            # Controls
            {"type": "potentiometer", "value": "10k", "properties": {"package": "16mm"}},
            {"type": "switch", "value": "Bypass"},
            
            # Indicators
            {"type": "led", "value": "Power"},
            {"type": "led", "value": "Signal"},
            
            # Filtering
            {"type": "ferrite_bead", "value": "100Ω"},
            {"type": "capacitor", "value": "100u", "properties": {"package": "electrolytic"}},
        ],
        "wires": [
            # Add some example wire connections
            {"from": "0", "to": "1"},  # Input jack to first resistor
            {"from": "1", "to": "2"},  # Resistor to capacitor
            {"from": "2", "to": "3"},  # Capacitor to op-amp input
        ]
    }

def create_synthesizer_module():
    """Create a synthesizer module with VCO, VCF, VCA components."""
    return {
        "elements": [
            # VCO section
            {"type": "vco", "value": "CEM3340", "properties": {"pins": "16"}},
            {"type": "resistor", "value": "100k"},
            {"type": "capacitor", "value": "1n"},
            {"type": "potentiometer", "value": "100k", "properties": {"package": "24mm"}},
            
            # VCF section
            {"type": "vcf", "value": "Moog Ladder", "properties": {"pins": "16"}},
            {"type": "transistor", "value": "2N3904", "properties": {"transistor_type": "bjt"}},
            {"type": "transistor", "value": "2N3904", "properties": {"transistor_type": "bjt"}},
            {"type": "transistor", "value": "2N3904", "properties": {"transistor_type": "bjt"}},
            {"type": "transistor", "value": "2N3904", "properties": {"transistor_type": "bjt"}},
            {"type": "resistor", "value": "10k"},
            {"type": "resistor", "value": "10k"},
            {"type": "resistor", "value": "10k"},
            {"type": "resistor", "value": "10k"},
            {"type": "capacitor", "value": "100n"},
            
            # VCA section
            {"type": "vca", "value": "THAT2180", "properties": {"pins": "8"}},
            {"type": "resistor", "value": "10k"},
            {"type": "resistor", "value": "10k"},
            
            # Control section
            {"type": "potentiometer", "value": "50k", "properties": {"package": "16mm"}},
            {"type": "potentiometer", "value": "50k", "properties": {"package": "16mm"}},
            {"type": "potentiometer", "value": "50k", "properties": {"package": "16mm"}},
            
            # Logic and timing
            {"type": "timer", "value": "555", "properties": {"pins": "8"}},
            {"type": "flipflop", "value": "CD4013", "properties": {"pins": "14"}},
            {"type": "counter", "value": "CD4020", "properties": {"pins": "16"}},
            
            # Power and ground
            {"type": "voltage", "value": "+12V"},
            {"type": "voltage", "value": "-12V"},
            {"type": "ground", "value": "GND"},
            
            # Connectors
            {"type": "jack", "value": "CV In", "properties": {"connector_type": "3.5mm"}},
            {"type": "jack", "value": "Gate In", "properties": {"connector_type": "3.5mm"}},
            {"type": "jack", "value": "Audio Out", "properties": {"connector_type": "3.5mm"}},
            {"type": "xlr", "value": "Main Out"},
            
            # Indicators
            {"type": "led", "value": "VCO"},
            {"type": "led", "value": "VCF"},
            {"type": "led", "value": "VCA"},
            
            # Switches
            {"type": "switch", "value": "Waveform"},
            {"type": "switch", "value": "Sync"},
            
            # Filtering and protection
            {"type": "ferrite_bead", "value": "100Ω"},
            {"type": "diode", "value": "1N4148"},
            {"type": "diode", "value": "1N4148"},
            {"type": "capacitor", "value": "10u", "properties": {"package": "electrolytic"}},
            {"type": "capacitor", "value": "10u", "properties": {"package": "electrolytic"}},
        ],
        "wires": [
            # Add some example wire connections
            {"from": "0", "to": "1"},  # VCO to resistor
            {"from": "1", "to": "2"},  # Resistor to capacitor
            {"from": "4", "to": "5"},  # VCF to first transistor
        ]
    }

def create_guitar_effects_pedal():
    """Create a guitar effects pedal circuit."""
    return {
        "elements": [
            # Input stage
            {"type": "jack", "value": "Input", "properties": {"connector_type": "6.35mm"}},
            {"type": "resistor", "value": "1M"},
            {"type": "capacitor", "value": "100n"},
            
            # JFET input stage
            {"type": "jfet", "value": "J201", "properties": {"transistor_type": "jfet"}},
            {"type": "resistor", "value": "10k"},
            {"type": "resistor", "value": "1k"},
            {"type": "capacitor", "value": "1u", "properties": {"package": "electrolytic"}},
            
            # Op-amp distortion stage
            {"type": "opamp", "value": "TL072", "properties": {"pins": "8"}},
            {"type": "diode", "value": "1N4148"},
            {"type": "diode", "value": "1N4148"},
            {"type": "resistor", "value": "100k"},
            {"type": "resistor", "value": "10k"},
            
            # Controls
            {"type": "potentiometer", "value": "100k", "properties": {"package": "16mm"}},
            {"type": "potentiometer", "value": "10k", "properties": {"package": "16mm"}},
            {"type": "switch", "value": "Bypass"},
            {"type": "switch", "value": "Tone"},
            
            # Output stage
            {"type": "transistor", "value": "2N3904", "properties": {"transistor_type": "bjt"}},
            {"type": "resistor", "value": "4.7k"},
            {"type": "capacitor", "value": "10u", "properties": {"package": "electrolytic"}},
            
            # Output
            {"type": "jack", "value": "Output", "properties": {"connector_type": "6.35mm"}},
            
            # Power
            {"type": "voltage", "value": "9V"},
            {"type": "ground", "value": "GND"},
            
            # Indicators
            {"type": "led", "value": "Power"},
            {"type": "led", "value": "Effect"},
            
            # Filtering
            {"type": "ferrite_bead", "value": "100Ω"},
            {"type": "capacitor", "value": "100n"},
            {"type": "capacitor", "value": "100n"},
        ],
        "wires": [
            # Add some example wire connections
            {"from": "0", "to": "1"},  # Input jack to resistor
            {"from": "1", "to": "2"},  # Resistor to capacitor
            {"from": "2", "to": "3"},  # Capacitor to JFET
        ]
    }

def test_component_support():
    """Test the extended component support."""
    print("Testing Extended Component Support")
    print("=" * 50)
    
    # Test footprint registry
    print("\n1. Testing Footprint Registry:")
    print("-" * 30)
    
    # List supported components
    supported_components = FootprintRegistry.list_supported_components()
    print(f"Total supported components: {len(supported_components)}")
    
    # Test some specific components
    test_components = [
        "resistor", "capacitor", "opamp", "transistor", "potentiometer", 
        "jack", "led", "diode", "ferrite_bead", "vco", "vcf", "vca"
    ]
    
    for comp in test_components:
        footprint = FootprintRegistry.get_default_footprint(comp, through_hole=True)
        print(f"  {comp:15} -> {footprint}")
    
    # Test Falstad importer
    print("\n2. Testing Falstad Importer:")
    print("-" * 30)
    
    importer = FalstadImporter()
    supported_falstad_components = importer.get_supported_components()
    print(f"Falstad importer supports {len(supported_falstad_components)} component types")
    
    # Test with audio amplifier circuit
    print("\n3. Testing Audio Amplifier Circuit:")
    print("-" * 30)
    
    audio_circuit = create_audio_amplifier_circuit()
    try:
        netlist = importer.to_netlist(audio_circuit, strict=False)
        print(f"Successfully created netlist with {len(netlist.footprints)} components")
        
        # Show some component details
        for i, fp in enumerate(netlist.footprints[:5]):  # Show first 5
            print(f"  {fp.ref:8} ({fp.value:10}) -> {fp.lib_id}")
            
    except Exception as e:
        print(f"Error creating netlist: {e}")
    
    # Test with synthesizer module
    print("\n4. Testing Synthesizer Module:")
    print("-" * 30)
    
    synth_circuit = create_synthesizer_module()
    try:
        netlist = importer.to_netlist(synth_circuit, strict=False)
        print(f"Successfully created netlist with {len(netlist.footprints)} components")
        
        # Show some component details
        for i, fp in enumerate(netlist.footprints[:5]):  # Show first 5
            print(f"  {fp.ref:8} ({fp.value:10}) -> {fp.lib_id}")
            
    except Exception as e:
        print(f"Error creating netlist: {e}")
    
    # Test with guitar effects pedal
    print("\n5. Testing Guitar Effects Pedal:")
    print("-" * 30)
    
    pedal_circuit = create_guitar_effects_pedal()
    try:
        netlist = importer.to_netlist(pedal_circuit, strict=False)
        print(f"Successfully created netlist with {len(netlist.footprints)} components")
        
        # Show some component details
        for i, fp in enumerate(netlist.footprints[:5]):  # Show first 5
            print(f"  {fp.ref:8} ({fp.value:10}) -> {fp.lib_id}")
            
    except Exception as e:
        print(f"Error creating netlist: {e}")
    
    print("\n" + "=" * 50)
    print("Component support test completed!")

if __name__ == "__main__":
    test_component_support() 