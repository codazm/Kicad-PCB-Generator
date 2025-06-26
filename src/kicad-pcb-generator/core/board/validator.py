"""Board validation using KiCad 9's native functionality."""
import logging
import pcbnew
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from ....utils.config.settings import Settings
from ....utils.logging.logger import Logger
from ..validation.base_validator import BaseValidator, ValidationCategory, ValidationResult

class ValidationCategory(Enum):
    """Categories for validation results."""
    GENERAL = "General"
    DIMENSIONS = "Dimensions"
    LAYERS = "Layers"
    DESIGN_RULES = "Design Rules"
    COMPONENTS = "Components"
    TRACES = "Traces"
    VIAS = "Vias"
    HOLES = "Holes"
    ZONES = "Zones"
    SILKSCREEN = "Silkscreen"
    MASK = "Mask"
    PASTE = "Paste"
    AUDIO = "Audio"
    MANUFACTURING = "Manufacturing"

@dataclass
class ValidationResult:
    """Result of a validation check."""
    category: ValidationCategory
    message: str
    severity: str
    location: Optional[Tuple[float, float]] = None
    details: Optional[Dict[str, Any]] = None

class BoardValidator(BaseValidator):
    """Validates PCB boards using KiCad 9's native functionality."""
    
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[Logger] = None):
        """Initialize the board validator.
        
        Args:
            settings: Optional settings instance
            logger: Optional logger instance
        """
        super().__init__(settings, logger)
        self._drc_engine: Optional[pcbnew.DRC_ENGINE] = None
    
    def _get_drc_engine(self, board: pcbnew.BOARD) -> pcbnew.DRC_ENGINE:
        """Get or create DRC engine.
        
        Args:
            board: KiCad board object
            
        Returns:
            DRC engine instance
        """
        if self._drc_engine is None:
            self._drc_engine = pcbnew.DRC_ENGINE()
            self._drc_engine.SetBoard(board)
        return self._drc_engine
    
    @lru_cache(maxsize=32)
    def _get_board_box(self, board: pcbnew.BOARD) -> Tuple[float, float]:
        """Get board dimensions.
        
        Args:
            board: KiCad board object
            
        Returns:
            Tuple of (width, height) in mm
        """
        board_box = board.GetBoardEdgesBoundingBox()
        return (board_box.GetWidth() / 1e6, board_box.GetHeight() / 1e6)
    
    @lru_cache(maxsize=32)
    def _get_power_planes(self, board: pcbnew.BOARD) -> Set[str]:
        """Get power plane names.
        
        Args:
            board: KiCad board object
            
        Returns:
            Set of power plane names
        """
        power_planes = set()
        for net in board.GetNetsByName().values():
            if net.GetNetname().startswith(('+', '-')):
                power_planes.add(net.GetNetname())
        return power_planes
    
    @lru_cache(maxsize=32)
    def _get_component_positions(self, board: pcbnew.BOARD) -> Dict[str, Tuple[float, float]]:
        """Get component positions.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary mapping component references to positions
        """
        positions = {}
        for footprint in board.GetFootprints():
            ref = footprint.GetReference()
            if ref:
                pos = footprint.GetPosition()
                positions[ref] = (pos.x / 1e6, pos.y / 1e6)
        return positions
    
    def validate_board(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate a PCB board.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results by category
        """
        try:
            # Get or create DRC engine
            drc_engine = self._get_drc_engine(board)
            
            # Run validation using base class method
            results = super().validate(board)
            
            # Clear component position cache if board changed
            self._get_component_positions.cache_clear()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to validate board: {str(e)}")
            return {ValidationCategory.GENERAL: [self._create_result(
                ValidationCategory.GENERAL,
                f"Error during validation: {str(e)}",
                "error"
            )]}
    
    def _validate_components(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate component placement and properties using KiCad's native functionality."""
        results = {ValidationCategory.COMPONENTS: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            component_rules = validation_rules.get('components', {})
            
            # Get component positions
            positions = self._get_component_positions(board)
            
            # Check each component
            for footprint in board.GetFootprints():
                # Get component properties
                ref = footprint.GetReference()
                value = footprint.GetValue()
                layer = board.GetLayerName(footprint.GetLayer())
                
                # Check component placement
                if layer not in ["F.Cu", "B.Cu"]:
                    results[ValidationCategory.COMPONENTS].append(self._create_result(
                        ValidationCategory.COMPONENTS,
                        f"Component {ref} is not on a copper layer",
                        "error",
                        positions.get(ref)
                    ))
                
                # Check component value
                if not value:
                    results[ValidationCategory.COMPONENTS].append(self._create_result(
                        ValidationCategory.COMPONENTS,
                        f"Component {ref} has no value",
                        "warning",
                        positions.get(ref)
                    ))
            
        except Exception as e:
            self.logger.error(f"Error validating components: {str(e)}")
            results[ValidationCategory.COMPONENTS].append(self._create_result(
                ValidationCategory.COMPONENTS,
                f"Error validating components: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_traces(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate traces using KiCad's native functionality."""
        results = {ValidationCategory.TRACES: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            trace_rules = validation_rules.get('traces', {})
            min_width = trace_rules.get('min_width', 0.1)
            
            # Get DRC engine
            drc_engine = self._get_drc_engine(board)
            
            # Check each track
            for track in board.GetTracks():
                if not track.IsTrack():
                    continue
                
                # Get track properties
                width = track.GetWidth() / 1e6  # Convert to mm
                layer = board.GetLayerName(track.GetLayer())
                
                # Check track width
                if width < min_width:
                    results[ValidationCategory.TRACES].append(self._create_result(
                        ValidationCategory.TRACES,
                        f"Track width {width:.2f}mm is below minimum {min_width}mm",
                        "error",
                        (track.GetStart().x/1e6, track.GetStart().y/1e6)
                    ))
                
                # Check track layer
                if layer not in ["F.Cu", "B.Cu"]:
                    results[ValidationCategory.TRACES].append(self._create_result(
                        ValidationCategory.TRACES,
                        f"Track is not on a copper layer",
                        "error",
                        (track.GetStart().x/1e6, track.GetStart().y/1e6)
                    ))
            
        except Exception as e:
            self.logger.error(f"Error validating traces: {str(e)}")
            results[ValidationCategory.TRACES].append(self._create_result(
                ValidationCategory.TRACES,
                f"Error validating traces: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_vias(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate vias using KiCad's native functionality."""
        results = {ValidationCategory.VIAS: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            via_rules = validation_rules.get('vias', {})
            min_size = via_rules.get('min_size', 0.3)
            
            # Get DRC engine
            drc_engine = self._get_drc_engine(board)
            
            # Check each via
            for track in board.GetTracks():
                if not track.IsVia():
                    continue
                
                # Get via properties
                size = track.GetWidth() / 1e6  # Convert to mm
                
                # Check via size
                if size < min_size:
                    results[ValidationCategory.VIAS].append(self._create_result(
                        ValidationCategory.VIAS,
                        f"Via size {size:.2f}mm is below minimum {min_size}mm",
                        "error",
                        (track.GetPosition().x/1e6, track.GetPosition().y/1e6)
                    ))
            
        except Exception as e:
            self.logger.error(f"Error validating vias: {str(e)}")
            results[ValidationCategory.VIAS].append(self._create_result(
                ValidationCategory.VIAS,
                f"Error validating vias: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_holes(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate holes using KiCad's native functionality."""
        results = {ValidationCategory.HOLES: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            hole_rules = validation_rules.get('holes', {})
            min_size = hole_rules.get('min_size', 0.3)
            
            # Get component positions
            positions = self._get_component_positions(board)
            
            # Check each hole
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                        size = pad.GetDrillSize().x / 1e6  # Convert to mm
                        
                        if size < min_size:
                            results[ValidationCategory.HOLES].append(self._create_result(
                                ValidationCategory.HOLES,
                                f"Hole size {size:.2f}mm is below minimum {min_size}mm",
                                "error",
                                positions.get(footprint.GetReference())
                            ))
            
        except Exception as e:
            self.logger.error(f"Error validating holes: {str(e)}")
            results[ValidationCategory.HOLES].append(self._create_result(
                ValidationCategory.HOLES,
                f"Error validating holes: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_zones(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate zones using KiCad's native functionality."""
        results = {ValidationCategory.ZONES: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            zone_rules = validation_rules.get('zones', {})
            min_width = zone_rules.get('min_width', 0.1)
            
            # Get DRC engine
            drc_engine = self._get_drc_engine(board)
            
            # Check each zone
            for zone in board.Zones():
                # Get zone properties
                width = zone.GetMinThickness() / 1e6  # Convert to mm
                
                # Check zone width
                if width < min_width:
                    results[ValidationCategory.ZONES].append(self._create_result(
                        ValidationCategory.ZONES,
                        f"Zone width {width:.2f}mm is below minimum {min_width}mm",
                        "error",
                        (zone.GetPosition().x/1e6, zone.GetPosition().y/1e6)
                    ))
            
        except Exception as e:
            self.logger.error(f"Error validating zones: {str(e)}")
            results[ValidationCategory.ZONES].append(self._create_result(
                ValidationCategory.ZONES,
                f"Error validating zones: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_silkscreen(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate silkscreen using KiCad's native functionality."""
        results = {ValidationCategory.SILKSCREEN: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            silkscreen_rules = validation_rules.get('silkscreen', {})
            min_width = silkscreen_rules.get('min_width', 0.1)
            
            # Check each text item
            for text in board.GetDrawings():
                if text.GetLayer() in [pcbnew.F_SilkS, pcbnew.B_SilkS]:
                    # Get text properties
                    width = text.GetThickness() / 1e6  # Convert to mm
                    
                    # Check text width
                    if width < min_width:
                        results[ValidationCategory.SILKSCREEN].append(self._create_result(
                            ValidationCategory.SILKSCREEN,
                            f"Silkscreen text width {width:.2f}mm is below minimum {min_width}mm",
                            "warning",
                            (text.GetPosition().x/1e6, text.GetPosition().y/1e6)
                        ))
            
        except Exception as e:
            self.logger.error(f"Error validating silkscreen: {str(e)}")
            results[ValidationCategory.SILKSCREEN].append(self._create_result(
                ValidationCategory.SILKSCREEN,
                f"Error validating silkscreen: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_mask(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate solder mask using KiCad's native functionality."""
        results = {ValidationCategory.MASK: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            mask_rules = validation_rules.get('mask', {})
            min_clearance = mask_rules.get('min_clearance', 0.1)
            
            # Get component positions
            positions = self._get_component_positions(board)
            
            # Check each pad
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    # Get pad properties
                    clearance = pad.GetLocalSolderMaskMargin() / 1e6  # Convert to mm
                    
                    # Check mask clearance
                    if clearance < min_clearance:
                        results[ValidationCategory.MASK].append(self._create_result(
                            ValidationCategory.MASK,
                            f"Solder mask clearance {clearance:.2f}mm is below minimum {min_clearance}mm",
                            "warning",
                            positions.get(footprint.GetReference())
                        ))
            
        except Exception as e:
            self.logger.error(f"Error validating solder mask: {str(e)}")
            results[ValidationCategory.MASK].append(self._create_result(
                ValidationCategory.MASK,
                f"Error validating solder mask: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_paste(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate solder paste using KiCad's native functionality."""
        results = {ValidationCategory.PASTE: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            paste_rules = validation_rules.get('paste', {})
            min_clearance = paste_rules.get('min_clearance', 0.1)
            
            # Get component positions
            positions = self._get_component_positions(board)
            
            # Check each pad
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    # Get pad properties
                    clearance = pad.GetLocalSolderPasteMargin() / 1e6  # Convert to mm
                    
                    # Check paste clearance
                    if clearance < min_clearance:
                        results[ValidationCategory.PASTE].append(self._create_result(
                            ValidationCategory.PASTE,
                            f"Solder paste clearance {clearance:.2f}mm is below minimum {min_clearance}mm",
                            "warning",
                            positions.get(footprint.GetReference())
                        ))
            
        except Exception as e:
            self.logger.error(f"Error validating solder paste: {str(e)}")
            results[ValidationCategory.PASTE].append(self._create_result(
                ValidationCategory.PASTE,
                f"Error validating solder paste: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_audio_rules(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate audio-specific rules using KiCad's native functionality."""
        results = {ValidationCategory.AUDIO: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            audio_rules = validation_rules.get('audio', {})
            min_trace_width = audio_rules.get('min_trace_width', 0.2)
            
            # Get component positions
            positions = self._get_component_positions(board)
            
            # Check each track
            for track in board.GetTracks():
                if not track.IsTrack():
                    continue
                
                # Get track properties
                width = track.GetWidth() / 1e6  # Convert to mm
                net = track.GetNetname()
                
                # Check audio signal traces
                if net.startswith(('AUDIO', 'SIGNAL')):
                    if width < min_trace_width:
                        results[ValidationCategory.AUDIO].append(self._create_result(
                            ValidationCategory.AUDIO,
                            f"Audio signal trace width {width:.2f}mm is below minimum {min_trace_width}mm",
                            "error",
                            (track.GetStart().x/1e6, track.GetStart().y/1e6)
                        ))
            
        except Exception as e:
            self.logger.error(f"Error validating audio rules: {str(e)}")
            results[ValidationCategory.AUDIO].append(self._create_result(
                ValidationCategory.AUDIO,
                f"Error validating audio rules: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_manufacturing(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate manufacturing rules using KiCad's native functionality."""
        results = {ValidationCategory.MANUFACTURING: []}
        
        try:
            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            manufacturing_rules = validation_rules.get('manufacturing', {})
            min_drill_size = manufacturing_rules.get('min_drill_size', 0.3)
            
            # Get component positions
            positions = self._get_component_positions(board)
            
            # Check each hole
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                        size = pad.GetDrillSize().x / 1e6  # Convert to mm
                        
                        if size < min_drill_size:
                            results[ValidationCategory.MANUFACTURING].append(self._create_result(
                                ValidationCategory.MANUFACTURING,
                                f"Drill size {size:.2f}mm is below minimum {min_drill_size}mm",
                                "error",
                                positions.get(footprint.GetReference())
                            ))
            
        except Exception as e:
            self.logger.error(f"Error validating manufacturing rules: {str(e)}")
            results[ValidationCategory.MANUFACTURING].append(self._create_result(
                ValidationCategory.MANUFACTURING,
                f"Error validating manufacturing rules: {str(e)}",
                "error"
            ))
        
        return results 