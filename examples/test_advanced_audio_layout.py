#!/usr/bin/env python3
"""
Test script for advanced audio layout features.

This script demonstrates:
1. Star grounding implementation
2. Analog/digital ground separation
3. Advanced audio component placement
4. Power decoupling optimization
5. Power supply rejection analysis
"""

import sys
import os
import pcbnew
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kicad_pcb_generator.audio.layout.converter import AudioLayoutConverter, StarGroundResult, GroundSeparationResult
from kicad_pcb_generator.audio.layout.power_decoupling import PowerDecouplingOptimizer, DecouplingResult

def create_test_board():
    """Create a test board with audio components."""
    print("Creating test board with audio components...")
    
    # Create a new board
    board = pcbnew.BOARD()
    
    # Set board properties
    board.SetBoardThickness(1.6)
    board.SetCopperWeight(1)
    
    # Enable layers
    board.SetEnabledLayers(
        pcbnew.F_Cu | pcbnew.B_Cu | pcbnew.In1_Cu | pcbnew.In2_Cu |
        pcbnew.F_SilkS | pcbnew.B_SilkS | pcbnew.Edge_Cuts
    )
    
    # Create test components
    components = [
        # Op-amps
        {"ref": "U1", "value": "OPA2134", "type": "opamp", "x": 50, "y": 50},
        {"ref": "U2", "value": "OPA2134", "type": "opamp", "x": 100, "y": 50},
        
        # Input connectors
        {"ref": "J1", "value": "AUDIO_IN_L", "type": "connector", "x": 10, "y": 30},
        {"ref": "J2", "value": "AUDIO_IN_R", "type": "connector", "x": 10, "y": 70},
        
        # Output connectors
        {"ref": "J3", "value": "AUDIO_OUT_L", "type": "connector", "x": 150, "y": 30},
        {"ref": "J4", "value": "AUDIO_OUT_R", "type": "connector", "x": 150, "y": 70},
        
        # Power components
        {"ref": "REG1", "value": "LM317", "type": "regulator", "x": 80, "y": 10},
        {"ref": "REG2", "value": "LM337", "type": "regulator", "x": 120, "y": 10},
        
        # Passive components
        {"ref": "R1", "value": "10k", "type": "resistor", "x": 60, "y": 40},
        {"ref": "R2", "value": "10k", "type": "resistor", "x": 110, "y": 40},
        {"ref": "C1", "value": "0.1µF", "type": "capacitor", "x": 55, "y": 45},
        {"ref": "C2", "value": "0.1µF", "type": "capacitor", "x": 105, "y": 45},
        {"ref": "C3", "value": "10µF", "type": "capacitor", "x": 85, "y": 15},
        {"ref": "C4", "value": "10µF", "type": "capacitor", "x": 125, "y": 15},
    ]
    
    # Add components to board
    for comp in components:
        footprint = pcbnew.FOOTPRINT(board)
        footprint.SetReference(comp["ref"])
        footprint.SetValue(comp["value"])
        footprint.SetPosition(pcbnew.VECTOR2I(
            int(comp["x"] * 1e6),  # Convert mm to nanometers
            int(comp["y"] * 1e6)
        ))
        
        # Set appropriate footprint
        if comp["type"] == "opamp":
            footprint.SetFootprintName("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
        elif comp["type"] == "connector":
            footprint.SetFootprintName("Connector_Audio:Jack_3.5mm_MJ-4-4-0")
        elif comp["type"] == "regulator":
            footprint.SetFootprintName("Package_TO_SOT_THT:TO-220-3_Vertical")
        elif comp["type"] == "resistor":
            footprint.SetFootprintName("Resistor_SMD:R_0603_1608Metric")
        elif comp["type"] == "capacitor":
            footprint.SetFootprintName("Capacitor_SMD:C_0603_1608Metric")
        
        board.Add(footprint)
    
    # Create nets
    nets = [
        "VCC", "VEE", "GND", "AGND", "DGND",
        "AUDIO_IN_L", "AUDIO_IN_R", "AUDIO_OUT_L", "AUDIO_OUT_R"
    ]
    
    for net_name in nets:
        net = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(net)
    
    return board

def test_star_grounding():
    """Test star grounding implementation."""
    print("\n=== Testing Star Grounding ===")
    
    board = create_test_board()
    converter = AudioLayoutConverter()
    
    # Implement star grounding
    result = converter.implement_star_grounding(board)
    
    if result.success:
        print(f"✓ Star grounding implemented successfully")
        print(f"  Star point: ({result.star_point.x/1e6:.1f}, {result.star_point.y/1e6:.1f}) mm")
        print(f"  Ground connections: {len(result.ground_connections)}")
    else:
        print(f"✗ Star grounding failed: {result.errors}")
    
    return result.success

def test_ground_separation():
    """Test analog/digital ground separation."""
    print("\n=== Testing Ground Separation ===")
    
    board = create_test_board()
    converter = AudioLayoutConverter()
    
    # Separate analog and digital grounds
    result = converter.separate_analog_digital_grounds(board)
    
    if result.success:
        print(f"✓ Ground separation implemented successfully")
        if result.analog_ground_zone:
            print(f"  Analog ground zone created")
        if result.digital_ground_zone:
            print(f"  Digital ground zone created")
        if result.connection_point:
            print(f"  Connection point: ({result.connection_point.x/1e6:.1f}, {result.connection_point.y/1e6:.1f}) mm")
    else:
        print(f"✗ Ground separation failed: {result.errors}")
    
    return result.success

def test_audio_component_placement():
    """Test advanced audio component placement."""
    print("\n=== Testing Audio Component Placement ===")
    
    board = create_test_board()
    converter = AudioLayoutConverter()
    
    # Place audio components optimally
    success = converter.place_audio_components(board)
    
    if success:
        print(f"✓ Audio component placement completed successfully")
        
        # Show component positions
        for footprint in board.GetFootprints():
            pos = footprint.GetPosition()
            print(f"  {footprint.GetReference()}: ({pos.x/1e6:.1f}, {pos.y/1e6:.1f}) mm")
    else:
        print(f"✗ Audio component placement failed")
    
    return success

def test_power_decoupling():
    """Test power decoupling optimization."""
    print("\n=== Testing Power Decoupling Optimization ===")
    
    board = create_test_board()
    optimizer = PowerDecouplingOptimizer()
    
    # Optimize decoupling
    result = optimizer.optimize_decoupling(board)
    
    if result.success:
        print(f"✓ Power decoupling optimization completed successfully")
        print(f"  Placed capacitors: {len(result.placed_capacitors)}")
        print(f"  Power rail optimizations: {len(result.power_rail_optimizations)}")
        
        # Show voltage drop analysis
        if result.voltage_drop_analysis:
            print("  Voltage drop analysis:")
            for rail, drop in result.voltage_drop_analysis.items():
                print(f"    {rail}: {drop*1000:.1f} mV")
        
        # Show power rail optimizations
        if result.power_rail_optimizations:
            print("  Power rail optimizations:")
            for opt in result.power_rail_optimizations:
                print(f"    {opt.get('rail', 'Unknown')}: {opt.get('recommendation', 'No recommendation')}")
    else:
        print(f"✗ Power decoupling optimization failed: {result.errors}")
    
    return result.success

def test_power_supply_rejection():
    """Test power supply rejection analysis."""
    print("\n=== Testing Power Supply Rejection Analysis ===")
    
    board = create_test_board()
    optimizer = PowerDecouplingOptimizer()
    
    # Analyze PSRR
    psrr_analysis = optimizer.analyze_power_supply_rejection(board)
    
    if psrr_analysis:
        print(f"✓ PSRR analysis completed successfully")
        print("  Power Supply Rejection Ratio (PSRR):")
        for opamp, psrr in psrr_analysis.items():
            print(f"    {opamp}: {psrr:.1f} dB")
            
            # Evaluate PSRR quality
            if psrr >= 100:
                quality = "Excellent"
            elif psrr >= 80:
                quality = "Good"
            elif psrr >= 60:
                quality = "Fair"
            else:
                quality = "Poor"
            print(f"      Quality: {quality}")
    else:
        print(f"✗ PSRR analysis failed")
    
    return len(psrr_analysis) > 0

def test_integrated_layout():
    """Test integrated advanced audio layout features."""
    print("\n=== Testing Integrated Advanced Audio Layout ===")
    
    board = create_test_board()
    converter = AudioLayoutConverter()
    
    # Apply all advanced features
    try:
        converter._apply_advanced_audio_layout(board)
        print(f"✓ Integrated advanced audio layout completed successfully")
        
        # Count components
        component_count = len(list(board.GetFootprints()))
        print(f"  Total components: {component_count}")
        
        # Count tracks
        track_count = len(list(board.GetTracks()))
        print(f"  Total tracks: {track_count}")
        
        # Count zones
        zone_count = len(list(board.Zones()))
        print(f"  Total zones: {zone_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Integrated layout failed: {e}")
        return False

def main():
    """Run all advanced audio layout tests."""
    print("Advanced Audio Layout Features Test")
    print("=" * 50)
    
    # Test individual features
    tests = [
        ("Star Grounding", test_star_grounding),
        ("Ground Separation", test_ground_separation),
        ("Audio Component Placement", test_audio_component_placement),
        ("Power Decoupling", test_power_decoupling),
        ("Power Supply Rejection", test_power_supply_rejection),
        ("Integrated Layout", test_integrated_layout),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 All tests passed! Advanced audio layout features are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 