#!/usr/bin/env python3

"""
Example script demonstrating how to import a schematic and generate a PCB.
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from kicad_pcb_generator.core.schematic_importer import SchematicImporter, ImportConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function demonstrating schematic import."""
    # Get the example directory
    example_dir = Path(__file__).parent
    output_dir = example_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Create importer
    importer = SchematicImporter()
    
    # Configure import options
    config = ImportConfig(
        apply_audio_optimizations=True,
        validate_schematic=True,
        generate_3d_models=True,
        optimize_placement=True,
        optimize_routing=True
    )
    
    try:
        # Import schematic and generate PCB
        schematic_path = example_dir / "example_schematic.kicad_sch"
        pcb_path = importer.import_schematic(
            schematic_path=str(schematic_path),
            output_dir=str(output_dir),
            config=config
        )
        
        logger.info(f"Successfully generated PCB: {pcb_path}")
        
    except Exception as e:
        logger.error(f"Error importing schematic: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 