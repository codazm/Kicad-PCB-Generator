"""Tests for board preset registry functionality."""

import pytest
from kicad_pcb_generator.core.templates.board_presets import (
    BoardProfile, 
    BoardPreset, 
    BoardPresetRegistry,
    board_preset_registry
)


class TestBoardPresetRegistry:
    """Test board preset registry functionality."""
    
    def test_preset_registry_initialization(self):
        """Test that the registry initializes with all presets."""
        registry = BoardPresetRegistry()
        presets = registry.list_presets()
        
        # Check that all expected profiles are present
        expected_profiles = [
            BoardProfile.EURORACK_3U,
            BoardProfile.EURORACK_6U,
            BoardProfile.EURORACK_1U,
            BoardProfile.PEDAL_STANDARD,
            BoardProfile.PEDAL_MINI,
            BoardProfile.PEDAL_LARGE,
            BoardProfile.RACK_1U,
            BoardProfile.RACK_2U,
            BoardProfile.RACK_3U
        ]
        
        for profile in expected_profiles:
            assert profile in presets
            assert presets[profile] is not None
    
    def test_get_preset_by_name(self):
        """Test getting presets by name."""
        registry = BoardPresetRegistry()
        
        # Test exact name match
        preset = registry.get_preset_by_name("Eurorack 3U")
        assert preset is not None
        assert preset.name == "Eurorack 3U"
        assert preset.width_mm == 128.5
        assert preset.height_mm == 128.5
        
        # Test case insensitive match
        preset = registry.get_preset_by_name("eurorack 3u")
        assert preset is not None
        assert preset.name == "Eurorack 3U"
        
        # Test non-existent preset
        preset = registry.get_preset_by_name("Non-existent Preset")
        assert preset is None
    
    def test_get_preset_names(self):
        """Test getting preset names mapping."""
        registry = BoardPresetRegistry()
        names = registry.get_preset_names()
        
        assert isinstance(names, dict)
        assert BoardProfile.EURORACK_3U.value in names
        assert names[BoardProfile.EURORACK_3U.value] == "Eurorack 3U"
    
    def test_validate_board_size(self):
        """Test board size validation."""
        registry = BoardPresetRegistry()
        
        # Test valid Eurorack 3U dimensions
        assert registry.validate_board_size(128.5, 128.5, BoardProfile.EURORACK_3U)
        
        # Test with tolerance
        assert registry.validate_board_size(127.5, 129.5, BoardProfile.EURORACK_3U)
        
        # Test invalid dimensions
        assert not registry.validate_board_size(100.0, 100.0, BoardProfile.EURORACK_3U)
    
    def test_get_manufacturing_constraints(self):
        """Test getting manufacturing constraints."""
        registry = BoardPresetRegistry()
        
        constraints = registry.get_manufacturing_constraints(BoardProfile.EURORACK_3U)
        assert constraints is not None
        assert "min_hole_size" in constraints
        assert "max_hole_size" in constraints
        assert "copper_weight" in constraints
        assert "solder_mask" in constraints
        assert "silkscreen" in constraints
    
    def test_global_registry_instance(self):
        """Test that the global registry instance works."""
        assert board_preset_registry is not None
        assert isinstance(board_preset_registry, BoardPresetRegistry)
        
        # Test that it has the expected presets
        presets = board_preset_registry.list_presets()
        assert BoardProfile.EURORACK_3U in presets
        assert BoardProfile.PEDAL_STANDARD in presets


class TestBoardPreset:
    """Test BoardPreset dataclass."""
    
    def test_board_preset_creation(self):
        """Test creating a board preset."""
        preset = BoardPreset(
            name="Test Preset",
            description="Test description",
            width_mm=100.0,
            height_mm=50.0,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=25.0,
            mounting_holes=(3.5, 3.5, 96.5, 46.5),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5
            }
        )
        
        assert preset.name == "Test Preset"
        assert preset.width_mm == 100.0
        assert preset.height_mm == 50.0
        assert preset.mounting_holes == (3.5, 3.5, 96.5, 46.5)
        assert preset.manufacturing_constraints["min_hole_size"] == 0.3


class TestBoardProfile:
    """Test BoardProfile enum."""
    
    def test_board_profile_values(self):
        """Test that all expected board profiles exist."""
        assert BoardProfile.EURORACK_3U.value == "eurorack_3u"
        assert BoardProfile.EURORACK_6U.value == "eurorack_6u"
        assert BoardProfile.EURORACK_1U.value == "eurorack_1u"
        assert BoardProfile.PEDAL_STANDARD.value == "pedal_standard"
        assert BoardProfile.PEDAL_MINI.value == "pedal_mini"
        assert BoardProfile.PEDAL_LARGE.value == "pedal_large"
        assert BoardProfile.RACK_1U.value == "rack_1u"
        assert BoardProfile.RACK_2U.value == "rack_2u"
        assert BoardProfile.RACK_3U.value == "rack_3u"
        assert BoardProfile.CUSTOM.value == "custom"
    
    def test_board_profile_creation(self):
        """Test creating board profiles from values."""
        profile = BoardProfile("eurorack_3u")
        assert profile == BoardProfile.EURORACK_3U
        
        with pytest.raises(ValueError):
            BoardProfile("invalid_profile") 