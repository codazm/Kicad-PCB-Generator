"""End-to-end tests for audio PCB validation."""
import os
import pytest
import pcbnew
from pathlib import Path
from kicad_pcb_generator.audio.validation.audio_validator import AudioPCBValidator
from kicad_pcb_generator.utils.config.settings import Settings
from kicad_pcb_generator.utils.logging.logger import Logger
from kicad_pcb_generator.core.validation.base_validator import ValidationCategory
from kicad_pcb_generator.core.validation import ValidationSeverity

class TestAudioPCBValidation:
    """Test suite for audio PCB validation."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent / "test_data"
    
    @pytest.fixture
    def settings(self):
        """Get settings instance."""
        settings = Settings()
        # Enable all validation rules
        settings.set("validation.components.enabled", True)
        settings.set("validation.connections.enabled", True)
        settings.set("validation.power.enabled", True)
        settings.set("validation.ground.enabled", True)
        settings.set("validation.signal.enabled", True)
        settings.set("validation.audio.enabled", True)
        settings.set("validation.manufacturing.enabled", True)
        return settings
    
    @pytest.fixture
    def logger(self):
        """Get logger instance."""
        return Logger(__name__)
    
    @pytest.fixture
    def validator(self, settings, logger):
        """Get validator instance."""
        return AudioPCBValidator(settings=settings, logger=logger)
    
    def test_valid_audio_pcb(self, validator, test_data_dir):
        """Test validation of a correctly designed audio PCB."""
        # Load test board
        board_path = test_data_dir / "valid_audio_pcb.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        
        # Check that all validation categories are present
        categories = {result.category for result in results}
        assert "components" in categories
        assert "connections" in categories
        assert "power" in categories
        assert "ground" in categories
        assert "signal" in categories
        assert "audio" in categories
        assert "manufacturing" in categories
        
        # Check that there are no errors
        errors = [result for result in results if result.severity == ValidationSeverity.ERROR]
        assert len(errors) == 0
    
    def test_invalid_component_placement(self, validator, test_data_dir):
        """Test validation of a PCB with incorrect component placement."""
        # Load test board
        board_path = test_data_dir / "invalid_component_placement.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        
        # Check for component placement errors
        component_errors = [
            result for result in results 
            if result.category == "components" and result.severity == ValidationSeverity.ERROR
        ]
        assert len(component_errors) > 0
        
        # Verify error messages
        error_messages = {error.message for error in component_errors}
        assert any("invalid layer" in msg.lower() for msg in error_messages)
    
    def test_invalid_power_supply(self, validator, test_data_dir):
        """Test validation of a PCB with power supply issues."""
        # Load test board
        board_path = test_data_dir / "invalid_power_supply.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        
        # Check for power supply errors
        power_errors = [
            result for result in results 
            if result.category == "power" and result.severity == ValidationSeverity.ERROR
        ]
        assert len(power_errors) > 0
        
        # Verify error messages
        error_messages = {error.message for error in power_errors}
        assert any("missing power net" in msg.lower() for msg in error_messages)
    
    def test_invalid_grounding(self, validator, test_data_dir):
        """Test validation of a PCB with grounding issues."""
        # Load test board
        board_path = test_data_dir / "invalid_grounding.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        
        # Check for grounding errors
        ground_errors = [
            result for result in results 
            if result.category == "ground" and result.severity == ValidationSeverity.ERROR
        ]
        assert len(ground_errors) > 0
        
        # Verify error messages
        error_messages = {error.message for error in ground_errors}
        assert any("missing ground connection" in msg.lower() for msg in error_messages)
    
    def test_invalid_signal_paths(self, validator, test_data_dir):
        """Test validation of a PCB with signal path issues."""
        # Load test board
        board_path = test_data_dir / "invalid_signal_paths.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        
        # Check for signal path errors
        signal_errors = [
            result for result in results 
            if result.category == "signal" and result.severity == ValidationSeverity.ERROR
        ]
        assert len(signal_errors) > 0
        
        # Verify error messages
        error_messages = {error.message for error in signal_errors}
        assert any("unconnected pin" in msg.lower() for msg in error_messages)
    
    def test_invalid_manufacturing(self, validator, test_data_dir):
        """Test validation of a PCB with manufacturing rule violations."""
        # Load test board
        board_path = test_data_dir / "invalid_manufacturing.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        
        # Check for manufacturing errors
        manufacturing_errors = [
            result for result in results 
            if result.category == "manufacturing" and result.severity == ValidationSeverity.ERROR
        ]
        assert len(manufacturing_errors) > 0
        
        # Verify error messages
        error_messages = {error.message for error in manufacturing_errors}
        assert any("trace width too small" in msg.lower() for msg in error_messages)
        assert any("clearance too small" in msg.lower() for msg in error_messages)
        assert any("via size too small" in msg.lower() for msg in error_messages)
        assert any("pad size too small" in msg.lower() for msg in error_messages)
    
    def test_disabled_validation(self, validator, test_data_dir):
        """Test that disabled validation rules are not checked."""
        # Disable all validation rules
        validator.settings.enabled = False
        
        # Load test board
        board_path = test_data_dir / "invalid_audio_pcb.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        assert len(results) == 0
    
    def test_custom_validation_rules(self, validator, test_data_dir):
        """Test validation with custom manufacturing rules."""
        # Update manufacturing rules to be more strict
        validator.settings.rules.manufacturing.min_trace_width = 0.3
        validator.settings.rules.manufacturing.min_clearance = 0.3
        
        # Load test board
        board_path = test_data_dir / "valid_audio_pcb.kicad_pcb"
        board = pcbnew.LoadBoard(str(board_path))
        
        results = validator.validate(board)
        
        # Check for manufacturing errors with new rules
        manufacturing_errors = [
            result for result in results 
            if result.category == "manufacturing" and result.severity == ValidationSeverity.ERROR
        ]
        assert len(manufacturing_errors) > 0
        
        # Verify error messages
        error_messages = {error.message for error in manufacturing_errors}
        assert any("trace width too small" in msg.lower() for msg in error_messages)
        assert any("clearance too small" in msg.lower() for msg in error_messages) 