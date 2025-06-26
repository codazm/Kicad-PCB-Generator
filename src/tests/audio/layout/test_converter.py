"""Tests for the audio layout converter."""
import pytest
from unittest.mock import MagicMock, patch
import pcbnew
from kicad_pcb_generator.audio.layout.converter import AudioLayoutConverter, LayoutResult
from kicad_pcb_generator.audio.rules.design import AudioDesignRules, SignalType

@pytest.fixture
def mock_schematic():
    """Create a mock schematic."""
    schematic = MagicMock()
    
    # Mock components
    components = []
    for ref, value in [
        ("U1", "OPA1612"),
        ("U2", "OPA1612"),
        ("J1", "AUDIO_IN"),
        ("J2", "AUDIO_OUT"),
        ("J3", "POWER_IN"),
        ("R1", "10k"),
        ("C1", "100nF"),
        ("L1", "10uH"),
        ("REG1", "POWER_REG"),
        ("C2", "DECOUPLING_100nF"),
        ("C3", "DECOUPLING_10uF")
    ]:
        comp = MagicMock()
        comp.GetReference.return_value = ref
        comp.GetValue.return_value = value
        comp.GetPins.return_value = []  # Mock pins
        components.append(comp)
    schematic.GetComponents.return_value = components
    
    # Mock nets
    nets = []
    for name in ["AUDIO_IN", "AUDIO_OUT", "POWER", "GND"]:
        net = MagicMock()
        net.GetNetname.return_value = name
        nets.append(net)
    schematic.GetNets.return_value = nets
    
    return schematic

@pytest.fixture
def mock_board():
    """Create a mock board."""
    board = MagicMock()
    
    # Mock board dimensions
    bbox = MagicMock()
    bbox.GetWidth.return_value = 100000000  # 100mm in nm
    bbox.GetHeight.return_value = 100000000  # 100mm in nm
    board.GetBoardEdgesBoundingBox.return_value = bbox
    
    # Mock design settings
    rules = MagicMock()
    board.GetDesignSettings.return_value = rules
    
    # Mock footprints
    board.GetFootprints.return_value = []
    
    return board

@pytest.fixture
def converter():
    """Create an audio layout converter."""
    return AudioLayoutConverter()

def test_convert_schematic_success(converter, mock_schematic, mock_board):
    """Test successful schematic conversion."""
    with patch("pcbnew.BOARD", return_value=mock_board):
        result = converter.convert_schematic(mock_schematic)
        
        assert result.success
        assert result.board == mock_board
        assert not result.errors
        assert isinstance(result.warnings, list)

def test_convert_schematic_validation_failure(converter, mock_schematic):
    """Test schematic conversion with validation failure."""
    # Mock schematic validator to return errors
    with patch.object(converter.schematic_validator, "validate_schematic") as mock_validate:
        mock_validate.return_value = [
            MagicMock(severity="error", message="Invalid component"),
            MagicMock(severity="warning", message="Component warning")
        ]
        
        result = converter.convert_schematic(mock_schematic)
        
        assert not result.success
        assert not result.board
        assert "Invalid component" in result.errors
        assert "Component warning" in result.warnings

def test_setup_board(converter, mock_board):
    """Test board setup."""
    converter._setup_board(mock_board)
    
    # Verify board settings
    mock_board.SetBoardThickness.assert_called_once()
    mock_board.SetCopperWeight.assert_called_once()
    mock_board.SetEnabledLayers.assert_called_once()
    
    # Verify design rules
    rules = mock_board.GetDesignSettings()
    rules.SetTrackWidth.assert_called_once()
    rules.SetViasMinSize.assert_called_once()
    rules.SetMinClearance.assert_called_once()

