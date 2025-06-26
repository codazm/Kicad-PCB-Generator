"""Tests for audio circuit templates."""
import pytest
from pathlib import Path

from kicad_pcb_generator.audio.circuits.templates import (
    AudioCircuitTemplate,
    PreamplifierTemplate,
    PowerAmplifierTemplate,
    EffectsPedalTemplate,
    AudioInterfaceTemplate,
    MixingConsoleTemplate
)

@pytest.fixture
def template_dir(tmp_path):
    """Create a temporary directory for template data."""
    return tmp_path / "templates"

@pytest.fixture
def audio_template(template_dir):
    """Create a basic audio circuit template."""
    return AudioCircuitTemplate(str(template_dir))

@pytest.fixture
def preamp_template(template_dir):
    """Create a preamplifier template."""
    return PreamplifierTemplate(str(template_dir))

@pytest.fixture
def power_amp_template(template_dir):
    """Create a power amplifier template."""
    return PowerAmplifierTemplate(str(template_dir))

@pytest.fixture
def effects_pedal_template(template_dir):
    """Create an effects pedal template."""
    return EffectsPedalTemplate(str(template_dir))

@pytest.fixture
def audio_interface_template(template_dir):
    """Create an audio interface template."""
    return AudioInterfaceTemplate(str(template_dir))

@pytest.fixture
def mixing_console_template(template_dir):
    """Create a mixing console template."""
    return MixingConsoleTemplate(str(template_dir))

def test_audio_template_initialization(audio_template):
    """Test audio template initialization."""
    assert audio_template.layer_stack.name == "Audio 4-Layer Stack"
    assert len(audio_template.layer_stack.layers) == 4
    assert "GND" in audio_template.zones
    assert "clearance" in audio_template.rules
    assert "track_width" in audio_template.rules

def test_preamp_template_initialization(preamp_template):
    """Test preamplifier template initialization."""
    assert preamp_template.name == "Preamplifier"
    assert preamp_template.description == "Template for preamplifier circuits"
    assert preamp_template.version == "1.0.0"
    
    # Check components
    components = preamp_template.component_manager.get_components()
    assert len(components) == 3
    assert any(c.id == "R1" and c.value == "10k" for c in components)
    assert any(c.id == "C1" and c.value == "100n" for c in components)
    assert any(c.id == "U1" and c.value == "NE5532" for c in components)
    
    # Check variants
    assert "Standard" in preamp_template.variants
    assert "HighGain" in preamp_template.variants

def test_power_amp_template_initialization(power_amp_template):
    """Test power amplifier template initialization."""
    assert power_amp_template.name == "Power Amplifier"
    assert power_amp_template.description == "Template for power amplifier circuits"
    assert power_amp_template.version == "1.0.0"
    
    # Check components
    components = power_amp_template.component_manager.get_components()
    assert len(components) == 3
    assert any(c.id == "R1" and c.value == "10k" for c in components)
    assert any(c.id == "Q1" and c.value == "2N3055" for c in components)
    assert any(c.id == "Q2" and c.value == "MJ2955" for c in components)
    
    # Check variants
    assert "Standard" in power_amp_template.variants
    assert "HighPower" in power_amp_template.variants

def test_effects_pedal_template_initialization(effects_pedal_template):
    """Test effects pedal template initialization."""
    assert effects_pedal_template.name == "Effects Pedal"
    assert effects_pedal_template.description == "Template for effects pedal circuits"
    assert effects_pedal_template.version == "1.0.0"
    
    # Check components
    components = effects_pedal_template.component_manager.get_components()
    assert len(components) == 3
    assert any(c.id == "R1" and c.value == "10k" for c in components)
    assert any(c.id == "U1" and c.value == "TL072" for c in components)
    assert any(c.id == "C1" and c.value == "100n" for c in components)
    
    # Check variants
    assert "Standard" in effects_pedal_template.variants
    assert "Bypass" in effects_pedal_template.variants

def test_audio_template_save_load(audio_template, template_dir):
    """Test saving and loading audio template."""
    # Save template
    audio_template.save()
    assert (template_dir / "template.json").exists()
    
    # Load template
    loaded_template = AudioCircuitTemplate(str(template_dir))
    loaded_template.load()
    
    assert loaded_template.layer_stack.name == audio_template.layer_stack.name
    assert loaded_template.layer_stack.layers == audio_template.layer_stack.layers
    assert loaded_template.zones == audio_template.zones
    assert loaded_template.rules == audio_template.rules

def test_preamp_template_save_load(preamp_template, template_dir):
    """Test saving and loading preamplifier template."""
    # Save template
    preamp_template.save()
    assert (template_dir / "template.json").exists()
    
    # Load template
    loaded_template = PreamplifierTemplate(str(template_dir))
    loaded_template.load()
    
    assert loaded_template.name == preamp_template.name
    assert loaded_template.description == preamp_template.description
    assert loaded_template.version == preamp_template.version
    
    # Check components
    loaded_components = loaded_template.component_manager.get_components()
    original_components = preamp_template.component_manager.get_components()
    assert len(loaded_components) == len(original_components)
    
    # Check variants
    assert loaded_template.variants == preamp_template.variants

