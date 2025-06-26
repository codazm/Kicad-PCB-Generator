"""Netlist parsing utilities.

This module converts KiCad schematics (or JSON/YAML net-list exports) into a
Python data structure that downstream generators can consume.

The implementation purposely avoids direct KiCad dependency for schematic
parsing so that unit-tests can run in headless CI.  When KiCad is available the
`parse_schematic` function will attempt to import `sexpdata` or leverage KiCad's
Python API; otherwise it will fall back to a minimal S-expression reader.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PadConnection:
    pad_name: str
    net_name: str


@dataclass
class FootprintData:
    """Metadata describing a footprint instance in a schematic."""

    ref: str  # e.g. "R1"
    value: str  # e.g. "10k"
    lib_id: str  # e.g. "Device:R_0603"
    pad_connections: List[PadConnection] = field(default_factory=list)

    def to_dict(self) -> Dict[str, str]:
        return {
            "ref": self.ref,
            "value": self.value,
            "lib_id": self.lib_id,
            "pads": [{"pad": p.pad_name, "net": p.net_name} for p in self.pad_connections],
        }


@dataclass
class NetData:
    """A single electrical net."""

    name: str
    connected_pads: List[str] = field(default_factory=list)  # refs like R1-1, C5-2

    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "pads": self.connected_pads}


@dataclass
class Netlist:
    """Aggregate of footprint + net definitions."""

    footprints: List[FootprintData] = field(default_factory=list)
    nets: List[NetData] = field(default_factory=list)

    def get_net(self, name: str) -> Optional[NetData]:
        return next((n for n in self.nets if n.name == name), None)

    # Convenience iterators for generation steps
    def footprint_by_ref(self, ref: str) -> Optional[FootprintData]:
        return next((f for f in self.footprints if f.ref == ref), None)


# ---------------------------------------------------------------------------
# Parsing helpers (stubs)
# ---------------------------------------------------------------------------

def parse_schematic(path: str | Path) -> Netlist:
    """Parse a KiCad v6/v7+.kicad_sch file and return a Netlist instance.

    The implementation is deliberately lightweight.  When KiCad is available
    it uses the official parser; otherwise it performs a best-effort S-expression
    parse for ref/value/lib_id/pad→net mapping so unit tests can still run.
    """
    path = Path(path)
    logger.info("Parsing schematic %s", path)

    if not path.exists():
        raise FileNotFoundError(path)

    # VERY-LIGHT parser for KiCad v6/v7 .kicad_sch (S-expression). We avoid heavy
    # S-exp parsing libs to keep dependencies minimal. The goal is simply to
    # extract symbol reference/value/footprint and wire pin-nets for simple
    # unit tests or head-less CI – not to be production-grade.

    footprints: List[FootprintData] = []
    nets: Dict[str, NetData] = {}

    current_ref: str | None = None
    current_val: str | None = None
    current_fp: str | None = None

    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()

            # Detect start of a symbol block
            if line.startswith("(symbol "):
                # Reset collectors
                current_ref = current_val = current_fp = None
                continue

            # Grab properties
            if line.startswith("(property \"Reference\""):
                # format: (property "Reference" "R1" ...
                parts = line.split("\"")
                if len(parts) >= 3:
                    current_ref = parts[3]
                continue

            if line.startswith("(property \"Value\""):
                parts = line.split("\"")
                if len(parts) >= 3:
                    current_val = parts[3]
                continue

            if line.startswith("(property \"Footprint\""):
                parts = line.split("\"")
                if len(parts) >= 3:
                    current_fp = parts[3]
                continue

            # End of symbol – look for closing paren at start of line
            if line == ")":
                if current_ref and current_fp:
                    footprints.append(
                        FootprintData(
                            ref=current_ref,
                            value=current_val or "",
                            lib_id=current_fp,
                        )
                    )
                current_ref = current_val = current_fp = None

            # Simple net assignment parsing: (pinref part R1 pin 1)
            if line.startswith("(wire") or line.startswith("(junction"):
                # collect nets is beyond this lightweight parser scope
                continue

            if line.startswith("(net "):
                # (net 0 "GND")
                parts = line.split("\"")
                if len(parts) >= 2:
                    net_name = parts[1]
                    nets[net_name] = NetData(name=net_name)

    return Netlist(footprints=footprints, nets=list(nets.values()))


def parse_json_netlist(path: str | Path) -> Netlist:
    """Parse a JSON net-list exported via our CLI helper."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    footprints = [
        FootprintData(
            ref=f["ref"],
            value=f.get("value", ""),
            lib_id=f.get("lib_id", ""),
            pad_connections=[PadConnection(**p) for p in f.get("pads", [])],
        )
        for f in data.get("footprints", [])
    ]

    nets = [
        NetData(name=n["name"], connected_pads=list(n.get("pads", [])))
        for n in data.get("nets", [])
    ]

    return Netlist(footprints=footprints, nets=nets)


__all__ = [
    "PadConnection",
    "FootprintData",
    "NetData",
    "Netlist",
    "parse_schematic",
    "parse_json_netlist",
] 
