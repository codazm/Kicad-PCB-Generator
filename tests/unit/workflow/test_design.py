"""Unit tests for design variants system."""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew
from datetime import datetime
from kicad_pcb_generator.core.workflow.design import DesignVariant, DesignManager
from kicad_pcb_generator.core.components.manager import ComponentData
from kicad_pcb_generator.core.board.layer_manager import LayerProperties

class TestDesignVariant(unittest.TestCase):
    """Test design variant functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={},
            layer_stack=None,
            rules={}
        )
    
    def test_variant_initialization(self):
        """Test variant initialization."""
        self.assertEqual(self.variant.name, "test_variant")
        self.assertEqual(self.variant.description, "Test variant")
        self.assertEqual(self.variant.components, {})
        self.assertIsNone(self.variant.layer_stack)
        self.assertEqual(self.variant.rules, {})
        self.assertIsInstance(self.variant.created_at, datetime)
        self.assertIsInstance(self.variant.updated_at, datetime)
    
    def test_variant_default_values(self):
        """Test variant default values."""
        variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={}
        )
        self.assertEqual(variant.rules, {})
        self.assertIsInstance(variant.created_at, datetime)
        self.assertIsInstance(variant.updated_at, datetime)

class TestDesignManager(unittest.TestCase):
    """Test design manager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.board = MagicMock(spec=pcbnew.BOARD)
        self.variant_data = MagicMock()
        self.board.GetDesignSettings().GetVariantData.return_value = self.variant_data
        self.manager = DesignManager(self.board)
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertEqual(self.manager.board, self.board)
        self.assertIsInstance(self.manager.variants, dict)
        self.assertEqual(len(self.manager.variants), 0)
    
    def test_create_variant(self):
        """Test variant creation."""
        # Create test variant
        variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={},
            layer_stack=None,
            rules={}
        )
        
        # Mock variant data
        self.variant_data.GetVariantNames.return_value = []
        
        # Create variant
        result = self.manager.create_variant(variant)
        
        # Verify
        self.assertTrue(result)
        self.variant_data.AddVariant.assert_called_once_with("test_variant", "Test variant")
        self.assertIn("test_variant", self.manager.variants)
    
    def test_create_duplicate_variant(self):
        """Test creating duplicate variant."""
        # Create test variant
        variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={},
            layer_stack=None,
            rules={}
        )
        
        # Add variant to manager
        self.manager.variants["test_variant"] = variant
        
        # Try to create duplicate
        result = self.manager.create_variant(variant)
        
        # Verify
        self.assertFalse(result)
    
    def test_update_variant(self):
        """Test variant update."""
        # Create test variant
        variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={},
            layer_stack=None,
            rules={}
        )
        
        # Add variant to manager
        self.manager.variants["test_variant"] = variant
        
        # Update variant
        result = self.manager.update_variant("test_variant", description="Updated description")
        
        # Verify
        self.assertTrue(result)
        self.variant_data.SetVariantDescription.assert_called_once_with(
            "test_variant", "Updated description"
        )
        self.assertEqual(
            self.manager.variants["test_variant"].description, "Updated description"
        )
    
    def test_update_nonexistent_variant(self):
        """Test updating nonexistent variant."""
        # Try to update nonexistent variant
        result = self.manager.update_variant("nonexistent", description="Updated description")
        
        # Verify
        self.assertFalse(result)
    
    def test_delete_variant(self):
        """Test variant deletion."""
        # Create test variant
        variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={},
            layer_stack=None,
            rules={}
        )
        
        # Add variant to manager
        self.manager.variants["test_variant"] = variant
        
        # Delete variant
        result = self.manager.delete_variant("test_variant")
        
        # Verify
        self.assertTrue(result)
        self.variant_data.RemoveVariant.assert_called_once_with("test_variant")
        self.assertNotIn("test_variant", self.manager.variants)
    
    def test_delete_nonexistent_variant(self):
        """Test deleting nonexistent variant."""
        # Try to delete nonexistent variant
        result = self.manager.delete_variant("nonexistent")
        
        # Verify
        self.assertFalse(result)
    
    def test_get_variant(self):
        """Test getting variant."""
        # Create test variant
        variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={},
            layer_stack=None,
            rules={}
        )
        
        # Add variant to manager
        self.manager.variants["test_variant"] = variant
        
        # Get variant
        result = self.manager.get_variant("test_variant")
        
        # Verify
        self.assertEqual(result, variant)
    
    def test_get_nonexistent_variant(self):
        """Test getting nonexistent variant."""
        # Try to get nonexistent variant
        result = self.manager.get_variant("nonexistent")
        
        # Verify
        self.assertIsNone(result)
    
    def test_get_variants(self):
        """Test getting all variants."""
        # Create test variants
        variant1 = DesignVariant(
            name="test_variant1",
            description="Test variant 1",
            components={},
            layer_stack=None,
            rules={}
        )
        variant2 = DesignVariant(
            name="test_variant2",
            description="Test variant 2",
            components={},
            layer_stack=None,
            rules={}
        )
        
        # Add variants to manager
        self.manager.variants["test_variant1"] = variant1
        self.manager.variants["test_variant2"] = variant2
        
        # Get variants
        result = self.manager.get_variants()
        
        # Verify
        self.assertEqual(len(result), 2)
        self.assertIn("test_variant1", result)
        self.assertIn("test_variant2", result)
    
    def test_switch_variant(self):
        """Test switching variant."""
        # Create test variant
        variant = DesignVariant(
            name="test_variant",
            description="Test variant",
            components={},
            layer_stack=None,
            rules={}
        )
        
        # Add variant to manager
        self.manager.variants["test_variant"] = variant
        
        # Switch variant
        result = self.manager.switch_variant("test_variant")
        
        # Verify
        self.assertTrue(result)
        self.variant_data.SetCurrentVariant.assert_called_once_with("test_variant")
        self.board.SetDesignSettings.assert_called_once_with(self.variant_data)
    
    def test_switch_nonexistent_variant(self):
        """Test switching to nonexistent variant."""
        # Try to switch to nonexistent variant
        result = self.manager.switch_variant("nonexistent")
        
        # Verify
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main() 
