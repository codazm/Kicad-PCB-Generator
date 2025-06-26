"""Netlist package.

Provides data structures and parsers that transform a KiCad schematic or other exported
net-list formats into an in-memory representation that can be consumed by the
`PCBGenerator` and other pipeline components.
"""

from .parser import (
    Netlist,
    FootprintData,
    NetData,
    parse_schematic,
    parse_json_netlist,
)

__all__ = [
    "Netlist",
    "FootprintData",
    "NetData",
    "parse_schematic",
    "parse_json_netlist",
] 
