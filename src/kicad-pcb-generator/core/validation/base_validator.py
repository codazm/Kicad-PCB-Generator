"""Base validator for the KiCad PCB Generator."""
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import pcbnew
import math
from functools import lru_cache
from ...utils.logging.logger import Logger
from ...utils.error_handling import (
    handle_validation_error,
    handle_operation_error,
    log_validation_error,
    ValidationError,
    ComponentError,
    ConnectionError,
    PowerError,
    GroundError,
    SignalError,
    AudioError,
    ManufacturingError
)
from .validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity,
    AudioValidationResult,
    SafetyValidationResult,
    ManufacturingValidationResult
)
from ...utils.config.settings import Settings
from ...utils.validation import (
    ValidationRule,
    ValidationRuleType
)

class BaseValidator:
    """Base class for PCB validators."""
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the validator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or Logger(__name__)
        self._enabled_rules: Dict[str, bool] = {}
        self._callback: Optional[Callable[[List[ValidationResult]], None]] = None
        self.settings = Settings()

    def enable_rule(self, rule: str) -> None:
        """Enable a validation rule.
        
        Args:
            rule: Rule name to enable
        """
        self._enabled_rules[rule] = True

    def disable_rule(self, rule: str) -> None:
        """Disable a validation rule.
        
        Args:
            rule: Rule name to disable
        """
        self._enabled_rules[rule] = False

    def is_rule_enabled(self, rule: str) -> bool:
        """Check if a rule is enabled.
        
        Args:
            rule: Rule name to check
            
        Returns:
            True if rule is enabled
        """
        return self._enabled_rules.get(rule, False)

    def set_callback(self, callback: Callable[[List[ValidationResult]], None]) -> None:
        """Set validation result callback.
        
        Args:
            callback: Callback function
        """
        self._callback = callback

    @handle_validation_error(logger=Logger(__name__), category="general")
    def validate(self) -> List[ValidationResult]:
        """Perform validation.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Get component positions
            positions: Dict[str, Tuple[float, float]] = {}
            for footprint in board.GetFootprints():
                pos = footprint.GetPosition()
                positions[footprint.GetReference()] = (pos.x/1e6, pos.y/1e6)

            # Run enabled validations
            if self.is_rule_enabled("design_rules"):
                results.extend(self._validate_design_rules())
            if self.is_rule_enabled("component_placement"):
                results.extend(self._validate_component_placement())
            if self.is_rule_enabled("routing"):
                results.extend(self._validate_routing())
            if self.is_rule_enabled("audio_specific"):
                results.extend(self._validate_audio_specific())
            if self.is_rule_enabled("manufacturing"):
                results.extend(self._validate_manufacturing())
            if self.is_rule_enabled("power"):
                results.extend(self._validate_power())
            if self.is_rule_enabled("ground"):
                results.extend(self._validate_ground())
            if self.is_rule_enabled("signal"):
                results.extend(self._validate_signal())
            if self.is_rule_enabled("thermal"):
                results.extend(self._validate_thermal())
            if self.is_rule_enabled("emi_emc"):
                results.extend(self._validate_emi_emc())
            if self.is_rule_enabled("components"):
                results.extend(self._validate_components())

            # Call callback if set
            if self._callback:
                self._callback(results)

        except Exception as e:
            self.logger.error(f"Error during validation: {str(e)}")
            results.append(ValidationResult(
                category=ValidationCategory.DESIGN_RULES,
                message=f"Error during validation: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="design_rules")
    def _validate_design_rules(self) -> List[ValidationResult]:
        """Validate design rules using KiCad's native DRC engine.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Get DRC engine
            drc_engine = pcbnew.DRC_ENGINE()
            drc_engine.SetBoard(board)

            # Run DRC
            drc_engine.RunDRC()

            # Get DRC results
            for item in drc_engine.GetResults():
                results.append(self._create_result(
                    category=ValidationCategory.DESIGN_RULES,
                    message=item.GetErrorMessage(),
                    severity=ValidationSeverity.ERROR if item.GetSeverity() == pcbnew.DRC_SEVERITY_ERROR else ValidationSeverity.WARNING,
                    location=(item.GetPosition().x/1e6, item.GetPosition().y/1e6),
                    details={
                        'error_code': item.GetErrorCode(),
                        'error_type': item.GetErrorType(),
                        'layer': board.GetLayerName(item.GetLayer())
                    }
                ))

        except Exception as e:
            self.logger.error(f"Error validating design rules: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.DESIGN_RULES,
                message=f"Error validating design rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="component_placement")
    def _validate_component_placement(self) -> List[ValidationResult]:
        """Validate component placement.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Get board edges
            board_edges = board.GetBoardEdgesBoundingBox()

            # Check each component
            for footprint in board.GetFootprints():
                # Check if component is within board boundaries
                pos = footprint.GetPosition()
                if not board_edges.Contains(pos):
                    results.append(self._create_result(
                        category=ValidationCategory.COMPONENT_PLACEMENT,
                        message=f"Component {footprint.GetReference()} is outside board boundaries",
                        severity=ValidationSeverity.ERROR,
                        location=(pos.x/1e6, pos.y/1e6),
                        details={'component': footprint.GetReference()}
                    ))

                # Check for overlapping components
                for other in board.GetFootprints():
                    if other != footprint and footprint.HitTest(other.GetPosition()):
                        results.append(self._create_result(
                            category=ValidationCategory.COMPONENT_PLACEMENT,
                            message=f"Component {footprint.GetReference()} overlaps with {other.GetReference()}",
                            severity=ValidationSeverity.ERROR,
                            location=(pos.x/1e6, pos.y/1e6),
                            details={
                                'component': footprint.GetReference(),
                                'overlapping_with': other.GetReference()
                            }
                        ))

                # Check component orientation
                if footprint.GetOrientationDegrees() % 90 != 0:
                    results.append(self._create_result(
                        category=ValidationCategory.COMPONENT_PLACEMENT,
                        message=f"Component {footprint.GetReference()} is not aligned to grid",
                        severity=ValidationSeverity.WARNING,
                        location=(pos.x/1e6, pos.y/1e6),
                        details={
                            'component': footprint.GetReference(),
                            'orientation': footprint.GetOrientationDegrees()
                        }
                    ))

        except Exception as e:
            self.logger.error(f"Error validating component placement: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.COMPONENT_PLACEMENT,
                message=f"Error validating component placement: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="routing")
    def _validate_routing(self) -> List[ValidationResult]:
        """Validate routing using KiCad's native functionality.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Get design settings
            settings = board.GetDesignSettings()
            min_track_width = settings.GetTrackWidth()
            min_clearance = settings.GetMinClearance()

            # Check tracks
            for track in board.GetTracks():
                if not track.IsTrack():
                    continue

                # Check track width
                if track.GetWidth() < min_track_width:
                    results.append(self._create_result(
                        category=ValidationCategory.ROUTING,
                        message=f"Track width {track.GetWidth()/1e6:.2f}mm is below minimum {min_track_width/1e6:.2f}mm",
                        severity=ValidationSeverity.ERROR,
                        location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                        details={
                            'net': track.GetNetname(),
                            'width': track.GetWidth()/1e6,
                            'min_width': min_track_width/1e6
                        }
                    ))

                # Check track layer
                layer = board.GetLayerName(track.GetLayer())
                if layer not in ["F.Cu", "B.Cu"]:
                    results.append(self._create_result(
                        category=ValidationCategory.ROUTING,
                        message=f"Track is not on a copper layer",
                        severity=ValidationSeverity.ERROR,
                        location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                        details={
                            'net': track.GetNetname(),
                            'layer': layer
                        }
                    ))

            # Check vias
            for via in board.GetVias():
                # Check via size
                if via.GetWidth() < min_track_width:
                    results.append(self._create_result(
                        category=ValidationCategory.ROUTING,
                        message=f"Via diameter {via.GetWidth()/1e6:.2f}mm is below minimum {min_track_width/1e6:.2f}mm",
                        severity=ValidationSeverity.ERROR,
                        location=(via.GetPosition().x/1e6, via.GetPosition().y/1e6),
                        details={
                            'net': via.GetNetname(),
                            'diameter': via.GetWidth()/1e6,
                            'min_diameter': min_track_width/1e6
                        }
                    ))

                # Check via drill
                if via.GetDrill() < min_track_width/2:
                    results.append(self._create_result(
                        category=ValidationCategory.ROUTING,
                        message=f"Via drill {via.GetDrill()/1e6:.2f}mm is below minimum {min_track_width/2e6:.2f}mm",
                        severity=ValidationSeverity.ERROR,
                        location=(via.GetPosition().x/1e6, via.GetPosition().y/1e6),
                        details={
                            'net': via.GetNetname(),
                            'drill': via.GetDrill()/1e6,
                            'min_drill': min_track_width/2e6
                        }
                    ))

        except Exception as e:
            self.logger.error(f"Error validating routing: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.ROUTING,
                message=f"Error validating routing: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="audio_specific")
    def _validate_audio_specific(self) -> List[ValidationResult]:
        """Validate audio-specific rules.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Check audio signal paths
            audio_nets = ["AUDIO_IN", "AUDIO_OUT", "LINE_IN", "LINE_OUT", "SPEAKER"]
            for net in board.GetNetsByName().values():
                if net.GetNetname() in audio_nets:
                    # Check track width for audio signals
                    min_width = 0.2  # 0.2mm minimum for audio tracks
                    for track in net.GetTracks():
                        if track.IsTrack() and track.GetWidth()/1e6 < min_width:
                            results.append(self._create_result(
                                category=ValidationCategory.AUDIO_SPECIFIC,
                                message=f"Audio signal track width {track.GetWidth()/1e6:.2f}mm is below minimum {min_width}mm",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net.GetNetname(),
                                    'width': track.GetWidth()/1e6,
                                    'min_width': min_width
                                }
                            ))

                    # Check for ground plane under audio signals
                    has_ground_plane = False
                    for zone in board.Zones():
                        if zone.GetNetname() == "GND" and zone.HitTest(track.GetStart()):
                            has_ground_plane = True
                            break
                    if not has_ground_plane:
                        results.append(self._create_result(
                            category=ValidationCategory.AUDIO_SPECIFIC,
                            message=f"Audio signal {net.GetNetname()} has no ground plane underneath",
                            severity=ValidationSeverity.WARNING,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={'net': net.GetNetname()}
                        ))

            # Check for audio components
            audio_components = ["OPAMP", "DAC", "ADC", "CODEC"]
            for footprint in board.GetFootprints():
                if any(comp in footprint.GetReference() for comp in audio_components):
                    # Check for decoupling capacitors
                    has_decoupling = False
                    for pad in footprint.GetPads():
                        if "C" in pad.GetParent().GetReference() and pad.GetNetname() in ["VCC", "VDD"]:
                            has_decoupling = True
                            break
                    if not has_decoupling:
                        results.append(self._create_result(
                            category=ValidationCategory.AUDIO_SPECIFIC,
                            message=f"Audio component {footprint.GetReference()} has no decoupling capacitor",
                            severity=ValidationSeverity.WARNING,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

                    # Check for ground connection
                    has_ground = False
                    for pad in footprint.GetPads():
                        if pad.GetNetname() == "GND":
                            has_ground = True
                            break
                    if not has_ground:
                        results.append(self._create_result(
                            category=ValidationCategory.AUDIO_SPECIFIC,
                            message=f"Audio component {footprint.GetReference()} has no ground connection",
                            severity=ValidationSeverity.ERROR,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

        except Exception as e:
            self.logger.error(f"Error validating audio-specific rules: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.AUDIO_SPECIFIC,
                message=f"Error validating audio-specific rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="manufacturing")
    def _validate_manufacturing(self) -> List[ValidationResult]:
        """Validate manufacturing rules.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Get board dimensions
            board_edges = board.GetBoardEdgesBoundingBox()
            width = board_edges.GetWidth() / 1e6  # Convert to mm
            height = board_edges.GetHeight() / 1e6

            # Check board size
            if width > 500 or height > 500:  # 500mm max size
                results.append(self._create_manufacturing_result(
                    category=ValidationCategory.MANUFACTURING,
                    message=f"Board size {width:.1f}x{height:.1f}mm exceeds maximum 500x500mm",
                    severity=ValidationSeverity.ERROR,
                    details={
                        'width': width,
                        'height': height,
                        'max_size': 500
                    }
                ))

            # Check minimum feature sizes
            min_track_width = 0.1  # 0.1mm minimum
            min_clearance = 0.1  # 0.1mm minimum
            min_via_drill = 0.2  # 0.2mm minimum

            for track in board.GetTracks():
                if track.IsTrack():
                    if track.GetWidth()/1e6 < min_track_width:
                        results.append(self._create_manufacturing_result(
                            category=ValidationCategory.MANUFACTURING,
                            message=f"Track width {track.GetWidth()/1e6:.2f}mm is below manufacturing minimum {min_track_width}mm",
                            severity=ValidationSeverity.ERROR,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            min_feature_size=min_track_width,
                            recommended_size=0.15
                        ))

            for via in board.GetVias():
                if via.GetDrill()/1e6 < min_via_drill:
                    results.append(self._create_manufacturing_result(
                        category=ValidationCategory.MANUFACTURING,
                        message=f"Via drill {via.GetDrill()/1e6:.2f}mm is below manufacturing minimum {min_via_drill}mm",
                        severity=ValidationSeverity.ERROR,
                        location=(via.GetPosition().x/1e6, via.GetPosition().y/1e6),
                        min_feature_size=min_via_drill,
                        recommended_size=0.3
                    ))

        except Exception as e:
            self.logger.error(f"Error validating manufacturing rules: {str(e)}")
            results.append(self._create_manufacturing_result(
                category=ValidationCategory.MANUFACTURING,
                message=f"Error validating manufacturing rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="power")
    def _validate_power(self) -> List[ValidationResult]:
        """Validate power rules.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Check power nets
            power_nets = ["VCC", "VDD", "3V3", "5V", "12V", "GND"]
            for net in board.GetNetsByName().values():
                if net.GetNetname() in power_nets:
                    # Check track width
                    min_width = 0.5  # 0.5mm minimum for power tracks
                    for track in net.GetTracks():
                        if track.IsTrack() and track.GetWidth()/1e6 < min_width:
                            results.append(self._create_result(
                                category=ValidationCategory.POWER,
                                message=f"Power track width {track.GetWidth()/1e6:.2f}mm is below minimum {min_width}mm",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net.GetNetname(),
                                    'width': track.GetWidth()/1e6,
                                    'min_width': min_width
                                }
                            ))

                    # Check for decoupling capacitors
                    has_decoupling = False
                    for pad in net.GetPads():
                        if "C" in pad.GetParent().GetReference():
                            has_decoupling = True
                            break
                    if not has_decoupling:
                        results.append(self._create_result(
                            category=ValidationCategory.POWER,
                            message=f"Power net {net.GetNetname()} has no decoupling capacitor",
                            severity=ValidationSeverity.WARNING,
                            details={'net': net.GetNetname()}
                        ))

        except Exception as e:
            self.logger.error(f"Error validating power rules: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.POWER,
                message=f"Error validating power rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="ground")
    def _validate_ground(self) -> List[ValidationResult]:
        """Validate ground rules.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Check ground nets
            ground_nets = ["GND", "AGND", "DGND"]
            for net in board.GetNetsByName().values():
                if net.GetNetname() in ground_nets:
                    # Check for ground plane
                    has_ground_plane = False
                    for zone in board.Zones():
                        if zone.GetNetname() == net.GetNetname():
                            has_ground_plane = True
                            break
                    if not has_ground_plane:
                        results.append(self._create_result(
                            category=ValidationCategory.GROUND,
                            message=f"Ground net {net.GetNetname()} has no ground plane",
                            severity=ValidationSeverity.WARNING,
                            details={'net': net.GetNetname()}
                        ))

                    # Check for ground vias
                    has_ground_vias = False
                    for via in board.GetVias():
                        if via.GetNetname() == net.GetNetname():
                            has_ground_vias = True
                            break
                    if not has_ground_vias:
                        results.append(self._create_result(
                            category=ValidationCategory.GROUND,
                            message=f"Ground net {net.GetNetname()} has no ground vias",
                            severity=ValidationSeverity.WARNING,
                            details={'net': net.GetNetname()}
                        ))

        except Exception as e:
            self.logger.error(f"Error validating ground rules: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.GROUND,
                message=f"Error validating ground rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="signal")
    def _validate_signal(self) -> List[ValidationResult]:
        """Validate signal integrity using KiCad's native functionality.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Get validation rules
            validation_rules = self.settings.get_validation_rules()
            signal_rules = validation_rules.get('signal', {})
            
            # Get impedance matching parameters
            target_impedance = signal_rules.get('target_impedance', 50.0)
            impedance_tolerance = signal_rules.get('impedance_tolerance', 10.0)
            max_crosstalk = signal_rules.get('max_crosstalk', 0.1)
            max_reflection = signal_rules.get('max_reflection', 0.1)
            min_impedance = signal_rules.get('min_impedance', 45.0)
            max_impedance = signal_rules.get('max_impedance', 55.0)

            # Check each track
            for track in board.GetTracks():
                if not track.IsTrack():
                    continue

                net = track.GetNetname()
                if not net:
                    continue

                # Skip power and ground nets
                if any(keyword in net.upper() for keyword in ["VCC", "VDD", "POWER", "GND", "GROUND"]):
                    continue

                # Get track properties
                width = track.GetWidth() / 1e6  # Convert to mm
                layer = board.GetLayerName(track.GetLayer())
                start_pos = (track.GetStart().x/1e6, track.GetStart().y/1e6)

                # Check for high-speed signals
                is_high_speed = any(keyword in net.upper() for keyword in [
                    "CLK", "DDR", "USB", "HDMI", "PCI", "SATA", "ETH", "MIPI"
                ])

                # Check for audio signals
                is_audio = any(keyword in net.upper() for keyword in [
                    "AUDIO", "LINE", "MIC", "SPKR", "AMP", "DAC", "ADC"
                ])

                # Check track width
                min_width = 0.2 if is_high_speed else 0.1
                if width < min_width:
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"Signal track width {width:.2f}mm is below minimum {min_width}mm",
                        severity=ValidationSeverity.ERROR,
                        location=start_pos,
                        details={
                            'net': net,
                            'width': width,
                            'min_width': min_width,
                            'type': 'high_speed' if is_high_speed else 'audio' if is_audio else 'signal'
                        }
                    ))

                # Calculate and check impedance
                impedance = self._calculate_track_impedance(track, board)
                if impedance:
                    if impedance < min_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Signal impedance {impedance:.1f}Ω is below minimum {min_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            location=start_pos,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'min_impedance': min_impedance
                            }
                        ))
                    elif impedance > max_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Signal impedance {impedance:.1f}Ω exceeds maximum {max_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            location=start_pos,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'max_impedance': max_impedance
                            }
                        ))

                # Check for ground plane reference
                has_ground_reference = False
                for zone in board.Zones():
                    if zone.GetNetname() == "GND" and zone.IsOnLayer(track.GetLayer() - 1):
                        has_ground_reference = True
                        break

                if not has_ground_reference:
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"Signal {net} lacks ground plane reference",
                        severity=ValidationSeverity.WARNING,
                        location=start_pos,
                        details={'net': net}
                    ))

                # Check for parallel tracks
                parallel_tracks = self._find_parallel_tracks(track, board)
                if len(parallel_tracks) > 2:  # Maximum 2 parallel tracks
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"Too many parallel signal tracks ({len(parallel_tracks)})",
                        severity=ValidationSeverity.WARNING,
                        location=start_pos,
                        details={
                            'net': net,
                            'parallel_count': len(parallel_tracks),
                            'max_parallel': 2
                        }
                    ))

                # Check for crosstalk
                crosstalk = self._calculate_crosstalk(track, parallel_tracks)
                if crosstalk > max_crosstalk:
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"High crosstalk detected ({crosstalk:.1%})",
                        severity=ValidationSeverity.WARNING,
                        location=start_pos,
                        details={
                            'net': net,
                            'crosstalk': crosstalk,
                            'max_crosstalk': max_crosstalk
                        }
                    ))

                # Check for reflections
                reflection = self._calculate_reflection(track, board)
                if reflection > max_reflection:
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"High reflection detected ({reflection:.1%})",
                        severity=ValidationSeverity.WARNING,
                        location=start_pos,
                        details={
                            'net': net,
                            'reflection': reflection,
                            'max_reflection': max_reflection
                        }
                    ))

                # Check for proper termination
                if is_high_speed and not self._has_termination(track, board):
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"High-speed signal {net} may need termination",
                        severity=ValidationSeverity.WARNING,
                        location=start_pos,
                        details={'net': net}
                    ))

        except Exception as e:
            self.logger.error(f"Error validating signal integrity: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.SIGNAL,
                message=f"Error validating signal integrity: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    def _calculate_track_impedance(self, track: pcbnew.TRACK, board: pcbnew.BOARD) -> Optional[float]:
        """Calculate track impedance.
        
        Args:
            track: Track to calculate impedance for
            board: Board object
            
        Returns:
            Impedance in ohms if calculable, None otherwise
        """
        try:
            # Get track properties
            width = track.GetWidth() / 1e6  # Convert to mm
            thickness = 0.035  # Typical copper thickness in mm
            h = 0.1  # Typical height to ground plane in mm
            er = 4.5  # Typical FR4 dielectric constant
            
            # Calculate characteristic impedance using microstrip formula
            # Z0 = (87 / sqrt(er + 1.41)) * ln(5.98 * h / (0.8 * w + t))
            # where:
            # w = track width
            # t = track thickness
            # h = height to ground plane
            # er = dielectric constant
            
            impedance = (87 / math.sqrt(er + 1.41)) * math.log(5.98 * h / (0.8 * width + thickness))
            return impedance
            
        except (AttributeError, TypeError) as e:
            self.logger.debug(f"Error accessing track properties for impedance calculation: {str(e)}")
            return None
        except (ValueError, ZeroDivisionError) as e:
            self.logger.debug(f"Error in impedance calculation: {str(e)}")
            return None
        except Exception as e:
            self.logger.debug(f"Unexpected error in impedance calculation: {str(e)}")
            return None

    def _find_parallel_tracks(self, track: pcbnew.TRACK, board: pcbnew.BOARD) -> List[pcbnew.TRACK]:
        """Find parallel tracks.
        
        Args:
            track: Track to find parallels for
            board: Board object
            
        Returns:
            List of parallel tracks
        """
        parallel_tracks = []
        try:
            # Get track properties
            start = track.GetStart()
            end = track.GetEnd()
            layer = track.GetLayer()
            
            # Calculate track angle
            dx = end.x - start.x
            dy = end.y - start.y
            angle = math.atan2(dy, dx)
            
            # Find parallel tracks
            for other in board.GetTracks():
                if other != track and other.IsTrack() and other.GetLayer() == layer:
                    other_start = other.GetStart()
                    other_end = other.GetEnd()
                    
                    # Calculate other track angle
                    other_dx = other_end.x - other_start.x
                    other_dy = other_end.y - other_start.y
                    other_angle = math.atan2(other_dy, other_dx)
                    
                    # Check if tracks are parallel (within 10 degrees)
                    angle_diff = abs(angle - other_angle)
                    if angle_diff < math.radians(10) or angle_diff > math.radians(170):
                        parallel_tracks.append(other)
            
            return parallel_tracks
            
        except (AttributeError, TypeError) as e:
            self.logger.debug(f"Error accessing track properties for parallel track detection: {str(e)}")
            return []
        except Exception as e:
            self.logger.debug(f"Unexpected error in parallel track detection: {str(e)}")
            return []

    def _calculate_crosstalk(self, track: pcbnew.TRACK, parallel_tracks: List[pcbnew.TRACK]) -> float:
        """Calculate crosstalk between tracks.
        
        Args:
            track: Track to calculate crosstalk for
            parallel_tracks: List of parallel tracks
            
        Returns:
            Crosstalk ratio (0-1)
        """
        try:
            if not parallel_tracks:
                return 0.0
            
            # Calculate total crosstalk
            total_crosstalk = 0.0
            for other in parallel_tracks:
                # Calculate distance between tracks
                distance = track.GetStart().Distance(other.GetStart()) / 1e6  # Convert to mm
                
                # Calculate crosstalk using simplified formula
                # XT = k * (w/h) * (1 / (1 + (d/h)^2))
                # where:
                # k = coupling coefficient (typically 0.1)
                # w = track width
                # h = height to ground plane
                # d = distance between tracks
                
                k = 0.1  # Coupling coefficient
                w = track.GetWidth() / 1e6  # Convert to mm
                h = 0.1  # Typical height to ground plane in mm
                
                crosstalk = k * (w/h) * (1 / (1 + (distance/h)**2))
                total_crosstalk += crosstalk
            
            return min(total_crosstalk, 1.0)  # Cap at 100%
            
        except (AttributeError, TypeError) as e:
            self.logger.debug(f"Error accessing track properties for crosstalk calculation: {str(e)}")
            return 0.0
        except (ValueError, ZeroDivisionError) as e:
            self.logger.debug(f"Error in crosstalk calculation: {str(e)}")
            return 0.0
        except Exception as e:
            self.logger.debug(f"Unexpected error in crosstalk calculation: {str(e)}")
            return 0.0

    def _calculate_reflection(self, track: pcbnew.TRACK, board: pcbnew.BOARD) -> float:
        """Calculate signal reflection.
        
        Args:
            track: Track to calculate reflection for
            board: Board object
            
        Returns:
            Reflection ratio (0-1)
        """
        try:
            # Get track impedance
            impedance = self._calculate_track_impedance(track, board)
            if not impedance:
                return 0.0
            
            # Calculate reflection coefficient
            # Γ = |(Z2 - Z1) / (Z2 + Z1)|
            # where:
            # Z1 = source impedance (typically 50 ohms)
            # Z2 = load impedance (track impedance)
            
            Z1 = 50.0  # Source impedance
            Z2 = impedance  # Load impedance
            
            reflection = abs((Z2 - Z1) / (Z2 + Z1))
            return min(reflection, 1.0)  # Cap at 100%
            
        except (AttributeError, TypeError) as e:
            self.logger.debug(f"Error accessing track properties for reflection calculation: {str(e)}")
            return 0.0
        except (ValueError, ZeroDivisionError) as e:
            self.logger.debug(f"Error in reflection calculation: {str(e)}")
            return 0.0
        except Exception as e:
            self.logger.debug(f"Unexpected error in reflection calculation: {str(e)}")
            return 0.0

    def _has_termination(self, track: pcbnew.TRACK, board: pcbnew.BOARD) -> bool:
        """Check if track has proper termination.
        
        Args:
            track: Track to check
            board: Board object
            
        Returns:
            True if track has termination, False otherwise
        """
        try:
            net = track.GetNetname()
            if not net:
                return False
            
            # Check for termination components
            for footprint in board.GetFootprints():
                if footprint.GetNetname() == net:
                    # Check for termination resistors
                    if any(keyword in footprint.GetValue().upper() for keyword in ["TERM", "RES"]):
                        return True
            
            return False
            
        except Exception:
            return False

    @handle_validation_error(logger=Logger(__name__), category="thermal")
    def _validate_thermal(self) -> List[ValidationResult]:
        """Validate thermal rules.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Check high-power components
            power_components = ["REG", "MOSFET", "TRANSISTOR", "IC", "POWER"]
            for footprint in board.GetFootprints():
                if any(comp in footprint.GetReference() for comp in power_components):
                    # Check for thermal relief
                    has_thermal_relief = False
                    for pad in footprint.GetPads():
                        if pad.GetNetname() in ["GND", "VCC", "VDD"]:
                            for zone in board.Zones():
                                if zone.GetNetname() == pad.GetNetname():
                                    if zone.GetThermalReliefGap() > 0:
                                        has_thermal_relief = True
                                        break
                    if not has_thermal_relief:
                        results.append(self._create_result(
                            category=ValidationCategory.THERMAL,
                            message=f"High-power component {footprint.GetReference()} has no thermal relief",
                            severity=ValidationSeverity.WARNING,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

                    # Check for thermal vias
                    has_thermal_vias = False
                    for via in board.GetVias():
                        if via.GetNetname() in ["GND", "VCC", "VDD"]:
                            if via.GetPosition().Distance(footprint.GetPosition()) < 2e6:  # 2mm radius
                                has_thermal_vias = True
                                break
                    if not has_thermal_vias:
                        results.append(self._create_result(
                            category=ValidationCategory.THERMAL,
                            message=f"High-power component {footprint.GetReference()} has no thermal vias",
                            severity=ValidationSeverity.WARNING,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

            # Check for thermal zones
            for zone in board.Zones():
                if zone.GetNetname() in ["GND", "VCC", "VDD"]:
                    # Check thermal relief settings
                    if zone.GetThermalReliefGap() == 0:
                        results.append(self._create_result(
                            category=ValidationCategory.THERMAL,
                            message=f"Zone {zone.GetNetname()} has no thermal relief gap",
                            severity=ValidationSeverity.WARNING,
                            location=(zone.GetPosition().x/1e6, zone.GetPosition().y/1e6),
                            details={'zone': zone.GetNetname()}
                        ))

                    # Check thermal relief spoke width
                    if zone.GetThermalReliefSpokeWidth() < 0.2e6:  # 0.2mm minimum
                        results.append(self._create_result(
                            category=ValidationCategory.THERMAL,
                            message=f"Zone {zone.GetNetname()} has thin thermal relief spokes",
                            severity=ValidationSeverity.WARNING,
                            location=(zone.GetPosition().x/1e6, zone.GetPosition().y/1e6),
                            details={
                                'zone': zone.GetNetname(),
                                'spoke_width': zone.GetThermalReliefSpokeWidth()/1e6,
                                'min_width': 0.2
                            }
                        ))

            # Check for heat sinks
            for footprint in board.GetFootprints():
                if "HS" in footprint.GetReference():
                    # Check for thermal vias under heat sink
                    has_thermal_vias = False
                    for via in board.GetVias():
                        if via.GetNetname() == "GND":
                            if via.GetPosition().Distance(footprint.GetPosition()) < 5e6:  # 5mm radius
                                has_thermal_vias = True
                                break
                    if not has_thermal_vias:
                        results.append(self._create_result(
                            category=ValidationCategory.THERMAL,
                            message=f"Heat sink {footprint.GetReference()} has no thermal vias",
                            severity=ValidationSeverity.WARNING,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

                    # Check for thermal paste layer
                    has_thermal_paste = False
                    for pad in footprint.GetPads():
                        if pad.GetLayer() == pcbnew.F_Paste:
                            has_thermal_paste = True
                            break
                    if not has_thermal_paste:
                        results.append(self._create_result(
                            category=ValidationCategory.THERMAL,
                            message=f"Heat sink {footprint.GetReference()} has no thermal paste layer",
                            severity=ValidationSeverity.WARNING,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

        except Exception as e:
            self.logger.error(f"Error validating thermal rules: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.THERMAL,
                message=f"Error validating thermal rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="emi_emc")
    def _validate_emi_emc(self) -> List[ValidationResult]:
        """Validate EMI/EMC rules.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Check for high-speed signals
            high_speed_nets = ["USB", "HDMI", "PCIe", "LVDS", "DDR"]
            for net in board.GetNetsByName().values():
                if any(signal in net.GetNetname() for signal in high_speed_nets):
                    # Check for ground plane under high-speed signals
                    has_ground_plane = False
                    for track in net.GetTracks():
                        if not track.IsTrack():
                            continue
                        for zone in board.Zones():
                            if zone.GetNetname() == "GND" and zone.HitTest(track.GetStart()):
                                has_ground_plane = True
                                break
                        if not has_ground_plane:
                            results.append(self._create_result(
                                category=ValidationCategory.EMI_EMC,
                                message=f"High-speed signal {net.GetNetname()} has no ground plane underneath",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={'net': net.GetNetname()}
                            ))

                    # Check for return path
                    has_return_path = False
                    for track in net.GetTracks():
                        if not track.IsTrack():
                            continue
                        for other in board.GetTracks():
                            if not other.IsTrack() or other == track:
                                continue
                            if other.GetNetname() == "GND":
                                if track.GetStart().Distance(other.GetStart()) < 0.2e6:  # 0.2mm
                                    has_return_path = True
                                    break
                        if not has_return_path:
                            results.append(self._create_result(
                                category=ValidationCategory.EMI_EMC,
                                message=f"High-speed signal {net.GetNetname()} has no return path",
                                severity=ValidationSeverity.WARNING,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={'net': net.GetNetname()}
                            ))

            # Check for shielding
            for footprint in board.GetFootprints():
                if "SHIELD" in footprint.GetReference():
                    # Check for ground connection
                    has_ground = False
                    for pad in footprint.GetPads():
                        if pad.GetNetname() == "GND":
                            has_ground = True
                            break
                    if not has_ground:
                        results.append(self._create_result(
                            category=ValidationCategory.EMI_EMC,
                            message=f"Shield {footprint.GetReference()} has no ground connection",
                            severity=ValidationSeverity.ERROR,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

                    # Check for vias around shield
                    has_shield_vias = False
                    for via in board.GetVias():
                        if via.GetNetname() == "GND":
                            if via.GetPosition().Distance(footprint.GetPosition()) < 2e6:  # 2mm radius
                                has_shield_vias = True
                                break
                    if not has_shield_vias:
                        results.append(self._create_result(
                            category=ValidationCategory.EMI_EMC,
                            message=f"Shield {footprint.GetReference()} has no ground vias",
                            severity=ValidationSeverity.WARNING,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

            # Check for ferrite beads
            for footprint in board.GetFootprints():
                if "FB" in footprint.GetReference():
                    # Check for proper placement
                    has_proper_placement = False
                    for pad in footprint.GetPads():
                        if pad.GetNetname() in ["VCC", "VDD"]:
                            has_proper_placement = True
                            break
                    if not has_proper_placement:
                        results.append(self._create_result(
                            category=ValidationCategory.EMI_EMC,
                            message=f"Ferrite bead {footprint.GetReference()} is not properly placed",
                            severity=ValidationSeverity.WARNING,
                            location=(footprint.GetPosition().x/1e6, footprint.GetPosition().y/1e6),
                            details={'component': footprint.GetReference()}
                        ))

        except Exception as e:
            self.logger.error(f"Error validating EMI/EMC rules: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.EMI_EMC,
                message=f"Error validating EMI/EMC rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="components")
    def _validate_components(self) -> List[ValidationResult]:
        """Validate component placement and properties using KiCad's native functionality.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Get component positions
            positions = self._get_component_positions(board)
            
            # Check each component
            for footprint in board.GetFootprints():
                # Get component properties
                ref = footprint.GetReference()
                value = footprint.GetValue()
                layer = board.GetLayerName(footprint.GetLayer())
                
                # Basic validation
                if not value:
                    results.append(self._create_result(
                        category=ValidationCategory.COMPONENTS,
                        message=f"Component {ref} has no value",
                        severity=ValidationSeverity.WARNING,
                        location=positions.get(ref)
                    ))
                
                # Layer validation
                if layer not in ["F.Cu", "B.Cu"]:
                    results.append(self._create_result(
                        category=ValidationCategory.COMPONENTS,
                        message=f"Component {ref} is not on a copper layer",
                        severity=ValidationSeverity.ERROR,
                        location=positions.get(ref)
                    ))
                
                # Reference format validation
                import re
                if not re.match(r"^[A-Z][0-9]+$", ref):
                    results.append(self._create_result(
                        category=ValidationCategory.COMPONENTS,
                        message=f"Invalid component reference format: {ref}",
                        severity=ValidationSeverity.ERROR,
                        location=positions.get(ref)
                    ))
                
                # Audio component validation
                if any(keyword in ref.upper() for keyword in ["AUDIO", "AMP", "DAC"]):
                    # Check required audio properties
                    required_properties = ["impedance", "gain"]
                    for prop in required_properties:
                        if not footprint.HasProperty(prop):
                            results.append(self._create_result(
                                category=ValidationCategory.AUDIO,
                                message=f"Audio component {ref} missing required property: {prop}",
                                severity=ValidationSeverity.ERROR,
                                location=positions.get(ref)
                            ))
                    
                    # Check impedance
                    impedance = self._get_impedance_from_value(value)
                    if impedance:
                        if impedance < 100 or impedance > 10000:
                            results.append(self._create_result(
                                category=ValidationCategory.AUDIO,
                                message=f"Audio component {ref} has invalid impedance: {impedance}",
                                severity=ValidationSeverity.WARNING,
                                location=positions.get(ref)
                            ))
                    
                    # Check gain
                    gain = self._get_gain_from_value(value)
                    if gain and gain > 40:
                        results.append(self._create_result(
                            category=ValidationCategory.AUDIO,
                            message=f"Audio component {ref} has high gain: {gain}",
                            severity=ValidationSeverity.WARNING,
                            location=positions.get(ref)
                        ))
                
                # Power component validation
                if any(keyword in ref.upper() for keyword in ["PWR", "POWER", "REG"]):
                    # Check voltage rating
                    voltage = self._get_voltage_from_value(value)
                    if voltage:
                        if voltage < 0 or voltage > 1000:
                            results.append(self._create_result(
                                category=ValidationCategory.SAFETY,
                                message=f"Power component {ref} has invalid voltage rating: {voltage}",
                                severity=ValidationSeverity.ERROR,
                                location=positions.get(ref)
                            ))
                    
                    # Check power rating
                    power = self._get_power_from_value(value)
                    if power:
                        if power < 0 or power > 100:
                            results.append(self._create_result(
                                category=ValidationCategory.SAFETY,
                                message=f"Power component {ref} has invalid power rating: {power}",
                                severity=ValidationSeverity.ERROR,
                                location=positions.get(ref)
                            ))
                
                # Manufacturing validation
                # Check placement clearance
                clearance = self._get_component_clearance(footprint)
                if clearance and clearance < 0.5:
                    results.append(self._create_result(
                        category=ValidationCategory.MANUFACTURING,
                        message=f"Component {ref} has insufficient clearance: {clearance}",
                        severity=ValidationSeverity.ERROR,
                        location=positions.get(ref)
                    ))
                
                # Check orientation
                orientation = footprint.GetOrientationDegrees()
                if orientation not in [0, 90, 180, 270]:
                    results.append(self._create_result(
                        category=ValidationCategory.MANUFACTURING,
                        message=f"Component {ref} has invalid orientation: {orientation}",
                        severity=ValidationSeverity.WARNING,
                        location=positions.get(ref)
                    ))
                
                # Check for overlapping components
                for other in board.GetFootprints():
                    if other != footprint and other.HitTest(footprint.GetPosition()):
                        results.append(self._create_result(
                            category=ValidationCategory.COMPONENTS,
                            message=f"Component {ref} overlaps with {other.GetReference()}",
                            severity=ValidationSeverity.ERROR,
                            location=positions.get(ref)
                        ))
                
                # Check for components outside board
                board_edges = board.GetBoardEdgesBoundingBox()
                if not board_edges.Contains(footprint.GetPosition()):
                    results.append(self._create_result(
                        category=ValidationCategory.COMPONENTS,
                        message=f"Component {ref} is outside board boundaries",
                        severity=ValidationSeverity.ERROR,
                        location=positions.get(ref)
                    ))

        except Exception as e:
            self.logger.error(f"Error validating components: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.COMPONENTS,
                message=f"Error validating components: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    def _get_impedance_from_value(self, value: str) -> Optional[float]:
        """Extract impedance value from component value string.
        
        Args:
            value: Component value string
            
        Returns:
            Impedance value in ohms if found, None otherwise
        """
        try:
            # Look for impedance values in ohms
            import re
            match = re.search(r'(\d+)\s*[oO][hH][mM]', value)
            if match:
                return float(match.group(1))
            return None
        except Exception:
            return None

    def _get_gain_from_value(self, value: str) -> Optional[float]:
        """Extract gain value from component value string.
        
        Args:
            value: Component value string
            
        Returns:
            Gain value if found, None otherwise
        """
        try:
            # Look for gain values in dB
            import re
            match = re.search(r'(\d+)\s*[dD][bB]', value)
            if match:
                return float(match.group(1))
            return None
        except Exception:
            return None

    def _get_voltage_from_value(self, value: str) -> Optional[float]:
        """Extract voltage value from component value string.
        
        Args:
            value: Component value string
            
        Returns:
            Voltage value in volts if found, None otherwise
        """
        try:
            # Look for voltage values in volts
            import re
            match = re.search(r'(\d+)\s*[vV]', value)
            if match:
                return float(match.group(1))
            return None
        except Exception:
            return None

    def _get_power_from_value(self, value: str) -> Optional[float]:
        """Extract power value from component value string.
        
        Args:
            value: Component value string
            
        Returns:
            Power value in watts if found, None otherwise
        """
        try:
            # Look for power values in watts
            import re
            match = re.search(r'(\d+)\s*[wW]', value)
            if match:
                return float(match.group(1))
            return None
        except Exception:
            return None

    def _get_component_clearance(self, footprint: pcbnew.FOOTPRINT) -> Optional[float]:
        """Calculate component clearance.
        
        Args:
            footprint: Component footprint
            
        Returns:
            Minimum clearance in mm if found, None otherwise
        """
        try:
            board = pcbnew.GetBoard()
            if not board:
                return None
            
            min_clearance = float('inf')
            for other in board.GetFootprints():
                if other != footprint:
                    distance = footprint.GetPosition().Distance(other.GetPosition()) / 1e6
                    min_clearance = min(min_clearance, distance)
            
            return min_clearance if min_clearance != float('inf') else None
        except Exception:
            return None

    def _create_result(self, category: ValidationCategory, message: str,
                      severity: ValidationSeverity,
                      location: Optional[Tuple[float, float]] = None,
                      details: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Create a validation result.
        
        Args:
            category: Validation category
            message: Validation message
            severity: Validation severity
            location: Optional location tuple (x, y)
            details: Optional details dictionary
            
        Returns:
            ValidationResult instance
        """
        return ValidationResult(
            category=category,
            message=message,
            severity=severity,
            location=location,
            details=details
        )

    def _create_audio_result(self, category: ValidationCategory, message: str,
                           severity: ValidationSeverity,
                           location: Optional[Tuple[float, float]] = None,
                           details: Optional[Dict[str, Any]] = None,
                           frequency: Optional[float] = None,
                           impedance: Optional[float] = None,
                           crosstalk: Optional[float] = None,
                           noise_level: Optional[float] = None,
                           power_quality: Optional[float] = None,
                           thermal_impact: Optional[float] = None) -> AudioValidationResult:
        """Create an audio validation result.
        
        Args:
            category: Validation category
            message: Validation message
            severity: Validation severity
            location: Optional location tuple (x, y)
            details: Optional details dictionary
            frequency: Optional frequency value
            impedance: Optional impedance value
            crosstalk: Optional crosstalk value
            noise_level: Optional noise level value
            power_quality: Optional power quality value
            thermal_impact: Optional thermal impact value
            
        Returns:
            AudioValidationResult instance
        """
        return AudioValidationResult(
            category=category,
            message=message,
            severity=severity,
            location=location,
            details=details,
            frequency=frequency,
            impedance=impedance,
            crosstalk=crosstalk,
            noise_level=noise_level,
            power_quality=power_quality,
            thermal_impact=thermal_impact
        )

    def _create_safety_result(self, category: ValidationCategory, message: str,
                            severity: ValidationSeverity,
                            location: Optional[Tuple[float, float]] = None,
                            details: Optional[Dict[str, Any]] = None,
                            voltage: Optional[float] = None,
                            current: Optional[float] = None,
                            power: Optional[float] = None,
                            temperature: Optional[float] = None,
                            clearance: Optional[float] = None,
                            creepage: Optional[float] = None) -> SafetyValidationResult:
        """Create a safety validation result.
        
        Args:
            category: Validation category
            message: Validation message
            severity: Validation severity
            location: Optional location tuple (x, y)
            details: Optional details dictionary
            voltage: Optional voltage value
            current: Optional current value
            power: Optional power value
            temperature: Optional temperature value
            clearance: Optional clearance value
            creepage: Optional creepage value
            
        Returns:
            SafetyValidationResult instance
        """
        return SafetyValidationResult(
            category=category,
            message=message,
            severity=severity,
            location=location,
            details=details,
            voltage=voltage,
            current=current,
            power=power,
            temperature=temperature,
            clearance=clearance,
            creepage=creepage
        )

    def _create_manufacturing_result(self, category: ValidationCategory, message: str,
                                  severity: ValidationSeverity,
                                  location: Optional[Tuple[float, float]] = None,
                                  details: Optional[Dict[str, Any]] = None,
                                  min_feature_size: Optional[float] = None,
                                  max_feature_size: Optional[float] = None,
                                  recommended_size: Optional[float] = None,
                                  manufacturing_cost: Optional[float] = None,
                                  yield_impact: Optional[float] = None) -> ManufacturingValidationResult:
        """Create a manufacturing validation result.
        
        Args:
            category: Validation category
            message: Validation message
            severity: Validation severity
            location: Optional location tuple (x, y)
            details: Optional details dictionary
            min_feature_size: Optional minimum feature size
            max_feature_size: Optional maximum feature size
            recommended_size: Optional recommended size
            manufacturing_cost: Optional manufacturing cost
            yield_impact: Optional yield impact
            
        Returns:
            ManufacturingValidationResult instance
        """
        return ManufacturingValidationResult(
            category=category,
            message=message,
            severity=severity,
            location=location,
            details=details,
            min_feature_size=min_feature_size,
            max_feature_size=max_feature_size,
            recommended_size=recommended_size,
            manufacturing_cost=manufacturing_cost,
            yield_impact=yield_impact
        ) 