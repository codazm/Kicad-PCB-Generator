"""Tests for template versioning functionality."""
import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)
from kicad_pcb_generator.core.templates.base import TemplateBase, LayerStack, ZoneSettings, DesignVariant
from kicad_pcb_generator.core.components import ComponentData

@pytest.fixture
def storage_path(tmp_path):
    """Create temporary storage path."""
    return tmp_path

@pytest.fixture
def manager(storage_path):
    """Create template version manager."""
    return TemplateVersionManager(storage_path)

@pytest.fixture
def template(storage_path):
    """Create test template."""
    template = TemplateBase(str(storage_path))
    template.name = "Test Template"
    template.description = "Test template description"
    template.version = "1.0.0"
    
    # Add layer stack
    template.layer_stack = LayerStack(
        name="4-Layer Stack",
        layers=["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
        thickness={
            "F.Cu": 0.035,
            "In1.Cu": 0.035,
            "In2.Cu": 0.035,
            "B.Cu": 0.035
        },
        material={
            "F.Cu": "Copper",
            "In1.Cu": "Copper",
            "In2.Cu": "Copper",
            "B.Cu": "Copper"
        },
        dielectric={
            "F.Cu": 0.1,
            "In1.Cu": 0.1,
            "In2.Cu": 0.1,
            "B.Cu": 0.1
        }
    )
    
    # Add zone
    template.zones["GND"] = ZoneSettings(
        name="GND",
        layer="F.Cu",
        net="GND",
        priority=1,
        fill_mode="solid",
        thermal_gap=0.5,
        thermal_bridge_width=0.5,
        min_thickness=0.5,
        keep_islands=True,
        smoothing=True
    )
    
    # Add component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric"
    )
    
    # Add variant
    template.variants["Standard"] = DesignVariant(
        name="Standard",
        description="Standard variant",
        components={"R1": component},
        nets={"GND": ["R1-1"], "VCC": ["R1-2"]},
        rules={"clearance": 0.2}
    )
    
    # Add rules
    template.rules = {
        "clearance": 0.2,
        "track_width": 0.2,
        "via_diameter": 0.4,
        "via_drill": 0.2
    }
    
    return template

@pytest.fixture
def mock_board():
    """Create mock KiCad board."""
    board = Mock()
    
    # Mock layer methods
    board.GetCopperLayerCount.return_value = 4
    board.GetLayerName.side_effect = lambda i: ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"][i]
    
    # Mock net methods
    net1 = Mock()
    net1.GetNetname.return_value = "GND"
    pad1 = Mock()
    pad1.GetName.return_value = "1"
    net1.GetPads.return_value = [pad1]
    
    net2 = Mock()
    net2.GetNetname.return_value = "VCC"
    pad2 = Mock()
    pad2.GetName.return_value = "2"
    net2.GetPads.return_value = [pad2]
    
    board.GetNetsByName.return_value = {"GND": net1, "VCC": net2}
    
    # Mock footprint methods
    fp1 = Mock()
    fp1.GetReference.return_value = "R1"
    board.GetFootprints.return_value = [fp1]
    
    # Mock track methods
    track1 = Mock()
    track1.GetNetname.return_value = "GND"
    board.GetTracks.return_value = [track1]
    
    # Mock zone methods
    zone1 = Mock()
    zone1.GetNetname.return_value = "GND"
    board.Zones.return_value = [zone1]
    
    # Mock design settings
    settings = Mock()
    settings.GetMinClearance.return_value = 200000  # 0.2mm in nanometers
    settings.GetTrackWidth.return_value = 200000
    settings.GetViasDimensions.return_value = 400000
    settings.GetViasDrill.return_value = 200000
    board.GetDesignSettings.return_value = settings
    
    return board

def test_init(manager, storage_path):
    """Test manager initialization."""
    assert manager.storage_path == storage_path
    assert manager.versions == {}
    assert (storage_path / "versions.json").exists()

def test_add_version(manager, template):
    """Test adding a version."""
    # Create change
    change = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    
    # Add version
    manager.add_version("test_template", template, change)
    
    # Check version was added
    assert "test_template" in manager.versions
    assert len(manager.versions["test_template"]) == 1
    
    version = manager.versions["test_template"][0]
    assert version.version == "v1"
    assert version.changes == [change]
    assert version.metadata["name"] == "Test Template"
    assert version.metadata["description"] == "Test template description"
    assert version.metadata["version"] == "1.0.0"

def test_add_version_with_board(manager, template, mock_board):
    """Test adding a version with KiCad board."""
    # Create change
    change = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    
    # Add version with board
    manager.add_version("test_template", template, change, mock_board)
    
    # Check version was added with board hash
    version = manager.versions["test_template"][0]
    assert version.kicad_board_hash is not None
    
    # Add another version with modified board
    mock_board.GetLayerName.side_effect = lambda i: ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "New.Cu"][i]
    mock_board.GetCopperLayerCount.return_value = 5
    
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Added new layer"
    )
    
    manager.add_version("test_template", template, change2, mock_board)
    
    # Check KiCad changes were tracked
    version2 = manager.versions["test_template"][1]
    assert version2.changes[0].kicad_changes is not None
    assert "layers" in version2.changes[0].kicad_changes
    assert "added" in version2.changes[0].kicad_changes["layers"]
    assert "New.Cu" in version2.changes[0].kicad_changes["layers"]["added"]

