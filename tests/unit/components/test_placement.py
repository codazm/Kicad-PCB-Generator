"""Unit tests for component placement system."""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew
from kicad_pcb_generator.core.components.placement import PlacementGroup, PlacementManager
from kicad_pcb_generator.core.components.manager import ComponentData

class TestPlacementGroup(unittest.TestCase):
    """Test placement group functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"],
            alignment="left",
            distribution="horizontal",
            spacing=1.0,
            rotation=0.0,
            mirror=False
        )
    
    def test_group_initialization(self):
        """Test group initialization."""
        self.assertEqual(self.group.name, "test_group")
        self.assertEqual(self.group.components, ["C1", "C2", "C3"])
        self.assertEqual(self.group.alignment, "left")
        self.assertEqual(self.group.distribution, "horizontal")
        self.assertEqual(self.group.spacing, 1.0)
        self.assertEqual(self.group.rotation, 0.0)
        self.assertFalse(self.group.mirror)
        self.assertEqual(self.group.metadata, {})
    
    def test_group_default_values(self):
        """Test group default values."""
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"]
        )
        self.assertEqual(group.alignment, "none")
        self.assertEqual(group.distribution, "none")
        self.assertEqual(group.spacing, 0.0)
        self.assertEqual(group.rotation, 0.0)
        self.assertFalse(group.mirror)
        self.assertEqual(group.metadata, {})

class TestPlacementManager(unittest.TestCase):
    """Test placement manager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.board = MagicMock(spec=pcbnew.BOARD)
        self.component_manager = MagicMock()
        self.manager = PlacementManager(self.board, self.component_manager)
        
        # Create test components
        self.comp1 = ComponentData(
            id="C1",
            type="capacitor",
            value="100nF",
            footprint="C_0805_2012Metric",
            position=(0.0, 0.0),
            orientation=0.0,
            layer="F.Cu"
        )
        self.comp2 = ComponentData(
            id="C2",
            type="capacitor",
            value="100nF",
            footprint="C_0805_2012Metric",
            position=(1.0, 0.0),
            orientation=0.0,
            layer="F.Cu"
        )
        self.comp3 = ComponentData(
            id="C3",
            type="capacitor",
            value="100nF",
            footprint="C_0805_2012Metric",
            position=(2.0, 0.0),
            orientation=0.0,
            layer="F.Cu"
        )
        
        # Set up component manager mock
        self.component_manager.get_component.side_effect = lambda x: {
            "C1": self.comp1,
            "C2": self.comp2,
            "C3": self.comp3
        }.get(x)
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertEqual(self.manager.board, self.board)
        self.assertEqual(self.manager.component_manager, self.component_manager)
        self.assertIsInstance(self.manager.groups, dict)
        self.assertEqual(len(self.manager.groups), 0)
    
    def test_create_group(self):
        """Test group creation."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"]
        )
        
        # Create group
        result = self.manager.create_group(group)
        
        # Verify
        self.assertTrue(result)
        self.assertIn("test_group", self.manager.groups)
        self.assertEqual(self.manager.groups["test_group"], group)
    
    def test_create_duplicate_group(self):
        """Test creating duplicate group."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"]
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Try to create duplicate
        result = self.manager.create_group(group)
        
        # Verify
        self.assertFalse(result)
    
    def test_update_group(self):
        """Test group update."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"]
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Update group
        result = self.manager.update_group("test_group", alignment="right")
        
        # Verify
        self.assertTrue(result)
        self.assertEqual(self.manager.groups["test_group"].alignment, "right")
    
    def test_update_nonexistent_group(self):
        """Test updating nonexistent group."""
        # Try to update nonexistent group
        result = self.manager.update_group("nonexistent", alignment="right")
        
        # Verify
        self.assertFalse(result)
    
    def test_delete_group(self):
        """Test group deletion."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"]
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Delete group
        result = self.manager.delete_group("test_group")
        
        # Verify
        self.assertTrue(result)
        self.assertNotIn("test_group", self.manager.groups)
    
    def test_delete_nonexistent_group(self):
        """Test deleting nonexistent group."""
        # Try to delete nonexistent group
        result = self.manager.delete_group("nonexistent")
        
        # Verify
        self.assertFalse(result)
    
    def test_align_components_left(self):
        """Test left alignment."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"],
            alignment="left"
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Align components
        result = self.manager.align_components("test_group")
        
        # Verify
        self.assertTrue(result)
        self.component_manager.update_component.assert_any_call("C1", position=(0.0, 0.0))
        self.component_manager.update_component.assert_any_call("C2", position=(0.0, 0.0))
        self.component_manager.update_component.assert_any_call("C3", position=(0.0, 0.0))
    
    def test_align_components_right(self):
        """Test right alignment."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"],
            alignment="right"
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Align components
        result = self.manager.align_components("test_group")
        
        # Verify
        self.assertTrue(result)
        self.component_manager.update_component.assert_any_call("C1", position=(2.0, 0.0))
        self.component_manager.update_component.assert_any_call("C2", position=(2.0, 0.0))
        self.component_manager.update_component.assert_any_call("C3", position=(2.0, 0.0))
    
    def test_distribute_components_horizontal(self):
        """Test horizontal distribution."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"],
            distribution="horizontal"
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Distribute components
        result = self.manager.distribute_components("test_group")
        
        # Verify
        self.assertTrue(result)
        self.component_manager.update_component.assert_any_call("C1", position=(0.0, 0.0))
        self.component_manager.update_component.assert_any_call("C2", position=(1.0, 0.0))
        self.component_manager.update_component.assert_any_call("C3", position=(2.0, 0.0))
    
    def test_distribute_components_vertical(self):
        """Test vertical distribution."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"],
            distribution="vertical"
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Distribute components
        result = self.manager.distribute_components("test_group")
        
        # Verify
        self.assertTrue(result)
        self.component_manager.update_component.assert_any_call("C1", position=(0.0, 0.0))
        self.component_manager.update_component.assert_any_call("C2", position=(0.0, 1.0))
        self.component_manager.update_component.assert_any_call("C3", position=(0.0, 2.0))
    
    def test_rotate_group(self):
        """Test group rotation."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"],
            rotation=90.0
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Rotate group
        result = self.manager.rotate_group("test_group")
        
        # Verify
        self.assertTrue(result)
        self.component_manager.update_component.assert_called()
    
    def test_mirror_group(self):
        """Test group mirroring."""
        # Create test group
        group = PlacementGroup(
            name="test_group",
            components=["C1", "C2", "C3"],
            mirror=True
        )
        
        # Add group to manager
        self.manager.groups["test_group"] = group
        
        # Mirror group
        result = self.manager.mirror_group("test_group")
        
        # Verify
        self.assertTrue(result)
        self.component_manager.update_component.assert_called()
    
    def test_swap_components(self):
        """Test component swapping."""
        # Swap components
        result = self.manager.swap_components("C1", "C2")
        
        # Verify
        self.assertTrue(result)
        self.component_manager.update_component.assert_any_call("C1", position=(1.0, 0.0))
        self.component_manager.update_component.assert_any_call("C2", position=(0.0, 0.0))

if __name__ == "__main__":
    unittest.main() 
