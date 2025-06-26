"""
Audio Router Module

This module provides audio signal routing functionality for KiCad PCB designs,
using configurable routing constraints instead of hardcoded values.
"""

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

try:
    import pcbnew
except ImportError:
    pcbnew = None

from ...config.audio_routing_config import (
    AudioRoutingConfig, OptimizationItem, RoutingConstraintItem, 
    SignalType, ValidationItem
)


@dataclass
class RoutingConstraints:
    """Constraints for audio signal routing."""
    min_width: float  # mm
    min_clearance: float  # mm
    max_length: float  # mm
    preferred_layer: int
    avoid_layers: List[int]
    require_ground_plane: bool = True
    require_power_plane: bool = True


@dataclass
class DifferentialPairConfig:
    """Configuration for differential pair routing."""
    spacing: float  # mm - spacing between pair traces
    width: float  # mm - width of each trace
    target_impedance: float  # ohms - target differential impedance
    max_length_mismatch: float  # mm - maximum length difference
    max_width_mismatch: float  # mm - maximum width difference
    serpentine_spacing: float  # mm - spacing for serpentine routing
    serpentine_amplitude: float  # mm - amplitude for serpentine routing


@dataclass
class RoutingResult:
    """Result of routing operation."""
    success: bool
    message: str
    routed_tracks: List[pcbnew.TRACK] = None
    warnings: List[str] = None
    errors: List[str] = None
    metrics: Dict[str, Any] = None


