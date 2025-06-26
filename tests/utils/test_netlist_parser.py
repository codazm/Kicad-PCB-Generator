import json
from pathlib import Path

import pytest

from kicad_pcb_generator.core.netlist.parser import (
    parse_json_netlist,
    FootprintData,
    PadConnection,
)


@pytest.fixture()
def tmp_netlist_file(tmp_path: Path) -> Path:
    data = {
        "footprints": [
            {
                "ref": "R1",
                "value": "10k",
                "lib_id": "Device:R_0603",
                "pads": [{"pad": "1", "net": "NET1"}, {"pad": "2", "net": "NET2"}],
            },
            {
                "ref": "C1",
                "value": "1uF",
                "lib_id": "Device:C_0603",
                "pads": [{"pad": "1", "net": "NET2"}, {"pad": "2", "net": "GND"}],
            },
        ],
        "nets": [
            {"name": "NET1", "pads": ["R1-1"]},
            {"name": "NET2", "pads": ["R1-2", "C1-1"]},
            {"name": "GND", "pads": ["C1-2"]},
        ],
    }
    file_path = tmp_path / "netlist.json"
    file_path.write_text(json.dumps(data))
    return file_path


def test_parse_json_netlist(tmp_netlist_file: Path):
    netlist = parse_json_netlist(tmp_netlist_file)

    assert len(netlist.footprints) == 2
    assert netlist.footprint_by_ref("R1").value == "10k"

    # Ensure pad connections preserved
    r1_pads = netlist.footprint_by_ref("R1").pad_connections
    assert any(pc.pad_name == "1" and pc.net_name == "NET1" for pc in r1_pads)

    # Ensure nets parsed
    assert netlist.get_net("GND").connected_pads == ["C1-2"] 