def test_power_amp_template_save_load(power_amp_template, template_dir):
    """Test saving and loading power amplifier template."""
    # Save template
    power_amp_template.save()
    assert (template_dir / "template.json").exists()
    
    # Load template
    loaded_template = PowerAmplifierTemplate(str(template_dir))
    loaded_template.load()
    
    assert loaded_template.name == power_amp_template.name
    assert loaded_template.description == power_amp_template.description
    assert loaded_template.version == power_amp_template.version
    
    # Check components
    loaded_components = loaded_template.component_manager.get_components()
    original_components = power_amp_template.component_manager.get_components()
    assert len(loaded_components) == len(original_components)
    
    # Check variants
    assert loaded_template.variants == power_amp_template.variants

def test_effects_pedal_template_save_load(effects_pedal_template, template_dir):
    """Test saving and loading effects pedal template."""
    # Save template
    effects_pedal_template.save()
    assert (template_dir / "template.json").exists()
    
    # Load template
    loaded_template = EffectsPedalTemplate(str(template_dir))
    loaded_template.load()
    
    assert loaded_template.name == effects_pedal_template.name
    assert loaded_template.description == effects_pedal_template.description
    assert loaded_template.version == effects_pedal_template.version
    
    # Check components
    loaded_components = loaded_template.component_manager.get_components()
    original_components = effects_pedal_template.component_manager.get_components()
    assert len(loaded_components) == len(original_components)
    
    # Check variants
    assert loaded_template.variants == effects_pedal_template.variants

def test_audio_interface_template_initialization(audio_interface_template):
    """Test audio interface template initialization."""
    assert audio_interface_template.name == "Audio Interface"
    assert audio_interface_template.description == "Template for audio interface circuits"
    assert audio_interface_template.version == "1.0.0"
    
    # Check components
    components = audio_interface_template.component_manager.get_components()
    assert len(components) == 4
    assert any(c.id == "U1" and c.value == "PCM1808" for c in components)
    assert any(c.id == "U2" and c.value == "PCM5102" for c in components)
    assert any(c.id == "U3" and c.value == "CP2102" for c in components)
    assert any(c.id == "U4" and c.value == "LM317" for c in components)
    
    # Check variants
    assert "Standard" in audio_interface_template.variants
    assert "Pro" in audio_interface_template.variants

def test_mixing_console_template_initialization(mixing_console_template):
    """Test mixing console template initialization."""
    assert mixing_console_template.name == "Mixing Console"
    assert mixing_console_template.description == "Template for mixing console circuits"
    assert mixing_console_template.version == "1.0.0"
    
    # Check components
    components = mixing_console_template.component_manager.get_components()
    assert len(components) == 4
    assert any(c.id == "U1" and c.value == "NE5532" for c in components)
    assert any(c.id == "R1" and c.value == "10k" for c in components)
    assert any(c.id == "U2" and c.value == "TL072" for c in components)
    assert any(c.id == "U3" and c.value == "NE5532" for c in components)
    
    # Check variants
    assert "Standard" in mixing_console_template.variants
    assert "Professional" in mixing_console_template.variants

def test_audio_interface_template_save_load(audio_interface_template, template_dir):
    """Test saving and loading audio interface template."""
    # Save template
    audio_interface_template.save()
    assert (template_dir / "template.json").exists()
    
    # Load template
    loaded_template = AudioInterfaceTemplate(str(template_dir))
    loaded_template.load()
    
    assert loaded_template.name == audio_interface_template.name
    assert loaded_template.description == audio_interface_template.description
    assert loaded_template.version == audio_interface_template.version
    
    # Check components
    loaded_components = loaded_template.component_manager.get_components()
    original_components = audio_interface_template.component_manager.get_components()
    assert len(loaded_components) == len(original_components)
    
    # Check variants
    assert loaded_template.variants == audio_interface_template.variants

def test_mixing_console_template_save_load(mixing_console_template, template_dir):
    """Test saving and loading mixing console template."""
    # Save template
    mixing_console_template.save()
    assert (template_dir / "template.json").exists()
    
    # Load template
    loaded_template = MixingConsoleTemplate(str(template_dir))
    loaded_template.load()
    
    assert loaded_template.name == mixing_console_template.name
    assert loaded_template.description == mixing_console_template.description
    assert loaded_template.version == mixing_console_template.version
    
    # Check components
    loaded_components = loaded_template.component_manager.get_components()
    original_components = mixing_console_template.component_manager.get_components()
    assert len(loaded_components) == len(original_components)
    
    # Check variants
    assert loaded_template.variants == mixing_console_template.variants 
