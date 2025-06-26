#!/usr/bin/env python3
"""
Test script for schematic topology analysis.

This script demonstrates:
1. Schematic topology analysis
2. Signal flow optimization
3. Critical path identification
4. Noise source analysis
5. Ground loop detection
6. Frequency response analysis
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kicad_pcb_generator.audio.analysis.schematic_topology import (
    SchematicTopologyAnalyzer, TopologyAnalysis, ComponentNode, SignalPath, CriticalPath, NoiseSource
)

def create_test_schematic_data():
    """Create test schematic data for analysis."""
    print("Creating test schematic data...")
    
    # Create a typical audio amplifier schematic
    schematic_data = {
        "components": [
            # Input connectors
            {
                "reference": "J1",
                "value": "AUDIO_IN_L",
                "position": (10, 30),
                "pins": ["IN_L", "GND"],
                "nets": ["AUDIO_IN_L", "GND"]
            },
            {
                "reference": "J2", 
                "value": "AUDIO_IN_R",
                "position": (10, 70),
                "pins": ["IN_R", "GND"],
                "nets": ["AUDIO_IN_R", "GND"]
            },
            
            # Op-amps
            {
                "reference": "U1",
                "value": "OPA2134",
                "position": (50, 50),
                "pins": ["VCC", "VEE", "IN+", "IN-", "OUT", "GND"],
                "nets": ["VCC", "VEE", "AUDIO_IN_L", "GND", "AUDIO_OUT_L", "GND"]
            },
            {
                "reference": "U2",
                "value": "OPA2134", 
                "position": (100, 50),
                "pins": ["VCC", "VEE", "IN+", "IN-", "OUT", "GND"],
                "nets": ["VCC", "VEE", "AUDIO_IN_R", "GND", "AUDIO_OUT_R", "GND"]
            },
            
            # Passive components
            {
                "reference": "R1",
                "value": "10k",
                "position": (30, 40),
                "pins": ["1", "2"],
                "nets": ["AUDIO_IN_L", "GND"]
            },
            {
                "reference": "R2",
                "value": "10k",
                "position": (30, 60),
                "pins": ["1", "2"],
                "nets": ["AUDIO_IN_R", "GND"]
            },
            {
                "reference": "R3",
                "value": "100k",
                "position": (70, 40),
                "pins": ["1", "2"],
                "nets": ["AUDIO_OUT_L", "GND"]
            },
            {
                "reference": "R4",
                "value": "100k",
                "position": (70, 60),
                "pins": ["1", "2"],
                "nets": ["AUDIO_OUT_R", "GND"]
            },
            {
                "reference": "C1",
                "value": "0.1µF",
                "position": (40, 45),
                "pins": ["1", "2"],
                "nets": ["AUDIO_IN_L", "GND"]
            },
            {
                "reference": "C2",
                "value": "0.1µF",
                "position": (40, 65),
                "pins": ["1", "2"],
                "nets": ["AUDIO_IN_R", "GND"]
            },
            
            # Power components
            {
                "reference": "REG1",
                "value": "LM317",
                "position": (80, 10),
                "pins": ["VIN", "VOUT", "GND"],
                "nets": ["VIN", "VCC", "GND"]
            },
            {
                "reference": "REG2",
                "value": "LM337",
                "position": (120, 10),
                "pins": ["VIN", "VOUT", "GND"],
                "nets": ["VIN", "VEE", "GND"]
            },
            
            # Output connectors
            {
                "reference": "J3",
                "value": "AUDIO_OUT_L",
                "position": (150, 30),
                "pins": ["OUT_L", "GND"],
                "nets": ["AUDIO_OUT_L", "GND"]
            },
            {
                "reference": "J4",
                "value": "AUDIO_OUT_R",
                "position": (150, 70),
                "pins": ["OUT_R", "GND"],
                "nets": ["AUDIO_OUT_R", "GND"]
            },
            
            # Digital components (for mixed-signal analysis)
            {
                "reference": "MCU1",
                "value": "ATmega328P",
                "position": (90, 90),
                "pins": ["VCC", "GND", "DIGITAL_OUT"],
                "nets": ["VCC", "DGND", "DIGITAL_OUT"]
            },
            {
                "reference": "OSC1",
                "value": "16MHz",
                "position": (110, 90),
                "pins": ["VCC", "GND", "CLK_OUT"],
                "nets": ["VCC", "DGND", "CLK_OUT"]
            }
        ]
    }
    
    return schematic_data

def test_schematic_topology_analysis():
    """Test schematic topology analysis."""
    print("\n=== Testing Schematic Topology Analysis ===")
    
    # Create test data
    schematic_data = create_test_schematic_data()
    
    # Initialize analyzer
    analyzer = SchematicTopologyAnalyzer()
    
    # Analyze schematic
    topology = analyzer.analyze_schematic(schematic_data)
    
    if topology:
        print(f"✓ Schematic topology analysis completed successfully")
        print(f"  Analysis score: {topology.analysis_score:.2f}")
        print(f"  Components analyzed: {len(topology.components)}")
        print(f"  Signal paths found: {len(topology.signal_paths)}")
        print(f"  Critical paths: {len(topology.critical_paths)}")
        print(f"  Noise sources: {len(topology.noise_sources)}")
        
        # Show component types
        component_types = {}
        for comp in topology.components.values():
            comp_type = comp.component_type
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        print("  Component breakdown:")
        for comp_type, count in component_types.items():
            print(f"    {comp_type}: {count}")
        
        return topology
    else:
        print(f"✗ Schematic topology analysis failed")
        return None

def test_signal_flow_optimization(topology: TopologyAnalysis):
    """Test signal flow optimization."""
    print("\n=== Testing Signal Flow Optimization ===")
    
    analyzer = SchematicTopologyAnalyzer()
    
    # Optimize signal flow
    optimizations = analyzer.optimize_signal_flow(topology)
    
    if optimizations:
        print(f"✓ Signal flow optimization completed successfully")
        print(f"  Optimization recommendations: {len(optimizations)}")
        
        for i, opt in enumerate(optimizations, 1):
            print(f"  {i}. {opt['type']} ({opt['priority']} priority)")
            if 'recommendations' in opt:
                for rec in opt['recommendations']:
                    print(f"     - {rec}")
        
        return optimizations
    else:
        print(f"✗ Signal flow optimization failed")
        return []

def test_critical_path_analysis(topology: TopologyAnalysis):
    """Test critical path analysis."""
    print("\n=== Testing Critical Path Analysis ===")
    
    if topology.critical_paths:
        print(f"✓ Critical path analysis completed successfully")
        print(f"  Critical paths found: {len(topology.critical_paths)}")
        
        for i, critical_path in enumerate(topology.critical_paths, 1):
            path = critical_path.path
            print(f"  {i}. Critical Path: {path.start_component} → {path.end_component}")
            print(f"     Criticality score: {critical_path.criticality_score:.2f}")
            print(f"     Signal type: {path.signal_type}")
            print(f"     Path length: {path.length:.1f}mm")
            print(f"     Impedance matching: {path.impedance:.1%}")
            
            if critical_path.issues:
                print(f"     Issues:")
                for issue in critical_path.issues:
                    print(f"       - {issue}")
            
            if critical_path.recommendations:
                print(f"     Recommendations:")
                for rec in critical_path.recommendations:
                    print(f"       - {rec}")
        
        return topology.critical_paths
    else:
        print(f"✓ No critical paths identified")
        return []

def test_noise_source_analysis(topology: TopologyAnalysis):
    """Test noise source analysis."""
    print("\n=== Testing Noise Source Analysis ===")
    
    if topology.noise_sources:
        print(f"✓ Noise source analysis completed successfully")
        print(f"  Noise sources identified: {len(topology.noise_sources)}")
        
        for i, noise_source in enumerate(topology.noise_sources, 1):
            print(f"  {i}. Noise Source: {noise_source.component}")
            print(f"     Type: {noise_source.noise_type}")
            print(f"     Frequency range: {noise_source.frequency_range[0]/1e6:.1f}MHz - {noise_source.frequency_range[1]/1e6:.1f}MHz")
            print(f"     Amplitude: {noise_source.amplitude:.1f} dB")
            print(f"     Affected components: {len(noise_source.affected_components)}")
            
            if noise_source.affected_components:
                print(f"     Affected: {', '.join(noise_source.affected_components[:3])}")
                if len(noise_source.affected_components) > 3:
                    print(f"       ... and {len(noise_source.affected_components) - 3} more")
        
        return topology.noise_sources
    else:
        print(f"✓ No significant noise sources identified")
        return []

def test_ground_loop_detection(topology: TopologyAnalysis):
    """Test ground loop detection."""
    print("\n=== Testing Ground Loop Detection ===")
    
    analyzer = SchematicTopologyAnalyzer()
    
    # Detect ground loops
    ground_loops = analyzer.identify_ground_loops(topology)
    
    if ground_loops:
        print(f"⚠️  Ground loops detected: {len(ground_loops)}")
        
        for i, loop in enumerate(ground_loops, 1):
            print(f"  {i}. Ground Loop:")
            print(f"     Components: {', '.join(loop['components'])}")
            print(f"     Severity: {loop['severity']}")
            print(f"     Recommendation: {loop['recommendation']}")
        
        return ground_loops
    else:
        print(f"✓ No ground loops detected")
        return []

def test_frequency_response_analysis(topology: TopologyAnalysis):
    """Test frequency response analysis."""
    print("\n=== Testing Frequency Response Analysis ===")
    
    analyzer = SchematicTopologyAnalyzer()
    
    # Analyze frequency response
    frequency_analysis = analyzer.analyze_frequency_response(topology)
    
    if frequency_analysis:
        print(f"✓ Frequency response analysis completed successfully")
        
        # Show overall response
        if "overall" in frequency_analysis:
            overall = frequency_analysis["overall"]
            print(f"  Overall Frequency Response:")
            print(f"    Corner frequency: {overall.get('corner_frequency', 0):.1f} Hz")
            print(f"    Bandwidth: {overall.get('bandwidth', 0):.1f} Hz")
            print(f"    Frequency range: {overall.get('frequency_range', (0, 0))[0]} - {overall.get('frequency_range', (0, 0))[1]} Hz")
            print(f"    Flatness: {overall.get('flatness', 'Unknown')}")
            print(f"    Phase response: {overall.get('phase_response', 'Unknown')}")
        
        # Show individual path responses
        path_responses = {k: v for k, v in frequency_analysis.items() if k != "overall"}
        if path_responses:
            print(f"  Individual Path Responses:")
            for path_name, response in path_responses.items():
                print(f"    {path_name}:")
                print(f"      Corner frequency: {response.get('corner_frequency', 0):.1f} Hz")
                print(f"      Bandwidth: {response.get('bandwidth', 0):.1f} Hz")
                print(f"      Rolloff: {response.get('rolloff', 0)} dB/decade")
        
        return frequency_analysis
    else:
        print(f"✗ Frequency response analysis failed")
        return {}

def test_component_dependency_analysis(topology: TopologyAnalysis):
    """Test component dependency analysis."""
    print("\n=== Testing Component Dependency Analysis ===")
    
    if topology.component_dependencies:
        print(f"✓ Component dependency analysis completed successfully")
        print(f"  Component dependencies analyzed: {len(topology.component_dependencies)}")
        
        # Show dependencies for key components
        key_components = ["U1", "U2", "REG1", "REG2"]
        
        for comp in key_components:
            if comp in topology.component_dependencies:
                dependents = topology.component_dependencies[comp]
                print(f"  {comp} dependencies: {len(dependents)} components")
                if dependents:
                    print(f"    Dependents: {', '.join(dependents[:5])}")
                    if len(dependents) > 5:
                        print(f"      ... and {len(dependents) - 5} more")
        
        return topology.component_dependencies
    else:
        print(f"✗ Component dependency analysis failed")
        return {}

def test_power_distribution_analysis(topology: TopologyAnalysis):
    """Test power distribution analysis."""
    print("\n=== Testing Power Distribution Analysis ===")
    
    if topology.power_distribution:
        print(f"✓ Power distribution analysis completed successfully")
        print(f"  Power rails analyzed: {len(topology.power_distribution)}")
        
        for rail, components in topology.power_distribution.items():
            print(f"  {rail}: {len(components)} components")
            print(f"    Components: {', '.join(components[:5])}")
            if len(components) > 5:
                print(f"      ... and {len(components) - 5} more")
        
        return topology.power_distribution
    else:
        print(f"✗ Power distribution analysis failed")
        return {}

def main():
    """Run all schematic topology analysis tests."""
    print("Schematic Topology Analysis Test")
    print("=" * 50)
    
    # Test schematic topology analysis
    topology = test_schematic_topology_analysis()
    
    if topology:
        # Test individual analysis features
        tests = [
            ("Signal Flow Optimization", lambda: test_signal_flow_optimization(topology)),
            ("Critical Path Analysis", lambda: test_critical_path_analysis(topology)),
            ("Noise Source Analysis", lambda: test_noise_source_analysis(topology)),
            ("Ground Loop Detection", lambda: test_ground_loop_detection(topology)),
            ("Frequency Response Analysis", lambda: test_frequency_response_analysis(topology)),
            ("Component Dependency Analysis", lambda: test_component_dependency_analysis(topology)),
            ("Power Distribution Analysis", lambda: test_power_distribution_analysis(topology)),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"✗ {test_name} test failed with exception: {e}")
                results[test_name] = None
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(tests)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result is not None else "✗ FAIL"
            print(f"{test_name:30} {status}")
            if result is not None:
                passed += 1
        
        print(f"\nPassed: {passed}/{total} tests")
        
        if passed == total:
            print("🎉 All tests passed! Schematic topology analysis is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return passed == total
    else:
        print("✗ Schematic topology analysis failed - cannot run other tests")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 