class AudioRouter:
    """Audio signal router for KiCad PCB designs."""
    
    def __init__(self, board: 'pcbnew.BOARD', logger: Optional[logging.Logger] = None):
        """Initialize the audio router.
        
        Args:
            board: KiCad board object
            logger: Logger instance
        """
        self.board = board
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize configuration
        self.config = AudioRoutingConfig()
        
        # Validate KiCad version
        self._validate_kicad_version()
        
        # Initialize routing constraints from configuration
        self._routing_constraints = self._initialize_constraints()
        
        # Initialize differential pair configuration
        self._diff_pair_config = DifferentialPairConfig(
            spacing=0.2,  # 0.2mm spacing
            width=0.3,    # 0.3mm width
            target_impedance=100.0,  # 100 ohms differential
            max_length_mismatch=0.1,  # 0.1mm max length difference
            max_width_mismatch=0.02,  # 0.02mm max width difference
            serpentine_spacing=0.5,   # 0.5mm serpentine spacing
            serpentine_amplitude=2.0   # 2.0mm serpentine amplitude
        )
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        if pcbnew is None:
            raise RuntimeError("KiCad Python module (pcbnew) is not available")
        
        version = pcbnew.Version()
        if not version.startswith('9'):
            raise RuntimeError(f"This module requires KiCad 9.x, but found version {version}")
        self.logger.info(f"Running with KiCad version: {version}")
    
    def _initialize_constraints(self) -> Dict[SignalType, RoutingConstraints]:
        """Initialize routing constraints from configuration."""
        constraints = {}
        
        try:
            # Get configuration
            config = self.config.get_config()
            
            # Create constraints for each signal type
            for signal_type in SignalType:
                constraint_config = config.signal_types.get(signal_type.value)
                if constraint_config:
                    # Get layer ID from configuration
                    preferred_layer_id = self.config.get_layer_id(constraint_config.preferred_layer)
                    if preferred_layer_id is None:
                        self.logger.warning(f"Unknown layer '{constraint_config.preferred_layer}' for {signal_type.value}, using default")
                        preferred_layer_id = 0  # Default to top layer
                    
                    # Get avoid layer IDs
                    avoid_layer_ids = []
                    for layer_name in constraint_config.avoid_layers:
                        layer_id = self.config.get_layer_id(layer_name)
                        if layer_id is not None:
                            avoid_layer_ids.append(layer_id)
                        else:
                            self.logger.warning(f"Unknown layer '{layer_name}' in avoid_layers for {signal_type.value}")
                    
                    constraints[signal_type] = RoutingConstraints(
                        min_width=constraint_config.min_width,
                        min_clearance=constraint_config.min_clearance,
                        max_length=constraint_config.max_length,
                        preferred_layer=preferred_layer_id,
                        avoid_layers=avoid_layer_ids,
                        require_ground_plane=constraint_config.require_ground_plane,
                        require_power_plane=constraint_config.require_power_plane
                    )
                else:
                    self.logger.warning(f"No configuration found for signal type {signal_type.value}")
            
            self.logger.info(f"Initialized routing constraints for {len(constraints)} signal types")
            return constraints
            
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Input error initializing routing constraints: {str(e)}")
            return self._get_default_constraints()
        except Exception as e:
            self.logger.error(f"Unexpected error initializing routing constraints: {str(e)}")
            return self._get_default_constraints()
    
    def _get_default_constraints(self) -> Dict[SignalType, RoutingConstraints]:
        """Get default routing constraints as fallback."""
        return {
            SignalType.AUDIO: RoutingConstraints(
                min_width=0.3,
                min_clearance=0.3,
                max_length=100.0,
                preferred_layer=0,  # F_Cu
                avoid_layers=[31],  # B_Cu
                require_ground_plane=True,
                require_power_plane=True
            ),
            SignalType.POWER: RoutingConstraints(
                min_width=0.5,
                min_clearance=0.3,
                max_length=50.0,
                preferred_layer=1,  # In1_Cu
                avoid_layers=[0, 31],  # F_Cu, B_Cu
                require_ground_plane=True,
                require_power_plane=True
            ),
            SignalType.GROUND: RoutingConstraints(
                min_width=0.5,
                min_clearance=0.3,
                max_length=50.0,
                preferred_layer=2,  # In2_Cu
                avoid_layers=[0, 31],  # F_Cu, B_Cu
                require_ground_plane=True,
                require_power_plane=True
            ),
            SignalType.CONTROL: RoutingConstraints(
                min_width=0.2,
                min_clearance=0.2,
                max_length=200.0,
                preferred_layer=31,  # B_Cu
                avoid_layers=[0],  # F_Cu
                require_ground_plane=False,
                require_power_plane=False
            )
        }
    
    def route_differential_pairs(self, board: pcbnew.BOARD) -> RoutingResult:
        """Route differential pairs for balanced audio signals.
        
        Args:
            board: KiCad board object
            
        Returns:
            Routing result with success status and details
        """
        try:
            self.logger.info("Starting differential pair routing...")
            
            # Find differential pairs
            diff_pairs = self._identify_differential_pairs(board)
            
            if not diff_pairs:
                return RoutingResult(
                    success=True,
                    message="No differential pairs found to route",
                    routed_tracks=[],
                    warnings=["No differential pairs identified"],
                    errors=[],
                    metrics={"pairs_found": 0}
                )
            
            routed_tracks = []
            warnings = []
            errors = []
            
            for pair_name, pair_data in diff_pairs.items():
                try:
                    # Route the differential pair
                    pair_result = self._route_single_differential_pair(
                        pair_data["net_p"], 
                        pair_data["net_n"],
                        pair_data["start_pos"],
                        pair_data["end_pos"]
                    )
                    
                    if pair_result.success:
                        routed_tracks.extend(pair_result.routed_tracks)
                        self.logger.info(f"Successfully routed differential pair: {pair_name}")
                    else:
                        errors.append(f"Failed to route {pair_name}: {pair_result.message}")
                        
                except (ValueError, KeyError, TypeError) as e:
                    error_msg = f"Input error routing differential pair {pair_name}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Unexpected error routing differential pair {pair_name}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            # Apply length matching if needed
            if routed_tracks:
                length_matching_result = self._apply_length_matching(routed_tracks)
                if not length_matching_result.success:
                    warnings.append(f"Length matching failed: {length_matching_result.message}")
            
            success = len(errors) == 0
            message = f"Routed {len(diff_pairs)} differential pairs" if success else f"Routed {len(diff_pairs) - len(errors)} of {len(diff_pairs)} differential pairs"
            
            return RoutingResult(
                success=success,
                message=message,
                routed_tracks=routed_tracks,
                warnings=warnings,
                errors=errors,
                metrics={
                    "pairs_found": len(diff_pairs),
                    "pairs_routed": len(diff_pairs) - len(errors),
                    "length_matching_applied": length_matching_result.success if routed_tracks else False
                }
            )
        except (ValueError, KeyError, TypeError) as e:
            error_msg = f"Input error in differential pair routing: {str(e)}"
            self.logger.error(error_msg)
            return RoutingResult(
                success=False,
                message=error_msg,
                routed_tracks=[],
                warnings=[],
                errors=[error_msg],
                metrics={}
            )
        except Exception as e:
            error_msg = f"Unexpected error in differential pair routing: {str(e)}"
            self.logger.error(error_msg)
            return RoutingResult(
                success=False,
                message=error_msg,
                routed_tracks=[],
                warnings=[],
                errors=[error_msg],
                metrics={}
            )
    
    def _identify_differential_pairs(self, board: pcbnew.BOARD) -> Dict[str, Dict[str, Any]]:
        """Identify differential pairs in the board.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of differential pair information
        """
        diff_pairs = {}
        
        # Get all nets
        nets = board.GetNetsByName()
        
        # Look for differential pair naming patterns
        for net_name, net in nets.items():
            net_name_lower = net_name.lower()
            
            # Check for common differential pair naming patterns
            if any(pattern in net_name_lower for pattern in ["_p", "_n", "_pos", "_neg", "+", "-"]):
                # Find the corresponding pair
                base_name = self._extract_base_name(net_name)
                if base_name:
                    if base_name not in diff_pairs:
                        diff_pairs[base_name] = {
                            "net_p": None,
                            "net_n": None,
                            "start_pos": None,
                            "end_pos": None
                        }
                    
                    # Determine if this is positive or negative
                    if any(pos_pattern in net_name_lower for pos_pattern in ["_p", "_pos", "+"]):
                        diff_pairs[base_name]["net_p"] = net_name
                    elif any(neg_pattern in net_name_lower for neg_pattern in ["_n", "_neg", "-"]):
                        diff_pairs[base_name]["net_n"] = net_name
        
        # Find start and end positions for complete pairs
        complete_pairs = {}
        for pair_name, pair_data in diff_pairs.items():
            if pair_data["net_p"] and pair_data["net_n"]:
                # Find start and end positions from existing tracks or pads
                start_pos, end_pos = self._find_pair_endpoints(pair_data["net_p"], pair_data["net_n"], board)
                if start_pos and end_pos:
                    pair_data["start_pos"] = start_pos
                    pair_data["end_pos"] = end_pos
                    complete_pairs[pair_name] = pair_data
        
        self.logger.info(f"Identified {len(complete_pairs)} differential pairs")
        return complete_pairs
    
    def _extract_base_name(self, net_name: str) -> Optional[str]:
        """Extract base name from differential pair net name.
        
        Args:
            net_name: Net name
            
        Returns:
            Base name or None if not a differential pair
        """
        net_name_lower = net_name.lower()
        
        # Remove common differential pair suffixes
        suffixes = ["_p", "_n", "_pos", "_neg", "+", "-"]
        for suffix in suffixes:
            if net_name_lower.endswith(suffix):
                return net_name[:-len(suffix)]
        
        return None
    
    def _find_pair_endpoints(self, net_p: str, net_n: str, board: pcbnew.BOARD) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        """Find start and end positions for a differential pair.
        
        Args:
            net_p: Positive net name
            net_n: Negative net name
            board: KiCad board object
            
        Returns:
            Tuple of (start_pos, end_pos) or (None, None) if not found
        """
        try:
            # Look for existing tracks
            tracks_p = [t for t in board.GetTracks() if t.GetNetname() == net_p]
            tracks_n = [t for t in board.GetTracks() if t.GetNetname() == net_n]
            
            if tracks_p and tracks_n:
                # Use existing track endpoints
                start_p = tracks_p[0].GetStart()
                end_p = tracks_p[0].GetEnd()
                start_n = tracks_n[0].GetStart()
                end_n = tracks_n[0].GetEnd()
                
                # Calculate center points
                start_pos = (
                    (start_p.x + start_n.x) / (2 * 1e6),  # Convert to mm
                    (start_p.y + start_n.y) / (2 * 1e6)
                )
                end_pos = (
                    (end_p.x + end_n.x) / (2 * 1e6),
                    (end_p.y + end_n.y) / (2 * 1e6)
                )
                
                return start_pos, end_pos
            
            # Look for pads
            pads_p = []
            pads_n = []
            
            for footprint in board.GetFootprints():
                for pad in footprint.Pads():
                    if pad.GetNetname() == net_p:
                        pos = pad.GetPosition()
                        pads_p.append((pos.x / 1e6, pos.y / 1e6))
                    elif pad.GetNetname() == net_n:
                        pos = pad.GetPosition()
                        pads_n.append((pos.x / 1e6, pos.y / 1e6))
            
            if len(pads_p) >= 2 and len(pads_n) >= 2:
                # Use pad positions
                start_pos = (
                    (pads_p[0][0] + pads_n[0][0]) / 2,
                    (pads_p[0][1] + pads_n[0][1]) / 2
                )
                end_pos = (
                    (pads_p[1][0] + pads_n[1][0]) / 2,
                    (pads_p[1][1] + pads_n[1][1]) / 2
                )
                
                return start_pos, end_pos
            
            return None, None
            
        except Exception as e:
            self.logger.error(f"Error finding pair endpoints: {str(e)}")
            return None, None
    
    def _route_single_differential_pair(self, net_p: str, net_n: str, 
                                      start_pos: Tuple[float, float], 
                                      end_pos: Tuple[float, float]) -> RoutingResult:
        """Route a single differential pair.
        
        Args:
            net_p: Positive net name
            net_n: Negative net name
            start_pos: Start position (x, y) in mm
            end_pos: End position (x, y) in mm
            
        Returns:
            Routing result
        """
        try:
            # Convert positions to KiCad units
            start_nm = (int(start_pos[0] * 1e6), int(start_pos[1] * 1e6))
            end_nm = (int(end_pos[0] * 1e6), int(end_pos[1] * 1e6))
            
            # Calculate differential pair positions
            spacing_nm = int(self._diff_pair_config.spacing * 1e6)
            width_nm = int(self._diff_pair_config.width * 1e6)
            
            # Calculate perpendicular vector for spacing
            dx = end_nm[0] - start_nm[0]
            dy = end_nm[1] - start_nm[1]
            length = math.sqrt(dx * dx + dy * dy)
            
            if length == 0:
                return RoutingResult(
                    success=False,
                    message="Start and end positions are identical",
                    routed_tracks=[],
                    warnings=[],
                    errors=["Invalid differential pair positions"]
                )
            
            # Normalize and rotate 90 degrees for spacing
            perp_x = -dy / length
            perp_y = dx / length
            
            # Calculate positive and negative track positions
            pos_start = (
                start_nm[0] + int(perp_x * spacing_nm / 2),
                start_nm[1] + int(perp_y * spacing_nm / 2)
            )
            pos_end = (
                end_nm[0] + int(perp_x * spacing_nm / 2),
                end_nm[1] + int(perp_y * spacing_nm / 2)
            )
            
            neg_start = (
                start_nm[0] - int(perp_x * spacing_nm / 2),
                start_nm[1] - int(perp_y * spacing_nm / 2)
            )
            neg_end = (
                end_nm[0] - int(perp_x * spacing_nm / 2),
                end_nm[1] - int(perp_y * spacing_nm / 2)
            )
            
            # Create tracks
            tracks = []
            
            # Positive track
            pos_track = pcbnew.TRACK(self.board)
            pos_track.SetStart(pcbnew.VECTOR2I(pos_start[0], pos_start[1]))
            pos_track.SetEnd(pcbnew.VECTOR2I(pos_end[0], pos_end[1]))
            pos_track.SetWidth(width_nm)
            pos_track.SetLayer(pcbnew.F_Cu)  # Top layer
            pos_track.SetNetCode(self.board.GetNetcodeFromNetname(net_p))
            self.board.Add(pos_track)
            tracks.append(pos_track)
            
            # Negative track
            neg_track = pcbnew.TRACK(self.board)
            neg_track.SetStart(pcbnew.VECTOR2I(neg_start[0], neg_start[1]))
            neg_track.SetEnd(pcbnew.VECTOR2I(neg_end[0], neg_end[1]))
            neg_track.SetWidth(width_nm)
            neg_track.SetLayer(pcbnew.F_Cu)  # Top layer
            neg_track.SetNetCode(self.board.GetNetcodeFromNetname(net_n))
            self.board.Add(neg_track)
            tracks.append(neg_track)
            
            # Update board connectivity
            self.board.BuildConnectivity()
            
            return RoutingResult(
                success=True,
                message=f"Successfully routed differential pair {net_p}/{net_n}",
                routed_tracks=tracks,
                warnings=[],
                errors=[],
                metrics={
                    "spacing": self._diff_pair_config.spacing,
                    "width": self._diff_pair_config.width,
                    "length": length / 1e6  # Convert back to mm
                }
            )
            
        except Exception as e:
            error_msg = f"Error routing differential pair {net_p}/{net_n}: {str(e)}"
            self.logger.error(error_msg)
            return RoutingResult(
                success=False,
                message=error_msg,
                routed_tracks=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _apply_length_matching(self, tracks: List[pcbnew.TRACK]) -> RoutingResult:
        """Apply length matching to differential pairs.
        
        Args:
            tracks: List of tracks to match
            
        Returns:
            Routing result
        """
        try:
            # Group tracks by differential pairs
            diff_pairs = self._group_tracks_by_pairs(tracks)
            
            if not diff_pairs:
                return RoutingResult(
                    success=True,
                    message="No differential pairs found for length matching",
                    routed_tracks=[],
                    warnings=[],
                    errors=[]
                )
            
            modified_tracks = []
            
            for pair_name, pair_tracks in diff_pairs.items():
                if len(pair_tracks) == 2:
                    # Calculate lengths
                    length1 = pair_tracks[0].GetLength() / 1e6  # Convert to mm
                    length2 = pair_tracks[1].GetLength() / 1e6
                    
                    length_diff = abs(length1 - length2)
                    
                    if length_diff > self._diff_pair_config.max_length_mismatch:
                        # Apply serpentine routing to shorter track
                        shorter_track = pair_tracks[0] if length1 < length2 else pair_tracks[1]
                        longer_track = pair_tracks[1] if length1 < length2 else pair_tracks[0]
                        
                        # Calculate required additional length
                        target_length = max(length1, length2)
                        current_length = min(length1, length2)
                        additional_length = target_length - current_length
                        
                        # Apply serpentine routing
                        serpentine_result = self._apply_serpentine_routing(
                            shorter_track, additional_length
                        )
                        
                        if serpentine_result.success:
                            modified_tracks.extend(serpentine_result.routed_tracks)
                            self.logger.info(f"Applied length matching to {pair_name}: {length_diff:.3f}mm -> {self._diff_pair_config.max_length_mismatch:.3f}mm")
                        else:
                            self.logger.warning(f"Failed to apply length matching to {pair_name}: {serpentine_result.message}")
            
            return RoutingResult(
                success=True,
                message=f"Applied length matching to {len(diff_pairs)} differential pairs",
                routed_tracks=modified_tracks,
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Error applying length matching: {str(e)}"
            self.logger.error(error_msg)
            return RoutingResult(
                success=False,
                message=error_msg,
                routed_tracks=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _group_tracks_by_pairs(self, tracks: List[pcbnew.TRACK]) -> Dict[str, List[pcbnew.TRACK]]:
        """Group tracks by differential pairs.
        
        Args:
            tracks: List of tracks
            
        Returns:
            Dictionary of differential pairs
        """
        diff_pairs = {}
        
        for track in tracks:
            net_name = track.GetNetname()
            base_name = self._extract_base_name(net_name)
            
            if base_name:
                if base_name not in diff_pairs:
                    diff_pairs[base_name] = []
                diff_pairs[base_name].append(track)
        
        return diff_pairs
    
    def _apply_serpentine_routing(self, track: pcbnew.TRACK, additional_length: float) -> RoutingResult:
        """Apply serpentine routing to add length to a track.
        
        Args:
            track: Track to modify
            additional_length: Additional length to add in mm
            
        Returns:
            Routing result
        """
        try:
            # Calculate serpentine parameters
            amplitude_nm = int(self._diff_pair_config.serpentine_amplitude * 1e6)
            spacing_nm = int(self._diff_pair_config.serpentine_spacing * 1e6)
            
            # Calculate number of serpentine segments needed
            segment_length = 2 * amplitude_nm  # Length of one serpentine segment
            num_segments = max(1, int(additional_length * 1e6 / segment_length))
            
            # Get track start and end
            start_pos = track.GetStart()
            end_pos = track.GetEnd()
            
            # Calculate direction vector
            dx = end_pos.x - start_pos.x
            dy = end_pos.y - start_pos.y
            length = math.sqrt(dx * dx + dy * dy)
            
            if length == 0:
                return RoutingResult(
                    success=False,
                    message="Track has zero length",
                    routed_tracks=[],
                    warnings=[],
                    errors=["Invalid track for serpentine routing"]
                )
            
            # Normalize direction
            dir_x = dx / length
            dir_y = dy / length
            
            # Calculate perpendicular vector
            perp_x = -dir_y
            perp_y = dir_x
            
            # Create serpentine path
            current_pos = start_pos
            serpentine_tracks = []
            
            for i in range(num_segments):
                # Calculate segment start and end
                segment_start = current_pos
                segment_end = pcbnew.VECTOR2I(
                    current_pos.x + int(dir_x * spacing_nm),
                    current_pos.y + int(dir_y * spacing_nm)
                )
                
                # Create main segment
                main_track = pcbnew.TRACK(self.board)
                main_track.SetStart(segment_start)
                main_track.SetEnd(segment_end)
                main_track.SetWidth(track.GetWidth())
                main_track.SetLayer(track.GetLayer())
                main_track.SetNetCode(track.GetNetCode())
                self.board.Add(main_track)
                serpentine_tracks.append(main_track)
                
                # Create serpentine loop
                loop_start = segment_end
                loop_mid1 = pcbnew.VECTOR2I(
                    segment_end.x + int(perp_x * amplitude_nm),
                    segment_end.y + int(perp_y * amplitude_nm)
                )
                loop_mid2 = pcbnew.VECTOR2I(
                    segment_end.x + int(perp_x * amplitude_nm) + int(dir_x * spacing_nm),
                    segment_end.y + int(perp_y * amplitude_nm) + int(dir_y * spacing_nm)
                )
                loop_end = pcbnew.VECTOR2I(
                    segment_end.x + int(dir_x * spacing_nm),
                    segment_end.y + int(dir_y * spacing_nm)
                )
                
                # Create loop tracks
                loop_track1 = pcbnew.TRACK(self.board)
                loop_track1.SetStart(loop_start)
                loop_track1.SetEnd(loop_mid1)
                loop_track1.SetWidth(track.GetWidth())
                loop_track1.SetLayer(track.GetLayer())
                loop_track1.SetNetCode(track.GetNetCode())
                self.board.Add(loop_track1)
                serpentine_tracks.append(loop_track1)
                
                loop_track2 = pcbnew.TRACK(self.board)
                loop_track2.SetStart(loop_mid1)
                loop_track2.SetEnd(loop_mid2)
                loop_track2.SetWidth(track.GetWidth())
                loop_track2.SetLayer(track.GetLayer())
                loop_track2.SetNetCode(track.GetNetCode())
                self.board.Add(loop_track2)
                serpentine_tracks.append(loop_track2)
                
                loop_track3 = pcbnew.TRACK(self.board)
                loop_track3.SetStart(loop_mid2)
                loop_track3.SetEnd(loop_end)
                loop_track3.SetWidth(track.GetWidth())
                loop_track3.SetLayer(track.GetLayer())
                loop_track3.SetNetCode(track.GetNetCode())
                self.board.Add(loop_track3)
                serpentine_tracks.append(loop_track3)
                
                current_pos = loop_end
            
            # Connect to original end
            final_track = pcbnew.TRACK(self.board)
            final_track.SetStart(current_pos)
            final_track.SetEnd(end_pos)
            final_track.SetWidth(track.GetWidth())
            final_track.SetLayer(track.GetLayer())
            final_track.SetNetCode(track.GetNetCode())
            self.board.Add(final_track)
            serpentine_tracks.append(final_track)
            
            # Remove original track
            self.board.Remove(track)
            
            # Update board connectivity
            self.board.BuildConnectivity()
            
            return RoutingResult(
                success=True,
                message=f"Applied serpentine routing with {num_segments} segments",
                routed_tracks=serpentine_tracks,
                warnings=[],
                errors=[],
                metrics={
                    "segments_added": num_segments,
                    "additional_length": additional_length
                }
            )
            
        except Exception as e:
            error_msg = f"Error applying serpentine routing: {str(e)}"
            self.logger.error(error_msg)
            return RoutingResult(
                success=False,
                message=error_msg,
                routed_tracks=[],
                warnings=[],
                errors=[error_msg]
            )

    def route_audio_signal(self, start: Tuple[float, float], end: Tuple[float, float], 
                          signal_type: SignalType = SignalType.AUDIO) -> bool:
        """Route an audio signal using KiCad's native router.
        
        Args:
            start: Start position (x, y) in mm
            end: End position (x, y) in mm
            signal_type: Type of signal to route
            
        Returns:
            True if routing was successful
        """
        try:
            # Get routing constraints
            constraints = self._routing_constraints[signal_type]
            
            # Convert positions to KiCad units (nm)
            start_nm = (int(start[0] * 1e6), int(start[1] * 1e6))
            end_nm = (int(end[0] * 1e6), int(end[1] * 1e6))
            
            # Create routing points
            start_point = pcbnew.VECTOR2I(start_nm[0], start_nm[1])
            end_point = pcbnew.VECTOR2I(end_nm[0], end_nm[1])
            
            # Get router
            router = pcbnew.ROUTER()
            router.SetBoard(self.board)
            
            # Set routing parameters from configuration
            router.SetMode(pcbnew.ROUTER_MODE_WALK)
            router.SetLayer(constraints.preferred_layer)
            router.SetWidth(int(constraints.min_width * 1e6))  # Convert to nm
            router.SetClearance(int(constraints.min_clearance * 1e6))  # Convert to nm
            
            # Route the track
            success = router.Route(start_point, end_point)
            
            if success:
                self.logger.info(f"Successfully routed {signal_type.value} signal from {start} to {end}")
            else:
                self.logger.warning(f"Failed to route {signal_type.value} signal from {start} to {end}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error routing audio signal: {str(e)}")
            return False

    def optimize_audio_routing(self) -> None:
        """Optimize audio signal routing using configuration settings."""
        try:
            # Get optimization settings from configuration
            opt_settings = self.config.get_optimization_settings()
            if not opt_settings:
                self.logger.warning("No optimization settings found, using defaults")
                return
            
            # Get all tracks
            tracks = self.board.GetTracks()
            
            # Group tracks by signal type
            audio_tracks = []
            power_tracks = []
            ground_tracks = []
            control_tracks = []
            
            for track in tracks:
                width = track.GetWidth() / 1e6  # Convert to mm
                
                if width >= 0.3:  # Audio signals typically use wider traces
                    audio_tracks.append(track)
                elif width >= 0.5:  # Power and ground typically use even wider traces
                    if track.GetNet().GetNetname().upper().startswith("GND"):
                        ground_tracks.append(track)
                    else:
                        power_tracks.append(track)
                else:
                    control_tracks.append(track)
            
            # Optimize tracks with retry logic
            max_attempts = opt_settings.max_reroute_attempts
            length_tolerance = opt_settings.length_tolerance
            
            # Optimize audio tracks
            for track in audio_tracks:
                if track.GetLength() / 1e6 > self._routing_constraints[SignalType.AUDIO].max_length + length_tolerance:
                    for attempt in range(max_attempts):
                        start = track.GetStart()
                        end = track.GetEnd()
                        if self.route_audio_signal(
                            (start.x/1e6, start.y/1e6),
                            (end.x/1e6, end.y/1e6),
                            SignalType.AUDIO
                        ):
                            break
                        else:
                            self.logger.debug(f"Reroute attempt {attempt + 1} failed for audio track")
            
            # Optimize power tracks
            for track in power_tracks:
                if track.GetLength() / 1e6 > self._routing_constraints[SignalType.POWER].max_length + length_tolerance:
                    for attempt in range(max_attempts):
                        start = track.GetStart()
                        end = track.GetEnd()
                        if self.route_audio_signal(
                            (start.x/1e6, start.y/1e6),
                            (end.x/1e6, end.y/1e6),
                            SignalType.POWER
                        ):
                            break
                        else:
                            self.logger.debug(f"Reroute attempt {attempt + 1} failed for power track")
            
            # Optimize ground tracks
            for track in ground_tracks:
                if track.GetLength() / 1e6 > self._routing_constraints[SignalType.GROUND].max_length + length_tolerance:
                    for attempt in range(max_attempts):
                        start = track.GetStart()
                        end = track.GetEnd()
                        if self.route_audio_signal(
                            (start.x/1e6, start.y/1e6),
                            (end.x/1e6, end.y/1e6),
                            SignalType.GROUND
                        ):
                            break
                        else:
                            self.logger.debug(f"Reroute attempt {attempt + 1} failed for ground track")
            
            self.logger.info("Audio routing optimization completed")
            
        except Exception as e:
            self.logger.error(f"Error optimizing audio routing: {str(e)}")
            raise

    def validate_routing(self) -> List[str]:
        """Validate audio routing against configuration constraints.
        
        Returns:
            List of validation messages
        """
        try:
            validation_messages = []
            
            # Get all tracks
            tracks = self.board.GetTracks()
            
            for track in tracks:
                if not track.IsTrack():
                    continue
                
                # Get track properties
                width = track.GetWidth() / 1e6  # Convert to mm
                length = track.GetLength() / 1e6  # Convert to mm
                net_name = track.GetNet().GetNetname()
                
                # Determine signal type
                signal_type = self._determine_signal_type(net_name, width)
                
                if signal_type in self._routing_constraints:
                    constraints = self._routing_constraints[signal_type]
                    
                    # Check width constraints
                    if width < constraints.min_width:
                        validation_messages.append(
                            f"Track '{net_name}' width {width:.3f}mm is below minimum {constraints.min_width}mm"
                        )
                    
                    # Check length constraints
                    if length > constraints.max_length:
                        validation_messages.append(
                            f"Track '{net_name}' length {length:.3f}mm exceeds maximum {constraints.max_length}mm"
                        )
                    
                    # Check layer constraints
                    if track.GetLayer() in constraints.avoid_layers:
                        validation_messages.append(
                            f"Track '{net_name}' is on avoided layer {track.GetLayer()}"
                        )
            
            # Check differential pair constraints
            diff_pair_issues = self._validate_differential_pairs()
            validation_messages.extend(diff_pair_issues)
            
            return validation_messages
            
        except Exception as e:
            self.logger.error(f"Error validating routing: {str(e)}")
            return [f"Routing validation error: {str(e)}"]
    
    def _determine_signal_type(self, net_name: str, width: float) -> SignalType:
        """Determine signal type based on net name and width.
        
        Args:
            net_name: Net name
            width: Track width in mm
            
        Returns:
            Signal type
        """
        net_name_upper = net_name.upper()
        
        if any(power_name in net_name_upper for power_name in ["VCC", "VDD", "POWER", "PWR"]):
            return SignalType.POWER
        elif any(ground_name in net_name_upper for ground_name in ["GND", "GROUND", "AGND", "DGND"]):
            return SignalType.GROUND
        elif any(audio_name in net_name_upper for audio_name in ["AUDIO", "IN", "OUT", "SIGNAL"]):
            return SignalType.AUDIO
        else:
            return SignalType.CONTROL
    
    def _validate_differential_pairs(self) -> List[str]:
        """Validate differential pair constraints.
        
        Returns:
            List of validation messages
        """
        validation_messages = []
        
        try:
            # Find differential pairs
            diff_pairs = self._identify_differential_pairs(self.board)
            
            for pair_name, pair_data in diff_pairs.items():
                # Find tracks for this pair
                tracks_p = [t for t in self.board.GetTracks() if t.GetNetname() == pair_data["net_p"]]
                tracks_n = [t for t in self.board.GetTracks() if t.GetNetname() == pair_data["net_n"]]
                
                if tracks_p and tracks_n:
                    track_p = tracks_p[0]
                    track_n = tracks_n[0]
                    
                    # Check width matching
                    width_p = track_p.GetWidth() / 1e6
                    width_n = track_n.GetWidth() / 1e6
                    width_diff = abs(width_p - width_n)
                    
                    if width_diff > self._diff_pair_config.max_width_mismatch:
                        validation_messages.append(
                            f"Differential pair '{pair_name}' width mismatch: {width_diff:.3f}mm (max {self._diff_pair_config.max_width_mismatch}mm)"
                        )
                    
                    # Check length matching
                    length_p = track_p.GetLength() / 1e6
                    length_n = track_n.GetLength() / 1e6
                    length_diff = abs(length_p - length_n)
                    
                    if length_diff > self._diff_pair_config.max_length_mismatch:
                        validation_messages.append(
                            f"Differential pair '{pair_name}' length mismatch: {length_diff:.3f}mm (max {self._diff_pair_config.max_length_mismatch}mm)"
                        )
                    
                    # Check spacing
                    spacing = self._calculate_track_spacing(track_p, track_n)
                    if spacing < self._diff_pair_config.spacing:
                        validation_messages.append(
                            f"Differential pair '{pair_name}' spacing {spacing:.3f}mm is below minimum {self._diff_pair_config.spacing}mm"
                        )
            
        except Exception as e:
            self.logger.error(f"Error validating differential pairs: {str(e)}")
            validation_messages.append(f"Differential pair validation error: {str(e)}")
        
        return validation_messages
    
    def _calculate_track_spacing(self, track1: pcbnew.TRACK, track2: pcbnew.TRACK) -> float:
        """Calculate spacing between two tracks.
        
        Args:
            track1: First track
            track2: Second track
            
        Returns:
            Spacing in mm
        """
        try:
            # Get track centerlines
            start1 = track1.GetStart()
            end1 = track1.GetEnd()
            start2 = track2.GetStart()
            end2 = track2.GetEnd()
            
            # Calculate minimum distance between line segments
            min_distance = float('inf')
            
            # Check distance between start points
            dist = math.sqrt((start1.x - start2.x)**2 + (start1.y - start2.y)**2) / 1e6
            min_distance = min(min_distance, dist)
            
            # Check distance between end points
            dist = math.sqrt((end1.x - end2.x)**2 + (end1.y - end2.y)**2) / 1e6
            min_distance = min(min_distance, dist)
            
            # Check distance between start1 and end2
            dist = math.sqrt((start1.x - end2.x)**2 + (start1.y - end2.y)**2) / 1e6
            min_distance = min(min_distance, dist)
            
            # Check distance between end1 and start2
            dist = math.sqrt((end1.x - start2.x)**2 + (end1.y - start2.y)**2) / 1e6
            min_distance = min(min_distance, dist)
            
            return min_distance
            
        except Exception as e:
            self.logger.error(f"Error calculating track spacing: {str(e)}")
            return 0.0

    def update_routing_constraints(self, signal_type: SignalType, constraints: RoutingConstraintItem) -> bool:
        """Update routing constraints for a signal type.
        
        Args:
            signal_type: Signal type to update
            constraints: New constraints
            
        Returns:
            True if update was successful
        """
        try:
            # Update configuration
            success = self.config.update_routing_constraints(signal_type, constraints)
            
            if success:
                # Reinitialize constraints
                self._routing_constraints = self._initialize_constraints()
                self.logger.info(f"Updated routing constraints for {signal_type.value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating routing constraints: {str(e)}")
            return False

    def update_optimization_settings(self, settings: OptimizationItem) -> bool:
        """Update optimization settings.
        
        Args:
            settings: New optimization settings
            
        Returns:
            True if update was successful
        """
        try:
            # Update configuration
            success = self.config.update_optimization_settings(settings)
            
            if success:
                self.logger.info("Updated optimization settings")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating optimization settings: {str(e)}")
            return False 
