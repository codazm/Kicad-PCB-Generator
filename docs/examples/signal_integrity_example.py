#!/usr/bin/env python3
"""
Signal Integrity Analysis Example

This example demonstrates how to use the signal integrity and crosstalk analysis
features of the KiCad PCB Generator for audio PCB design.
"""

import os
from typing import Dict, List, Tuple

from kicad_pcb_generator import PCBGenerator
from kicad_pcb_generator.core.signal_integrity import (
    SignalIntegrityAnalyzer,
    CrosstalkAnalyzer
)
from kicad_pcb_generator.core.manufacturing import (
    ThermalManagement,
    RoutingManagement
)

def analyze_signal_integrity(board_path: str) -> None:
    """Analyze signal integrity of a PCB design."""
    # Initialize the generator
    generator = PCBGenerator()
    
    # Load the board
    board = generator.load_board(board_path)
    
    # Initialize analyzers
    si_analyzer = SignalIntegrityAnalyzer(board)
    crosstalk_analyzer = CrosstalkAnalyzer(board)
    
    # Get sensitive nets (e.g., audio signals)
    sensitive_nets = [
        "audio_in",
        "audio_out",
        "left_channel",
        "right_channel"
    ]
    
    print("Analyzing signal integrity...")
    
    # Analyze each sensitive net
    for net in sensitive_nets:
        print(f"\nAnalyzing net: {net}")
        
        # Impedance analysis
        impedance_results = si_analyzer.analyze_impedance(net)
        print(f"Impedance: {impedance_results['impedance']} ohms")
        print(f"Impedance variation: {impedance_results['variation']}%")
        
        # Reflection analysis
        reflection_results = si_analyzer.analyze_reflections(net)
        print("\nReflections:")
        for reflection in reflection_results:
            print(f"  Position: {reflection['position']}")
            print(f"  Magnitude: {reflection['magnitude']}")
            print(f"  Time: {reflection['time']} ns")
        
        # Termination analysis
        termination_results = si_analyzer.analyze_termination(net)
        print("\nTermination:")
        print(f"  Effectiveness: {termination_results['effectiveness']}%")
        print(f"  Recommendations: {termination_results['recommendations']}")
        
        # Crosstalk analysis
        crosstalk_results = crosstalk_analyzer.analyze_crosstalk(net)
        print("\nCrosstalk:")
        print(f"  Maximum crosstalk: {crosstalk_results['max_crosstalk']}")
        print(f"  Average crosstalk: {crosstalk_results['avg_crosstalk']}")
        
        # Find coupling nets
        coupling_nets = crosstalk_analyzer.find_coupling_nets(net)
        print("\nCoupling nets:")
        for coupling_net in coupling_nets:
            coefficient = crosstalk_analyzer.calculate_coupling_coefficient(
                net, coupling_net
            )
            print(f"  {coupling_net}: {coefficient}")

def optimize_design(board_path: str) -> None:
    """Optimize the PCB design for better signal integrity."""
    # Initialize the generator
    generator = PCBGenerator()
    
    # Load the board
    board = generator.load_board(board_path)
    
    # Initialize managers
    thermal = ThermalManagement(board)
    routing = RoutingManagement(board)
    
    print("Optimizing design...")
    
    # Create thermal zones for sensitive components
    thermal_zones = [
        ("opamp_zone", (50.0, 50.0), (20.0, 20.0)),
        ("power_zone", (100.0, 50.0), (30.0, 20.0))
    ]
    
    for name, position, size in thermal_zones:
        thermal.create_thermal_zone(name, position, size)
    
    # Create differential pairs for sensitive signals
    differential_pairs = [
        ("audio_pair", "left_channel", "right_channel", 0.2, 0.1),
        ("power_pair", "vcc", "gnd", 0.3, 0.15)
    ]
    
    for name, net1, net2, width, gap in differential_pairs:
        routing.create_differential_pair(name, net1, net2, width, gap)
        routing.match_trace_lengths(name)
    
    # Validate thermal design
    thermal_errors = thermal.validate_thermal_design()
    if thermal_errors:
        print("\nThermal design issues:")
        for error in thermal_errors:
            print(f"  {error}")
    
    # Validate routing
    routing_errors = routing.validate_routing()
    if routing_errors:
        print("\nRouting issues:")
        for error in routing_errors:
            print(f"  {error}")

def main():
    """Main function."""
    # Get the board path from command line or use default
    board_path = os.getenv("BOARD_PATH", "examples/audio_amplifier.kicad_pcb")
    
    print("Signal Integrity Analysis Example")
    print("================================")
    
    # Analyze signal integrity
    analyze_signal_integrity(board_path)
    
    # Optimize design
    optimize_design(board_path)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main() 