def test_get_version(manager, template):
    """Test getting a version."""
    # Add version
    change = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change)
    
    # Get version
    version = manager.get_version("test_template", "v1")
    assert version is not None
    assert version.version == "v1"
    assert version.metadata["name"] == "Test Template"

def test_get_latest_version(manager, template):
    """Test getting latest version."""
    # Add versions
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change1)
    
    template.name = "Updated Template"
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Updated name"
    )
    manager.add_version("test_template", template, change2)
    
    # Get latest version
    version = manager.get_latest_version("test_template")
    assert version is not None
    assert version.version == "v2"
    assert version.metadata["name"] == "Updated Template"

def test_get_version_history(manager, template):
    """Test getting version history."""
    # Add versions
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change1)
    
    template.name = "Updated Template"
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Updated name"
    )
    manager.add_version("test_template", template, change2)
    
    # Get history
    history = manager.get_version_history("test_template")
    assert len(history) == 2
    assert history[0].version == "v1"
    assert history[1].version == "v2"

def test_compare_versions(manager, template):
    """Test comparing versions."""
    # Add versions
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change1)
    
    template.name = "Updated Template"
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Updated name"
    )
    manager.add_version("test_template", template, change2)
    
    # Compare versions
    changes = manager.compare_versions("test_template", "v1", "v2")
    assert len(changes) == 1
    assert changes[0].change_type == ChangeType.MODIFIED
    assert changes[0].description == "Updated name"

def test_rollback_to_version(manager, template):
    """Test rolling back to a version."""
    # Add versions
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change1)
    
    template.name = "Updated Template"
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Updated name"
    )
    manager.add_version("test_template", template, change2)
    
    # Rollback
    rolled_back = manager.rollback_to_version("test_template", "v1", "test_user")
    assert rolled_back is not None
    assert rolled_back.name == "Test Template"
    
    # Check new version was created
    latest = manager.get_latest_version("test_template")
    assert latest is not None
    assert latest.version == "v3"
    assert latest.metadata["name"] == "Test Template"

def test_deprecate_version(manager, template):
    """Test deprecating a version."""
    # Add version
    change = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change)
    
    # Deprecate version
    success = manager.deprecate_version(
        "test_template",
        "v1",
        "test_user",
        "Replaced by new version"
    )
    assert success
    
    # Check version was deprecated
    version = manager.get_version("test_template", "v1")
    assert version is not None
    assert version.deprecated
    assert version.deprecated_by == "test_user"

def test_get_deprecated_versions(manager, template):
    """Test getting deprecated versions."""
    # Add versions
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change1)
    
    template.name = "Updated Template"
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Updated name"
    )
    manager.add_version("test_template", template, change2)
    
    # Deprecate first version
    manager.deprecate_version(
        "test_template",
        "v1",
        "test_user",
        "Replaced by new version"
    )
    
    # Get deprecated versions
    deprecated = manager.get_deprecated_versions("test_template")
    assert len(deprecated) == 1
    assert deprecated[0].version == "v1"

@patch('kicad_pcb_generator.core.compatibility.kicad9.KiCad9Compatibility.get_version')
def test_get_compatible_versions(mock_get_version, manager, template):
    """Test getting compatible versions."""
    # Mock KiCad version
    mock_get_version.return_value = "9.0.0"
    
    # Add versions
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Initial version"
    )
    manager.add_version("test_template", template, change1)
    
    template.name = "Updated Template"
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Updated name"
    )
    manager.add_version("test_template", template, change2)
    
    # Get compatible versions
    compatible = manager.get_compatible_versions("test_template")
    assert len(compatible) == 2
    assert all(v.kicad_version == "9.0.0" for v in compatible)

def test_calculate_board_hash(manager, mock_board):
    """Test calculating board hash."""
    hash_value = manager._calculate_board_hash(mock_board)
    assert hash_value is not None
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA-256 hash length

def test_get_kicad_changes(manager, mock_board):
    """Test getting KiCad changes."""
    # Create modified board
    modified_board = Mock()
    modified_board.GetCopperLayerCount.return_value = 5
    modified_board.GetLayerName.side_effect = lambda i: ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "New.Cu"][i]
    
    # Get changes
    changes = manager._get_kicad_changes(mock_board, modified_board)
    
    # Check changes
    assert "layers" in changes
    assert "added" in changes["layers"]
    assert "New.Cu" in changes["layers"]["added"]

