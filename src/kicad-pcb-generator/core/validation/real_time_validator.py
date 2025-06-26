"""Real-time PCB validation using KiCad 9's native functionality."""
import logging
import pcbnew
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass
from enum import Enum
import threading
import time
import math
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..utils.config.settings import Settings
from ..utils.logging.logger import Logger
from ..core.validation.cache_manager import CacheManager
from ..core.validation.base_validator import BaseValidator, ValidationResult, ValidationSeverity, ValidationCategory
from ..core.validation.validation_results import (
    SafetyValidationResult,
    ManufacturingValidationResult
)
from ..core.validation.validation_result_factory import ValidationResultFactory
from ..core.utils.pcb_utils import PCBUtils
from ..core.validation.validation_rule import ValidationRule, RuleType
from ..utils.error_handling import (
    handle_validation_error,
    handle_operation_error,
    log_validation_error,
    ValidationError,
    ComponentError,
    ConnectionError,
    PowerError,
    GroundError,
    SignalError,
    ManufacturingError
)
from ...core.validation.common_validator import CommonValidatorMixin
from ...audio.validation.audio_validator import AudioValidator, AudioValidationResult

class ValidationType(Enum):
    """Types of real-time validation."""
    DESIGN_RULES = "design_rules"
    COMPONENT_PLACEMENT = "component_placement"
    ROUTING = "routing"
    MANUFACTURING = "manufacturing"
    POWER = "power"
    GROUND = "ground"
    SIGNAL = "signal"

