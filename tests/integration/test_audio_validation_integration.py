"""Integration tests for audio validation with new validation modules."""

import unittest
from unittest.mock import MagicMock, patch
import pcbnew
import numpy as np
from pathlib import Path
import tempfile
import shutil

from kicad_pcb_generator.audio.validation.audio_validator import AudioPCBValidator
from kicad_pcb_generator.core.testing.signal_integrity_tester import SignalIntegrityTester
from kicad_pcb_generator.core.testing.power_ground_tester import PowerGroundTester
from kicad_pcb_generator.core.testing.emi_emc_tester import EMIEMCTester
from kicad_pcb_generator.core.validation.base_validator import ValidationCategory
from kicad_pcb_generator.audio.rules.design import AudioDesignRules, SignalType

class TestAudioValidationIntegration(unittest.TestCase):
    """Test integration between audio validation and new validation modules."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_dir = tempfile.mkdtemp()
        cls.board = MagicMock(spec=pcbnew.BOARD)
        
        # Create mock audio tracks
        cls.audio_track = MagicMock(spec=pcbnew.TRACK)
        cls.audio_track.GetNetname.return_value = "AUDIO_SIG"
        cls.audio_track.GetWidth.return_value = 0.2e6  # 0.2mm
        cls.audio_track.GetStart.return_value = MagicMock(x=0, y=0)
        cls.audio_track.GetEnd.return_value = MagicMock(x=10e6, y=0)
        cls.audio_track.GetLayer.return_value = pcbnew.F_Cu
        
        # Create mock ground zone
        cls.ground_zone = MagicMock(spec=pcbnew.ZONE)
        cls.ground_zone.GetNetname.return_value = "GND"
        cls.ground_zone.GetArea.return_value = 5000e6  # 5000mm² (50% coverage)
        
        # Set up board mocks
        cls.board.GetTracks.return_value = [cls.audio_track]
        cls.board.GetZones.return_value = [cls.ground_zone]
        
        # Initialize validators
        cls.audio_validator = AudioPCBValidator()
        cls.si_tester = SignalIntegrityTester(cls.board)
        cls.pg_tester = PowerGroundTester(cls.board)
        cls.emi_tester = EMIEMCTester(cls.board)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.test_dir)

    def test_audio_signal_integrity_integration(self):
        """Test integration between audio validation and signal integrity testing."""
        # Run audio validation
        audio_results = self.audio_validator.validate_board(self.board)
        
        # Run signal integrity tests
        si_results = self.si_tester.test_signal_integrity()
        
        # Verify both validations are consistent
        self.assertIn(ValidationCategory.SIGNAL, audio_results)
        self.assertIn('impedance', si_results)
        self.assertIn('crosstalk', si_results)
        self.assertIn('reflections', si_results)
        
        # Check signal integrity metrics
        self.assertTrue(si_results['impedance']['passed'])
        self.assertTrue(si_results['crosstalk']['passed'])
        self.assertTrue(si_results['reflections']['passed'])

    def test_audio_power_ground_integration(self):
        """Test integration between audio validation and power/ground testing."""
        # Run audio validation
        audio_results = self.audio_validator.validate_board(self.board)
        
        # Run power/ground tests
        pg_results = self.pg_tester.test_power_ground()
        
        # Verify both validations are consistent
        self.assertIn(ValidationCategory.GROUND, audio_results)
        self.assertIn('power_supply', pg_results)
        self.assertIn('ground_plane', pg_results)
        self.assertIn('power_distribution', pg_results)
        
        # Check power/ground metrics
        self.assertTrue(pg_results['power_supply']['passed'])
        self.assertTrue(pg_results['ground_plane']['passed'])
        self.assertTrue(pg_results['power_distribution']['passed'])

    def test_audio_emi_emc_integration(self):
        """Test integration between audio validation and EMI/EMC testing."""
        # Run audio validation
        audio_results = self.audio_validator.validate_board(self.board)
        
        # Run EMI/EMC tests
        emi_results = self.emi_tester.test_emi_emc()
        
        # Verify both validations are consistent
        self.assertIn(ValidationCategory.EMI_EMC, audio_results)
        self.assertIn('emissions', emi_results)
        self.assertIn('immunity', emi_results)
        self.assertIn('shielding', emi_results)
        
        # Check EMI/EMC metrics
        self.assertTrue(emi_results['emissions']['passed'])
        self.assertTrue(emi_results['immunity']['passed'])
        self.assertTrue(emi_results['shielding']['passed'])

    def test_audio_specific_validation_rules(self):
        """Test audio-specific validation rules with new validation modules."""
        # Create audio-specific test cases
        test_cases = [
            {
                'name': 'balanced_audio',
                'track': MagicMock(spec=pcbnew.TRACK),
                'expected_si': True,
                'expected_pg': True,
                'expected_emi': True
            },
            {
                'name': 'unbalanced_audio',
                'track': MagicMock(spec=pcbnew.TRACK),
                'expected_si': False,
                'expected_pg': True,
                'expected_emi': False
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case['name']):
                # Set up test case
                track = case['track']
                track.GetNetname.return_value = f"{case['name']}_SIG"
                track.GetWidth.return_value = 0.2e6
                self.board.GetTracks.return_value = [track]
                
                # Run validations
                si_results = self.si_tester.test_signal_integrity()
                pg_results = self.pg_tester.test_power_ground()
                emi_results = self.emi_tester.test_emi_emc()
                
                # Verify results match expectations
                self.assertEqual(si_results['impedance']['passed'], case['expected_si'])
                self.assertEqual(pg_results['power_supply']['passed'], case['expected_pg'])
                self.assertEqual(emi_results['emissions']['passed'], case['expected_emi'])

    def test_validation_rule_interactions(self):
        """Test interactions between audio validation rules and new validation modules."""
        # Create test cases with conflicting rules
        test_cases = [
            {
                'name': 'tight_impedance',
                'si_config': {'impedance_mismatch_threshold': 2.0},  # Stricter
                'audio_config': {'impedance_tolerance': 5.0},  # More lenient
                'expected_result': False  # Should fail due to stricter SI rule
            },
            {
                'name': 'loose_impedance',
                'si_config': {'impedance_mismatch_threshold': 10.0},  # More lenient
                'audio_config': {'impedance_tolerance': 2.0},  # Stricter
                'expected_result': False  # Should fail due to stricter audio rule
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case['name']):
                # Configure validators
                self.si_tester.config.impedance_mismatch_threshold = case['si_config']['impedance_mismatch_threshold']
                self.audio_validator.settings.set_rule_setting('audio', 'impedance_tolerance', case['audio_config']['impedance_tolerance'])
                
                # Run validations
                si_results = self.si_tester.test_signal_integrity()
                audio_results = self.audio_validator.validate_board(self.board)
                
                # Verify results
                self.assertEqual(si_results['impedance']['passed'], case['expected_result'])
                self.assertEqual(
                    all(not result.is_error() for result in audio_results.get(ValidationCategory.SIGNAL, [])),
                    case['expected_result']
                )

if __name__ == '__main__':
    unittest.main() 
