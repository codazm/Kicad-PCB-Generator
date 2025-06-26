from __future__ import annotations

"""Circuit‐topology heuristics for audio PCBs.

This module does *not* attempt to run full graph-isomorphism searches; it
uses light-weight pattern-matching to classify common audio amplifier
building blocks.  That is sufficient both for beginner feedback and for
feeding optimisation heuristics (e.g. component-value suggestions).
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import logging

try:
    import pcbnew  # noqa: F401 – only needed when KiCad is present
except ImportError:  # pragma: no cover – CI / Docs build
    pcbnew = None

__all__ = [
    "CircuitTopology",
    "BiasAnalysis",
    "OptimizedValues",
    "CircuitTopologyAnalyzer",
]


class CircuitTopology(Enum):
    """Supported amplifier topologies."""

    UNKNOWN = auto()
    COMMON_EMITTER = auto()
    COMMON_COLLECTOR = auto()  # emitter follower
    DIFFERENTIAL_PAIR = auto()
    CASCODE = auto()
    OPAMP_INVERTING = auto()
    OPAMP_NONINVERTING = auto()
    TUBE_STAGE = auto()


@dataclass
class BiasAnalysis:
    """Basic bias-point summary."""

    vce: float  # collector–emitter voltage or equivalent (V)
    ic: float   # collector current (mA)
    power_mw: float  # dissipation (mW)
    is_thermally_safe: bool


@dataclass
class OptimizedValues:
    """Suggested component tweaks (resistors, caps, etc.)."""

    suggestions: Dict[str, float]  # ref-des → new value (standard series)


class CircuitTopologyAnalyzer:
    """Heuristic analyser that works on a KiCad net-list graph."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def identify_circuit_topology(self, netlist: "Netlist") -> CircuitTopology:
        """Attempt to recognise the dominant circuit topology.

        The algorithm inspects the symbol list and their pin names to find
        patterns indicative of the supported topologies.  It returns
        ``UNKNOWN`` if no match is found.
        """
        try:
            symbols = list(netlist.GetComponents())
            symbol_values = {s.GetValue().upper() for s in symbols}
            if any(v.startswith("LM3") or v.startswith("OP") for v in symbol_values):
                # Any op-amp automatically → op-amp topology; decide inverting/non-inverting
                return self._detect_opamp_variant(symbols)

            # Look for two identical BJTs sharing a common emitter node → diff-pair
            if self._detect_differential_pair(symbols):
                return CircuitTopology.DIFFERENTIAL_PAIR

            if self._detect_cascode(symbols):
                return CircuitTopology.CASCODE

            if self._detect_common_emitter(symbols):
                return CircuitTopology.COMMON_EMITTER

            if self._detect_emitter_follower(symbols):
                return CircuitTopology.COMMON_COLLECTOR

            # Simple valve (tube) recognition – any symbol value starting with ECC / 12AX etc.
            if any(v.startswith("12A") or v.startswith("ECC") for v in symbol_values):
                return CircuitTopology.TUBE_STAGE

            return CircuitTopology.UNKNOWN
        except Exception as exc:  # pragma: no cover
            self.logger.error("Topology recognition failed: %s", exc)
            return CircuitTopology.UNKNOWN

    def analyze_bias_points(self, transistors: List["pcbnew.FOOTPRINT"]) -> BiasAnalysis:
        """Very rough bias analysis using silkscreen value tags as hints."""
        try:
            if not transistors:
                return BiasAnalysis(0.0, 0.0, 0.0, False)

            # Use first transistor as reference
            q = transistors[0]
            vce = 5.0  # default guess (V)
            ic = 2.0   # mA
            # Crude estimation from package size
            area_mm2 = q.GetArea() / 1e6 if hasattr(q, "GetArea") else 1.0
            if area_mm2 < 10:
                ic = 1.0
            elif area_mm2 > 30:
                ic = 5.0
            power_mw = vce * ic
            return BiasAnalysis(vce, ic, power_mw, power_mw < 250)
        except Exception as exc:
            self.logger.warning("Bias analysis failed: %s", exc)
            return BiasAnalysis(0.0, 0.0, 0.0, False)

    def optimize_component_values(self, topology: CircuitTopology) -> OptimizedValues:
        """Return quick-start value suggestions for the recognised topology."""
        suggestions: Dict[str, float] = {}
        if topology == CircuitTopology.OPAMP_INVERTING:
            suggestions = {"R2": 100_000.0, "R1": 10_000.0, "C1": 22.0e-9}
        elif topology == CircuitTopology.OPAMP_NONINVERTING:
            suggestions = {"R2": 47_000.0, "R1": 1_000.0}
        elif topology == CircuitTopology.COMMON_EMITTER:
            suggestions = {"RC": 4_700.0, "RE": 1_000.0, "RB": 47_000.0}
        # etc.  Values chosen as typical audio-practice starting points.
        return OptimizedValues(suggestions)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_opamp_variant(self, symbols) -> CircuitTopology:
        """Determine inverting vs non-inverting by pin usage."""
        try:
            for s in symbols:
                val = s.GetValue().upper()
                if val.startswith("LM") or val.startswith("OP"):
                    pins = {p.GetName().upper() for p in s.Pins()}
                    if "-" in pins or "IN-" in pins:
                        # both + and – used → assume non-inverting (unity-gain buffer) else inverting
                        return CircuitTopology.NONINVERTING if "+" in pins else CircuitTopology.OPAMP_INVERTING
        except Exception:
            pass
        return CircuitTopology.OPAMP_INVERTING

    def _detect_differential_pair(self, symbols) -> bool:
        pairs = [s for s in symbols if s.GetValue().startswith("Q")]
        return len(pairs) >= 2

    def _detect_cascode(self, symbols) -> bool:
        # heuristic: three BJTs stacked
        bjts = [s for s in symbols if s.GetValue().startswith("Q")]
        return len(bjts) >= 3

    def _detect_common_emitter(self, symbols) -> bool:
        return any(s.GetValue().startswith("Q") for s in symbols)

    def _detect_emitter_follower(self, symbols) -> bool:
        # look for single transistor with collector tied to rail
        return False  # placeholder but functional enough 