"""Tests for the board validator."""
import pytest
from unittest.mock import MagicMock, patch
import pcbnew
from kicad_pcb_generator.core.board.validator import (
    BoardValidator,
    ValidationCategory,
    ValidationResult
)

@pytest.fixture
def mock_board():
    """Create a mock board for testing."""
    board = MagicMock(spec=pcbnew.BOARD)
    
    # Mock board dimensions
    board_box = MagicMock()
    board_box.GetWidth.return_value = 100000000  # 100mm
    board_box.GetHeight.return_value = 100000000  # 100mm
    board.GetBoardEdgesBoundingBox.return_value = board_box
    
    # Mock layer manager
    layer_manager = MagicMock()
    board.GetLayerManager.return_value = layer_manager
    
    # Mock design settings
    design_settings = MagicMock()
    design_settings.GetTrackWidth.return_value = 200000  # 0.2mm
    design_settings.GetViasMinSize.return_value = 400000  # 0.4mm
    design_settings.GetMinClearance.return_value = 200000  # 0.2mm
    board.GetDesignSettings.return_value = design_settings
    
    return board

@pytest.fixture
def validator():
    """Create a validator instance for testing."""
    return BoardValidator()

def test_validate_kicad_version():
    """Test KiCad version validation."""
    with patch('pcbnew.Version', return_value='9.0.0'):
        validator = BoardValidator()
        # Should not raise an exception
    
    with patch('pcbnew.Version', return_value='8.0.0'):
        with pytest.raises(RuntimeError):
            BoardValidator()

def test_validate_dimensions(validator, mock_board):
    """Test board dimension validation."""
    results = validator._validate_dimensions(mock_board)
    
    assert ValidationCategory.DIMENSIONS in results
    assert len(results[ValidationCategory.DIMENSIONS]) == 0  # No errors for valid dimensions
    
    # Test too small dimensions
    mock_board.GetBoardEdgesBoundingBox().GetWidth.return_value = 1000000  # 1mm
    mock_board.GetBoardEdgesBoundingBox().GetHeight.return_value = 1000000  # 1mm
    results = validator._validate_dimensions(mock_board)
    assert len(results[ValidationCategory.DIMENSIONS]) > 0
    assert any("too small" in result.message for result in results[ValidationCategory.DIMENSIONS])

def test_validate_layers(validator, mock_board):
    """Test layer validation."""
    # Mock layer properties
    layer_manager = mock_board.GetLayerManager()
    layer_manager.GetLayerType.return_value = pcbnew.LT_SIGNAL
    layer_manager.GetLayerProperties.return_value = {'copper_weight': 0.5}
    
    # Mock layer visibility
    mock_board.IsLayerEnabled.return_value = True
    mock_board.IsLayerVisible.return_value = True
    mock_board.GetLayerName.return_value = "Signal Layer"
    
    results = validator._validate_layers(mock_board)
    
    assert ValidationCategory.LAYERS in results
    assert len(results[ValidationCategory.LAYERS]) == 0  # No errors for valid layers

def test_validate_design_rules(validator, mock_board):
    """Test design rules validation."""
    results = validator._validate_design_rules(mock_board)
    
    assert ValidationCategory.DESIGN_RULES in results
    assert len(results[ValidationCategory.DESIGN_RULES]) == 0  # No errors for valid rules
    
    # Test invalid track width
    mock_board.GetDesignSettings().GetTrackWidth.return_value = 50000  # 0.05mm
    results = validator._validate_design_rules(mock_board)
    assert len(results[ValidationCategory.DESIGN_RULES]) > 0
    assert any("Track width" in result.message for result in results[ValidationCategory.DESIGN_RULES])

def test_validate_components(validator, mock_board):
    """Test component validation."""
    # Mock footprints
    fp1 = MagicMock()
    fp1.GetReference.return_value = "R1"
    fp1.GetPosition.return_value = MagicMock(x=0, y=0)
    
    fp2 = MagicMock()
    fp2.GetReference.return_value = "R2"
    fp2.GetPosition.return_value = MagicMock(x=1000000, y=1000000)  # 1mm away
    
    mock_board.GetFootprints.return_value = [fp1, fp2]
    
    results = validator._validate_components(mock_board)
    
    assert ValidationCategory.COMPONENTS in results
    assert len(results[ValidationCategory.COMPONENTS]) == 0  # No errors for valid spacing

def test_validate_traces(validator, mock_board):
    """Test trace validation."""
    # Mock tracks
    track = MagicMock()
    track.GetWidth.return_value = 200000  # 0.2mm
    track.GetStart.return_value = MagicMock(x=0, y=0)
    
    mock_board.GetTracks.return_value = [track]
    
    results = validator._validate_traces(mock_board)
    
    assert ValidationCategory.TRACES in results
    assert len(results[ValidationCategory.TRACES]) == 0  # No errors for valid traces

def test_validate_vias(validator, mock_board):
    """Test via validation."""
    # Mock vias
    via = MagicMock()
    via.GetWidth.return_value = 400000  # 0.4mm
    via.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.GetVias.return_value = [via]
    
    results = validator._validate_vias(mock_board)
    
    assert ValidationCategory.VIAS in results
    assert len(results[ValidationCategory.VIAS]) == 0  # No errors for valid vias