def test_version_conflict_resolution(manager, template):
    """Test handling version conflicts during concurrent operations."""
    # Create initial version
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="user1",
        description="Initial version"
    )
    manager.add_version("test_template", template, change1)
    
    # Simulate concurrent version creation
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="user2",
        description="Concurrent modification"
    )
    
    # Mock file system operations to simulate conflict
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.side_effect = [True, False]  # First check succeeds, second fails
        
        # Attempt to add version
        result = manager.add_version("test_template", template, change2)
        
        # Verify conflict was handled
        assert result is not None
        assert result.version == "v2"
        
        # Verify both changes are preserved
        history = manager.get_version_history("test_template")
        assert len(history) == 2
        assert history[0].changes[0].user == "user1"
        assert history[1].changes[0].user == "user2"

def test_bulk_version_operations(manager, template):
    """Test bulk version operations."""
    # Create multiple versions in bulk
    changes = [
        TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description=f"Version {i}"
        )
        for i in range(5)
    ]
    
    # Add versions in bulk
    versions = manager.add_versions("test_template", template, changes)
    
    # Verify all versions were created
    assert len(versions) == 5
    assert versions[0].version == "v1"
    assert versions[-1].version == "v5"
    
    # Verify version history
    history = manager.get_version_history("test_template")
    assert len(history) == 5
    
    # Test bulk version update
    updated_versions = []
    for version in versions:
        version.metadata["updated"] = True
        updated_versions.append(version)
    
    # Update versions in bulk
    result = manager.update_versions("test_template", updated_versions)
    assert result
    
    # Verify updates were applied
    history = manager.get_version_history("test_template")
    for version in history:
        assert version.metadata.get("updated", False)

def test_version_migration(manager, template):
    """Test version migration scenarios."""
    # Create old format version
    old_version = TemplateVersion(
        version="v1",
        timestamp=datetime.now(),
        changes=[
            TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description="Old format version"
            )
        ],
        metadata={
            "format_version": "1.0",
            "name": "Test Template",
            "description": "Test template description"
        }
    )
    
    # Save old version
    manager.versions["test_template"] = [old_version]
    manager._save_versions("test_template")
    
    # Migrate to new format
    migrated = manager.migrate_version_format("test_template", "2.0")
    assert migrated
    
    # Verify migration
    version = manager.get_version("test_template", "v1")
    assert version.metadata["format_version"] == "2.0"
    assert "migration_timestamp" in version.metadata

def test_cross_version_compatibility(manager, template):
    """Test cross-version compatibility checks."""
    # Create versions with different compatibility requirements
    v1_template = Mock()
    v1_template.metadata = {
        "name": "Test Template",
        "version": "1.0.0",
        "compatibility": {
            "min_version": "1.0.0",
            "max_version": "1.9.9"
        }
    }
    
    v2_template = Mock()
    v2_template.metadata = {
        "name": "Test Template",
        "version": "2.0.0",
        "compatibility": {
            "min_version": "2.0.0",
            "max_version": "2.9.9"
        }
    }
    
    # Add versions
    change1 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.CREATED,
        user="test_user",
        description="Version 1"
    )
    manager.add_version("test_template", v1_template, change1)
    
    change2 = TemplateChange(
        timestamp=datetime.now(),
        change_type=ChangeType.MODIFIED,
        user="test_user",
        description="Version 2"
    )
    manager.add_version("test_template", v2_template, change2)
    
    # Test compatibility checks
    assert manager.check_version_compatibility("test_template", "v1", "1.5.0")
    assert not manager.check_version_compatibility("test_template", "v1", "2.0.0")
    assert manager.check_version_compatibility("test_template", "v2", "2.5.0")
    assert not manager.check_version_compatibility("test_template", "v2", "1.5.0")

def test_long_term_version_history(manager, template):
    """Test long-term version history management."""
    # Create many versions over a long period
    versions = []
    for i in range(100):  # Create 100 versions
        template = Mock()
        template.metadata = {
            "name": f"Test Template v{i+1}",
            "version": f"{i+1}.0.0"
        }
        
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="test_user",
            description=f"Version {i+1}"
        )
        
        version = manager.add_version("test_template", template, change)
        versions.append(version)
    
    # Test history pagination
    page1 = manager.get_version_history("test_template", page=1, page_size=20)
    assert len(page1) == 20
    assert page1[0].version == "v100"  # Most recent first
    
    page2 = manager.get_version_history("test_template", page=2, page_size=20)
    assert len(page2) == 20
    assert page2[0].version == "v80"
    
    # Test history filtering
    filtered = manager.get_version_history(
        "test_template",
        start_date=datetime.now(),
        end_date=datetime.now(),
        user="test_user"
    )
    assert len(filtered) > 0
    
    # Test history compression
    compressed = manager.compress_version_history("test_template", max_versions=50)
    assert len(compressed) == 50
    
    # Verify compression preserved important versions
    history = manager.get_version_history("test_template")
    assert history[0].version == "v100"  # Most recent version
    assert history[-1].version == "v1"   # Original version 