class RealTimeValidator(BaseValidator, CommonValidatorMixin):
    """Real-time validator for PCB design."""
    
    def __init__(self):
        super().__init__()
        self._validation_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._validation_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._last_board_state: Optional[Dict[str, Any]] = None
        self._validation_interval = 1.0  # seconds
        self._audio_validator = AudioValidator()
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register default validation rules."""
        self.register_rule(
            "check_design_rules",
            self._check_design_rules,
            metadata={"category": "drc", "priority": "high"}
        )
        self.register_rule(
            "check_audio_rules",
            self._check_audio_rules,
            metadata={"category": "audio", "priority": "high"}
        )
        self.register_rule(
            "check_manufacturing",
            self._check_manufacturing,
            metadata={"category": "manufacturing", "priority": "medium"}
        )
        self.register_rule(
            "check_cost",
            self._check_cost,
            metadata={"category": "cost", "priority": "low"}
        )

    def start_validation(self, board: Any) -> None:
        """Start real-time validation."""
        if self._validation_thread is not None and self._validation_thread.is_alive():
            return

        self._stop_event.clear()
        self._validation_thread = threading.Thread(
            target=self._validation_loop,
            args=(board,),
            daemon=True
        )
        self._validation_thread.start()

    def stop_validation(self) -> None:
        """Stop real-time validation."""
        self._stop_event.set()
        if self._validation_thread is not None:
            self._validation_thread.join()
            self._validation_thread = None

    def _validation_loop(self, board: Any) -> None:
        """Main validation loop."""
        last_validation_time = 0
        min_validation_interval = 0.5  # Minimum time between validations
        
        while not self._stop_event.is_set():
            current_time = time.time()
            
            # Only check for changes if enough time has passed
            if current_time - last_validation_time >= min_validation_interval:
                with self._validation_lock:
                    current_state = self._get_board_state(board)
                    if self._has_board_changed(current_state):
                        self._last_board_state = current_state
                        self.validate(board)
                        last_validation_time = current_time
            
            # Sleep for a shorter interval to be more responsive
            time.sleep(min(self._validation_interval, 0.1))

    def _get_board_state(self, board: pcbnew.BOARD) -> Dict[str, Any]:
        """Get the current state of the board.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary containing board state information
        """
        try:
            # Get component positions (cached)
            component_positions = self._get_component_positions(board)
            
            # Get board dimensions (cached)
            board_box = self._get_board_box(board)
            
            # Get track information with optimized collection
            tracks = []
            board_tracks = board.GetTracks()
            for track in board_tracks:
                if track.IsTrack():
                    # Cache track properties to avoid repeated API calls
                    net_name = track.GetNetname()
                    layer_name = board.GetLayerName(track.GetLayer())
                    width = track.GetWidth()
                    start_pos = track.GetStart()
                    end_pos = track.GetEnd()
                    
                    tracks.append({
                        'net': net_name,
                        'layer': layer_name,
                        'width': width,
                        'start': (start_pos.x, start_pos.y),
                        'end': (end_pos.x, end_pos.y)
                    })
            
            # Get via information with optimized collection
            vias = []
            board_vias = board.GetVias()
            for via in board_vias:
                # Cache via properties
                net_name = via.GetNetname()
                position = via.GetPosition()
                width = via.GetWidth()
                drill = via.GetDrill()
                
                vias.append({
                    'net': net_name,
                    'position': (position.x, position.y),
                    'width': width,
                    'drill': drill
                })
            
            # Get zone information with optimized collection
            zones = []
            board_zones = board.Zones()
            for zone in board_zones:
                # Cache zone properties
                net_name = zone.GetNetname()
                layer_name = board.GetLayerName(zone.GetLayer())
                area = zone.GetArea()
                
                zones.append({
                    'net': net_name,
                    'layer': layer_name,
                    'area': area
                })
            
            # Get design rules (cached)
            settings = board.GetDesignSettings()
            design_rules = {
                'min_track_width': settings.GetTrackWidth(),
                'min_clearance': settings.GetMinClearance(),
                'via_diameter': settings.GetViasDimensions(),
                'via_drill': settings.GetViasDrill()
            }
            
            # Get layer information
            layers = []
            for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT):
                if board.IsLayerEnabled(layer_id):
                    layers.append({
                        'id': layer_id,
                        'name': board.GetLayerName(layer_id),
                        'enabled': True
                    })
            
            return {
                'components': component_positions,
                'dimensions': board_box,
                'tracks': tracks,
                'vias': vias,
                'zones': zones,
                'design_rules': design_rules,
                'layers': layers,
                'timestamp': time.time()
            }
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error getting board state: {str(e)}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error getting board state: {str(e)}")
            return {}

    def _has_board_changed(self, current_state: Dict[str, Any]) -> bool:
        """Check if the board state has changed.
        
        Args:
            current_state: Current board state dictionary
            
        Returns:
            True if board has changed, False otherwise
        """
        if self._last_board_state is None:
            return True
            
        try:
            # Quick timestamp check first
            if abs(current_state.get('timestamp', 0) - self._last_board_state.get('timestamp', 0)) < 0.1:
                return False
            
            # Check component count and positions (most likely to change)
            current_components = current_state.get('components', {})
            last_components = self._last_board_state.get('components', {})
            
            if len(current_components) != len(last_components):
                return True
            
            # Check if any component positions changed (using hash for efficiency)
            current_comp_hash = hash(frozenset(current_components.items()))
            last_comp_hash = hash(frozenset(last_components.items()))
            if current_comp_hash != last_comp_hash:
                return True
            
            # Check track count and basic properties
            current_tracks = current_state.get('tracks', [])
            last_tracks = self._last_board_state.get('tracks', [])
            
            if len(current_tracks) != len(last_tracks):
                return True
            
            # Quick track change detection using hash of track properties
            current_track_hash = hash(tuple(sorted(
                (t['net'], t['layer'], t['width']) for t in current_tracks
            )))
            last_track_hash = hash(tuple(sorted(
                (t['net'], t['layer'], t['width']) for t in last_tracks
            )))
            if current_track_hash != last_track_hash:
                return True
            
            # Check via count
            current_vias = current_state.get('vias', [])
            last_vias = self._last_board_state.get('vias', [])
            if len(current_vias) != len(last_vias):
                return True
            
            # Check zone count
            current_zones = current_state.get('zones', [])
            last_zones = self._last_board_state.get('zones', [])
            if len(current_zones) != len(last_zones):
                return True
            
            # Check dimensions (rarely change)
            if current_state.get('dimensions') != self._last_board_state.get('dimensions'):
                return True
            
            # Check design rules (rarely change)
            if current_state.get('design_rules') != self._last_board_state.get('design_rules'):
                return True
            
            # Check layer configuration (rarely change)
            if current_state.get('layers') != self._last_board_state.get('layers'):
                return True
            
            return False
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error checking board changes: {str(e)}")
            return True  # Return True on error to ensure validation runs
        except Exception as e:
            self.logger.error(f"Unexpected error checking board changes: {str(e)}")
            return True  # Return True on error to ensure validation runs

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
                positions[ref] = (pos.x / 1e6, pos.y / 1e6)  # Convert to mm
        return positions

    @lru_cache(maxsize=32)
    def _get_board_box(self, board: pcbnew.BOARD) -> Tuple[float, float]:
        """Get board dimensions.
        
        Args:
            board: KiCad board object
            
        Returns:
            Tuple of (width, height) in mm
        """
        box = board.GetBoardEdgesBoundingBox()
        width = (box.GetWidth() / 1e6)  # Convert to mm
        height = (box.GetHeight() / 1e6)  # Convert to mm
        return (width, height)

    def validate(self, board: Any) -> ValidationResult:
        """Validate the PCB board."""
        result = ValidationResult()
        
        # Run all registered rules in parallel
        futures = []
        for rule_name in self._validation_order:
            if not self.is_check_enabled(rule_name):
                continue
            rule_func = self._validation_rules[rule_name]
            futures.append(self._executor.submit(rule_func, board))

        # Collect results
        for future in futures:
            try:
                rule_result = future.result()
                if isinstance(rule_result, ValidationResult):
                    for issue in rule_result.issues:
                        result.add_issue(
                            message=issue.message,
                            severity=issue.severity,
                            category=issue.category,
                            location=issue.location,
                            details=issue.details,
                            suggestion=issue.suggestion,
                            documentation_ref=issue.documentation_ref
                        )
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                result.add_issue(
                    message=f"Input error in validation rule: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.DESIGN_RULES,
                    details={"error": str(e)}
                )
            except Exception as e:
                result.add_issue(
                    message=f"Unexpected error in validation rule: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.DESIGN_RULES,
                    details={"error": str(e)}
                )

        return result

    def _check_design_rules(self, board: Any) -> ValidationResult:
        """Check design rules."""
        try:
            # Get DRC configuration
            drc_config = self.config.get_drc_config() if hasattr(self, 'config') else None
            
            # Default DRC rules if no config available
            min_track_width = 0.1  # mm
            min_clearance = 0.1    # mm
            min_via_size = 0.2     # mm
            min_via_drill = 0.1    # mm
            min_hole_size = 0.3    # mm
            
            if drc_config:
                min_track_width = drc_config.get('min_track_width', min_track_width)
                min_clearance = drc_config.get('min_clearance', min_clearance)
                min_via_size = drc_config.get('min_via_size', min_via_size)
                min_via_drill = drc_config.get('min_via_drill', min_via_drill)
                min_hole_size = drc_config.get('min_hole_size', min_hole_size)
            
            # Check track widths
            thin_tracks = []
            for track in board.GetTracks():
                if track.IsTrack():
                    track_width = track.GetWidth() / 1e6  # Convert to mm
                    if track_width < min_track_width:
                        thin_tracks.append({
                            'width': track_width,
                            'position': (track.GetStart().x / 1e6, track.GetStart().y / 1e6)
                        })
            
            if thin_tracks:
                return self._result_factory.create_result(
                    category=ValidationCategory.DESIGN_RULES,
                    message=f"Found {len(thin_tracks)} tracks below minimum width {min_track_width}mm",
                    severity=ValidationSeverity.ERROR,
                    details={
                        'thin_tracks': thin_tracks,
                        'min_track_width': min_track_width
                    }
                )
            
            # Check via sizes
            small_vias = []
            for via in board.GetVias():
                via_width = via.GetWidth() / 1e6  # Convert to mm
                via_drill = via.GetDrill() / 1e6  # Convert to mm
                
                if via_width < min_via_size or via_drill < min_via_drill:
                    small_vias.append({
                        'width': via_width,
                        'drill': via_drill,
                        'position': (via.GetPosition().x / 1e6, via.GetPosition().y / 1e6)
                    })
            
            if small_vias:
                return self._result_factory.create_result(
                    category=ValidationCategory.DESIGN_RULES,
                    message=f"Found {len(small_vias)} vias below minimum size requirements",
                    severity=ValidationSeverity.ERROR,
                    details={
                        'small_vias': small_vias,
                        'min_via_size': min_via_size,
                        'min_via_drill': min_via_drill
                    }
                )
            
            # Check clearances
            clearance_violations = []
            for track1 in board.GetTracks():
                if not track1.IsTrack():
                    continue
                    
                for track2 in board.GetTracks():
                    if track1 == track2 or not track2.IsTrack():
                        continue
                    
                    # Skip if same net
                    if track1.GetNetname() == track2.GetNetname():
                        continue
                    
                    # Calculate clearance (simplified)
                    pos1 = track1.GetStart()
                    pos2 = track2.GetStart()
                    distance = math.sqrt(
                        ((pos1.x - pos2.x) / 1e6) ** 2 +
                        ((pos1.y - pos2.y) / 1e6) ** 2
                    )
                    
                    if distance < min_clearance:
                        clearance_violations.append({
                            'distance': distance,
                            'position': (pos1.x / 1e6, pos1.y / 1e6),
                            'net1': track1.GetNetname(),
                            'net2': track2.GetNetname()
                        })
            
            if clearance_violations:
                return self._result_factory.create_result(
                    category=ValidationCategory.DESIGN_RULES,
                    message=f"Found {len(clearance_violations)} clearance violations",
                    severity=ValidationSeverity.ERROR,
                    details={
                        'clearance_violations': clearance_violations,
                        'min_clearance': min_clearance
                    }
                )
            
            return self._result_factory.create_result(
                category=ValidationCategory.DESIGN_RULES,
                message="Design rules check passed",
                severity=ValidationSeverity.INFO
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in design rules check: {str(e)}")
            return self._result_factory.create_result(
                category=ValidationCategory.DESIGN_RULES,
                message=f"Input error in design rules check: {str(e)}",
                severity=ValidationSeverity.ERROR,
                details={"error": str(e)}
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in design rules check: {str(e)}")
            return self._result_factory.create_result(
                category=ValidationCategory.DESIGN_RULES,
                message=f"Unexpected error in design rules check: {str(e)}",
                severity=ValidationSeverity.ERROR,
                details={"error": str(e)}
            )

    def _check_audio_rules(self, board: Any) -> ValidationResult:
        """Check audio-specific rules."""
        return self._audio_validator.validate(board)

    def _check_manufacturing(self, board: Any) -> ValidationResult:
        """Check manufacturing requirements."""
        try:
            # Check component spacing
            spacing_violations = []
            for footprint1 in board.GetFootprints():
                for footprint2 in board.GetFootprints():
                    if footprint1 == footprint2:
                        continue
                    
                    pos1 = footprint1.GetPosition()
                    pos2 = footprint2.GetPosition()
                    distance = math.sqrt(
                        ((pos1.x - pos2.x) / 1e6) ** 2 +
                        ((pos1.y - pos2.y) / 1e6) ** 2
                    )
                    
                    min_spacing = 0.5  # 0.5mm minimum spacing
                    if distance < min_spacing:
                        spacing_violations.append({
                            'distance': distance,
                            'component1': footprint1.GetReference(),
                            'component2': footprint2.GetReference(),
                            'position': (pos1.x / 1e6, pos1.y / 1e6)
                        })
            
            if spacing_violations:
                return self._result_factory.create_result(
                    category=ValidationCategory.MANUFACTURING,
                    message=f"Found {len(spacing_violations)} component spacing violations",
                    severity=ValidationSeverity.WARNING,
                    details={
                        'spacing_violations': spacing_violations,
                        'min_spacing': min_spacing
                    }
                )
            
            # Check board edge clearance
            edge_violations = []
            board_box = board.GetBoardEdgesBoundingBox()
            board_width = board_box.GetWidth() / 1e6
            board_height = board_box.GetHeight() / 1e6
            
            for footprint in board.GetFootprints():
                pos = footprint.GetPosition()
                x = pos.x / 1e6
                y = pos.y / 1e6
                
                min_edge_clearance = 2.0  # 2mm minimum edge clearance
                if (x < min_edge_clearance or x > board_width - min_edge_clearance or
                    y < min_edge_clearance or y > board_height - min_edge_clearance):
                    edge_violations.append({
                        'component': footprint.GetReference(),
                        'position': (x, y),
                        'edge_clearance': min(x, y, board_width - x, board_height - y)
                    })
            
            if edge_violations:
                return self._result_factory.create_result(
                    category=ValidationCategory.MANUFACTURING,
                    message=f"Found {len(edge_violations)} edge clearance violations",
                    severity=ValidationSeverity.WARNING,
                    details={
                        'edge_violations': edge_violations,
                        'min_edge_clearance': min_edge_clearance
                    }
                )
            
            return self._result_factory.create_result(
                category=ValidationCategory.MANUFACTURING,
                message="Manufacturing check passed",
                severity=ValidationSeverity.INFO
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in manufacturing check: {str(e)}")
            return self._result_factory.create_result(
                category=ValidationCategory.MANUFACTURING,
                message=f"Input error in manufacturing check: {str(e)}",
                severity=ValidationSeverity.ERROR,
                details={"error": str(e)}
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in manufacturing check: {str(e)}")
            return self._result_factory.create_result(
                category=ValidationCategory.MANUFACTURING,
                message=f"Unexpected error in manufacturing check: {str(e)}",
                severity=ValidationSeverity.ERROR,
                details={"error": str(e)}
            )

    def _check_cost(self, board: Any) -> ValidationResult:
        """Check cost optimization opportunities."""
        try:
            # Calculate board area
            board_box = board.GetBoardEdgesBoundingBox()
            board_area = (board_box.GetWidth() * board_box.GetHeight()) / 1e12  # Convert to mm²
            
            # Check board size
            if board_area > 10000:  # More than 100cm²
                return self._result_factory.create_result(
                    category=ValidationCategory.COST,
                    message=f"Large board area ({board_area:.1f}mm²) may increase manufacturing cost",
                    severity=ValidationSeverity.INFO,
                    details={
                        'board_area': board_area,
                        'suggestion': 'Consider reducing board size or using panelization'
                    }
                )
            
            # Check layer count
            layer_count = len([layer for layer in range(pcbnew.PCB_LAYER_ID_COUNT) if board.IsLayerEnabled(layer)])
            if layer_count > 4:  # More than 4 layers
                return self._result_factory.create_result(
                    category=ValidationCategory.COST,
                    message=f"High layer count ({layer_count}) may increase manufacturing cost",
                    severity=ValidationSeverity.INFO,
                    details={
                        'layer_count': layer_count,
                        'suggestion': 'Consider reducing layer count if possible'
                    }
                )
            
            # Check hole count
            hole_count = len([pad for pad in board.GetPads() if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH])
            if hole_count > 1000:  # More than 1000 holes
                return self._result_factory.create_result(
                    category=ValidationCategory.COST,
                    message=f"High hole count ({hole_count}) may increase manufacturing cost",
                    severity=ValidationSeverity.INFO,
                    details={
                        'hole_count': hole_count,
                        'suggestion': 'Consider using SMD components where possible'
                    }
                )
            
            return self._result_factory.create_result(
                category=ValidationCategory.COST,
                message="Cost optimization check passed",
                severity=ValidationSeverity.INFO
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in cost check: {str(e)}")
            return self._result_factory.create_result(
                category=ValidationCategory.COST,
                message=f"Input error in cost check: {str(e)}",
                severity=ValidationSeverity.ERROR,
                details={"error": str(e)}
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in cost check: {str(e)}")
            return self._result_factory.create_result(
                category=ValidationCategory.COST,
                message=f"Unexpected error in cost check: {str(e)}",
                severity=ValidationSeverity.ERROR,
                details={"error": str(e)}
            )

    def get_audio_metrics(self) -> Dict[str, float]:
        """Get audio-specific metrics."""
        return self._audio_validator.get_audio_metrics()

    def get_signal_paths(self) -> List[Dict[str, Any]]:
        """Get signal path analysis results."""
        return self._audio_validator.get_signal_paths()

    def get_power_metrics(self) -> Dict[str, float]:
        """Get power-related metrics."""
        return self._audio_validator.get_power_metrics()

    def get_ground_metrics(self) -> Dict[str, float]:
        """Get ground-related metrics."""
        return self._audio_validator.get_ground_metrics()

    def set_validation_interval(self, interval: float) -> None:
        """Set the validation interval in seconds."""
        self._validation_interval = max(0.1, interval)

    def get_validation_interval(self) -> float:
        """Get the current validation interval in seconds."""
        return self._validation_interval

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_validation()
        self._executor.shutdown(wait=True)

    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility.
        
        Raises:
            RuntimeError: If KiCad version is incompatible
        """
        try:
            version = pcbnew.Version()
            if not version.startswith("9"):
                raise RuntimeError(f"Unsupported KiCad version: {version}. Version 9.x required.")
        except Exception as e:
            raise RuntimeError(f"Error checking KiCad version: {str(e)}")

    def _get_drc_engine(self, board: pcbnew.BOARD) -> pcbnew.DRC_ENGINE:
        """Get or create DRC engine with thread safety.
        
        Args:
            board: KiCad board object
            
        Returns:
            DRC engine instance
        """
        with self._drc_engine_lock:
            if self._drc_engine is None:
                self._drc_engine = pcbnew.DRC_ENGINE()
                self._drc_engine.SetBoard(board)
            return self._drc_engine
    
    def _get_cached_results(self) -> Optional[List[ValidationResult]]:
        """Get cached validation results if available and not expired.
        
        Returns:
            Cached results if available and not expired, None otherwise
        """
        current_time = time.time()
        
        # Check if cache is expired
        if current_time - self._last_cache_update > self._cache_ttl:
            return None
        
        # Get current board state
        board = pcbnew.GetBoard()
        if not board:
            return None
        
        # Calculate board state hash
        board_state = self._get_board_state(board)
        return self._cache_manager.get_cached(board_state)

    def _cache_results(self, results: List[ValidationResult]) -> None:
        """Cache validation results.
        
        Args:
            results: Validation results to cache
        """
        board = pcbnew.GetBoard()
        if not board:
            return
        
        # Get current board state
        board_state = self._get_board_state(board)
        
        # Cache results
        self._cache_manager.cache_results(board_state, results)
        self._last_cache_update = time.time()

    def validate(self) -> List[ValidationResult]:
        """Perform validation in parallel.
        
        Returns:
            List of validation results
        """
        try:
            board = pcbnew.GetBoard()
            if not board:
                return []
            
            # Get enabled validation types
            enabled_types = [
                validation_type.value
                for validation_type in ValidationType
                if self.is_rule_enabled(validation_type.value)
            ]
            
            # Create thread pool
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                # Submit validation tasks
                future_to_type = {
                    executor.submit(self._validation_tasks[validation_type]): validation_type
                    for validation_type in enabled_types
                }
                
                # Collect results
                results = []
                for future in as_completed(future_to_type):
                    validation_type = future_to_type[future]
                    try:
                        validation_results = future.result()
                        results.extend(validation_results)
                    except Exception as e:
                        self.logger.error(f"Error in {validation_type} validation: {str(e)}")
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory(validation_type),
                            message=f"Validation error: {str(e)}",
                            severity=ValidationSeverity.ERROR
                        ))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in validation: {str(e)}")
            return []

    @handle_validation_error(logger=Logger(__name__), category="design_rules")
    def _validate_design_rules(self) -> List[ValidationResult]:
        """Validate design rules with optimized DRC engine usage.
        
        Returns:
            List of validation results
        """
        try:
            board = pcbnew.GetBoard()
            if not board:
                return []
            
            # Get DRC engine with thread safety
            drc_engine = self._get_drc_engine(board)
            
            # Run DRC with optimized settings
            drc_engine.SetReportAllTrackErrors(True)
            drc_engine.SetReportAllPadErrors(True)
            drc_engine.SetReportAllViaErrors(True)
            drc_engine.SetReportAllZoneErrors(True)
            
            # Run DRC
            drc_engine.RunDRC()
            
            # Get DRC results
            results = []
            for item in drc_engine.GetReportItems():
                results.append(self._result_factory.create_result(
                    category=ValidationCategory.DESIGN_RULES,
                    message=item.GetErrorMessage(),
                    severity=ValidationSeverity.ERROR if item.IsError() else ValidationSeverity.WARNING,
                    location=(item.GetPosition().x / 1e6, item.GetPosition().y / 1e6),
                    details={"error_code": item.GetErrorCode()}
                ))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in design rules validation: {str(e)}")
            return []

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

            rule = self._rules[RuleType.COMPONENT_PLACEMENT]
            min_spacing = rule.get_parameter("min_spacing")
            edge_clearance = rule.get_parameter("edge_clearance")
            max_rotation = rule.get_parameter("max_rotation")

            # Get board outline
            board_rect = board.GetBoardEdgesBoundingBox()
            board_width = board_rect.GetWidth() / 1e6  # Convert to mm
            board_height = board_rect.GetHeight() / 1e6  # Convert to mm

            # Check component spacing and edge clearance
            for footprint in board.GetFootprints():
                pos = footprint.GetPosition()
                x = pos.x / 1e6  # Convert to mm
                y = pos.y / 1e6  # Convert to mm
                rotation = footprint.GetOrientationDegrees()

                # Check edge clearance
                if (x < edge_clearance or x > board_width - edge_clearance or
                    y < edge_clearance or y > board_height - edge_clearance):
                    results.append(self._result_factory.create_result(
                        category=ValidationCategory.COMPONENT_PLACEMENT,
                        message=f"Component {footprint.GetReference()} is too close to board edge",
                        severity=rule.severity,
                        location=(x, y),
                        details={
                            'reference': footprint.GetReference(),
                            'position': (x, y),
                            'edge_clearance': edge_clearance
                        }
                    ))

                # Check rotation
                if abs(rotation) > max_rotation:
                    results.append(self._result_factory.create_result(
                        category=ValidationCategory.COMPONENT_PLACEMENT,
                        message=f"Component {footprint.GetReference()} rotation {rotation:.1f}° exceeds maximum {max_rotation}°",
                        severity=rule.severity,
                        location=(x, y),
                        details={
                            'reference': footprint.GetReference(),
                            'rotation': rotation,
                            'max_rotation': max_rotation
                        }
                    ))

                # Check spacing with other components
                for other in board.GetFootprints():
                    if other != footprint:
                        other_pos = other.GetPosition()
                        other_x = other_pos.x / 1e6
                        other_y = other_pos.y / 1e6
                        distance = math.sqrt((x - other_x)**2 + (y - other_y)**2)
                        if distance < min_spacing:
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.COMPONENT_PLACEMENT,
                                message=f"Components {footprint.GetReference()} and {other.GetReference()} are too close",
                                severity=rule.severity,
                                location=(x, y),
                                details={
                                    'reference1': footprint.GetReference(),
                                    'reference2': other.GetReference(),
                                    'distance': distance,
                                    'min_spacing': min_spacing
                                }
                            ))

        except Exception as e:
            self.logger.error(f"Error validating component placement: {str(e)}")
            results.append(self._result_factory.create_result(
                category=ValidationCategory.COMPONENT_PLACEMENT,
                message=f"Error validating component placement: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="routing")
    def _validate_routing(self) -> List[ValidationResult]:
        """Validate routing.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            rule = self._rules[RuleType.ROUTING]
            min_track_width = rule.get_parameter("min_track_width")
            max_track_width = rule.get_parameter("max_track_width")
            min_via_size = rule.get_parameter("min_via_size")
            max_via_size = rule.get_parameter("max_via_size")
            min_clearance = rule.get_parameter("min_clearance")
            max_length = rule.get_parameter("max_length")

            # Check track widths
            for track in board.GetTracks():
                if track.GetClass() == 'TRACK':
                    width = track.GetWidth() / 1e6  # Convert to mm
                    if width < min_track_width:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.ROUTING,
                            message=f"Track width {width:.2f}mm is less than minimum {min_track_width}mm",
                            severity=rule.severity,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'width': width,
                                'min_width': min_track_width,
                                'net': track.GetNetname()
                            }
                        ))
                    elif width > max_track_width:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.ROUTING,
                            message=f"Track width {width:.2f}mm exceeds maximum {max_track_width}mm",
                            severity=rule.severity,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'width': width,
                                'max_width': max_track_width,
                                'net': track.GetNetname()
                            }
                        ))

                    # Check track length
                    length = track.GetLength() / 1e6  # Convert to mm
                    if length > max_length:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.ROUTING,
                            message=f"Track length {length:.2f}mm exceeds maximum {max_length}mm",
                            severity=rule.severity,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'length': length,
                                'max_length': max_length,
                                'net': track.GetNetname()
                            }
                        ))

            # Check via sizes
            for track in board.GetTracks():
                if track.GetClass() == 'VIA':
                    drill_size = track.GetDrillValue() / 1e6  # Convert to mm
                    if drill_size < min_via_size:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.ROUTING,
                            message=f"Via drill size {drill_size:.2f}mm is less than minimum {min_via_size}mm",
                            severity=rule.severity,
                            location=(track.GetPosition().x/1e6, track.GetPosition().y/1e6),
                            details={
                                'drill_size': drill_size,
                                'min_drill_size': min_via_size,
                                'net': track.GetNetname()
                            }
                        ))
                    elif drill_size > max_via_size:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.ROUTING,
                            message=f"Via drill size {drill_size:.2f}mm exceeds maximum {max_via_size}mm",
                            severity=rule.severity,
                            location=(track.GetPosition().x/1e6, track.GetPosition().y/1e6),
                            details={
                                'drill_size': drill_size,
                                'max_drill_size': max_via_size,
                                'net': track.GetNetname()
                            }
                        ))

            # Check track clearances
            for track1 in board.GetTracks():
                if track1.GetClass() == 'TRACK':
                    for track2 in board.GetTracks():
                        if track2.GetClass() == 'TRACK' and track1 != track2:
                            distance = self._calculate_track_distance(track1, track2)
                            if distance < min_clearance:
                                results.append(self._result_factory.create_result(
                                    category=ValidationCategory.ROUTING,
                                    message=f"Track clearance {distance:.2f}mm is less than minimum {min_clearance}mm",
                                    severity=rule.severity,
                                    location=(track1.GetStart().x/1e6, track1.GetStart().y/1e6),
                                    details={
                                        'distance': distance,
                                        'min_clearance': min_clearance,
                                        'net1': track1.GetNetname(),
                                        'net2': track2.GetNetname()
                                    }
                                ))

        except Exception as e:
            self.logger.error(f"Error validating routing: {str(e)}")
            results.append(self._result_factory.create_result(
                category=ValidationCategory.ROUTING,
                message=f"Error validating routing: {str(e)}",
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

            rule = self._rules[RuleType.MANUFACTURING]
            min_feature_size = rule.get_parameter("min_feature_size")
            max_board_size = rule.get_parameter("max_board_size")
            min_annular_ring = rule.get_parameter("min_annular_ring")
            min_drill_size = rule.get_parameter("min_drill_size")

            # Check board size
            board_rect = board.GetBoardEdgesBoundingBox()
            board_width = board_rect.GetWidth() / 1e6  # Convert to mm
            board_height = board_rect.GetHeight() / 1e6  # Convert to mm
            board_size = max(board_width, board_height)
            if board_size > max_board_size:
                results.append(self._result_factory.create_result(
                    category=ValidationCategory.MANUFACTURING,
                    message=f"Board size {board_size:.1f}mm exceeds maximum {max_board_size}mm",
                    severity=rule.severity,
                    details={
                        'width': board_width,
                        'height': board_height,
                        'max_size': max_board_size
                    }
                ))

            # Check vias
            for track in board.GetTracks():
                if track.GetClass() == 'VIA':
                    drill_size = track.GetDrillValue() / 1e6  # Convert to mm
                    if drill_size < min_drill_size:
                        results.append(self._result_factory.create_manufacturing_result(
                            category=ValidationCategory.MANUFACTURING,
                            message=f"Via drill size {drill_size:.2f}mm is less than minimum {min_drill_size}mm",
                            severity=rule.severity,
                            location=(track.GetPosition().x/1e6, track.GetPosition().y/1e6),
                            details={
                                'drill_size': drill_size,
                                'min_drill_size': min_drill_size,
                                'net': track.GetNetname()
                            }
                        ))

                    # Check annular ring
                    pad_size = track.GetWidth() / 1e6  # Convert to mm
                    annular_ring = (pad_size - drill_size) / 2
                    if annular_ring < min_annular_ring:
                        results.append(self._result_factory.create_manufacturing_result(
                            category=ValidationCategory.MANUFACTURING,
                            message=f"Via annular ring {annular_ring:.2f}mm is less than minimum {min_annular_ring}mm",
                            severity=rule.severity,
                            location=(track.GetPosition().x/1e6, track.GetPosition().y/1e6),
                            details={
                                'annular_ring': annular_ring,
                                'min_annular_ring': min_annular_ring,
                                'net': track.GetNetname()
                            }
                        ))

            # Check traces
            for track in board.GetTracks():
                if track.GetClass() == 'TRACK':
                    width = track.GetWidth() / 1e6  # Convert to mm
                    if width < min_feature_size:
                        results.append(self._result_factory.create_manufacturing_result(
                            category=ValidationCategory.MANUFACTURING,
                            message=f"Trace width {width:.2f}mm is less than minimum {min_feature_size}mm",
                            severity=rule.severity,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'width': width,
                                'min_feature_size': min_feature_size,
                                'net': track.GetNetname()
                            }
                        ))

            # Check component pads
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    drill_size = pad.GetDrillSize().x / 1e6  # Convert to mm
                    if drill_size < min_drill_size:
                        results.append(self._result_factory.create_manufacturing_result(
                            category=ValidationCategory.MANUFACTURING,
                            message=f"Pad drill size {drill_size:.2f}mm is less than minimum {min_drill_size}mm",
                            severity=rule.severity,
                            location=(pad.GetPosition().x/1e6, pad.GetPosition().y/1e6),
                            details={
                                'drill_size': drill_size,
                                'min_drill_size': min_drill_size,
                                'reference': footprint.GetReference(),
                                'pad_number': pad.GetNumber()
                            }
                        ))

                    # Check annular ring
                    pad_size = pad.GetSize().x / 1e6  # Convert to mm
                    annular_ring = (pad_size - drill_size) / 2
                    if annular_ring < min_annular_ring:
                        results.append(self._result_factory.create_manufacturing_result(
                            category=ValidationCategory.MANUFACTURING,
                            message=f"Pad annular ring {annular_ring:.2f}mm is less than minimum {min_annular_ring}mm",
                            severity=rule.severity,
                            location=(pad.GetPosition().x/1e6, pad.GetPosition().y/1e6),
                            details={
                                'annular_ring': annular_ring,
                                'min_annular_ring': min_annular_ring,
                                'reference': footprint.GetReference(),
                                'pad_number': pad.GetNumber()
                            }
                        ))

            # Calculate manufacturing cost and yield impact
            cost_factor = self._calculate_manufacturing_cost(board)
            yield_impact = self._calculate_yield_impact(board)

            if cost_factor > 0.8:  # 80% threshold
                results.append(self._result_factory.create_manufacturing_result(
                    category=ValidationCategory.MANUFACTURING,
                    message=f"High manufacturing cost factor ({cost_factor:.1%})",
                    severity=rule.severity,
                    details={
                        'cost_factor': cost_factor,
                        'threshold': 0.8
                    },
                    manufacturing_cost=cost_factor
                ))

            if yield_impact > 0.2:  # 20% threshold
                results.append(self._result_factory.create_manufacturing_result(
                    category=ValidationCategory.MANUFACTURING,
                    message=f"High yield impact factor ({yield_impact:.1%})",
                    severity=rule.severity,
                    details={
                        'yield_impact': yield_impact,
                        'threshold': 0.2
                    },
                    yield_impact=yield_impact
                ))

        except Exception as e:
            self.logger.error(f"Error validating manufacturing rules: {str(e)}")
            results.append(self._result_factory.create_manufacturing_result(
                category=ValidationCategory.MANUFACTURING,
                message=f"Error validating manufacturing rules: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    def _calculate_manufacturing_cost(self, board: pcbnew.BOARD) -> float:
        """Calculate manufacturing cost factor.
        
        Args:
            board: KiCad board
            
        Returns:
            Cost factor (0-1)
        """
        # Simplified cost calculation
        # In a real implementation, this would consider:
        # - Board size
        # - Number of layers
        # - Minimum feature sizes
        # - Via count
        # - Component count
        # - Special requirements
        
        # Get board size
        board_rect = board.GetBoardEdgesBoundingBox()
        board_area = (board_rect.GetWidth() * board_rect.GetHeight()) / 1e12  # Convert to m²
        
        # Get minimum feature size
        min_feature_size = float('inf')
        for track in board.GetTracks():
            if track.GetClass() == 'TRACK':
                width = track.GetWidth() / 1e6  # Convert to mm
                min_feature_size = min(min_feature_size, width)
        
        # Get via count
        via_count = sum(1 for track in board.GetTracks() if track.GetClass() == 'VIA')
        
        # Get layer count
        layer_count = board.GetCopperLayerCount()
        
        # Calculate cost factors
        size_factor = min(1.0, board_area / 0.1)  # Normalize to 0.1m²
        feature_factor = min(1.0, 0.1 / min_feature_size)  # Normalize to 0.1mm
        via_factor = min(1.0, via_count / 1000)  # Normalize to 1000 vias
        layer_factor = min(1.0, layer_count / 8)  # Normalize to 8 layers
        
        # Combine factors with weights
        return (0.3 * size_factor +
                0.3 * feature_factor +
                0.2 * via_factor +
                0.2 * layer_factor)

    def _calculate_yield_impact(self, board: pcbnew.BOARD) -> float:
        """Calculate manufacturing yield impact factor.
        
        Args:
            board: KiCad board
            
        Returns:
            Yield impact factor (0-1)
        """
        # Simplified yield impact calculation
        # In a real implementation, this would consider:
        # - Minimum feature sizes
        # - Via aspect ratios
        # - Component density
        # - Trace density
        # - Special requirements
        
        # Get minimum feature size
        min_feature_size = float('inf')
        for track in board.GetTracks():
            if track.GetClass() == 'TRACK':
                width = track.GetWidth() / 1e6  # Convert to mm
                min_feature_size = min(min_feature_size, width)
        
        # Get via aspect ratios
        max_aspect_ratio = 0.0
        for track in board.GetTracks():
            if track.GetClass() == 'VIA':
                drill_size = track.GetDrillValue() / 1e6  # Convert to mm
                pad_size = track.GetWidth() / 1e6  # Convert to mm
                aspect_ratio = pad_size / drill_size
                max_aspect_ratio = max(max_aspect_ratio, aspect_ratio)
        
        # Get component density
        board_rect = board.GetBoardEdgesBoundingBox()
        board_area = (board_rect.GetWidth() * board_rect.GetHeight()) / 1e12  # Convert to m²
        component_count = board.GetFootprintCount()
        component_density = component_count / board_area if board_area > 0 else 0
        
        # Calculate impact factors
        feature_risk = min(1.0, 0.1 / min_feature_size)  # Normalize to 0.1mm
        via_risk = min(1.0, max_aspect_ratio / 2.0)  # Normalize to 2:1
        density_risk = min(1.0, component_density / 100)  # Normalize to 100 components/m²
        
        # Combine factors with weights
        return (0.4 * feature_risk +
                0.3 * via_risk +
                0.3 * density_risk)

    @handle_validation_error(logger=Logger(__name__), category="power")
    def _validate_power(self) -> List[ValidationResult]:
        """Validate power distribution.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            rule = self._rules[RuleType.POWER]
            max_voltage_drop = rule.get_parameter("max_voltage_drop")
            max_current_density = rule.get_parameter("max_current_density")
            min_trace_width = rule.get_parameter("min_trace_width")
            max_trace_width = rule.get_parameter("max_trace_width")

            # Check power traces
            for track in board.GetTracks():
                if track.GetClass() == 'TRACK':
                    net = track.GetNetname()
                    if 'power' in net.lower() or 'vcc' in net.lower():
                        width = track.GetWidth() / 1e6  # Convert to mm
                        if width < min_trace_width:
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.POWER,
                                message=f"Power trace width {width:.2f}mm is less than minimum {min_trace_width}mm",
                                severity=rule.severity,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'width': width,
                                    'min_width': min_trace_width,
                                    'net': net
                                }
                            ))
                        elif width > max_trace_width:
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.POWER,
                                message=f"Power trace width {width:.2f}mm exceeds maximum {max_trace_width}mm",
                                severity=rule.severity,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'width': width,
                                    'max_width': max_trace_width,
                                    'net': net
                                }
                            ))

                        # Check current capacity
                        current_capacity = self._pcb_utils.estimate_track_current(width)
                        if current_capacity > max_current_density * width:
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.POWER,
                                message=f"Power trace current capacity {current_capacity:.1f}A exceeds maximum {max_current_density * width:.1f}A",
                                severity=rule.severity,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'current_capacity': current_capacity,
                                    'max_current': max_current_density * width,
                                    'net': net
                                }
                            ))

                        # Check voltage drop
                        length = track.GetLength() / 1e6  # Convert to mm
                        voltage_drop = self._pcb_utils.calculate_voltage_drop(length, width, current_capacity)
                        if voltage_drop > max_voltage_drop:
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.POWER,
                                message=f"Power trace voltage drop {voltage_drop:.3f}V exceeds maximum {max_voltage_drop}V",
                                severity=rule.severity,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'voltage_drop': voltage_drop,
                                    'max_voltage_drop': max_voltage_drop,
                                    'net': net
                                }
                            ))

        except Exception as e:
            self.logger.error(f"Error validating power distribution: {str(e)}")
            results.append(self._result_factory.create_result(
                category=ValidationCategory.POWER,
                message=f"Error validating power distribution: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="ground")
    def _validate_ground(self) -> List[ValidationResult]:
        """Validate ground distribution.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            rule = self._rules[RuleType.GROUND]
            max_loop_area = rule.get_parameter("max_loop_area")
            min_ground_area = rule.get_parameter("min_ground_area")
            max_impedance = rule.get_parameter("max_impedance")

            # Check ground nets
            for net in board.GetNetsByName():
                if 'gnd' in net.lower() or 'ground' in net.lower():
                    # Check ground loop area
                    loop_area = self._pcb_utils.calculate_ground_loop_area(net)
                    if loop_area > max_loop_area:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.GROUND,
                            message=f"Ground loop area {loop_area:.1f}mm² exceeds maximum {max_loop_area}mm²",
                            severity=rule.severity,
                            details={
                                'loop_area': loop_area,
                                'max_loop_area': max_loop_area,
                                'net': net
                            }
                        ))

                    # Check ground plane coverage
                    total_area = board.GetBoardEdgesBoundingBox().GetArea() / 1e12  # Convert to m²
                    ground_area = 0.0
                    for zone in board.Zones():
                        if zone.GetNetname() == net:
                            ground_area += zone.GetArea() / 1e12  # Convert to m²
                    
                    ground_ratio = ground_area / total_area if total_area > 0 else 0
                    if ground_ratio < min_ground_area:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.GROUND,
                            message=f"Ground plane coverage {ground_ratio:.1%} is less than minimum {min_ground_area:.1%}",
                            severity=rule.severity,
                            details={
                                'ground_ratio': ground_ratio,
                                'min_ground_area': min_ground_area,
                                'net': net
                            }
                        ))

                    # Check ground impedance
                    for track in board.GetTracks():
                        if track.GetNetname() == net:
                            width = track.GetWidth() / 1e6  # Convert to mm
                            impedance = self._pcb_utils.calculate_trace_impedance(width, track.GetLayer())
                            if impedance > max_impedance:
                                results.append(self._result_factory.create_result(
                                    category=ValidationCategory.GROUND,
                                    message=f"Ground trace impedance {impedance:.1f}Ω exceeds maximum {max_impedance}Ω",
                                    severity=rule.severity,
                                    location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                    details={
                                        'impedance': impedance,
                                        'max_impedance': max_impedance,
                                        'net': net
                                    }
                                ))

        except Exception as e:
            self.logger.error(f"Error validating ground distribution: {str(e)}")
            results.append(self._result_factory.create_result(
                category=ValidationCategory.GROUND,
                message=f"Error validating ground distribution: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="signal")
    def _validate_signal(self) -> List[ValidationResult]:
        """Validate signal integrity.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            rule = self._rules[RuleType.SIGNAL]
            max_crosstalk = rule.get_parameter("max_crosstalk")
            max_reflection = rule.get_parameter("max_reflection")
            min_impedance = rule.get_parameter("min_impedance")
            max_impedance = rule.get_parameter("max_impedance")

            # Check signal traces
            for track1 in board.GetTracks():
                if track1.GetClass() == 'TRACK':
                    net1 = track1.GetNetname()
                    if 'signal' in net1.lower():
                        width1 = track1.GetWidth() / 1e6  # Convert to mm
                        
                        # Check impedance
                        impedance = self._pcb_utils.calculate_trace_impedance(width1, track1.GetLayer())
                        if impedance < min_impedance:
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.SIGNAL,
                                message=f"Signal trace impedance {impedance:.1f}Ω is less than minimum {min_impedance}Ω",
                                severity=rule.severity,
                                location=(track1.GetStart().x/1e6, track1.GetStart().y/1e6),
                                details={
                                    'impedance': impedance,
                                    'min_impedance': min_impedance,
                                    'net': net1
                                }
                            ))
                        elif impedance > max_impedance:
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.SIGNAL,
                                message=f"Signal trace impedance {impedance:.1f}Ω exceeds maximum {max_impedance}Ω",
                                severity=rule.severity,
                                location=(track1.GetStart().x/1e6, track1.GetStart().y/1e6),
                                details={
                                    'impedance': impedance,
                                    'max_impedance': max_impedance,
                                    'net': net1
                                }
                            ))

                        # Check crosstalk
                        for track2 in board.GetTracks():
                            if track2.GetClass() == 'TRACK' and track1 != track2:
                                net2 = track2.GetNetname()
                                if 'signal' in net2.lower():
                                    width2 = track2.GetWidth() / 1e6  # Convert to mm
                                    distance = self._pcb_utils.calculate_track_distance(
                                        (track1.GetStart().x/1e6, track1.GetStart().y/1e6),
                                        (track1.GetEnd().x/1e6, track1.GetEnd().y/1e6),
                                        (track2.GetStart().x/1e6, track2.GetStart().y/1e6),
                                        (track2.GetEnd().x/1e6, track2.GetEnd().y/1e6)
                                    )
                                    crosstalk_risk = self._pcb_utils.calculate_crosstalk_risk(
                                        distance, width1, width2
                                    )
                                    if crosstalk_risk > max_crosstalk:
                                        results.append(self._result_factory.create_result(
                                            category=ValidationCategory.SIGNAL,
                                            message=f"High crosstalk risk ({crosstalk_risk:.1%}) between signal traces",
                                            severity=rule.severity,
                                            location=(track1.GetStart().x/1e6, track1.GetStart().y/1e6),
                                            details={
                                                'crosstalk_risk': crosstalk_risk,
                                                'max_crosstalk': max_crosstalk,
                                                'net1': net1,
                                                'net2': net2,
                                                'distance': distance
                                            }
                                        ))

        except Exception as e:
            self.logger.error(f"Error validating signal integrity: {str(e)}")
            results.append(self._result_factory.create_result(
                category=ValidationCategory.SIGNAL,
                message=f"Error validating signal integrity: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    def _validate_audio_specific(self) -> List[ValidationResult]:
        """Validate audio-specific rules using BaseValidator interface.
        
        Returns:
            List of validation results
        """
        results = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Use the audio validator for audio-specific validation
            if hasattr(self, '_audio_validator') and self._audio_validator:
                audio_results = self._audio_validator.validate(board)
                if hasattr(audio_results, 'issues'):
                    for issue in audio_results.issues:
                        results.append(self._result_factory.create_result(
                            category=ValidationCategory.AUDIO,
                            message=issue.message,
                            severity=issue.severity,
                            location=issue.location,
                            details=issue.details,
                            suggestion=issue.suggestion,
                            documentation_ref=issue.documentation_ref
                        ))
                elif isinstance(audio_results, list):
                    results.extend(audio_results)

            # Check for audio-specific components and nets
            audio_components = []
            audio_nets = []
            
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["AUDIO", "AMP", "DAC", "OP", "U"]):
                    audio_components.append(footprint)
                    
                    # Get audio nets from this component
                    for pad in footprint.Pads():
                        net = pad.GetNetname()
                        if net and net not in audio_nets:
                            audio_nets.append(net)

            # Validate audio signal paths
            for net in audio_nets:
                if any(keyword in net.upper() for keyword in ["AUDIO", "SIGNAL", "IN", "OUT"]):
                    # Check for proper audio signal routing
                    tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                    for track in tracks:
                        width = track.GetWidth() / 1e6  # Convert to mm
                        if width < 0.2:  # Minimum audio trace width
                            results.append(self._result_factory.create_result(
                                category=ValidationCategory.AUDIO,
                                message=f"Audio signal trace width {width:.2f}mm is below minimum 0.2mm",
                                severity=ValidationSeverity.WARNING,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net,
                                    'width': width,
                                    'min_width': 0.2
                                }
                            ))

        except Exception as e:
            self.logger.error(f"Error in audio-specific validation: {e}")
            results.append(self._result_factory.create_result(
                category=ValidationCategory.AUDIO,
                message=f"Error in audio-specific validation: {e}",
                severity=ValidationSeverity.ERROR
            ))
        
        return results

    def _calculate_track_distance(self, track1: Any, track2: Any) -> float:
        """Calculate the minimum distance between two tracks.
        
        Args:
            track1: First track
            track2: Second track
            
        Returns:
            Minimum distance between tracks in mm
        """
        try:
            # Get track endpoints
            start1 = track1.GetStart()
            end1 = track1.GetEnd()
            start2 = track2.GetStart()
            end2 = track2.GetEnd()
            
            # Convert to mm
            x1_start, y1_start = start1.x / 1e6, start1.y / 1e6
            x1_end, y1_end = end1.x / 1e6, end1.y / 1e6
            x2_start, y2_start = start2.x / 1e6, start2.y / 1e6
            x2_end, y2_end = end2.x / 1e6, end2.y / 1e6
            
            # Calculate distances between all endpoints
            distances = []
            
            # Distance from track1 start to track2 start
            dist1 = ((x1_start - x2_start) ** 2 + (y1_start - y2_start) ** 2) ** 0.5
            distances.append(dist1)
            
            # Distance from track1 start to track2 end
            dist2 = ((x1_start - x2_end) ** 2 + (y1_start - y2_end) ** 2) ** 0.5
            distances.append(dist2)
            
            # Distance from track1 end to track2 start
            dist3 = ((x1_end - x2_start) ** 2 + (y1_end - y2_start) ** 2) ** 0.5
            distances.append(dist3)
            
            # Distance from track1 end to track2 end
            dist4 = ((x1_end - x2_end) ** 2 + (y1_end - y2_end) ** 2) ** 0.5
            distances.append(dist4)
            
            # Return minimum distance
            return min(distances)
            
        except Exception as e:
            self.logger.error(f"Error calculating track distance: {str(e)}")
            return float('inf')  # Return infinity if calculation fails 