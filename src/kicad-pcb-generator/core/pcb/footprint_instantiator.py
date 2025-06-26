"""Footprint instantiation helper.

Isolates the logic that turns our neutral `FootprintData` records into KiCad
`pcbnew.FOOTPRINT` objects and adds them to a board.  Keeping it separate helps
unit-test placement logic without bloating `PCBGenerator`.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

import pcbnew
from pcbnew import PAD_SHAPE_CIRCLE, PAD_ATTRIB_SMD

from ..netlist.parser import FootprintData, Netlist

logger = logging.getLogger(__name__)


_LIBRARY_CACHE: Dict[str, pcbnew.FOOTPRINT] = {}


def _load_footprint_from_library(lib_id: str) -> Optional[pcbnew.FOOTPRINT]:
    """Attempt to load a footprint from KiCad library, cache for speed.

    Returns None if library access fails (e.g., running on CI without KiCad).
    """
    if lib_id in _LIBRARY_CACHE:
        return _LIBRARY_CACHE[lib_id].Clone()

    try:
        fp_lib_table = pcbnew.FootprintLibTable().GetGlobalLibTable()
        fp = pcbnew.FootprintLoad(fp_lib_table, lib_id)
        if fp is not None:
            _LIBRARY_CACHE[lib_id] = fp
            return fp.Clone()
    except Exception as exc:  # pragma: no cover – depends on KiCad runtime
        logger.warning("Could not load footprint '%s': %s", lib_id, exc)
    return None


def instantiate_footprints(board: pcbnew.BOARD, netlist: Netlist) -> None:
    """Add all footprints from *netlist* onto *board* at origin (0,0).

    Footprints are left un-placed so that `LayoutOptimizer` can position them
    later.  Pads are renamed to match the schematic pad names to preserve
    connectivity when a router is plugged in.
    """
    for fp_data in netlist.footprints:
        footprint = _load_footprint_from_library(fp_data.lib_id) or pcbnew.FOOTPRINT()
        footprint.SetReference(fp_data.ref)
        footprint.SetValue(fp_data.value)

        # Create dummy pads if library footprint missing (unit-test path)
        if footprint.GetPadCount() == 0 and fp_data.pad_connections:
            for idx, pad_conn in enumerate(fp_data.pad_connections, start=1):
                pad = pcbnew.FOOTPRINT_PAD(footprint)
                pad.SetName(pad_conn.pad_name or str(idx))
                pad.SetAttribute(PAD_ATTRIB_SMD)
                pad.SetShape(PAD_SHAPE_CIRCLE)
                pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1), pcbnew.FromMM(1)))
                footprint.Add(pad)

        board.Add(footprint)

        # --------------------------------------------------------------
        #  Net assignment
        # --------------------------------------------------------------
        if pcbnew is None:
            continue  # headless env – skip pad→net linking

        try:
            netcode_cache: Dict[str, int] = {}

            for pad_conn in fp_data.pad_connections:
                pad = footprint.FindPadByName(pad_conn.pad_name)
                if pad is None:
                    continue

                net_name = pad_conn.net_name
                if net_name not in netcode_cache:
                    # create or fetch net
                    net = board.FindNet(net_name)
                    if net is None:
                        new_net = pcbnew.NETINFO_ITEM(board, net_name)
                        board.Add(new_net)
                        netcode_cache[net_name] = new_net.GetNet()
                    else:
                        netcode_cache[net_name] = net.GetNet()

                pad.SetNetCode(netcode_cache[net_name])
        except Exception as exc:
            logger.warning("Failed to assign nets for footprint %s: %s", fp_data.ref, exc) 
