"""Tests for the audio amplifier example."""
import pytest
from unittest.mock import MagicMock, patch
import pcbnew
from kicad_pcb_generator.examples.audio_amplifier import create_audio_amplifier
from kicad_pcb_generator.audio.components.stability import (
    StabilityManager,
    FilterType,
    FilterSpec
)

@pytest.fixture
def mock_schematic():
    """Create a mock schematic for testing."""
    schematic = MagicMock(spec=pcbnew.SCHEMATIC)
    return schematic

@pytest.fixture
def mock_board():
    """Create a mock board for testing."""
    board = MagicMock(spec=pcbnew.BOARD)
    board.GetDesignSettings.return_value = MagicMock()
    return board

@pytest.fixture
def mock_converter():
    """Create a mock converter for testing."""
    converter = MagicMock()
    converter.convert_schematic.return_value = MagicMock(
        success=True,
        board=MagicMock(),
        warnings=[],
        errors=[]
    )
    return converter

def test_create_audio_amplifier_success(mock_schematic, mock_board, mock_converter):
    """Test successful creation of audio amplifier."""
    with patch('pcbnew.SCHEMATIC', return_value=mock_schematic), \
         patch('pcbnew.COMPONENT', return_value=MagicMock()), \
         patch('kicad_pcb_generator.audio.layout.converter.AudioLayoutConverter', return_value=mock_converter):
        
        create_audio_amplifier()
        
        # Verify components were added
        assert mock_schematic.Add.call_count == 14  # Total number of components
        
        # Verify converter was called
        mock_converter.convert_schematic.assert_called_once_with(mock_schematic)

def test_create_audio_amplifier_failure(mock_schematic, mock_converter):
    """Test audio amplifier creation with conversion failure."""
    # Configure mock to simulate failure
    mock_converter.convert_schematic.return_value = MagicMock(
        success=False,
        errors=["Test error"]
    )
    
    with patch('pcbnew.SCHEMATIC', return_value=mock_schematic), \
         patch('pcbnew.COMPONENT', return_value=MagicMock()), \
         patch('kicad_pcb_generator.audio.layout.converter.AudioLayoutConverter', return_value=mock_converter):
        
        create_audio_amplifier()
        
        # Verify converter was called
        mock_converter.convert_schematic.assert_called_once_with(mock_schematic)

def test_stability_components():
    """Test stability components configuration."""
    stability = StabilityManager()
    
    # Test ferrite beads
    fb1 = stability.add_ferrite_bead("FB1", impedance=100, current_rating=1.0)
    assert fb1.reference == "FB1"
    assert fb1.type == "ferrite_bead"
    assert fb1.properties["impedance"] == 100
    assert fb1.properties["current_rating"] == 1.0
    
    # Test EMC filters
    emc_filter = FilterSpec(
        type=FilterType.EMI,
        cutoff_freq=1e6,
        order=2,
        attenuation=-40
    )
    emc1 = stability.add_emc_filter("EMC1", emc_filter)
    assert emc1.reference == "EMC1"
    assert emc1.type == "emc_filter"
    assert emc1.filter_spec == emc_filter
    
    # Test power filters
    pf1 = stability.add_power_filter("C5", capacitance=10.0, voltage_rating=16.0)
    assert pf1.reference == "C5"
    assert pf1.type == "capacitor"
    assert pf1.properties["capacitance"] == 10.0
    assert pf1.properties["voltage_rating"] == 16.0
    
    # Test audio filters
    audio_filter = FilterSpec(
        type=FilterType.LOW_PASS,
        cutoff_freq=20e3,
        order=2,
        ripple=0.1
    )
    af1 = stability.add_audio_filter("AF1", audio_filter)
    assert af1.reference == "AF1"
    assert af1.type == "audio_filter"
    assert af1.filter_spec == audio_filter

def test_component_retrieval():
    """Test stability component retrieval methods."""
    stability = StabilityManager()
    
    # Add test components
    stability.add_ferrite_bead("FB1", impedance=100, current_rating=1.0)
    stability.add_ferrite_bead("FB2", impedance=100, current_rating=0.5)
    stability.add_power_filter("C5", capacitance=10.0, voltage_rating=16.0)
    
    # Test get_component_by_reference
    fb1 = stability.get_component_by_reference("FB1")
    assert fb1 is not None
    assert fb1.reference == "FB1"
    
    # Test get_components_by_type
    ferrite_beads = stability.get_components_by_type("ferrite_bead")
    assert len(ferrite_beads) == 2
    
    capacitors = stability.get_components_by_type("capacitor")
    assert len(capacitors) == 1
    
    # Test get_components_by_filter_type
    emi_filters = stability.get_components_by_filter_type(FilterType.EMI)
    assert len(emi_filters) == 0  # No EMI filters added in this test 
