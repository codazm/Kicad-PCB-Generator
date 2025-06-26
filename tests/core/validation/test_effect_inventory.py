"""Tests for the effect inventory system."""
import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
from pathlib import Path
from ....src.kicad_pcb_generator.core.validation.effect_inventory import (
    EffectInventory,
    EffectMetadata,
    EffectCategory
)

class TestEffectInventory(unittest.TestCase):
    """Test cases for the effect inventory system."""

    def setUp(self):
        """Set up test fixtures."""
        self.inventory = EffectInventory()

    def test_register_and_get_effect(self):
        """Test registering and retrieving an effect."""
        # Create test effect metadata
        metadata = EffectMetadata(
            name="Test Effect",
            description="A test effect",
            categories={EffectCategory.UTILITY},
            tags={"test", "utility"},
            config_class=MagicMock,
            validator_class=MagicMock,
            parameters={
                "param1": {"min": 0, "max": 100, "default": 50},
                "param2": {"options": ["a", "b", "c"], "default": "a"}
            },
            version="1.0.0",
            author="Test Author",
            dependencies={"base_effect"},
            documentation_url="https://docs.example.com/test"
        )
        
        # Register the effect
        self.inventory.register_effect("test_effect", metadata)
        
        # Retrieve and verify
        retrieved = self.inventory.get_effect("test_effect")
        self.assertEqual(retrieved.name, "Test Effect")
        self.assertEqual(retrieved.description, "A test effect")
        self.assertEqual(retrieved.categories, {EffectCategory.UTILITY})
        self.assertEqual(retrieved.tags, {"test", "utility"})
        self.assertEqual(retrieved.parameters["param1"]["default"], 50)
        self.assertEqual(retrieved.version, "1.0.0")
        self.assertEqual(retrieved.author, "Test Author")
        self.assertEqual(retrieved.dependencies, {"base_effect"})
        self.assertEqual(retrieved.documentation_url, "https://docs.example.com/test")

    def test_register_duplicate_effect(self):
        """Test registering a duplicate effect."""
        metadata = EffectMetadata(
            name="Test Effect",
            description="A test effect",
            categories={EffectCategory.UTILITY},
            tags={"test"}
        )
        
        # Register first time
        self.inventory.register_effect("test_effect", metadata)
        
        # Try to register again
        with self.assertRaises(ValueError):
            self.inventory.register_effect("test_effect", metadata)

    def test_register_effect_with_missing_dependency(self):
        """Test registering an effect with a missing dependency."""
        metadata = EffectMetadata(
            name="Test Effect",
            description="A test effect",
            categories={EffectCategory.UTILITY},
            tags={"test"},
            dependencies={"nonexistent_effect"}
        )
        
        with self.assertRaises(ValueError):
            self.inventory.register_effect("test_effect", metadata)

    def test_unregister_effect(self):
        """Test unregistering an effect."""
        metadata = EffectMetadata(
            name="Test Effect",
            description="A test effect",
            categories={EffectCategory.UTILITY},
            tags={"test"}
        )
        
        # Register the effect
        self.inventory.register_effect("test_effect", metadata)
        
        # Unregister
        self.inventory.unregister_effect("test_effect")
        
        # Verify it's gone
        with self.assertRaises(ValueError):
            self.inventory.get_effect("test_effect")

    def test_unregister_effect_with_dependencies(self):
        """Test unregistering an effect that other effects depend on."""
        # Register base effect
        base_metadata = EffectMetadata(
            name="Base Effect",
            description="A base effect",
            categories={EffectCategory.UTILITY},
            tags={"base"}
        )
        self.inventory.register_effect("base_effect", base_metadata)
        
        # Register dependent effect
        dependent_metadata = EffectMetadata(
            name="Dependent Effect",
            description="A dependent effect",
            categories={EffectCategory.UTILITY},
            tags={"dependent"},
            dependencies={"base_effect"}
        )
        self.inventory.register_effect("dependent_effect", dependent_metadata)
        
        # Try to unregister base effect
        with self.assertRaises(ValueError):
            self.inventory.unregister_effect("base_effect")

    def test_get_effects_by_category(self):
        """Test getting effects by category."""
        # Get all distortion effects
        distortion_effects = self.inventory.get_effects_by_category(EffectCategory.DISTORTION)
        
        # Verify we got the distortion effect
        self.assertTrue(any(effect.name == "Distortion" for effect in distortion_effects))
        
        # Get all synth effects
        synth_effects = self.inventory.get_effects_by_category(EffectCategory.SYNTH)
        
        # Verify we got the VCO, VCF, and VCA
        self.assertTrue(any(effect.name == "Voltage Controlled Oscillator" for effect in synth_effects))
        self.assertTrue(any(effect.name == "Voltage Controlled Filter" for effect in synth_effects))
        self.assertTrue(any(effect.name == "Voltage Controlled Amplifier" for effect in synth_effects))

    def test_get_effects_by_tag(self):
        """Test getting effects by tag."""
        # Get all guitar effects
        guitar_effects = self.inventory.get_effects_by_tag("guitar")
        
        # Verify we got the distortion, delay, and chorus
        self.assertTrue(any(effect.name == "Distortion" for effect in guitar_effects))
        self.assertTrue(any(effect.name == "Delay" for effect in guitar_effects))
        self.assertTrue(any(effect.name == "Chorus" for effect in guitar_effects))
        
        # Get all modular effects
        modular_effects = self.inventory.get_effects_by_tag("modular")
        
        # Verify we got the VCO, VCF, and VCA
        self.assertTrue(any(effect.name == "Voltage Controlled Oscillator" for effect in modular_effects))
        self.assertTrue(any(effect.name == "Voltage Controlled Filter" for effect in modular_effects))
        self.assertTrue(any(effect.name == "Voltage Controlled Amplifier" for effect in modular_effects))

    def test_get_effects_by_author(self):
        """Test getting effects by author."""
        # Get all effects by System
        system_effects = self.inventory.get_effects_by_author("System")
        
        # Verify we got all the default effects
        self.assertTrue(all(effect.author == "System" for effect in system_effects))
        self.assertTrue(len(system_effects) > 0)

    def test_get_effects_by_version(self):
        """Test getting effects by version."""
        # Get all effects with version 1.0.0
        v1_effects = self.inventory.get_effects_by_version("1.0.0")
        
        # Verify we got all the default effects
        self.assertTrue(all(effect.version == "1.0.0" for effect in v1_effects))
        self.assertTrue(len(v1_effects) > 0)

    def test_get_effect_parameters(self):
        """Test getting effect parameters."""
        # Get parameters for distortion effect
        params = self.inventory.get_effect_parameters("distortion")
        
        # Verify parameters
        self.assertIn("gain", params)
        self.assertIn("tone", params)
        self.assertIn("volume", params)
        self.assertEqual(params["gain"]["default"], 50)

    def test_get_effect_dependencies(self):
        """Test getting effect dependencies."""
        # Register base effect
        base_metadata = EffectMetadata(
            name="Base Effect",
            description="A base effect",
            categories={EffectCategory.UTILITY},
            tags={"base"}
        )
        self.inventory.register_effect("base_effect", base_metadata)
        
        # Register dependent effect
        dependent_metadata = EffectMetadata(
            name="Dependent Effect",
            description="A dependent effect",
            categories={EffectCategory.UTILITY},
            tags={"dependent"},
            dependencies={"base_effect"}
        )
        self.inventory.register_effect("dependent_effect", dependent_metadata)
        
        # Get dependencies
        deps = self.inventory.get_effect_dependencies("dependent_effect")
        self.assertEqual(deps, {"base_effect"})

    def test_validate_effect_dependencies(self):
        """Test validating effect dependencies."""
        # Register base effect
        base_metadata = EffectMetadata(
            name="Base Effect",
            description="A base effect",
            categories={EffectCategory.UTILITY},
            tags={"base"}
        )
        self.inventory.register_effect("base_effect", base_metadata)
        
        # Register dependent effect
        dependent_metadata = EffectMetadata(
            name="Dependent Effect",
            description="A dependent effect",
            categories={EffectCategory.UTILITY},
            tags={"dependent"},
            dependencies={"base_effect"}
        )
        self.inventory.register_effect("dependent_effect", dependent_metadata)
        
        # Validate dependencies
        is_valid, missing = self.inventory.validate_effect_dependencies("dependent_effect")
        self.assertTrue(is_valid)
        self.assertEqual(missing, [])
        
        # Test with missing dependency
        metadata = EffectMetadata(
            name="Test Effect",
            description="A test effect",
            categories={EffectCategory.UTILITY},
            tags={"test"},
            dependencies={"nonexistent_effect"}
        )
        self.inventory.register_effect("test_effect", metadata)
        
        is_valid, missing = self.inventory.validate_effect_dependencies("test_effect")
        self.assertFalse(is_valid)
        self.assertEqual(missing, ["nonexistent_effect"])

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_config(self, mock_json_load, mock_file):
        """Test loading effect configuration from file."""
        # Mock configuration data
        mock_json_load.return_value = {
            "test_effect": {
                "name": "Test Effect",
                "description": "A test effect",
                "categories": ["UTILITY"],
                "tags": ["test", "utility"],
                "parameters": {
                    "param1": {"min": 0, "max": 100, "default": 50}
                },
                "version": "1.0.0",
                "author": "Test Author",
                "dependencies": [],
                "documentation_url": "https://docs.example.com/test"
            }
        }
        
        # Create inventory with config path
        inventory = EffectInventory(Path("test_config.json"))
        
        # Verify effect was loaded
        effect = inventory.get_effect("test_effect")
        self.assertEqual(effect.name, "Test Effect")
        self.assertEqual(effect.categories, {EffectCategory.UTILITY})
        self.assertEqual(effect.parameters["param1"]["default"], 50)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_config(self, mock_file):
        """Test saving effect configuration to file."""
        # Create test effect
        metadata = EffectMetadata(
            name="Test Effect",
            description="A test effect",
            categories={EffectCategory.UTILITY},
            tags={"test", "utility"},
            parameters={"param1": {"min": 0, "max": 100, "default": 50}},
            version="1.0.0",
            author="Test Author",
            documentation_url="https://docs.example.com/test"
        )
        self.inventory.register_effect("test_effect", metadata)
        
        # Save configuration
        self.inventory.save_config(Path("test_config.json"))
        
        # Verify file was written with correct data
        mock_file.assert_called_once_with(Path("test_config.json"), 'w')
        written_data = json.loads(mock_file().write.call_args[0][0])
        self.assertEqual(written_data["test_effect"]["name"], "Test Effect")
        self.assertEqual(written_data["test_effect"]["categories"], ["UTILITY"])
        self.assertEqual(written_data["test_effect"]["parameters"]["param1"]["default"], 50) 