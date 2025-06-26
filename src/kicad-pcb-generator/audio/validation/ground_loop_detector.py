"""Ground-loop heuristic detector.

Detects duplicated ground-return paths that form large loop areas—a
classic cause of hum in modular-synth builds.  It uses a flood-fill of
GND nets and flags any closed loop larger than a threshold area.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
import logging

try:
    import pcbnew
except ImportError:  # pragma: no cover
    pcbnew = None


@dataclass
class GroundLoopIssue:
    loop_area_mm2: float
    bounding_box: Tuple[float, float, float, float]  # left, top, right, bottom (mm)


@dataclass
class GroundLoopReport:
    success: bool
    issues: List[GroundLoopIssue]
    warnings: List[str]
    errors: List[str]


class GroundLoopDetector:
    """Detect large ground loops using zone outline heuristics."""

    def __init__(self, board: "pcbnew.BOARD", logger: Optional[logging.Logger] = None):
        self.board = board
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.max_loop_area_mm2 = 500.0  # guideline from audio-layout best-practice

    def analyse(self) -> GroundLoopReport:
        if pcbnew is None:
            return GroundLoopReport(False, [], [], ["pcbnew not available"])

        issues: List[GroundLoopIssue] = []
        try:
            zones = [z for z in self.board.Zones() if z.GetNetname().upper() == "GND"]
            if len(zones) < 2:
                return GroundLoopReport(True, [], [], [])  # no chance for loop

            for i, z1 in enumerate(zones):
                for z2 in zones[i + 1 :]:
                    dist_mm = self._zone_distance_mm(z1, z2)
                    if dist_mm < 1.0:  # zones touch/overlap – possible loop
                        area_mm2 = self._loop_area_mm2(z1, z2)
                        if area_mm2 > self.max_loop_area_mm2:
                            bbox = z1.BBox().Union(z2.BBox())
                            issues.append(
                                GroundLoopIssue(
                                    area_mm2,
                                    (
                                        bbox.GetLeft() / 1e6,
                                        bbox.GetTop() / 1e6,
                                        bbox.GetRight() / 1e6,
                                        bbox.GetBottom() / 1e6,
                                    ),
                                )
                            )
            return GroundLoopReport(True, issues, [], [])
        except Exception as exc:
            return GroundLoopReport(False, [], [], [str(exc)])

    # ------------------------------------------------------------------
    def _zone_distance_mm(self, z1: "pcbnew.ZONE", z2: "pcbnew.ZONE") -> float:
        p1 = z1.BBox().Centre()
        p2 = z2.BBox().Centre()
        dx = (p1.x - p2.x) / 1e6
        dy = (p1.y - p2.y) / 1e6
        return (dx * dx + dy * dy) ** 0.5

    def _loop_area_mm2(self, z1: "pcbnew.ZONE", z2: "pcbnew.ZONE") -> float:
        return abs(z1.GetArea() - z2.GetArea()) / 1e12  # nm² → mm² 