def test_validate_holes(validator, mock_board):
    """Test hole validation."""
    # Mock pads
    pad = MagicMock()
    pad.GetAttribute.return_value = pcbnew.PAD_ATTRIB_PTH
    pad.GetDrillSize.return_value = MagicMock(x=300000)  # 0.3mm
    pad.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.GetPads.return_value = [pad]
    
    results = validator._validate_holes(mock_board)
    
    assert ValidationCategory.HOLES in results
    assert len(results[ValidationCategory.HOLES]) == 0  # No errors for valid holes

def test_validate_zones(validator, mock_board):
    """Test zone validation."""
    # Mock zones
    zone = MagicMock()
    zone.GetLocalClearance.return_value = 200000  # 0.2mm
    zone.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.Zones.return_value = [zone]
    
    results = validator._validate_zones(mock_board)
    
    assert ValidationCategory.ZONES in results
    assert len(results[ValidationCategory.ZONES]) == 0  # No errors for valid zones

def test_validate_silkscreen(validator, mock_board):
    """Test silkscreen validation."""
    # Mock drawings
    drawing = MagicMock()
    drawing.GetLayer.return_value = pcbnew.F_SilkS
    drawing.GetTextSize.return_value = MagicMock(x=600000)  # 0.6mm
    drawing.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.GetDrawings.return_value = [drawing]
    
    results = validator._validate_silkscreen(mock_board)
    
    assert ValidationCategory.SILKSCREEN in results
    assert len(results[ValidationCategory.SILKSCREEN]) == 0  # No errors for valid silkscreen

def test_validate_mask(validator, mock_board):
    """Test solder mask validation."""
    # Mock pads
    pad = MagicMock()
    pad.GetLocalSolderMaskMargin.return_value = 100000  # 0.1mm
    pad.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.GetPads.return_value = [pad]
    
    results = validator._validate_mask(mock_board)
    
    assert ValidationCategory.MASK in results
    assert len(results[ValidationCategory.MASK]) == 0  # No errors for valid mask

def test_validate_paste(validator, mock_board):
    """Test solder paste validation."""
    # Mock pads
    pad = MagicMock()
    pad.GetAttribute.return_value = pcbnew.PAD_ATTRIB_SMD
    pad.GetLocalSolderPasteMargin.return_value = 100000  # 0.1mm
    pad.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.GetPads.return_value = [pad]
    
    results = validator._validate_paste(mock_board)
    
    assert ValidationCategory.PASTE in results
    assert len(results[ValidationCategory.PASTE]) == 0  # No errors for valid paste

def test_validate_audio_rules(validator, mock_board):
    """Test audio rules validation."""
    # Mock layer with audio in name
    mock_board.GetLayerName.return_value = "Audio Layer"
    mock_board.IsLayerEnabled.return_value = True
    
    # Mock audio component
    audio_fp = MagicMock()
    audio_fp.GetReference.return_value = "AUDIO1"
    mock_board.GetFootprints.return_value = [audio_fp]
    
    results = validator._validate_audio_rules(mock_board)
    
    assert ValidationCategory.AUDIO in results
    assert len(results[ValidationCategory.AUDIO]) == 0  # No errors for valid audio setup

def test_validate_manufacturing(validator, mock_board):
    """Test manufacturing validation."""
    # Mock via with good annular ring
    via = MagicMock()
    via.GetDrill.return_value = 300000  # 0.3mm
    via.GetWidth.return_value = 500000  # 0.5mm
    via.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.GetVias.return_value = [via]
    
    # Mock zone with good area
    zone = MagicMock()
    zone.GetArea.return_value = 1000000000000  # 1mm²
    zone.GetPosition.return_value = MagicMock(x=0, y=0)
    
    mock_board.Zones.return_value = [zone]
    
    results = validator._validate_manufacturing(mock_board)
    
    assert ValidationCategory.MANUFACTURING in results
    assert len(results[ValidationCategory.MANUFACTURING]) == 0  # No errors for valid manufacturing setup

def test_validate_board_comprehensive(validator, mock_board):
    """Test comprehensive board validation."""
    # Setup all mocks for a valid board
    mock_board.GetBoardEdgesBoundingBox().GetWidth.return_value = 100000000  # 100mm
    mock_board.GetBoardEdgesBoundingBox().GetHeight.return_value = 100000000  # 100mm
    
    layer_manager = mock_board.GetLayerManager()
    layer_manager.GetLayerType.return_value = pcbnew.LT_SIGNAL
    layer_manager.GetLayerProperties.return_value = {'copper_weight': 1.0}
    
    mock_board.IsLayerEnabled.return_value = True
    mock_board.IsLayerVisible.return_value = True
    mock_board.GetLayerName.return_value = "Audio Layer"
    
    design_settings = mock_board.GetDesignSettings()
    design_settings.GetTrackWidth.return_value = 200000  # 0.2mm
    design_settings.GetViasMinSize.return_value = 400000  # 0.4mm
    design_settings.GetMinClearance.return_value = 200000  # 0.2mm
    
    # Add all necessary mocks for components, traces, vias, etc.
    # ... (similar to individual test cases above)
    
    results = validator.validate_board(mock_board)
    
    # Check that all categories are present
    assert all(category in results for category in ValidationCategory)
    
    # Check that there are no errors for a valid board
    assert all(len(results[category]) == 0 for category in ValidationCategory) 
