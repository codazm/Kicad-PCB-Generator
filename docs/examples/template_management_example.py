#!/usr/bin/env python3
"""
Template Management Example

This example demonstrates how to use the template management features of the
KiCad PCB Generator for creating, managing, and using PCB design templates.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from kicad_pcb_generator import PCBGenerator
from kicad_pcb_generator.core.templates import (
    TemplateManager,
    VersionManager,
    TemplateImportExport
)

def create_templates(template_manager: TemplateManager) -> None:
    """Create example templates."""
    print("Creating templates...")
    
    # Create audio amplifier template
    amplifier_template = template_manager.create_template(
        name="Audio Amplifier",
        category="audio",
        description="Template for audio amplifier PCB design with power supply"
    )
    print(f"Created template: {amplifier_template.name}")
    
    # Create filter template
    filter_template = template_manager.create_template(
        name="Audio Filter",
        category="audio",
        description="Template for audio filter PCB design"
    )
    print(f"Created template: {filter_template.name}")
    
    # Create power supply template
    power_template = template_manager.create_template(
        name="Power Supply",
        category="power",
        description="Template for power supply PCB design"
    )
    print(f"Created template: {power_template.name}")

def manage_versions(version_manager: VersionManager,
                   template_id: str) -> None:
    """Demonstrate version management features."""
    print("\nManaging versions...")
    
    # Create initial version
    version1 = version_manager.create_version(
        template_id=template_id,
        version="1.0.0",
        changes="Initial version"
    )
    print(f"Created version: {version1.version}")
    
    # Create updated version
    version2 = version_manager.create_version(
        template_id=template_id,
        version="1.1.0",
        changes="Added power supply section"
    )
    print(f"Created version: {version2.version}")
    
    # List versions
    versions = version_manager.list_versions(template_id)
    print("\nVersion history:")
    for version in versions:
        print(f"  {version.version}: {version.changes}")
    
    # Compare versions
    diff = version_manager.compare_versions(
        template_id=template_id,
        version1="1.0.0",
        version2="1.1.0"
    )
    print("\nVersion comparison:")
    print(f"  Changes: {diff['changes']}")
    print(f"  Added components: {diff['added_components']}")
    print(f"  Modified components: {diff['modified_components']}")

def import_export_templates(io_manager: TemplateImportExport,
                          template_id: str) -> None:
    """Demonstrate import/export features."""
    print("\nImport/Export operations...")
    
    # Export template
    output_path = "templates/audio_amplifier.json"
    io_manager.export_template(template_id, output_path)
    print(f"Exported template to: {output_path}")
    
    # Import template
    imported_template = io_manager.import_template(output_path)
    print(f"Imported template: {imported_template.name}")
    
    # Export all templates
    output_dir = "templates"
    io_manager.export_all_templates(output_dir)
    print(f"Exported all templates to: {output_dir}")
    
    # Import all templates
    imported_templates = io_manager.import_templates(output_dir)
    print(f"Imported {len(imported_templates)} templates")

def main():
    """Main function."""
    # Initialize the generator
    generator = PCBGenerator()
    
    # Initialize managers
    template_manager = TemplateManager()
    version_manager = VersionManager(template_manager)
    io_manager = TemplateImportExport(template_manager)
    
    print("Template Management Example")
    print("==========================")
    
    # Create templates
    create_templates(template_manager)
    
    # List templates
    templates = template_manager.list_templates()
    print("\nAvailable templates:")
    for template in templates:
        print(f"  {template.name} ({template.category})")
    
    # Get audio amplifier template
    amplifier_template = template_manager.get_template(
        template_manager.list_templates(category="audio")[0].id
    )
    
    # Manage versions
    manage_versions(version_manager, amplifier_template.id)
    
    # Import/Export operations
    import_export_templates(io_manager, amplifier_template.id)
    
    print("\nExample complete!")

if __name__ == "__main__":
    main() 
