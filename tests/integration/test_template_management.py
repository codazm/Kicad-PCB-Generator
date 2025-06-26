"""
Integration tests for template management system.
"""

import unittest
import os
import shutil
import tempfile
from datetime import datetime

from kicad_pcb_generator.core.templates import (
    TemplateManager,
    VersionManager,
    TemplateImportExport,
    Template,
    TemplateVersion
)

class TestTemplateManagementIntegration(unittest.TestCase):
    """Integration tests for template management system."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.template_manager = TemplateManager()
        self.version_manager = VersionManager(self.template_manager)
        self.io_manager = TemplateImportExport(self.template_manager)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_template_creation_and_retrieval(self):
        """Test template creation and retrieval."""
        # Create template
        template = self.template_manager.create_template(
            name="Audio Amplifier",
            category="audio",
            description="Template for audio amplifier PCB design"
        )
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Audio Amplifier")
        self.assertEqual(template.category, "audio")

        # Retrieve template
        retrieved = self.template_manager.get_template(template.id)
        self.assertEqual(retrieved.id, template.id)
        self.assertEqual(retrieved.name, template.name)

    def test_template_listing_and_filtering(self):
        """Test template listing and filtering."""
        # Create templates
        self.template_manager.create_template(
            name="Audio Amplifier",
            category="audio",
            description="Template for audio amplifier PCB design"
        )
        self.template_manager.create_template(
            name="Power Supply",
            category="power",
            description="Template for power supply PCB design"
        )

        # List all templates
        all_templates = self.template_manager.list_templates()
        self.assertEqual(len(all_templates), 2)

        # List audio templates
        audio_templates = self.template_manager.list_templates(category="audio")
        self.assertEqual(len(audio_templates), 1)
        self.assertEqual(audio_templates[0].category, "audio")

    def test_template_versioning(self):
        """Test template versioning functionality."""
        # Create template
        template = self.template_manager.create_template(
            name="Audio Amplifier",
            category="audio",
            description="Template for audio amplifier PCB design"
        )

        # Create versions
        version1 = self.version_manager.create_version(
            template_id=template.id,
            version="1.0.0",
            changes="Initial version"
        )
        self.assertEqual(version1.version, "1.0.0")

        version2 = self.version_manager.create_version(
            template_id=template.id,
            version="1.1.0",
            changes="Added power supply section"
        )
        self.assertEqual(version2.version, "1.1.0")

        # List versions
        versions = self.version_manager.list_versions(template.id)
        self.assertEqual(len(versions), 2)

        # Compare versions
        diff = self.version_manager.compare_versions(
            template_id=template.id,
            version1="1.0.0",
            version2="1.1.0"
        )
        self.assertIn("changes", diff)
        self.assertIn("added_components", diff)
        self.assertIn("modified_components", diff)

    def test_template_import_export(self):
        """Test template import and export functionality."""
        # Create template
        template = self.template_manager.create_template(
            name="Audio Amplifier",
            category="audio",
            description="Template for audio amplifier PCB design"
        )

        # Export template
        export_path = os.path.join(self.test_dir, "template.json")
        self.io_manager.export_template(template.id, export_path)
        self.assertTrue(os.path.exists(export_path))

        # Import template
        imported = self.io_manager.import_template(export_path)
        self.assertEqual(imported.name, template.name)
        self.assertEqual(imported.category, template.category)

    def test_template_update_and_delete(self):
        """Test template update and delete functionality."""
        # Create template
        template = self.template_manager.create_template(
            name="Audio Amplifier",
            category="audio",
            description="Template for audio amplifier PCB design"
        )

        # Update template
        updated = self.template_manager.update_template(
            template_id=template.id,
            updates={
                "name": "Updated Amplifier",
                "description": "Updated description"
            }
        )
        self.assertEqual(updated.name, "Updated Amplifier")
        self.assertEqual(updated.description, "Updated description")

        # Delete template
        self.template_manager.delete_template(template.id)
        templates = self.template_manager.list_templates()
        self.assertEqual(len(templates), 0)

    def test_template_validation(self):
        """Test template validation functionality."""
        # Create template with invalid data
        template = self.template_manager.create_template(
            name="",  # Invalid empty name
            category="audio",
            description="Template for audio amplifier PCB design"
        )

        # Validate template
        validation_results = self.template_manager.validate_template(template.id)
        self.assertFalse(validation_results.is_valid)
        self.assertGreater(len(validation_results.errors), 0)

    def test_template_search(self):
        """Test template search functionality."""
        # Create templates
        self.template_manager.create_template(
            name="Audio Amplifier",
            category="audio",
            description="Template for audio amplifier PCB design"
        )
        self.template_manager.create_template(
            name="Power Supply",
            category="power",
            description="Template for power supply PCB design"
        )

        # Search by name
        results = self.template_manager.search_templates("Amplifier")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Audio Amplifier")

        # Search by category
        results = self.template_manager.search_templates("power")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].category, "power")

if __name__ == '__main__':
    unittest.main() 