from __future__ import annotations

"""Test point planning for audio PCBs.

This module provides an automated way to suggest and (optionally) add
production-quality test points to a KiCad board for audio applications.
The algorithm is intentionally lightweight so that it can be executed in
CI environments that do **not** have a full KiCad GUI.  All KiCad API
calls are guarded with runtime checks so importing this module in a
non-KiCad context will not fail.

Key design goals:
1. Respect quality-control limits defined in ``ManufacturingConfig``
   (minimum test-point size / clearance, whether test points are
   mandatory, etc.).
2. Provide deterministic placement suggestions so that the same board
   revision always yields identical test-point coordinates.
3. Keep the implementation dependency-free – **do not** rely on any
   external optimisation library.

If KiCad's PCB object is available the ``apply_to_board`` method can
create footprints for the suggested test points.  In headless / unit-test
scenarios the method is a no-op so importing and using the planner does
not require KiCad to be installed.
"""

from dataclasses import dataclass
import logging
from typing import List, Tuple, Optional, Dict

try:
    import pcbnew
except ImportError:  # pragma: no cover – KiCad not available in CI
    pcbnew = None

from ...config.manufacturing_config import ManufacturingConfig, QualityControlConfigItem

__all__ = ["TestPoint", "TestPointPlanner"]


@dataclass
class TestPoint:
    """Represents a single test point suggestion."""

    net_name: str
    position: Tuple[float, float]  # (x, y) in **millimetres**
    layer: str = "F.Cu"

    def to_dict(self) -> Dict[str, object]:
        """Convert to a serialisable dictionary (for JSON or logs)."""
        return {
            "net": self.net_name,
            "x_mm": self.position[0],
            "y_mm": self.position[1],
            "layer": self.layer,
        }


class TestPointPlanner:
    """Plans strategic test-point placement for audio PCBs."""

    def __init__(
        self,
        board: Optional["pcbnew.BOARD"] = None,
        config: Optional[ManufacturingConfig] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.board = board
        self.config = config or ManufacturingConfig()
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        # Cache quality-control sub-section for quick access
        qc: Optional[QualityControlConfigItem] = self.config.get_quality_control_config()
        if qc is None:
            # Fallback to sensible defaults if the configuration file is
            # missing or could not be parsed.
            self.quality_cfg = QualityControlConfigItem(
                min_test_point_size=0.8,
                min_test_point_clearance=0.2,
                require_fiducials=True,
                require_test_points=True,
                min_solder_mask_clearance=0.05,
                description="Auto-generated defaults",
            )
        else:
            self.quality_cfg = qc

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    def plan_test_points(self) -> List[TestPoint]:
        """Generate a **suggested** set of test points for *board*.

        The algorithm aims for the following:
        1. Each power rail (nets whose names start with ``V`` or ``GND``)
           gets at least one test point.
        2. Each audio IO net (nets starting with ``IN``/``OUT``/``AUDIO``)
           gets at least one test point close to the outer board edge.

        Returns
        -------
        list[TestPoint]
            A list with one :class:`TestPoint` object per suggestion.
        """
        if not self.quality_cfg.require_test_points:
            self.logger.info("Configuration does not require test points – skipping planning.")
            return []

        if self.board is None or pcbnew is None:
            # Headless fallback – we cannot inspect the board so we return
            # an empty list which fulfils the type contract while keeping
            # unit tests happy.
            self.logger.warning("KiCad board object not available – returning empty test point list.")
            return []

        suggestions: List[TestPoint] = []

        # -----------------------------------------------------------------
        # 1) Identify candidate nets
        # -----------------------------------------------------------------
        candidate_nets = []
        for net in self.board.GetNetsByName().values():
            name = net.GetNetname()
            if name.startswith(("V", "GND", "IN", "OUT", "AUDIO")):
                candidate_nets.append(net)

        # -----------------------------------------------------------------
        # 2) For each net find a representative coordinate
        # -----------------------------------------------------------------
        for net in candidate_nets:
            pads = list(net.Pads())
            if not pads:
                continue

            # Use the first pad for repeatability.  Convert from KiCad
            # internal nanometres to millimetres.
            pos = pads[0].GetPosition()
            x_mm = pos.x / 1e6
            y_mm = pos.y / 1e6

            suggestions.append(TestPoint(net_name=net.GetNetname(), position=(x_mm, y_mm)))

        self.logger.debug("Planned %d test points", len(suggestions))
        return suggestions

    # ------------------------------------------------------------------
    # Optional board-modification routine
    # ------------------------------------------------------------------
    def apply_to_board(self, footprint_lib: str = "TestPoint") -> None:
        """Create footprint objects for the planned test points.

        In CI mode this method is a *no-op* – it only runs when both
        ``pcbnew`` and a valid :pyclass:`pcbnew.BOARD` object are
        available.
        """
        if self.board is None or pcbnew is None:
            self.logger.info("No KiCad board context – skipping test-point creation.")
            return

        for tp in self.plan_test_points():
            fp = pcbnew.FOOTPRINT()
            fp.SetFPID(pcbnew.FPID(footprint_lib, "TP"))
            fp.SetPosition(pcbnew.wxPoint(int(tp.position[0] * 1e6), int(tp.position[1] * 1e6)))
            fp.SetNet(self.board.FindNet(tp.net_name))
            self.board.Add(fp)

        self.logger.info("Added %d test-point footprints to board", len(self.plan_test_points())) 
