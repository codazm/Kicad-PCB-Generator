import os
import json
import pytest
from pathlib import Path
from kicad_pcb_generator.core.validation.base_validator import BaseValidator
from kicad_pcb_generator.audio.validation.audio_validator import AudioPCBValidator
from kicad_pcb_generator.core.settings import ValidationSettings

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def validation_rules(test_data_dir):
    """Load validation rules from the test configuration file."""
    rules_file = test_data_dir / "validation_rules.json"
    with open(rules_file) as f:
        return json.load(f)

@pytest.fixture
def settings(validation_rules):
    """Create validation settings from the test configuration."""
    return ValidationSettings(**validation_rules["validation"])

@pytest.fixture
def validator(settings):
    """Create an audio PCB validator with test settings."""
    return AudioPCBValidator(settings)

@pytest.fixture
def valid_pcb(test_data_dir):
    """Load the valid PCB test file."""
    pcb_file = test_data_dir / "valid_audio_pcb.kicad_pcb"
    with open(pcb_file) as f:
        return f.read()

@pytest.fixture
def invalid_component_placement(test_data_dir):
    """Load the invalid component placement test file."""
    pcb_file = test_data_dir / "invalid_component_placement.kicad_pcb"
    with open(pcb_file) as f:
        return f.read()

@pytest.fixture
def invalid_power_supply(test_data_dir):
    """Load the invalid power supply test file."""
    pcb_file = test_data_dir / "invalid_power_supply.kicad_pcb"
    with open(pcb_file) as f:
        return f.read()

@pytest.fixture
def invalid_grounding(test_data_dir):
    """Load the invalid grounding test file."""
    pcb_file = test_data_dir / "invalid_grounding.kicad_pcb"
    with open(pcb_file) as f:
        return f.read()

@pytest.fixture
def invalid_signal_paths(test_data_dir):
    """Load the invalid signal paths test file."""
    pcb_file = test_data_dir / "invalid_signal_paths.kicad_pcb"
    with open(pcb_file) as f:
        return f.read()

@pytest.fixture
def invalid_manufacturing(test_data_dir):
    """Load the invalid manufacturing test file."""
    pcb_file = test_data_dir / "invalid_manufacturing.kicad_pcb"
    with open(pcb_file) as f:
        return f.read() 