"""Simple inter-channel crosstalk estimator for audio PCBs.

The implementation is intentionally heuristic so it can run in seconds
and without external dependencies.  It walks all audio nets (names
starting with "IN", "OUT", "AUDIO") and flags pairs of tracks that run
in parallel for more than a configurable threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import logging

try:
    import pcbnew
except ImportError:  # pragma: no cover
    pcbnew = None

@dataclass
class CrosstalkIssue:
    track_a: "pcbnew.TRACK"
    track_b: "pcbnew.TRACK"
    crosstalk_db: float
    length_mm: float


@dataclass
class CrosstalkReport:
    success: bool
    issues: List[CrosstalkIssue]
    warnings: List[str]
    errors: List[str]


class CrosstalkAnalyzer:
    """Light-weight crosstalk checker."""

    def __init__(self, board: "pcbnew.BOARD", logger: Optional[logging.Logger] = None):
        self.board = board
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.max_parallel_len_mm = 50.0  # threshold from roadmap
        self.max_cxt_db = -60.0  # acceptable limit

    # ------------------------------------------------------------------
    def analyse(self) -> CrosstalkReport:
        if pcbnew is None:
            return CrosstalkReport(False, [], [], ["pcbnew not available"])

        issues: List[CrosstalkIssue] = []
        warnings: List[str] = []
        try:
            tracks = [t for t in self.board.GetTracks() if t.IsTrack()]
            for i, t1 in enumerate(tracks):
                net1 = t1.GetNetname().upper()
                if not net1.startswith(("IN", "OUT", "AUDIO")):
                    continue
                for t2 in tracks[i + 1 :]:
                    net2 = t2.GetNetname().upper()
                    if net1 == net2:
                        continue
                    if not net2.startswith(("IN", "OUT", "AUDIO")):
                        continue
                    if not t1.IsParallel(t2):
                        continue
                    length = t1.GetLength() / 1e6  # mm
                    if length < self.max_parallel_len_mm:
                        continue
                    # reuse DRC helper if available
                    try:
                        from ...core.board.advanced_drc import AdvancedDRCManager  # late import

                        cxt = AdvancedDRCManager._calculate_crosstalk
                        crosstalk_db = cxt(AdvancedDRCManager(None), t1, t2)  # dummy instance
                    except Exception:
                        crosstalk_db = -40.0  # fallback estimate

                    if crosstalk_db > self.max_cxt_db:
                        issues.append(CrosstalkIssue(t1, t2, crosstalk_db, length))
            return CrosstalkReport(True, issues, warnings, [])
        except Exception as exc:
            return CrosstalkReport(False, [], warnings, [str(exc)]) 