def test_add_components(converter, mock_board, mock_schematic):
    """Test component addition with audio-specific placement."""
    converter._add_components(mock_board, mock_schematic)
    
    # Verify components were added
    assert mock_board.Add.call_count == len(mock_schematic.GetComponents())
    
    # Get all placed footprints
    footprints = [call[0][0] for call in mock_board.Add.call_args_list]
    
    # Verify opamp placement
    opamps = [f for f in footprints if f.GetReference().startswith("U")]
    assert len(opamps) == 2  # U1 and U2
    
    # Verify opamps are placed in a grid in the center
    for i, opamp in enumerate(opamps):
        pos = opamp.GetPosition()
        row = i // 2
        col = i % 2
        expected_x = 50000000 + (col - 0.5) * 20000000  # 50mm + offset
        expected_y = 50000000 + (row - 0.5) * 20000000  # 50mm + offset
        assert pos.x == expected_x
        assert pos.y == expected_y
    
    # Verify connector placement
    connectors = [f for f in footprints if f.GetReference().startswith("J")]
    assert len(connectors) == 3  # J1, J2, J3
    
    # Verify input connector (J1) is on left edge
    j1 = next(f for f in connectors if f.GetReference() == "J1")
    assert j1.GetPosition().x == 10000000  # 10mm margin
    assert j1.GetPosition().y == 10000000  # 10mm margin
    
    # Verify output connector (J2) is on right edge
    j2 = next(f for f in connectors if f.GetReference() == "J2")
    assert j2.GetPosition().x == 90000000  # 100mm - 10mm margin
    assert j2.GetPosition().y == 10000000  # 10mm margin
    
    # Verify power connector (J3) is on top edge
    j3 = next(f for f in connectors if f.GetReference() == "J3")
    assert j3.GetPosition().x == 10000000  # 10mm margin
    assert j3.GetPosition().y == 10000000  # 10mm margin
    
    # Verify passive components
    passives = [f for f in footprints if f.GetReference().startswith(("R", "C", "L"))]
    assert len(passives) == 3  # R1, C1, L1
    
    # Verify power component
    power = [f for f in footprints if f.GetReference() == "REG1"]
    assert len(power) == 1
    assert power[0].GetPosition().x == 10000000  # 10mm margin
    assert power[0].GetPosition().y == 20000000  # 20mm from top

def test_place_decoupling_capacitors(converter, mock_board, mock_schematic):
    """Test decoupling capacitor placement."""
    # Create mock opamp and decoupling capacitors
    opamp = MagicMock()
    opamp.GetReference.return_value = "U1"
    opamp.GetValue.return_value = "OPA1612"
    
    decoupling = []
    for ref, value in [("C2", "DECOUPLING_100nF"), ("C3", "DECOUPLING_10uF")]:
        cap = MagicMock()
        cap.GetReference.return_value = ref
        cap.GetValue.return_value = value
        decoupling.append(cap)
    
    # Mock component positions
    opamp_pos = pcbnew.VECTOR2I(50000000, 50000000)  # 50mm, 50mm
    mock_board.GetFootprints.return_value = [
        MagicMock(GetReference=lambda: "U1", GetPosition=lambda: opamp_pos)
    ]
    
    # Place decoupling capacitors
    converter._place_decoupling_capacitors(opamp, decoupling, mock_board, mock_schematic)
    
    # Verify capacitors were added
    assert mock_board.Add.call_count == len(decoupling)
    
    # Verify capacitor placement
    for i, call in enumerate(mock_board.Add.call_args_list):
        footprint = call[0][0]
        pos = footprint.GetPosition()
        
        # Verify capacitors are placed next to opamp
        expected_x = opamp_pos.x + 2000000  # 2% of board width
        expected_y = opamp_pos.y + (i * 2000000)  # 2% of board width spacing
        assert pos.x == expected_x
        assert pos.y == expected_y

def test_are_components_connected(converter, mock_schematic):
    """Test component connection detection."""
    # Create mock components with connected pins
    comp1 = MagicMock()
    comp2 = MagicMock()
    
    # Mock pins with common net
    pin1 = MagicMock()
    pin1.GetNetname.return_value = "AUDIO_IN"
    pin2 = MagicMock()
    pin2.GetNetname.return_value = "AUDIO_IN"
    
    comp1.GetPins.return_value = [pin1]
    comp2.GetPins.return_value = [pin2]
    
    # Test connected components
    assert converter._are_components_connected(comp1, comp2, mock_schematic)
    
    # Test unconnected components
    pin2.GetNetname.return_value = "DIFFERENT_NET"
    assert not converter._are_components_connected(comp1, comp2, mock_schematic)

