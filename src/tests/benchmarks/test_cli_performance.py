import json, time
from pathlib import Path

import pytest

from kicad_pcb_generator.core.netlist.parser import Netlist, FootprintData, PadConnection
from kicad_pcb_generator.core.pcb import PCBGenerator
from kicad_pcb_generator.core.project_manager import ProjectManager


def _dummy_netlist() -> Netlist:
    fp = FootprintData(
        ref="R1",
        value="10k",
        lib_id="Device:R_0603",
        pad_connections=[PadConnection(pad_name="1", net_name="N1"), PadConnection(pad_name="2", net_name="N2")],
    )
    return Netlist(footprints=[fp], nets=[])


@pytest.mark.performance
def test_generate_pcb_performance(tmp_path: Path):
    pm = ProjectManager()
    project_name = "perf_project"
    pm.create_project(name=project_name, template="basic_audio_amp", description="Perf test", author="tester")

    pcb_gen = PCBGenerator(pm)
    netlist = _dummy_netlist()

    start = time.time()
    res = pcb_gen.generate_pcb(project_name, netlist=netlist)
    duration = time.time() - start

    assert res.success, res.errors
    # Ensure under 5 seconds in CI
    assert duration < 5, f"PCB generation too slow: {duration:.2f}s" 