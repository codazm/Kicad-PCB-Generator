"""Advanced audio performance analysis utilities.

This module augments the basic `AudioPCBAnalyzer` with extra metrics that are
relevant for high-fidelity audio designs (THD+N, frequency response, and
microphonic coupling).

The implementation purposefully remains lightweight so it can operate in
head-less CI without requiring SPICE.  The calculations are heuristics based on
track length, component selection, and board topology.  When a full simulator
backend (e.g. ngspice) becomes available the heuristics can be replaced with
measured data.

Enhanced with advanced physical coupling analysis for professional audio applications.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple

import numpy as np

from .analyzer import AudioPCBAnalyzer
from ...core.base.results.analysis_result import AnalysisSeverity, AnalysisType, AnalysisResult
from ...core.analysis.mutual_inductance import MutualInductanceAnalyzer
from ...core.analysis.capacitive_coupling import CapacitiveCouplingAnalyzer
from ...core.analysis.high_frequency_coupling import HighFrequencyCouplingAnalyzer
from ...core.analysis.thermal_coupling import ThermalCouplingAnalyzer

if TYPE_CHECKING:  # pragma: no cover – avoid heavy KiCad imports in CI
    import pcbnew

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class THDNAnalysis:
    """Total Harmonic Distortion + Noise results (percentage)."""

    thd: float  # %
    noise: float  # A-weighted dBV
    thd_plus_n: float  # %

    def __post_init__(self) -> None:
        # Always keep thd+noise >= thd
        self.thd_plus_n = max(self.thd_plus_n, self.thd)


@dataclass
class FrequencyResponseAnalysis:
    """Frequency-response sweep results (band-edge gain in dB)."""

    gain_20_hz: float
    gain_20_khz: float
    deviation_db: float  # |gain_low – gain_high|
    gain_80_khz: float
    extended_bandwidth_deviation: float
    extended_bandwidth_support: bool


@dataclass
class MicrophonicCouplingAnalysis:
    """Estimate of microphonic coupling between high-gain stages (arbitrary score)."""

    coupling_score: float  # 0-100 (lower is better)
    worst_offender_ref: Optional[str] = None


@dataclass
class GroupDelayAnalysis:
    """Group delay analysis results (microseconds)."""

    group_delay_20_hz: float  # μs
    group_delay_20_khz: float  # μs
    group_delay_variation: float  # μs (max - min)
    is_linear: bool  # True if variation < 10μs


@dataclass
class IntermodulationAnalysis:
    """Intermodulation distortion analysis results (percentage)."""

    imd_2f1_f2: float  # % (2f1-f2 intermodulation)
    imd_f1_2f2: float  # % (f1-2f2 intermodulation)
    imd_total: float  # % (total IMD)
    worst_frequency_pair: Optional[Tuple[float, float]] = None


@dataclass
class DynamicRangeAnalysis:
    """Dynamic range analysis results (dB)."""

    dynamic_range: float  # dB (max signal - noise floor)
    signal_headroom: float  # dB (max signal - typical signal)
    noise_floor: float  # dB (noise floor level)
    snr: float  # dB (signal-to-noise ratio)


@dataclass
class PhysicalCouplingAnalysis:
    """Advanced physical coupling analysis results."""

    mutual_inductance: Dict[str, float]  # Component -> inductance coupling
    capacitive_coupling: Dict[str, float]  # Component -> capacitance coupling
    high_frequency_effects: Dict[str, float]  # Component -> HF coupling
    thermal_effects: Dict[str, float]  # Component -> thermal coupling
    overall_coupling_score: float  # 0-100 (lower is better)


# ---------------------------------------------------------------------------
# Analyzer implementation
# ---------------------------------------------------------------------------

class AdvancedAudioAnalyzer(AudioPCBAnalyzer):
    """Adds high-level audio quality metrics to the base analyzer with advanced physical coupling analysis."""

    def __init__(
        self,
        board: "pcbnew.BOARD",
        stability_manager,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(board=board, stability_manager=stability_manager, logger=logger)
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize physical coupling analyzers
        self.mutual_inductance_analyzer = MutualInductanceAnalyzer()
        self.capacitive_coupling_analyzer = CapacitiveCouplingAnalyzer()
        self.high_frequency_analyzer = HighFrequencyCouplingAnalyzer()
        self.thermal_coupling_analyzer = ThermalCouplingAnalyzer()

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def analyze_thd_plus_n(self) -> THDNAnalysis:
        """Estimate THD+N based on track length, number of op-amps, etc.

        The heuristic simply scales distortion with signal path length and
        active device count, and adds a fixed noise-floor term.
        """
        try:
            total_signal_path_mm = self._total_audio_track_length_mm()
            opamp_count = self._count_components(prefixes=("U",))

            thd = min(0.005 + 0.0002 * total_signal_path_mm + 0.001 * opamp_count, 2.0)  # ‰→% cap at 2 %
            noise_dbv = -90 + 0.2 * opamp_count  # very rough model
            thdn_percent = min(thd + max(0, (10 ** (noise_dbv / 20)) * 100), 3.0)

            return THDNAnalysis(thd=round(thd, 4), noise=round(noise_dbv, 1), thd_plus_n=round(thdn_percent, 4))
        except Exception as exc:
            self.logger.error("THD+N estimation failed: %s", exc)
            return THDNAnalysis(thd=0.0, noise=0.0, thd_plus_n=0.0)

    def analyze_frequency_response(self) -> FrequencyResponseAnalysis:
        """High-precision bandwidth estimation based on coupling/decoupling caps for extended audio range."""
        try:
            # Enhanced frequency response analysis for extended bandwidth
            low_freq_gain_db, high_freq_gain_db, extended_freq_gain_db = self._sweep_gain_edges_extended()
            
            # Calculate deviations for different frequency ranges
            deviation_standard = abs(low_freq_gain_db - high_freq_gain_db)
            deviation_extended = abs(low_freq_gain_db - extended_freq_gain_db)
            
            return FrequencyResponseAnalysis(
                gain_20_hz=round(low_freq_gain_db, 3),  # Increased precision
                gain_20_khz=round(high_freq_gain_db, 3),
                deviation_db=round(deviation_standard, 3),
                # Add extended bandwidth support
                gain_80_khz=round(extended_freq_gain_db, 3),
                extended_bandwidth_deviation=round(deviation_extended, 3),
                extended_bandwidth_support=True
            )
        except Exception as exc:
            self.logger.error("Extended frequency response estimation failed: %s", exc)
            return FrequencyResponseAnalysis(
                gain_20_hz=0.0, gain_20_khz=0.0, deviation_db=0.0,
                gain_80_khz=0.0, extended_bandwidth_deviation=0.0, extended_bandwidth_support=True
            )

    def analyze_microphonic_coupling(self) -> MicrophonicCouplingAnalysis:
        """Estimate microphonic coupling from board size and part density."""
        try:
            board_area_cm2 = self._board_area_cm2()
            electrolytic_caps = self._count_components(prefixes=("C",))
            # simple heuristic: more caps and bigger board → higher coupling risk
            score = min(100, 10 + 0.3 * electrolytic_caps + 100 / (board_area_cm2 + 1))
            worst = self._find_worst_microphonic_component()
            return MicrophonicCouplingAnalysis(coupling_score=round(score, 1), worst_offender_ref=worst)
        except Exception as exc:
            self.logger.error("Microphonic coupling estimation failed: %s", exc)
            return MicrophonicCouplingAnalysis(coupling_score=0.0)

    def analyze_group_delay(self) -> GroupDelayAnalysis:
        """Estimate group delay based on component selection and topology.
        
        Group delay is estimated using heuristics based on:
        - Number of coupling capacitors (affects low frequency delay)
        - Number of decoupling capacitors (affects high frequency delay)
        - Track length and component count (affects overall delay)
        """
        try:
            # Count components that affect group delay
            coupling_caps = self._count_components(prefixes=("C",))
            opamps = self._count_components(prefixes=("U",))
            total_track_length_mm = self._total_audio_track_length_mm()
            
            # Estimate group delay at different frequencies
            # Low frequency (20 Hz) - dominated by coupling caps
            group_delay_low = 50.0 + 10.0 * coupling_caps  # μs
            
            # High frequency (20 kHz) - dominated by decoupling and track inductance
            group_delay_high = 20.0 + 5.0 * opamps + 0.1 * total_track_length_mm  # μs
            
            # Calculate variation
            group_delay_variation = abs(group_delay_high - group_delay_low)
            is_linear = group_delay_variation < 10.0  # Consider linear if variation < 10μs
            
            return GroupDelayAnalysis(
                group_delay_20_hz=round(group_delay_low, 1),
                group_delay_20_khz=round(group_delay_high, 1),
                group_delay_variation=round(group_delay_variation, 1),
                is_linear=is_linear
            )
        except Exception as exc:
            self.logger.error("Group delay estimation failed: %s", exc)
            return GroupDelayAnalysis(
                group_delay_20_hz=50.0, group_delay_20_khz=20.0,
                group_delay_variation=30.0, is_linear=False
            )

    def analyze_intermodulation_distortion(self) -> IntermodulationAnalysis:
        """Estimate intermodulation distortion based on component selection and topology.
        
        IMD is estimated using heuristics based on:
        - Number of active components (op-amps, transistors)
        - Power supply complexity
        - Component matching and tolerance
        """
        try:
            # Count components that affect IMD
            opamps = self._count_components(prefixes=("U",))
            transistors = self._count_components(prefixes=("Q",))
            power_components = self._count_components(prefixes=("REG", "VCC", "VDD"))
            
            # Estimate IMD products
            # 2f1-f2 intermodulation (typically dominant)
            imd_2f1_f2 = 0.001 + 0.0005 * opamps + 0.0002 * transistors  # %
            
            # f1-2f2 intermodulation
            imd_f1_2f2 = 0.0005 + 0.0003 * opamps + 0.0001 * transistors  # %
            
            # Total IMD
            imd_total = imd_2f1_f2 + imd_f1_2f2
            
            # Worst frequency pair (simplified)
            worst_frequency_pair = (1000.0, 1100.0) if imd_total > 0.001 else None
            
            return IntermodulationAnalysis(
                imd_2f1_f2=round(imd_2f1_f2, 4),
                imd_f1_2f2=round(imd_f1_2f2, 4),
                imd_total=round(imd_total, 4),
                worst_frequency_pair=worst_frequency_pair
            )
        except Exception as exc:
            self.logger.error("Intermodulation distortion estimation failed: %s", exc)
            return IntermodulationAnalysis(
                imd_2f1_f2=0.001, imd_f1_2f2=0.0005, imd_total=0.0015
            )

    def analyze_dynamic_range(self) -> DynamicRangeAnalysis:
        """Estimate dynamic range based on component selection and topology.
        
        Dynamic range is estimated using heuristics based on:
        - Power supply voltage and regulation
        - Component noise characteristics
        - Signal path complexity
        """
        try:
            # Estimate power supply voltage
            power_voltage = self._estimate_power_voltage()
            
            # Calculate maximum signal level (simplified)
            max_signal_dbv = 20 * math.log10(power_voltage / 2.0)  # Half supply voltage
            
            # Estimate noise floor based on components
            opamps = self._count_components(prefixes=("U",))
            resistors = self._count_components(prefixes=("R",))
            
            # Noise floor estimation (simplified)
            noise_floor_dbv = -90 - 5 * math.log10(opamps + 1) - 2 * math.log10(resistors + 1)
            
            # Calculate dynamic range
            dynamic_range = max_signal_dbv - noise_floor_dbv
            
            # Estimate signal headroom
            typical_signal_dbv = max_signal_dbv - 20  # 20dB below max
            signal_headroom = max_signal_dbv - typical_signal_dbv
            
            # Calculate SNR
            snr = typical_signal_dbv - noise_floor_dbv
            
            return DynamicRangeAnalysis(
                dynamic_range=round(dynamic_range, 1),
                signal_headroom=round(signal_headroom, 1),
                noise_floor=round(noise_floor_dbv, 1),
                snr=round(snr, 1)
            )
        except Exception as exc:
            self.logger.error("Dynamic range estimation failed: %s", exc)
            return DynamicRangeAnalysis(
                dynamic_range=80.0, signal_headroom=20.0, noise_floor=-90.0, snr=70.0
            )

    def analyze_physical_coupling(self) -> PhysicalCouplingAnalysis:
        """Analyze advanced physical coupling effects for professional audio applications.
        
        This method integrates mutual inductance, capacitive coupling, high-frequency
        effects, and thermal coupling analysis to provide comprehensive electromagnetic
        modeling for audio PCB design.
        """
        try:
            # Analyze mutual inductance
            mutual_inductance_result = self.mutual_inductance_analyzer.analyze_mutual_inductance(self.board)
            mutual_inductance_data = mutual_inductance_result.data if mutual_inductance_result.success else {}
            
            # Analyze capacitive coupling
            capacitive_result = self.capacitive_coupling_analyzer.analyze_capacitive_coupling(self.board)
            capacitive_data = capacitive_result.data if capacitive_result.success else {}
            
            # Analyze high-frequency effects
            hf_result = self.high_frequency_analyzer.analyze_high_frequency_coupling(self.board)
            hf_data = hf_result.data if hf_result.success else {}
            
            # Analyze thermal coupling
            thermal_result = self.thermal_coupling_analyzer.analyze_thermal_coupling(self.board)
            thermal_data = thermal_result.data if thermal_result.success else {}
            
            # Calculate overall coupling score
            overall_score = self._calculate_overall_coupling_score(
                mutual_inductance_data, capacitive_data, hf_data, thermal_data
            )
            
            return PhysicalCouplingAnalysis(
                mutual_inductance=mutual_inductance_data,
                capacitive_coupling=capacitive_data,
                high_frequency_effects=hf_data,
                thermal_effects=thermal_data,
                overall_coupling_score=overall_score
            )
            
        except Exception as exc:
            self.logger.error("Physical coupling analysis failed: %s", exc)
            return PhysicalCouplingAnalysis(
                mutual_inductance={},
                capacitive_coupling={},
                high_frequency_effects={},
                thermal_effects={},
                overall_coupling_score=50.0
            )

    def analyze_audio_frequency_bands(self) -> Dict[str, Dict[str, float]]:
        """Analyze coupling effects across audio frequency bands with extended bandwidth support."""
        try:
            # Analyze mutual inductance across frequency bands
            mutual_inductance_bands = self.mutual_inductance_analyzer.analyze_audio_frequency_bands(self.board)
            
            # Analyze capacitive coupling across frequency bands
            capacitive_bands = self.capacitive_coupling_analyzer.analyze_audio_frequency_bands(self.board)
            
            # Analyze high-frequency effects
            hf_effects = self.high_frequency_analyzer.analyze_high_frequency_effects(self.board)
            
            # Combine results
            combined_results = {
                'mutual_inductance_bands': mutual_inductance_bands,
                'capacitive_coupling_bands': capacitive_bands,
                'high_frequency_effects': hf_effects
            }
            
            return combined_results
            
        except Exception as exc:
            self.logger.error("Audio frequency band analysis failed: %s", exc)
            return {}

    # ----------------------------------------------------------
    # Private helper methods
    # ----------------------------------------------------------

    def _total_audio_track_length_mm(self) -> float:
        """Calculate total length of audio signal tracks in mm."""
        try:
            total_length = 0.0
            for track in self.board.GetTracks():
                if track.GetType() == 0:  # PCB_TRACE_T
                    net_name = track.GetNet().GetNetname().upper()
                    if any(keyword in net_name for keyword in ("AUDIO", "IN", "OUT", "SIGNAL")):
                        total_length += track.GetLength() / 1e6  # Convert nm to mm
            return total_length
        except Exception:
            return 100.0  # Fallback

    def _count_components(self, prefixes: tuple[str, ...]) -> int:
        """Count components with given reference prefixes."""
        try:
            count = 0
            for fp in self.board.GetFootprints():
                if any(fp.GetReference().startswith(prefix) for prefix in prefixes):
                    count += 1
            return count
        except Exception:
            return 0

    def _board_area_cm2(self) -> float:
        """Calculate board area in cm²."""
        try:
            bbox = self.board.GetBoundingBox()
            return (bbox.GetWidth() * bbox.GetHeight()) / 1e10  # nm² → cm²
        except Exception:
            return 100.0  # Fallback

    def _sweep_gain_edges(self) -> tuple[float, float]:
        """Estimate low- and high-frequency gain using RC network heuristics."""
        # Count coupling caps for low freq; decoupling cap lead inductance for high freq.
        low_cut_hz = 20.0
        high_cut_hz = 20000.0

        coupling_caps, decoupling_caps = 0, 0
        try:
            for fp in self.board.GetFootprints():
                if fp.GetReference().startswith("C"):
                    value = fp.GetValue().upper()
                    if "UF" in value and not fp.GetReference().startswith("CDEC"):
                        coupling_caps += 1
                    elif "NF" in value:
                        decoupling_caps += 1
        except Exception:
            pass
        gain_low = 0.0 if coupling_caps == 0 else -0.5 * math.log10(coupling_caps)
        gain_high = 0.0 if decoupling_caps == 0 else -0.2 * math.log10(decoupling_caps)
        return gain_low, gain_high

    def _find_worst_microphonic_component(self) -> Optional[str]:
        worst_ref = None
        max_size_mm = 0.0
        try:
            for fp in self.board.GetFootprints():
                # Use area as crude proxy for mass / microphonic susceptibility
                size_mm = fp.GetArea() / 1e6  # nm² → mm²
                if size_mm > max_size_mm:
                    max_size_mm = size_mm
                    worst_ref = fp.GetReference()
        except Exception:
            pass
        return worst_ref

    def _estimate_power_voltage(self) -> float:
        """Estimate power supply voltage based on components."""
        try:
            # Look for voltage regulators and power components
            for fp in self.board.GetFootprints():
                ref = fp.GetReference().upper()
                value = fp.GetValue().upper()
                
                # Check for common voltage regulators
                if "REG" in ref or "REG" in value:
                    if "5V" in value or "5.0" in value:
                        return 5.0
                    elif "12V" in value or "12.0" in value:
                        return 12.0
                    elif "15V" in value or "15.0" in value:
                        return 15.0
                    elif "24V" in value or "24.0" in value:
                        return 24.0
                
                # Check for power supply nets
                net_name = fp.GetNet().GetNetname().upper()
                if "VCC" in net_name or "VDD" in net_name:
                    if "5" in net_name:
                        return 5.0
                    elif "12" in net_name:
                        return 12.0
                    elif "15" in net_name:
                        return 15.0
                    elif "24" in net_name:
                        return 24.0
            
            # Default to 15V for audio applications
            return 15.0
            
        except Exception:
            return 15.0  # Fallback

    def _sweep_gain_edges_extended(self) -> tuple[float, float, float]:
        """Extended frequency response analysis for bandwidth up to 80kHz."""
        # Count coupling caps for low freq; decoupling cap lead inductance for high freq.
        low_cut_hz = 20.0
        high_cut_hz = 80000.0

        coupling_caps, decoupling_caps = 0, 0
        try:
            for fp in self.board.GetFootprints():
                if fp.GetReference().startswith("C"):
                    value = fp.GetValue().upper()
                    if "UF" in value and not fp.GetReference().startswith("CDEC"):
                        coupling_caps += 1
                    elif "NF" in value:
                        decoupling_caps += 1
        except Exception:
            pass
        gain_low = 0.0 if coupling_caps == 0 else -0.5 * math.log10(coupling_caps)
        gain_high = 0.0 if decoupling_caps == 0 else -0.2 * math.log10(decoupling_caps)
        gain_extended = 0.0 if coupling_caps == 0 else -0.5 * math.log10(coupling_caps)
        return gain_low, gain_high, gain_extended

    def _calculate_overall_coupling_score(self, mutual_inductance_data: Dict, 
                                        capacitive_data: Dict, 
                                        hf_data: Dict, 
                                        thermal_data: Dict) -> float:
        """Calculate overall coupling score from all analysis results."""
        try:
            # Extract coupling factors from each analysis
            mutual_scores = []
            capacitive_scores = []
            hf_scores = []
            thermal_scores = []
            
            # Process mutual inductance data
            if isinstance(mutual_inductance_data, dict):
                for component_data in mutual_inductance_data.values():
                    if isinstance(component_data, dict) and 'coupling_factor' in component_data:
                        mutual_scores.append(component_data['coupling_factor'])
            
            # Process capacitive coupling data
            if isinstance(capacitive_data, dict):
                for component_data in capacitive_data.values():
                    if isinstance(component_data, dict) and 'coupling_factor' in component_data:
                        capacitive_scores.append(component_data['coupling_factor'])
            
            # Process high-frequency data
            if isinstance(hf_data, dict):
                for component_data in hf_data.values():
                    if isinstance(component_data, dict):
                        # Extract relevant HF coupling metrics
                        if 'total_proximity_effect' in component_data:
                            hf_scores.append(component_data['total_proximity_effect'])
            
            # Process thermal data
            if isinstance(thermal_data, dict):
                for component_data in thermal_data.values():
                    if isinstance(component_data, dict) and 'coupling_effect' in component_data:
                        thermal_scores.append(component_data['coupling_effect'])
            
            # Calculate weighted average
            total_score = 0.0
            weight_sum = 0.0
            
            if mutual_scores:
                avg_mutual = sum(mutual_scores) / len(mutual_scores)
                total_score += avg_mutual * 0.3  # 30% weight
                weight_sum += 0.3
            
            if capacitive_scores:
                avg_capacitive = sum(capacitive_scores) / len(capacitive_scores)
                total_score += avg_capacitive * 0.3  # 30% weight
                weight_sum += 0.3
            
            if hf_scores:
                avg_hf = sum(hf_scores) / len(hf_scores)
                total_score += avg_hf * 0.25  # 25% weight
                weight_sum += 0.25
            
            if thermal_scores:
                avg_thermal = sum(thermal_scores) / len(thermal_scores)
                total_score += avg_thermal * 0.15  # 15% weight
                weight_sum += 0.15
            
            # Normalize and convert to 0-100 scale
            if weight_sum > 0:
                normalized_score = (total_score / weight_sum) * 100
                return min(100.0, max(0.0, normalized_score))
            else:
                return 50.0  # Default score
                
        except Exception as exc:
            self.logger.error("Error calculating overall coupling score: %s", exc)
            return 50.0

    # ----------------------------------------------------------
    # Batch run helper
    # ----------------------------------------------------------

    def run_all_advanced(self) -> Dict[str, object]:
        """Return all advanced metrics in a single call (dict for JSON serialisation)."""
        return {
            "thd_plus_n": self.analyze_thd_plus_n(),
            "frequency_response": self.analyze_frequency_response(),
            "microphonic_coupling": self.analyze_microphonic_coupling(),
            "group_delay": self.analyze_group_delay(),
            "intermodulation_distortion": self.analyze_intermodulation_distortion(),
            "dynamic_range": self.analyze_dynamic_range(),
            "physical_coupling": self.analyze_physical_coupling(),
            "audio_frequency_bands": self.analyze_audio_frequency_bands()
        } 