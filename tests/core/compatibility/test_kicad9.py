"""Tests for KiCad 9 compatibility layer."""
import pytest
from unittest.mock import patch, MagicMock

from kicad_pcb_generator.core.compatibility.kicad9 import KiCad9Compatibility

@pytest.fixture
def mock_pcbnew():
    """Mock pcbnew module."""
    with patch("kicad_pcb_generator.core.compatibility.kicad9.pcbnew") as mock:
        # Mock version
        mock.GetBuildVersion.return_value = "9.0.0"
        
        # Mock board
        mock_board = MagicMock()
        mock.GetBoard.return_value = mock_board
        
        # Mock footprints
        mock_footprint = MagicMock()
        mock_footprint.GetReference.return_value = "R1"
        mock_board.GetFootprints.return_value = [mock_footprint]
        
        # Mock nets
        mock_net = MagicMock()
        mock_net.GetNetname.return_value = "GND"
        mock_pad = MagicMock()
        mock_pad.GetName.return_value = "1"
        mock_pad.GetParent.return_value = mock_footprint
        mock_net.GetPads.return_value = [mock_pad]
        mock_board.GetNetsByName.return_value = {"GND": mock_net}
        
        # Mock tracks
        mock_board.GetTracks.return_value = []
        
        # Mock zones
        mock_board.Zones.return_value = []
        
        # Mock layers
        mock_board.GetCopperLayerCount.return_value = 2
        mock_board.GetLayerName.side_effect = ["F.Cu", "B.Cu"]
        
        # Mock design rules
        mock_settings = MagicMock()
        mock_settings.GetMinClearance.return_value = 0.2
        mock_settings.GetTrackWidth.return_value = 0.2
        mock_settings.GetViasDimensions.return_value = 0.4
        mock_settings.GetViasDrill.return_value = 0.2
        mock_board.GetDesignSettings.return_value = mock_settings
        
        yield mock

def test_version_check(mock_pcbnew):
    """Test version checking."""
    # Test valid version
    compatibility = KiCad9Compatibility()
    assert compatibility.board is None
    
    # Test invalid version
    mock_pcbnew.GetBuildVersion.return_value = "8.0.0"
    with pytest.raises(RuntimeError):
        KiCad9Compatibility()
    
    # Test invalid version format
    mock_pcbnew.GetBuildVersion.return_value = "invalid"
    with pytest.raises(RuntimeError):
        KiCad9Compatibility()

def test_get_board(mock_pcbnew):
    """Test getting board."""
    compatibility = KiCad9Compatibility()
    board = compatibility.get_board()
    assert board is not None
    mock_pcbnew.GetBoard.assert_called_once()

def test_get_footprints(mock_pcbnew):
    """Test getting footprints."""
    compatibility = KiCad9Compatibility()
    footprints = compatibility.get_footprints()
    assert len(footprints) == 1
    assert footprints[0].GetReference() == "R1"

def test_get_footprint(mock_pcbnew):
    """Test getting footprint."""
    compatibility = KiCad9Compatibility()
    
    # Test existing footprint
    footprint = compatibility.get_footprint("R1")
    assert footprint is not None
    assert footprint.GetReference() == "R1"
    
    # Test non-existing footprint
    footprint = compatibility.get_footprint("R2")
    assert footprint is None

def test_update_footprint(mock_pcbnew):
    """Test updating footprint."""
    compatibility = KiCad9Compatibility()
    
    # Test successful update
    assert compatibility.update_footprint("R1", (10.0, 20.0), 90.0)
    mock_pcbnew.VECTOR2I.assert_called_once_with(10000000, 20000000)
    
    # Test non-existing footprint
    assert not compatibility.update_footprint("R2", (10.0, 20.0), 90.0)

def test_get_nets(mock_pcbnew):
    """Test getting nets."""
    compatibility = KiCad9Compatibility()
    nets = compatibility.get_nets()
    assert "GND" in nets
    assert nets["GND"] == ["R1-1"]

def test_get_tracks(mock_pcbnew):
    """Test getting tracks."""
    compatibility = KiCad9Compatibility()
    tracks = compatibility.get_tracks()
    assert len(tracks) == 0

def test_get_zones(mock_pcbnew):
    """Test getting zones."""
    compatibility = KiCad9Compatibility()
    zones = compatibility.get_zones()
    assert len(zones) == 0

def test_get_layers(mock_pcbnew):
    """Test getting layers."""
    compatibility = KiCad9Compatibility()
    layers = compatibility.get_layers()
    assert layers == ["F.Cu", "B.Cu"]

def test_get_design_rules(mock_pcbnew):
    """Test getting design rules."""
    compatibility = KiCad9Compatibility()
    rules = compatibility.get_design_rules()
    assert rules["clearance"] == 0.2
    assert rules["track_width"] == 0.2
    assert rules["via_diameter"] == 0.4
    assert rules["via_drill"] == 0.2

def test_save_load_board(mock_pcbnew):
    """Test saving and loading board."""
    compatibility = KiCad9Compatibility()
    
    # Test saving board
    assert compatibility.save_board("test.kicad_pcb")
    mock_pcbnew.GetBoard.return_value.Save.assert_called_once_with("test.kicad_pcb")
    
    # Test loading board
    assert compatibility.load_board("test.kicad_pcb")
    mock_pcbnew.LoadBoard.assert_called_once_with("test.kicad_pcb") 
