"""Advanced PCB analysis using KiCad 9's native functionality."""
import logging
import math
import pcbnew
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from ..core.base.base_manager import BaseManager
from ..core.base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from ..config.analysis_manager_config import AnalysisManagerConfig
from ..audio.analysis.advanced_audio_analyzer import AdvancedAudioAnalyzer

if TYPE_CHECKING:
    from ..core.base.results.analysis_result import AnalysisResult as BaseAnalysisResult

class AnalysisType(Enum):
    """Types of PCB analysis."""
    SIGNAL_INTEGRITY = "signal_integrity"
    THERMAL = "thermal"
    EMI = "emi"
    POWER_DISTRIBUTION = "power_distribution"
    AUDIO_PERFORMANCE = "audio_performance"
    ADVANCED_AUDIO = "advanced_audio"

@dataclass
class AnalysisResult:
    """Results from PCB analysis."""
    type: AnalysisType
    severity: str  # "error", "warning", "info"
    message: str
    location: Optional[Tuple[float, float]] = None  # (x, y) in mm
    component: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None

class AnalysisManager(BaseManager[AnalysisResult]):
    """Manages PCB analysis using KiCad 9's native functionality."""
    
    def __init__(self, board: pcbnew.BOARD, logger: Optional[logging.Logger] = None, config: Optional[AnalysisManagerConfig] = None):
        """Initialize the analysis manager.
        
        Args:
            board: KiCad board object
            logger: Optional logger instance
            config: Optional analysis manager configuration
        """
        super().__init__()
        self.board = board
        self.logger = logger or logging.getLogger(__name__)
        self._validate_kicad_version()
        self._analysis_results: List[AnalysisResult] = []
        self.config = config or AnalysisManagerConfig()
        # Load config sections
        self.signal_config = self.config.get_signal_integrity_config() or None
        self.thermal_config = self.config.get_thermal_config() or None
        self.emi_config = self.config.get_emi_config() or None
        self.power_config = self.config.get_power_distribution_config() or None
        self.audio_config = self.config.get_audio_performance_config() or None
        self.units_config = self.config.get_units_config() or None
        
        # Performance optimization: Cache board data
        self._cached_tracks = None
        self._cached_footprints = None
        self._cached_tracks_by_layer = None
        self._cached_power_tracks = None
        self._cached_audio_tracks = None
        self._cache_timestamp = 0
        
        # Advanced analyzer is optional to prevent KiCad import errors in headless CI
        try:
            from ..audio.components.stability import StabilityManager
            self._advanced_analyzer = AdvancedAudioAnalyzer(board, stability_manager=None, logger=self.logger)
        except Exception:
            self._advanced_analyzer = None
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        version = pcbnew.Version()
        if not version.startswith('9'):
            raise RuntimeError(f"This module requires KiCad 9.x, but found version {version}")
        self.logger.info(f"Running with KiCad version: {version}")
    
    def _get_cached_tracks(self) -> List:
        """Get cached tracks or fetch from board if cache is invalid."""
        if self._cached_tracks is None:
            self._cached_tracks = self.board.GetTracks()
        return self._cached_tracks
    
    def _get_cached_footprints(self) -> List:
        """Get cached footprints or fetch from board if cache is invalid."""
        if self._cached_footprints is None:
            self._cached_footprints = self.board.GetFootprints()
        return self._cached_footprints
    
    def _get_cached_tracks_by_layer(self) -> Dict:
        """Get cached tracks grouped by layer or create if not cached."""
        if self._cached_tracks_by_layer is None:
            tracks = self._get_cached_tracks()
            self._cached_tracks_by_layer = {}
            for track in tracks:
                layer = track.GetLayer()
                if layer not in self._cached_tracks_by_layer:
                    self._cached_tracks_by_layer[layer] = []
                self._cached_tracks_by_layer[layer].append(track)
        return self._cached_tracks_by_layer
    
    def _get_cached_power_tracks(self) -> List:
        """Get cached power tracks or filter if not cached."""
        if self._cached_power_tracks is None:
            tracks = self._get_cached_tracks()
            self._cached_power_tracks = []
            for track in tracks:
                net_name = track.GetNet().GetNetname()
                if net_name.startswith(("VCC", "VDD", "VSS", "GND")):
                    self._cached_power_tracks.append(track)
        return self._cached_power_tracks
    
    def _get_cached_audio_tracks(self) -> List:
        """Get cached audio tracks or filter if not cached."""
        if self._cached_audio_tracks is None:
            tracks = self._get_cached_tracks()
            self._cached_audio_tracks = []
            for track in tracks:
                net_name = track.GetNet().GetNetname()
                if net_name.startswith(("AUDIO", "IN", "OUT")):
                    self._cached_audio_tracks.append(track)
        return self._cached_audio_tracks
    
    def _clear_cache(self) -> None:
        """Clear all caches when board data changes."""
        self._cached_tracks = None
        self._cached_footprints = None
        self._cached_tracks_by_layer = None
        self._cached_power_tracks = None
        self._cached_audio_tracks = None
        self._cache_timestamp = 0
        super()._clear_cache()
    
    def analyze_signal_integrity(self) -> List[AnalysisResult]:
        """Analyze signal integrity of the PCB.
        
        Returns:
            List of analysis results
        """
        results = []
        
        try:
            # Get all tracks once
            tracks = self._get_cached_tracks()
            
            # Analyze each track with cached properties
            for track in tracks:
                # Cache track properties to avoid repeated API calls
                width = track.GetWidth() / 1e6  # Convert to mm
                length = track.GetLength() / 1e6  # Convert to mm
                start_pos = track.GetStart()
                start_x, start_y = start_pos.x / 1e6, start_pos.y / 1e6
                
                # Check track width
                if width < self.signal_config.min_width:
                    results.append(AnalysisResult(
                        type=AnalysisType.SIGNAL_INTEGRITY,
                        severity="warning",
                        message=f"Track width {width:.2f}mm is below recommended minimum",
                        location=(start_x, start_y),
                        value=width,
                        unit="mm"
                    ))
                
                # Check track length
                if length > self.signal_config.max_length:
                    results.append(AnalysisResult(
                        type=AnalysisType.SIGNAL_INTEGRITY,
                        severity="warning",
                        message=f"Track length {length:.2f}mm exceeds recommended maximum",
                        location=(start_x, start_y),
                        value=length,
                        unit="mm"
                    ))
                
                # Check for sharp angles (only for straight tracks)
                if track.GetShape() == pcbnew.SEG:
                    end_pos = track.GetEnd()
                    angle = abs(math.atan2(end_pos.y - start_pos.y, end_pos.x - start_pos.x) * 180 / math.pi)
                    if angle > self.signal_config.max_angle:
                        results.append(AnalysisResult(
                            type=AnalysisType.SIGNAL_INTEGRITY,
                            severity="warning",
                            message=f"Track has sharp angle of {angle:.1f} degrees",
                            location=(start_x, start_y),
                            value=angle,
                            unit="degrees"
                        ))
            
        except (AttributeError, TypeError) as e:
            self.logger.error(f"Error accessing track properties: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.SIGNAL_INTEGRITY,
                severity="error",
                message=f"Error accessing track properties: {str(e)}"
            ))
        except RuntimeError as e:
            self.logger.error(f"Runtime error during signal integrity analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.SIGNAL_INTEGRITY,
                severity="error",
                message=f"Runtime error during signal integrity analysis: {str(e)}"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error during signal integrity analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.SIGNAL_INTEGRITY,
                severity="error",
                message=f"Unexpected error during signal integrity analysis: {str(e)}"
            ))
        
        return results
    
    def analyze_thermal(self) -> List[AnalysisResult]:
        """Analyze thermal characteristics of the PCB.
        
        Returns:
            List of analysis results
        """
        results = []
        
        try:
            # Get all footprints once
            footprints = self._get_cached_footprints()
            
            # Pre-calculate footprint positions for spatial analysis
            footprint_positions = []
            for footprint in footprints:
                pos = footprint.GetPosition()
                footprint_positions.append({
                    'footprint': footprint,
                    'x': pos.x / 1e6,
                    'y': pos.y / 1e6,
                    'ref': footprint.GetReference()
                })
            
            # Analyze each component with optimized spatial queries
            for fp_data in footprint_positions:
                footprint = fp_data['footprint']
                
                # Check for thermal pads (cached pad analysis)
                has_thermal_pad = False
                for pad in footprint.Pads():
                    if pad.GetSize().x >= 2e6:  # 2mm thermal pad
                        has_thermal_pad = True
                        break
                
                if not has_thermal_pad and footprint.GetReference().startswith(("U", "Q", "VR")):
                    results.append(AnalysisResult(
                        type=AnalysisType.THERMAL,
                        severity="warning",
                        message=f"Component {footprint.GetReference()} may need thermal pad",
                        location=(fp_data['x'], fp_data['y']),
                        component=footprint.GetReference()
                    ))
                
                # Optimized component density check using spatial indexing
                nearby_components = 0
                search_radius = 5.0  # 5mm radius
                search_radius_sq = search_radius * search_radius
                
                for other_fp_data in footprint_positions:
                    if other_fp_data['footprint'] == footprint:
                        continue
                    
                    # Use squared distance to avoid square root calculation
                    dx = fp_data['x'] - other_fp_data['x']
                    dy = fp_data['y'] - other_fp_data['y']
                    distance_sq = dx * dx + dy * dy
                    
                    if distance_sq < search_radius_sq:
                        nearby_components += 1
                
                if nearby_components > 3:
                    results.append(AnalysisResult(
                        type=AnalysisType.THERMAL,
                        severity="warning",
                        message=f"High component density around {footprint.GetReference()}",
                        location=(fp_data['x'], fp_data['y']),
                        component=footprint.GetReference(),
                        value=nearby_components,
                        unit="components"
                    ))
            
        except (AttributeError, TypeError) as e:
            self.logger.error(f"Error accessing footprint properties: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.THERMAL,
                severity="error",
                message=f"Error accessing footprint properties: {str(e)}"
            ))
        except RuntimeError as e:
            self.logger.error(f"Runtime error during thermal analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.THERMAL,
                severity="error",
                message=f"Runtime error during thermal analysis: {str(e)}"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error during thermal analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.THERMAL,
                severity="error",
                message=f"Unexpected error during thermal analysis: {str(e)}"
            ))
        
        return results
    
    def analyze_emi(self) -> List[AnalysisResult]:
        """Analyze EMI characteristics of the PCB.
        
        Returns:
            List of analysis results
        """
        results = []
        
        try:
            # Get cached tracks by layer for efficient parallel detection
            tracks_by_layer = self._get_cached_tracks_by_layer()
            tracks = self._get_cached_tracks()
            
            # Analyze each track with optimized parallel detection
            for track in tracks:
                # Cache track properties
                length = track.GetLength() / 1e6  # Convert to mm
                start_pos = track.GetStart()
                start_x, start_y = start_pos.x / 1e6, start_pos.y / 1e6
                layer = track.GetLayer()
                
                # Check for long parallel tracks (only check tracks on same layer)
                if length > 50:  # Only check if track is long enough to be problematic
                    parallel_tracks = 0
                    layer_tracks = tracks_by_layer.get(layer, [])
                    
                    for other_track in layer_tracks:
                        if other_track == track:
                            continue
                        
                        # Quick check: only analyze if other track is also long
                        if other_track.GetLength() / 1e6 > 25:  # Minimum length for parallel analysis
                            if track.IsParallel(other_track):
                                parallel_tracks += 1
                    
                    if parallel_tracks > 0:
                        results.append(AnalysisResult(
                            type=AnalysisType.EMI,
                            severity="warning",
                            message=f"Long parallel tracks may cause EMI issues",
                            location=(start_x, start_y),
                            value=length,
                            unit="mm"
                        ))
                
                # Check for sharp corners (only for straight tracks)
                if track.GetShape() == pcbnew.SEG:
                    end_pos = track.GetEnd()
                    angle = abs(math.atan2(end_pos.y - start_pos.y, end_pos.x - start_pos.x) * 180 / math.pi)
                    if angle > 45:  # Maximum angle for good EMI
                        results.append(AnalysisResult(
                            type=AnalysisType.EMI,
                            severity="warning",
                            message=f"Sharp corner may cause EMI issues",
                            location=(start_x, start_y),
                            value=angle,
                            unit="degrees"
                        ))
            
        except (AttributeError, TypeError) as e:
            self.logger.error(f"Error accessing track properties during EMI analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.EMI,
                severity="error",
                message=f"Error accessing track properties during EMI analysis: {str(e)}"
            ))
        except RuntimeError as e:
            self.logger.error(f"Runtime error during EMI analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.EMI,
                severity="error",
                message=f"Runtime error during EMI analysis: {str(e)}"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error during EMI analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.EMI,
                severity="error",
                message=f"Error analyzing EMI characteristics: {str(e)}"
            ))
        
        return results
    
    def analyze_power_distribution(self) -> List[AnalysisResult]:
        """Analyze power distribution of the PCB.
        
        Returns:
            List of analysis results
        """
        results = []
        
        try:
            # Get cached power tracks for efficiency
            power_tracks = self._get_cached_power_tracks()
            
            # Analyze power tracks with cached properties
            for track in power_tracks:
                # Cache track properties
                width = track.GetWidth() / 1e6  # Convert to mm
                length = track.GetLength() / 1e6  # Convert to mm
                start_pos = track.GetStart()
                start_x, start_y = start_pos.x / 1e6, start_pos.y / 1e6
                
                # Check track width
                if width < self.power_config.min_width:
                    results.append(AnalysisResult(
                        type=AnalysisType.POWER_DISTRIBUTION,
                        severity="warning",
                        message=f"Power track width {width:.2f}mm is below recommended minimum",
                        location=(start_x, start_y),
                        value=width,
                        unit="mm"
                    ))
                
                # Check track length
                if length > self.power_config.max_length:
                    results.append(AnalysisResult(
                        type=AnalysisType.POWER_DISTRIBUTION,
                        severity="warning",
                        message=f"Power track length {length:.2f}mm exceeds recommended maximum",
                        location=(start_x, start_y),
                        value=length,
                        unit="mm"
                    ))
            
        except (AttributeError, TypeError) as e:
            self.logger.error(f"Error accessing track properties during power analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.POWER_DISTRIBUTION,
                severity="error",
                message=f"Error accessing track properties during power analysis: {str(e)}"
            ))
        except RuntimeError as e:
            self.logger.error(f"Runtime error during power distribution analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.POWER_DISTRIBUTION,
                severity="error",
                message=f"Runtime error during power distribution analysis: {str(e)}"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error during power distribution analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.POWER_DISTRIBUTION,
                severity="error",
                message=f"Unexpected error during power distribution analysis: {str(e)}"
            ))
        
        return results
    
    def analyze_audio_performance(self) -> List[AnalysisResult]:
        """Analyze audio performance characteristics of the PCB.
        
        Returns:
            List of analysis results
        """
        results = []
        
        try:
            # Get cached audio tracks for efficiency
            audio_tracks = self._get_cached_audio_tracks()
            
            # Analyze audio tracks with cached properties
            for track in audio_tracks:
                # Cache track properties to avoid repeated API calls
                width = track.GetWidth() / 1e6  # Convert to mm
                length = track.GetLength() / 1e6  # Convert to mm
                start_pos = track.GetStart()
                start_x, start_y = start_pos.x / 1e6, start_pos.y / 1e6
                
                # Check track width
                if width < self.audio_config.min_width:
                    results.append(AnalysisResult(
                        type=AnalysisType.AUDIO_PERFORMANCE,
                        severity="warning",
                        message=f"Audio track width {width:.2f}mm is below recommended minimum",
                        location=(start_x, start_y),
                        value=width,
                        unit="mm"
                    ))
                
                # Check track length
                if length > self.audio_config.max_length:
                    results.append(AnalysisResult(
                        type=AnalysisType.AUDIO_PERFORMANCE,
                        severity="warning",
                        message=f"Audio track length {length:.2f}mm exceeds recommended maximum",
                        location=(start_x, start_y),
                        value=length,
                        unit="mm"
                    ))
                
                # Check for sharp corners (only for straight tracks)
                if track.GetShape() == pcbnew.SEG:
                    end_pos = track.GetEnd()
                    angle = abs(math.atan2(end_pos.y - start_pos.y, end_pos.x - start_pos.x) * 180 / math.pi)
                    if angle > self.audio_config.max_angle:
                        results.append(AnalysisResult(
                            type=AnalysisType.AUDIO_PERFORMANCE,
                            severity="warning",
                            message=f"Sharp corner may affect audio performance",
                            location=(start_x, start_y),
                            value=angle,
                            unit="degrees"
                        ))
            
        except (AttributeError, TypeError) as e:
            self.logger.error(f"Error accessing track properties during audio analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.AUDIO_PERFORMANCE,
                severity="error",
                message=f"Error accessing track properties during audio analysis: {str(e)}"
            ))
        except RuntimeError as e:
            self.logger.error(f"Runtime error during audio performance analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.AUDIO_PERFORMANCE,
                severity="error",
                message=f"Runtime error during audio performance analysis: {str(e)}"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error during audio performance analysis: {str(e)}")
            results.append(AnalysisResult(
                type=AnalysisType.AUDIO_PERFORMANCE,
                severity="error",
                message=f"Unexpected error during audio performance analysis: {str(e)}"
            ))
        
        return results
    
    def run_all_analysis(self) -> Dict[AnalysisType, List[AnalysisResult]]:
        """Run all analysis types.
        
        Returns:
            Dictionary of analysis results by type
        """
        results: Dict[AnalysisType, List[AnalysisResult]] = {
            AnalysisType.SIGNAL_INTEGRITY: self.analyze_signal_integrity(),
            AnalysisType.THERMAL: self.analyze_thermal(),
            AnalysisType.EMI: self.analyze_emi(),
            AnalysisType.POWER_DISTRIBUTION: self.analyze_power_distribution(),
            AnalysisType.AUDIO_PERFORMANCE: self.analyze_audio_performance()
        }
        
        # Append advanced audio metrics as pseudo-analysis results for unified reporting
        if self._advanced_analyzer is not None:
            adv = self._advanced_analyzer.run_all_advanced()

            # Flatten into AnalysisResult stubs for consistency
            results[AnalysisType.ADVANCED_AUDIO] = [
                AnalysisResult(
                    type=AnalysisType.ADVANCED_AUDIO,
                    severity="info",
                    message="THD+N estimate",
                    value=adv["thd_plus_n"].thd_plus_n,
                    unit="%",
                ),
                AnalysisResult(
                    type=AnalysisType.ADVANCED_AUDIO,
                    severity="info",
                    message="Frequency response deviation",
                    value=adv["frequency_response"].deviation_db,
                    unit="dB",
                ),
                AnalysisResult(
                    type=AnalysisType.ADVANCED_AUDIO,
                    severity="info",
                    message="Microphonic coupling score",
                    value=adv["microphonic_coupling"].coupling_score,
                    unit="score",
                    component=adv["microphonic_coupling"].worst_offender_ref,
                ),
                AnalysisResult(
                    type=AnalysisType.ADVANCED_AUDIO,
                    severity="info",
                    message="Group delay variation",
                    value=adv["group_delay"].group_delay_variation,
                    unit="μs",
                ),
                AnalysisResult(
                    type=AnalysisType.ADVANCED_AUDIO,
                    severity="info",
                    message="Intermodulation distortion",
                    value=adv["intermodulation_distortion"].imd_total,
                    unit="%",
                ),
                AnalysisResult(
                    type=AnalysisType.ADVANCED_AUDIO,
                    severity="info",
                    message="Dynamic range",
                    value=adv["dynamic_range"].dynamic_range,
                    unit="dB",
                ),
            ]
        
        self._analysis_results = [r for results_list in results.values() for r in results_list]
        return results
    
    def _validate_data(self, data: AnalysisResult) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.type:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Analysis type is required",
                    errors=["Analysis type cannot be empty"]
                )
            
            if not data.message:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Analysis message is required",
                    errors=["Analysis message cannot be empty"]
                )
            
            if data.severity not in ["error", "warning", "info"]:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid severity level",
                    errors=["Severity must be 'error', 'warning', or 'info'"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Analysis result validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Analysis result validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Remove an analysis result from the internal store and clear caches.

        Args:
            key: Analysis result key to clean up
        """
        if key in self._items:
            del self._items[key]
            self.logger.debug("Removed analysis result %s", key)
            self._clear_cache()
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache and update analysis results
        super()._clear_cache()
        # Update the analysis results list with current items
        self._analysis_results = list(self._items.values()) 
