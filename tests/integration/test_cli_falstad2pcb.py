import json
import sys
from pathlib import Path
from importlib import reload

import pytest

import kicad_pcb_generator.cli as cli


@pytest.fixture()
def falstad_json(tmp_path: Path):
    data = {
        "elements": [
            {"type": "resistor", "x": 0, "y": 0, "rotation": 0, "value": "1k", "properties": {}},
            {"type": "ground", "x": 1, "y": 1, "rotation": 0, "value": "", "properties": {}},
        ],
        "wires": [
            {"x1": 0, "y1": 0, "x2": 1, "y2": 1}
        ],
    }
    fp = tmp_path / "circuit.json"
    fp.write_text(json.dumps(data))
    return fp


def test_falstad2pcb_cli(tmp_path: Path, falstad_json: Path, monkeypatch):
    """End-to-end CLI test: falstad JSON → PCB generation (headless)."""
    proj_name = "cli_test_project"
    # Fake argv
    argv = [
        "kicad-pcb-gen",
        "falstad2pcb",
        str(falstad_json),
        proj_name,
    ]
    monkeypatch.setattr(sys, "argv", argv)
    # Ensure CLI main exits without SystemExit error
    try:
        reload(cli)
        cli.main()
    except SystemExit as exc:
        # Expect exit code 0
        assert exc.code == 0
    # Verify project folder exists
    pm = cli.ProjectManager()
    assert pm.get_project_path(proj_name).exists() 