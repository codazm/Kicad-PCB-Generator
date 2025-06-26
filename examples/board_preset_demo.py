#!/usr/bin/env python3
"""
Demonstration of the Board Preset System

This script shows how the modular board size preset registry works
for common audio PCB standards without requiring KiCad installation.
"""

import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kicad_pcb_generator.core.templates.board_presets import (
    BoardProfile, 
    board_preset_registry
)


def demo_board_presets():
    """Demonstrate the board preset system functionality."""
    print("=" * 60)
    print("KiCad PCB Generator - Board Preset System Demo")
    print("=" * 60)
    print()
    
    # List all available presets
    print("Available Board Size Presets:")
    print("-" * 40)
    presets = board_preset_registry.list_presets()
    
    for profile, preset in presets.items():
        print(f"{profile.value:20} - {preset.name}")
        print(f"{'':20}   {preset.description}")
        print(f"{'':20}   {preset.width_mm}mm x {preset.height_mm}mm")
        print()
    
    # Show detailed information for Eurorack 3U
    print("Detailed Eurorack 3U Preset:")
    print("-" * 40)
    eurorack_3u = board_preset_registry.get_preset(BoardProfile.EURORACK_3U)
    if eurorack_3u:
        print(f"Name: {eurorack_3u.name}")
        print(f"Description: {eurorack_3u.description}")
        print(f"Dimensions: {eurorack_3u.width_mm}mm x {eurorack_3u.height_mm}mm")
        print(f"Max Thickness: {eurorack_3u.max_thickness_mm}mm")
        print(f"Min Track Width: {eurorack_3u.min_track_width_mm}mm")
        print(f"Min Via Diameter: {eurorack_3u.min_via_diameter_mm}mm")
        print(f"Min Clearance: {eurorack_3u.min_clearance_mm}mm")
        print(f"Max Component Height: {eurorack_3u.max_component_height_mm}mm")
        print(f"Edge Clearance: {eurorack_3u.edge_clearance_mm}mm")
        if eurorack_3u.mounting_holes:
            print(f"Mounting Holes: {eurorack_3u.mounting_holes}")
        print()
    
    # Demonstrate board size validation
    print("Board Size Validation Examples:")
    print("-" * 40)
    
    # Test valid dimensions
    is_valid = board_preset_registry.validate_board_size(128.5, 128.5, BoardProfile.EURORACK_3U)
    print(f"128.5mm x 128.5mm for Eurorack 3U: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Test with tolerance
    is_valid = board_preset_registry.validate_board_size(127.5, 129.5, BoardProfile.EURORACK_3U)
    print(f"127.5mm x 129.5mm for Eurorack 3U: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Test invalid dimensions
    is_valid = board_preset_registry.validate_board_size(100.0, 100.0, BoardProfile.EURORACK_3U)
    print(f"100.0mm x 100.0mm for Eurorack 3U: {'✓ Valid' if is_valid else '✗ Invalid'}")
    print()
    
    # Show manufacturing constraints
    print("Manufacturing Constraints for Eurorack 3U:")
    print("-" * 40)
    constraints = board_preset_registry.get_manufacturing_constraints(BoardProfile.EURORACK_3U)
    if constraints:
        for key, value in constraints.items():
            print(f"  {key}: {value}")
    print()
    
    # Demonstrate CLI usage examples
    print("CLI Usage Examples:")
    print("-" * 40)
    print("# List all board presets:")
    print("kicadpcb board-presets")
    print()
    print("# Show details for a specific preset:")
    print("kicadpcb board-presets --preset 'Eurorack 3U'")
    print()
    print("# Create project with board preset:")
    print("kicadpcb create my_amp --template basic_audio_amp --board-preset 'Eurorack 3U'")
    print()
    print("# Generate PCB with board preset:")
    print("kicadpcb generate my_amp --schematic circuit.kicad_sch --board-preset 'Standard Guitar Pedal'")
    print()
    
    # Show preset names mapping
    print("Preset Names Mapping:")
    print("-" * 40)
    names = board_preset_registry.get_preset_names()
    for profile_value, display_name in names.items():
        print(f"  {profile_value:20} -> {display_name}")
    print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print("The board preset system provides standardized board sizes")
    print("for common audio PCB standards with validation and constraints.")
    print("=" * 60)


if __name__ == "__main__":
    demo_board_presets() 