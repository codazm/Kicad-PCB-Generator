"""Tests for template version control system."""

import os
import json
import shutil
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pcbnew
from kicad_pcb_generator.core.template.version_control import (
    TemplateVersionControl,
    VersionMetadata
)

class TestTemplateVersionControl(unittest.TestCase):
    """Test cases for template version control system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = TemporaryDirectory()
        self.template_dir = Path(self.temp_dir.name)
        self.version_control = TemplateVersionControl(str(self.template_dir))
        
        # Create a test board
        self.board = pcbnew.BOARD()
        
        # Create test metadata
        self.metadata = VersionMetadata(
            version="1.0.0",
            author="Test Author",
            date=datetime.now().isoformat(),
            description="Test version",
            changes=["Initial version"],
            validation_status={"drc": False, "erc": False},
            dependencies={},
            tags=["test"]
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_create_version(self):
        """Test creating a new version."""
        # Create version
        result = self.version_control.create_version(self.board, self.metadata)
        self.assertTrue(result)
        
        # Check version directory
        version_dir = self.template_dir / "versions" / "1.0.0"
        self.assertTrue(version_dir.exists())
        
        # Check board file
        board_file = version_dir / "board.kicad_pcb"
        self.assertTrue(board_file.exists())
        
        # Check metadata file
        metadata_file = version_dir / "metadata.json"
        self.assertTrue(metadata_file.exists())
        
        # Check history
        history_file = self.template_dir / "version_history.json"
        self.assertTrue(history_file.exists())
        
        with open(history_file, 'r') as f:
            history = json.load(f)
            self.assertIn("1.0.0", history)
    
    def test_get_version(self):
        """Test getting a version."""
        # Create version
        self.version_control.create_version(self.board, self.metadata)
        
        # Get version
        result = self.version_control.get_version("1.0.0")
        self.assertIsNotNone(result)
        
        board, metadata = result
        self.assertIsInstance(board, pcbnew.BOARD)
        self.assertIsInstance(metadata, VersionMetadata)
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.author, "Test Author")
    
    def test_get_nonexistent_version(self):
        """Test getting a nonexistent version."""
        result = self.version_control.get_version("2.0.0")
        self.assertIsNone(result)
    
    def test_get_version_history(self):
        """Test getting version history."""
        # Create multiple versions
        metadata1 = VersionMetadata(
            version="1.0.0",
            author="Test Author",
            date=datetime.now().isoformat(),
            description="First version",
            changes=["Initial version"],
            validation_status={"drc": False, "erc": False},
            dependencies={},
            tags=["test"]
        )
        
        metadata2 = VersionMetadata(
            version="1.1.0",
            author="Test Author",
            date=datetime.now().isoformat(),
            description="Second version",
            changes=["Added features"],
            validation_status={"drc": True, "erc": True},
            dependencies={},
            tags=["test"]
        )
        
        self.version_control.create_version(self.board, metadata1)
        self.version_control.create_version(self.board, metadata2)
        
        # Get history
        history = self.version_control.get_version_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["version"], "1.0.0")
        self.assertEqual(history[1]["version"], "1.1.0")
    
    def test_compare_versions(self):
        """Test comparing versions."""
        # Create two versions
        metadata1 = VersionMetadata(
            version="1.0.0",
            author="Test Author",
            date=datetime.now().isoformat(),
            description="First version",
            changes=["Initial version"],
            validation_status={"drc": False, "erc": False},
            dependencies={},
            tags=["test"]
        )
        
        metadata2 = VersionMetadata(
            version="1.1.0",
            author="Different Author",
            date=datetime.now().isoformat(),
            description="Second version",
            changes=["Added features"],
            validation_status={"drc": True, "erc": True},
            dependencies={},
            tags=["test"]
        )
        
        self.version_control.create_version(self.board, metadata1)
        self.version_control.create_version(self.board, metadata2)
        
        # Compare versions
        differences = self.version_control.compare_versions("1.0.0", "1.1.0")
        self.assertIn("board_differences", differences)
        self.assertIn("metadata_differences", differences)
        
        # Check metadata differences
        meta_diff = differences["metadata_differences"]
        self.assertTrue(meta_diff["author"])
        self.assertTrue(meta_diff["description"])
        self.assertTrue(meta_diff["validation_status"])
    
    def test_rollback_version(self):
        """Test rolling back to a previous version."""
        # Create version
        self.version_control.create_version(self.board, self.metadata)
        
        # Modify board
        self.board.SetCopperLayerCount(4)
        
        # Rollback
        result = self.version_control.rollback_version("1.0.0")
        self.assertTrue(result)
        
        # Check current board
        current_board = pcbnew.LoadBoard(str(self.template_dir / "board.kicad_pcb"))
        self.assertEqual(current_board.GetCopperLayerCount(), 2)
    
    def test_validate_version(self):
        """Test validating a version."""
        # Create version
        self.version_control.create_version(self.board, self.metadata)
        
        # Validate version
        results = self.version_control.validate_version("1.0.0")
        self.assertIn("drc", results)
        self.assertIn("erc", results)
        
        # Check validation status in history
        with open(self.template_dir / "version_history.json", 'r') as f:
            history = json.load(f)
            self.assertIn("validation_status", history["1.0.0"])
    
    def test_invalid_version_number(self):
        """Test creating version with invalid version number."""
        invalid_metadata = VersionMetadata(
            version="invalid",
            author="Test Author",
            date=datetime.now().isoformat(),
            description="Test version",
            changes=["Initial version"],
            validation_status={"drc": False, "erc": False},
            dependencies={},
            tags=["test"]
        )
        
        result = self.version_control.create_version(self.board, invalid_metadata)
        self.assertFalse(result)
    
    def test_duplicate_version(self):
        """Test creating duplicate version."""
        # Create first version
        self.version_control.create_version(self.board, self.metadata)
        
        # Try to create same version again
        result = self.version_control.create_version(self.board, self.metadata)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main() 
