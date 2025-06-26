"""
Unit tests for custom component functionality.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import json
from pathlib import Path
import tempfile
import shutil

from kicad_pcb_generator.audio.components.custom_component import (
    CustomComponentManager,
    CustomComponentTemplate,
    CustomComponentData,
    ComponentType
)

class TestCustomComponentManager(unittest.TestCase):
    """Test cases for CustomComponentManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for components
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CustomComponentManager(self.temp_dir)
        
        # Sample component data
        self.sample_component = CustomComponentData(
            name="TEST_COMP",
            type=ComponentType.PASSIVE,
            value="10k",
            footprint="R_0805_2012Metric",
            pins=[
                {
                    'number': '1',
                    'name': 'A',
                    'type': 'passive'
                },
                {
                    'number': '2',
                    'name': 'B',
                    'type': 'passive'
                }
            ],
            properties={
                'tolerance': '1%',
                'power': '0.125W'
            }
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_component(self):
        """Test component creation."""
        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.manager.create_component(self.sample_component)
            
            # Verify results
            self.assertTrue(result)
            self.assertIn(self.sample_component.name, self.manager.components)
            mock_file.assert_called_once()
            
            # Verify JSON data
            call_args = mock_file.call_args[0]
            self.assertEqual(call_args[0], str(Path(self.temp_dir) / "TEST_COMP.json"))
            self.assertEqual(call_args[1], 'w')
    
    def test_get_component(self):
        """Test component retrieval."""
        # Add component
        self.manager.components[self.sample_component.name] = self.sample_component
        
        # Get component
        component = self.manager.get_component(self.sample_component.name)
        
        # Verify results
        self.assertIsNotNone(component)
        self.assertEqual(component.name, self.sample_component.name)
        self.assertEqual(component.type, self.sample_component.type)
        self.assertEqual(component.value, self.sample_component.value)
    
    def test_update_component(self):
        """Test component update."""
        # Add component
        self.manager.components[self.sample_component.name] = self.sample_component
        
        # Update component
        updated_component = CustomComponentData(
            name=self.sample_component.name,
            type=self.sample_component.type,
            value="20k",  # Updated value
            footprint=self.sample_component.footprint,
            pins=self.sample_component.pins,
            properties=self.sample_component.properties
        )
        
        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.manager.update_component(
                self.sample_component.name,
                updated_component
            )
            
            # Verify results
            self.assertTrue(result)
            self.assertEqual(
                self.manager.components[self.sample_component.name].value,
                "20k"
            )
            mock_file.assert_called_once()
    
    def test_delete_component(self):
        """Test component deletion."""
        # Add component
        self.manager.components[self.sample_component.name] = self.sample_component
        
        # Mock file operations
        with patch('pathlib.Path.unlink') as mock_unlink:
            result = self.manager.delete_component(self.sample_component.name)
            
            # Verify results
            self.assertTrue(result)
            self.assertNotIn(self.sample_component.name, self.manager.components)
            mock_unlink.assert_called_once()
    
    def test_list_components(self):
        """Test component listing."""
        # Add components
        self.manager.components[self.sample_component.name] = self.sample_component
        self.manager.components["TEST_COMP2"] = self.sample_component
        
        # List components
        components = self.manager.list_components()
        
        # Verify results
        self.assertEqual(len(components), 2)
        self.assertIn(self.sample_component.name, components)
        self.assertIn("TEST_COMP2", components)
    
    def test_validate_component_data(self):
        """Test component data validation."""
        # Test valid data
        self.assertTrue(self.manager._validate_component_data(self.sample_component))
        
        # Test missing required fields
        invalid_component = CustomComponentData(
            name="",  # Missing name
            type=ComponentType.PASSIVE,
            value="10k",
            footprint="R_0805_2012Metric",
            pins=[{'number': '1', 'name': 'A', 'type': 'passive'}],
            properties={}
        )
        self.assertFalse(self.manager._validate_component_data(invalid_component))
        
        # Test invalid pins
        invalid_pins_component = CustomComponentData(
            name="TEST_COMP",
            type=ComponentType.PASSIVE,
            value="10k",
            footprint="R_0805_2012Metric",
            pins=[],  # Empty pins
            properties={}
        )
        self.assertFalse(self.manager._validate_component_data(invalid_pins_component))
        
        # Test invalid pin data
        invalid_pin_data_component = CustomComponentData(
            name="TEST_COMP",
            type=ComponentType.PASSIVE,
            value="10k",
            footprint="R_0805_2012Metric",
            pins=[{'number': '1'}],  # Missing name and type
            properties={}
        )
        self.assertFalse(self.manager._validate_component_data(invalid_pin_data_component))

class TestCustomComponentTemplate(unittest.TestCase):
    """Test cases for CustomComponentTemplate."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.component_dir = Path(self.temp_dir) / "components"
        self.template_dir = Path(self.temp_dir) / "templates"
        
        # Create directories
        self.component_dir.mkdir()
        self.template_dir.mkdir()
        
        # Create manager and template
        self.manager = CustomComponentManager(str(self.component_dir))
        self.template = CustomComponentTemplate(
            str(self.template_dir),
            self.manager
        )
        
        # Sample component data
        self.sample_component = CustomComponentData(
            name="TEST_COMP",
            type=ComponentType.PASSIVE,
            value="10k",
            footprint="R_0805_2012Metric",
            pins=[
                {
                    'number': '1',
                    'name': 'A',
                    'type': 'passive'
                },
                {
                    'number': '2',
                    'name': 'B',
                    'type': 'passive'
                }
            ],
            properties={
                'tolerance': '1%',
                'power': '0.125W'
            }
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_add_custom_component(self):
        """Test adding custom component to template."""
        # Mock component manager
        with patch.object(
            self.manager,
            'create_component',
            return_value=True
        ):
            result = self.template.add_custom_component(self.sample_component)
            
            # Verify results
            self.assertTrue(result)
            self.assertIn(self.sample_component.name, self.template.get_components())
            
            # Verify component data
            component_data = self.template.get_components()[self.sample_component.name]
            self.assertEqual(component_data['id'], self.sample_component.name)
            self.assertEqual(component_data['type'], self.sample_component.type.value)
            self.assertEqual(component_data['value'], self.sample_component.value)
    
    def test_remove_custom_component(self):
        """Test removing custom component from template."""
        # Add component to template
        self.template.template_data['components'] = {
            self.sample_component.name: {
                'id': self.sample_component.name,
                'type': self.sample_component.type.value,
                'value': self.sample_component.value,
                'footprint': self.sample_component.footprint,
                'pins': self.sample_component.pins,
                'properties': self.sample_component.properties
            }
        }
        
        # Mock component manager
        with patch.object(
            self.manager,
            'delete_component',
            return_value=True
        ):
            result = self.template.remove_custom_component(self.sample_component.name)
            
            # Verify results
            self.assertTrue(result)
            self.assertNotIn(self.sample_component.name, self.template.get_components())
    
    def test_template_validation(self):
        """Test template validation."""
        # Add required sections
        self.template.template_data.update({
            'layer_stack': {
                'layers': ['F.Cu', 'B.Cu'],
                'thickness': 1.6,
                'material': 'FR4'
            },
            'zone_settings': {
                'clearance': 0.3,
                'min_width': 0.2
            },
            'components': {
                self.sample_component.name: {
                    'id': self.sample_component.name,
                    'type': self.sample_component.type.value,
                    'value': self.sample_component.value,
                    'footprint': self.sample_component.footprint
                }
            },
            'nets': {
                'VCC': {
                    'name': 'VCC',
                    'type': 'power',
                    'width': 0.5
                }
            },
            'design_rules': {
                'min_trace_width': 0.2,
                'min_clearance': 0.3
            }
        })
        
        # Validate template
        self.assertTrue(self.template.validate_template())

if __name__ == '__main__':
    unittest.main() 