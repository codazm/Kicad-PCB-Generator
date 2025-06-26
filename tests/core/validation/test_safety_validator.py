"""Tests for safety validation functionality."""

import unittest
from unittest.mock import MagicMock, patch
import pcbnew

from kicad_pcb_generator.core.validation.safety_validator import (
    SafetyValidator,
    SafetyCategory,
    SafetyResult
)

class TestSafetyValidator(unittest.TestCase):
    """Test cases for safety validation functionality."""
    
    def setUp(self):
        """Set up test cases."""
        self.validator = SafetyValidator()
        self.board = MagicMock(spec=pcbnew.BOARD)
        
        # Mock board methods
        self.board.GetTracks.return_value = []
        self.board.GetFootprints.return_value = []
        self.board.GetVias.return_value = []
        self.board.Zones.return_value = []
        self.board.GetDesignSettings.return_value = MagicMock()
        self.board.GetDesignSettings().GetMinClearanceValue.return_value = 0.2
        self.board.GetDesignSettings().GetEdgeClearance.return_value = 0.3
    
    def test_electrical_safety_validation(self):
        """Test electrical safety validation."""
        # Create mock high-voltage track
        track = MagicMock(spec=pcbnew.PCB_TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetNetname.return_value = "HV_PWR"
        track.GetStart.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        self.board.GetTracks.return_value = [track]
        
        # Create mock ground zone
        zone = MagicMock(spec=pcbnew.ZONE)
        zone.GetNetname.return_value = "GND"
        zone.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        self.board.Zones.return_value = [zone]
        
        # Run validation
        results = self.validator._validate_electrical_safety(self.board)
        
        # Check results
        self.assertIn(ValidationCategory.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, SafetyResult) and
            r.safety_category == SafetyCategory.ELECTRICAL and
            "Clearance" in r.message
            for r in results[ValidationCategory.GENERAL]
        ))
    
    def test_thermal_safety_validation(self):
        """Test thermal safety validation."""
        # Create mock high-power component
        footprint = MagicMock(spec=pcbnew.FOOTPRINT)
        footprint.GetReference.return_value = "U1"
        footprint.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        footprint.GetValue.return_value = "IC"
        
        # Create mock pad without thermal relief
        pad = MagicMock(spec=pcbnew.PAD)
        pad.GetNetname.return_value = "VCC"
        pad.GetThermalSpokeWidth.return_value = 0
        footprint.Pads.return_value = [pad]
        
        self.board.GetFootprints.return_value = [footprint]
        
        # Run validation
        results = self.validator._validate_thermal_safety(self.board)
        
        # Check results
        self.assertIn(ValidationCategory.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, SafetyResult) and
            r.safety_category == SafetyCategory.THERMAL and
            "thermal relief" in r.message.lower()
            for r in results[ValidationCategory.GENERAL]
        ))
    
    def test_mechanical_safety_validation(self):
        """Test mechanical safety validation."""
        # Create mock mounting hole
        footprint = MagicMock(spec=pcbnew.FOOTPRINT)
        footprint.GetReference.return_value = "MH1"
        footprint.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        # Create mock pad with insufficient clearance
        pad = MagicMock(spec=pcbnew.PAD)
        pad.GetClearance.return_value = 0.5
        footprint.Pads.return_value = [pad]
        
        self.board.GetFootprints.return_value = [footprint]
        
        # Run validation
        results = self.validator._validate_mechanical_safety(self.board)
        
        # Check results
        self.assertIn(ValidationCategory.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, SafetyResult) and
            r.safety_category == SafetyCategory.MECHANICAL and
            "clearance" in r.message.lower()
            for r in results[ValidationCategory.GENERAL]
        ))
    
    def test_component_safety_validation(self):
        """Test component safety validation."""
        # Create mock resistor
        footprint = MagicMock(spec=pcbnew.FOOTPRINT)
        footprint.GetReference.return_value = "R1"
        footprint.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        footprint.GetValue.return_value = "10k"
        
        self.board.GetFootprints.return_value = [footprint]
        
        # Run validation
        results = self.validator._validate_component_safety(self.board)
        
        # Check results
        self.assertIn(ValidationCategory.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, SafetyResult) and
            r.safety_category == SafetyCategory.COMPONENT and
            "power rating" in r.message.lower()
            for r in results[ValidationCategory.GENERAL]
        ))
    
    def test_audio_safety_validation(self):
        """Test audio safety validation."""
        # Create mock balanced pair tracks
        track1 = MagicMock(spec=pcbnew.PCB_TRACK)
        track1.GetType.return_value = pcbnew.PCB_TRACE_T
        track1.GetNetname.return_value = "AUDIO_IN+"
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        
        track2 = MagicMock(spec=pcbnew.PCB_TRACK)
        track2.GetType.return_value = pcbnew.PCB_TRACE_T
        track2.GetNetname.return_value = "AUDIO_IN-"
        track2.GetStart.return_value = MagicMock(x=1 * 1e6, y=1 * 1e6)  # 1mm away
        
        self.board.GetTracks.return_value = [track1, track2]
        
        # Create mock ground zone
        zone = MagicMock(spec=pcbnew.ZONE)
        zone.GetNetname.return_value = "GND"
        zone.GetBoundingBox.return_value = MagicMock()
        zone.GetBoundingBox().GetWidth.return_value = 50 * 1e6  # 50mm
        zone.GetBoundingBox().GetHeight.return_value = 50 * 1e6  # 50mm
        zone.GetBoundingBox().GetLeft.return_value = 0
        zone.GetBoundingBox().GetRight.return_value = 50 * 1e6
        zone.GetBoundingBox().GetTop.return_value = 0
        zone.GetBoundingBox().GetBottom.return_value = 50 * 1e6
        
        self.board.Zones.return_value = [zone]
        
        # Create mock IC with decoupling caps
        ic = MagicMock(spec=pcbnew.FOOTPRINT)
        ic.GetReference.return_value = "U1"
        ic.GetPosition.return_value = MagicMock(x=25 * 1e6, y=25 * 1e6)
        
        cap1 = MagicMock(spec=pcbnew.FOOTPRINT)
        cap1.GetReference.return_value = "C1"
        cap1.GetPosition.return_value = MagicMock(x=26 * 1e6, y=26 * 1e6)
        
        cap2 = MagicMock(spec=pcbnew.FOOTPRINT)
        cap2.GetReference.return_value = "C2"
        cap2.GetPosition.return_value = MagicMock(x=27 * 1e6, y=27 * 1e6)
        
        self.board.GetFootprints.return_value = [ic, cap1, cap2]
        
        # Run validation
        results = self.validator.validate_board(self.board)
        
        # Check results
        self.assertIn(pcbnew.ValidationCategory.GENERAL, results)
        audio_results = [r for r in results[pcbnew.ValidationCategory.GENERAL]
                        if isinstance(r, SafetyResult) and r.safety_category == SafetyCategory.AUDIO]
        
        # Should have warnings for:
        # 1. Balanced pair spacing
        # 2. Ground plane coverage
        self.assertGreaterEqual(len(audio_results), 2)
        
        # Verify balanced pair spacing warning
        spacing_warnings = [r for r in audio_results if "spacing" in r.message.lower()]
        self.assertGreaterEqual(len(spacing_warnings), 1)
        
        # Verify ground plane coverage warning
        coverage_warnings = [r for r in audio_results if "coverage" in r.message.lower()]
        self.assertGreaterEqual(len(coverage_warnings), 1)
    
    def test_voltage_level_detection(self):
        """Test voltage level detection."""
        self.assertEqual(self.validator._get_voltage_level("HV_PWR"), "HV")
        self.assertEqual(self.validator._get_voltage_level("VCC"), "MV")
        self.assertEqual(self.validator._get_voltage_level("SIG"), "LV")
        self.assertIsNone(self.validator._get_voltage_level("UNKNOWN"))
    
    def test_component_type_detection(self):
        """Test component type detection."""
        self.assertEqual(self.validator._get_component_type("R1"), "R")
        self.assertEqual(self.validator._get_component_type("C1"), "C")
        self.assertEqual(self.validator._get_component_type("L1"), "L")
        self.assertEqual(self.validator._get_component_type("U1"), "IC")
        self.assertEqual(self.validator._get_component_type("Q1"), "PWR")
        self.assertIsNone(self.validator._get_component_type("UNKNOWN"))
    
    def test_component_value_extraction(self):
        """Test component value extraction."""
        # Create mock footprint
        footprint = MagicMock(spec=pcbnew.FOOTPRINT)
        
        # Test resistor value
        footprint.GetValue.return_value = "10k"
        self.assertEqual(self.validator._get_component_value(footprint), 10000.0)
        
        # Test capacitor value
        footprint.GetValue.return_value = "100nF"
        self.assertEqual(self.validator._get_component_value(footprint), 0.0001)
        
        # Test inductor value
        footprint.GetValue.return_value = "10uH"
        self.assertEqual(self.validator._get_component_value(footprint), 0.00001)
        
        # Test invalid value
        footprint.GetValue.return_value = "INVALID"
        self.assertIsNone(self.validator._get_component_value(footprint))
    
    def test_power_rating_calculation(self):
        """Test power rating calculation."""
        # Create mock footprint
        footprint = MagicMock(spec=pcbnew.FOOTPRINT)
        footprint.GetReference.return_value = "R1"
        footprint.GetValue.return_value = "10k"
        
        # Test resistor power rating
        self.assertEqual(self.validator._get_power_rating(footprint), 1000.0)
        
        # Test capacitor power rating
        footprint.GetReference.return_value = "C1"
        footprint.GetValue.return_value = "100nF"
        self.assertEqual(self.validator._get_power_rating(footprint), 0.001)
        
        # Test inductor power rating
        footprint.GetReference.return_value = "L1"
        footprint.GetValue.return_value = "10uH"
        self.assertEqual(self.validator._get_power_rating(footprint), 0.00001)
        
        # Test invalid component
        footprint.GetReference.return_value = "UNKNOWN"
        self.assertIsNone(self.validator._get_power_rating(footprint))
    
    def test_component_distance_calculation(self):
        """Test component distance calculation."""
        # Create mock components
        comp1 = MagicMock(spec=pcbnew.FOOTPRINT)
        comp1.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        comp2 = MagicMock(spec=pcbnew.FOOTPRINT)
        comp2.GetPosition.return_value = pcbnew.VECTOR2I(2000000, 2000000)
        
        # Calculate distance
        distance = self.validator._calculate_component_distance(comp1, comp2)
        
        # Check result
        self.assertAlmostEqual(distance, 1.414, places=3)  # sqrt(2) mm
    
    def test_decoupling_cap_counting(self):
        """Test decoupling capacitor counting."""
        # Create mock target
        target = MagicMock(spec=pcbnew.ZONE)
        target.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        # Create mock decoupling capacitor
        footprint = MagicMock(spec=pcbnew.FOOTPRINT)
        footprint.GetReference.return_value = "C1"
        footprint.GetNetname.return_value = "GND"
        footprint.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        self.board.GetFootprints.return_value = [footprint]
        
        # Count decoupling capacitors
        count = self.validator._count_decoupling_caps(self.board, target)
        
        # Check result
        self.assertEqual(count, 1)
    
    def test_emi_emc_safety_validation(self):
        """Test EMI/EMC safety validation."""
        # Create mock ground zones
        zone1 = MagicMock(spec=pcbnew.ZONE)
        zone1.GetNetname.return_value = "GND"
        zone1.GetBoundingBox.return_value = MagicMock()
        zone1.GetBoundingBox().GetWidth.return_value = 50 * 1e6
        zone1.GetBoundingBox().GetHeight.return_value = 50 * 1e6
        
        zone2 = MagicMock(spec=pcbnew.ZONE)
        zone2.GetNetname.return_value = "GND"
        zone2.GetBoundingBox.return_value = MagicMock()
        zone2.GetBoundingBox().GetWidth.return_value = 50 * 1e6
        zone2.GetBoundingBox().GetHeight.return_value = 50 * 1e6
        
        self.board.Zones.return_value = [zone1, zone2]
        
        # Create mock ground vias
        via1 = MagicMock(spec=pcbnew.PCB_VIA)
        via1.GetNetname.return_value = "GND"
        via1.GetPosition.return_value = MagicMock(x=0, y=0)
        
        via2 = MagicMock(spec=pcbnew.PCB_VIA)
        via2.GetNetname.return_value = "GND"
        via2.GetPosition.return_value = MagicMock(x=15 * 1e6, y=15 * 1e6)  # 15mm away
        
        self.board.GetVias.return_value = [via1, via2]
        
        # Create mock RF track
        rf_track = MagicMock(spec=pcbnew.PCB_TRACK)
        rf_track.GetType.return_value = pcbnew.PCB_TRACE_T
        rf_track.GetNetname.return_value = "RF_IN"
        rf_track.GetStart.return_value = MagicMock(x=25 * 1e6, y=25 * 1e6)
        rf_track.GetLayer.return_value = 1
        
        # Create mock clock track
        clock_track = MagicMock(spec=pcbnew.PCB_TRACK)
        clock_track.GetType.return_value = pcbnew.PCB_TRACE_T
        clock_track.GetNetname.return_value = "CLK"
        clock_track.GetStart.return_value = MagicMock(x=26 * 1e6, y=26 * 1e6)
        
        self.board.GetTracks.return_value = [rf_track, clock_track]
        
        # Create mock filter capacitor
        filter_cap = MagicMock(spec=pcbnew.FOOTPRINT)
        filter_cap.GetReference.return_value = "C1"
        filter_cap.GetValue.return_value = "EMI_FILTER"
        filter_cap.GetPosition.return_value = MagicMock(x=40 * 1e6, y=40 * 1e6)
        
        self.board.GetFootprints.return_value = [filter_cap]
        
        # Run validation
        results = self.validator.validate_board(self.board)
        
        # Check results
        self.assertIn(pcbnew.ValidationCategory.GENERAL, results)
        emi_results = [r for r in results[pcbnew.ValidationCategory.GENERAL]
                      if isinstance(r, SafetyResult) and r.safety_category == SafetyCategory.EMI_EMC]
        
        # Should have warnings for:
        # 1. Ground stitching via spacing
        # 2. RF signal shielding
        # 3. Clock trace isolation
        # 4. Filter capacitor placement
        self.assertGreaterEqual(len(emi_results), 4)
        
        # Verify ground stitching warning
        stitching_warnings = [r for r in emi_results if "stitching" in r.message.lower()]
        self.assertGreaterEqual(len(stitching_warnings), 1)
        
        # Verify RF shielding warning
        shielding_warnings = [r for r in emi_results if "shielding" in r.message.lower()]
        self.assertGreaterEqual(len(shielding_warnings), 1)
        
        # Verify clock trace warning
        clock_warnings = [r for r in emi_results if "clock" in r.message.lower()]
        self.assertGreaterEqual(len(clock_warnings), 1)
        
        # Verify filter cap warning
        filter_warnings = [r for r in emi_results if "filter" in r.message.lower()]
        self.assertGreaterEqual(len(filter_warnings), 1)
    
    def test_balanced_pair_detection(self):
        """Test balanced pair detection."""
        # Create mock tracks with balanced pair naming
        track1 = MagicMock(spec=pcbnew.PCB_TRACK)
        track1.GetType.return_value = pcbnew.PCB_TRACE_T
        track1.GetNetname.return_value = "AUDIO_IN+"
        
        track2 = MagicMock(spec=pcbnew.PCB_TRACK)
        track2.GetType.return_value = pcbnew.PCB_TRACE_T
        track2.GetNetname.return_value = "AUDIO_IN-"
        
        self.board.GetTracks.return_value = [track1, track2]
        
        # Test balanced pair detection
        pairs = self.validator._find_balanced_pairs(self.board)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0].GetNetname(), "AUDIO_IN+")
        self.assertEqual(pairs[0][1].GetNetname(), "AUDIO_IN-")
    
    def test_shielding_coverage_calculation(self):
        """Test shielding coverage calculation."""
        # Create mock track
        track = MagicMock(spec=pcbnew.PCB_TRACK)
        track.GetStart.return_value = MagicMock(x=25 * 1e6, y=25 * 1e6)
        
        # Create mock ground zone
        zone = MagicMock(spec=pcbnew.ZONE)
        zone.GetBoundingBox.return_value = MagicMock()
        zone.GetBoundingBox().GetLeft.return_value = 0
        zone.GetBoundingBox().GetRight.return_value = 50 * 1e6
        zone.GetBoundingBox().GetTop.return_value = 0
        zone.GetBoundingBox().GetBottom.return_value = 50 * 1e6
        
        # Test shielding coverage calculation
        coverage = self.validator._calculate_shielding_coverage(track, zone)
        self.assertEqual(coverage, 1.0)  # Track is within zone bounds
        
        # Test track outside zone bounds
        track.GetStart.return_value = MagicMock(x=75 * 1e6, y=75 * 1e6)
        coverage = self.validator._calculate_shielding_coverage(track, zone)
        self.assertEqual(coverage, 0.0)  # Track is outside zone bounds
    
    def test_crosstalk_calculation(self):
        """Test crosstalk calculation."""
        # Create mock tracks
        track1 = MagicMock(spec=pcbnew.PCB_TRACK)
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        
        track2 = MagicMock(spec=pcbnew.PCB_TRACK)
        track2.GetStart.return_value = MagicMock(x=1 * 1e6, y=1 * 1e6)  # 1mm away
        
        # Test crosstalk calculation
        crosstalk = self.validator._calculate_crosstalk(track1, track2)
        self.assertGreater(crosstalk, 0.0)
        self.assertLess(crosstalk, 1.0)
        
        # Test tracks further apart
        track2.GetStart.return_value = MagicMock(x=10 * 1e6, y=10 * 1e6)  # 10mm away
        crosstalk = self.validator._calculate_crosstalk(track1, track2)
        self.assertLess(crosstalk, 0.1)  # Should be much lower for greater distance

if __name__ == '__main__':
    unittest.main() 