def test_get_component_position(converter, mock_board):
    """Test component position retrieval."""
    # Create mock component and footprint
    component = MagicMock()
    component.GetReference.return_value = "U1"
    
    footprint = MagicMock()
    footprint.GetReference.return_value = "U1"
    footprint.GetPosition.return_value = pcbnew.VECTOR2I(50000000, 50000000)  # 50mm, 50mm
    
    mock_board.GetFootprints.return_value = [footprint]
    
    # Test position retrieval
    pos = converter._get_component_position(component, mock_board)
    assert pos.x == 50000000
    assert pos.y == 50000000
    
    # Test non-existent component
    component.GetReference.return_value = "NONEXISTENT"
    pos = converter._get_component_position(component, mock_board)
    assert pos.x == 0
    assert pos.y == 0

def test_get_connected_components(converter, mock_board):
    """Test getting components connected to a net."""
    # Create mock net and components
    net = MagicMock()
    net.GetNetname.return_value = "AUDIO_IN"
    
    # Create mock footprints with pads
    footprints = []
    for ref in ["U1", "J1"]:
        footprint = MagicMock()
        footprint.GetReference.return_value = ref
        pad = MagicMock()
        pad.GetNetname.return_value = "AUDIO_IN"
        footprint.GetPads.return_value = [pad]
        footprints.append(footprint)
    
    mock_board.GetFootprints.return_value = footprints
    
    # Test getting connected components
    components = converter._get_connected_components(net, mock_board)
    assert len(components) == 2
    assert all(c.GetReference() in ["U1", "J1"] for c in components)

def test_calculate_audio_path(converter, mock_board):
    """Test audio signal path calculation."""
    # Create mock components
    start = MagicMock()
    start.GetPosition.return_value = pcbnew.VECTOR2I(0, 0)
    
    end = MagicMock()
    end.GetPosition.return_value = pcbnew.VECTOR2I(100000000, 100000000)  # 100mm, 100mm
    
    # Calculate path
    path = converter._calculate_audio_path(start, end, mock_board)
    
    # Verify path
    assert len(path) == 3
    assert path[0] == pcbnew.VECTOR2I(0, 0)
    assert path[-1] == pcbnew.VECTOR2I(100000000, 100000000)
    
    # Verify intermediate point creates a curve
    mid_x = 50000000  # 50mm
    mid_y = 50000000  # 50mm
    curve_offset = 2000000  # 2% of board width
    assert path[1] == pcbnew.VECTOR2I(mid_x, mid_y + curve_offset)

def test_calculate_digital_path(converter, mock_board):
    """Test digital signal path calculation."""
    # Create mock components
    start = MagicMock()
    start.GetPosition.return_value = pcbnew.VECTOR2I(0, 0)
    
    end = MagicMock()
    end.GetPosition.return_value = pcbnew.VECTOR2I(100000000, 100000000)  # 100mm, 100mm
    
    # Calculate path
    path = converter._calculate_digital_path(start, end, mock_board)
    
    # Verify path
    assert len(path) == 4
    assert path[0] == pcbnew.VECTOR2I(0, 0)
    assert path[-1] == pcbnew.VECTOR2I(100000000, 100000000)
    
    # Verify intermediate points route around center
    mid_x = 50000000  # 50mm
    mid_y = 50000000  # 50mm
    assert path[1] == pcbnew.VECTOR2I(mid_x, 0)  # First horizontal
    assert path[2] == pcbnew.VECTOR2I(mid_x, 100000000)  # Then vertical

def test_route_signals(converter, mock_board):
    """Test signal routing with audio-specific considerations."""
    # Create mock net and components
    net = MagicMock()
    net.GetNetname.return_value = "AUDIO_IN"
    
    # Create mock components
    components = []
    for i in range(3):
        comp = MagicMock()
        comp.GetPosition.return_value = pcbnew.VECTOR2I(i * 10000000, i * 10000000)  # 10mm spacing
        components.append(comp)
    
    # Mock getting connected components
    with patch.object(converter, "_get_connected_components", return_value=components):
        # Route signals
        converter._route_signals(mock_board)
        
        # Verify tracks were added
        assert mock_board.Add.call_count == 2  # One track between each pair of components
        
        # Verify track properties
        for call in mock_board.Add.call_args_list:
            track = call[0][0]
            track.SetWidth.assert_called_once()
            track.SetClearance.assert_called_once()
            track.SetLayer.assert_called_once()
            
            # Verify track points
            track.SetStart.assert_called_once()
            track.SetEnd.assert_called_once()
            track.AddPoint.assert_called()  # For curved paths 
