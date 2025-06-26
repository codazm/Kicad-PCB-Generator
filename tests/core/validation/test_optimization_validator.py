"""Tests for the optimization validator module."""

import unittest
from unittest.mock import MagicMock, patch
import pcbnew
import math

from kicad_pcb_generator.core.validation.optimization_validator import (
    OptimizationValidator,
    OptimizationCategory,
    OptimizationResult
)

class TestOptimizationValidator(unittest.TestCase):
    """Test cases for the OptimizationValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = OptimizationValidator()
        self.mock_board = MagicMock(spec=pcbnew.BOARD)
        
        # Mock board methods
        self.mock_board.GetFootprints.return_value = []
        self.mock_board.GetTracks.return_value = []
        self.mock_board.GetVias.return_value = []
        self.mock_board.Zones.return_value = []
        self.mock_board.GetPads.return_value = []
        self.mock_board.GetLayerName.return_value = "Test Layer"
        
        # Mock board dimensions
        self.mock_board.GetBoardEdgesBoundingBox.return_value = MagicMock(
            GetWidth=lambda: 100000000,  # 100mm
            GetHeight=lambda: 100000000  # 100mm
        )
    
    def test_routing_optimization(self):
        """Test routing optimization validation."""
        # Create mock tracks with long lengths
        mock_track1 = MagicMock()
        mock_track1.GetType.return_value = pcbnew.PCB_TRACE_T
        mock_track1.GetLength.return_value = 100000000  # 100mm
        
        mock_track2 = MagicMock()
        mock_track2.GetType.return_value = pcbnew.PCB_TRACE_T
        mock_track2.GetLength.return_value = 100000000  # 100mm
        
        self.mock_board.GetTracks.return_value = [mock_track1, mock_track2]
        
        # Create mock vias
        mock_via = MagicMock()
        self.mock_board.GetVias.return_value = [mock_via] * 1200  # 1200 vias
        
        # Run validation
        results = self.validator._validate_routing_optimization(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.ROUTING and
            "High average track length" in r.message
            for r in results[pcbnew.GENERAL]
        ))
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.ROUTING and
            "High via count" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_component_placement_optimization(self):
        """Test component placement optimization validation."""
        # Create mock footprints
        mock_footprints = []
        for i in range(200):  # 200 components
            mock_footprint = MagicMock()
            mock_footprint.GetPosition.return_value = pcbnew.VECTOR2I(
                50000000, 50000000  # All in center quadrant
            )
            mock_footprints.append(mock_footprint)
        
        self.mock_board.GetFootprints.return_value = mock_footprints
        
        # Run validation
        results = self.validator._validate_component_placement_optimization(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.COMPONENT_PLACEMENT and
            "High component density" in r.message
            for r in results[pcbnew.GENERAL]
        ))
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.COMPONENT_PLACEMENT and
            "Uneven component distribution" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_power_distribution_optimization(self):
        """Test power distribution optimization validation."""
        # Create mock power zone
        mock_zone = MagicMock()
        mock_zone.GetNetname.return_value = "PWR_3V3"
        mock_zone.GetArea.return_value = 2000000000000  # 2000mm²
        
        self.mock_board.Zones.return_value = [mock_zone]
        self.mock_board.GetPads.return_value = []  # No connected pads
        
        # Run validation
        results = self.validator._validate_power_distribution_optimization(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.POWER_DISTRIBUTION and
            "Low power plane coverage" in r.message
            for r in results[pcbnew.GENERAL]
        ))
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.POWER_DISTRIBUTION and
            "Low number of connections" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_thermal_optimization(self):
        """Test thermal optimization validation."""
        # Create mock high-power components
        mock_comp1 = MagicMock()
        mock_comp1.GetReference.return_value = "U1"
        mock_comp1.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_comp1.GetPowerDissipation.return_value = 2.0  # 2W
        
        mock_comp2 = MagicMock()
        mock_comp2.GetReference.return_value = "U2"
        mock_comp2.GetPosition.return_value = pcbnew.VECTOR2I(2000000, 2000000)
        mock_comp2.GetPowerDissipation.return_value = 3.0  # 3W
        
        self.mock_board.GetFootprints.return_value = [mock_comp1, mock_comp2]
        
        # Run validation
        results = self.validator._validate_thermal_optimization(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.THERMAL and
            "High-power components" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_manufacturing_optimization(self):
        """Test manufacturing optimization validation."""
        # Create mock footprints with non-orthogonal orientation
        mock_footprints = []
        for i in range(20):  # 20 components
            mock_footprint = MagicMock()
            mock_footprint.GetOrientation.return_value = 45  # 45-degree rotation
            mock_footprints.append(mock_footprint)
        
        self.mock_board.GetFootprints.return_value = mock_footprints
        
        # Create mock vias
        mock_vias = []
        for i in range(100):  # 100 vias
            mock_via = MagicMock()
            mock_via.GetViaType.return_value = pcbnew.VIA_BLIND if i < 30 else pcbnew.VIA_THROUGH
            mock_vias.append(mock_via)
        
        self.mock_board.GetVias.return_value = mock_vias
        
        # Run validation
        results = self.validator._validate_manufacturing_optimization(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.MANUFACTURING and
            "High number of non-orthogonal components" in r.message
            for r in results[pcbnew.GENERAL]
        ))
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.MANUFACTURING and
            "High ratio of complex vias" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_cost_optimization(self):
        """Test cost optimization validation."""
        # Mock board dimensions for large area
        self.mock_board.GetBoardEdgesBoundingBox.return_value = MagicMock(
            GetWidth=lambda: 200000000,  # 200mm
            GetHeight=lambda: 200000000  # 200mm
        )
        
        # Mock layer count
        self.mock_board.IsLayerEnabled.side_effect = lambda x: x < 6  # 6 layers
        
        # Mock hole count
        mock_pads = []
        for i in range(1200):  # 1200 holes
            mock_pad = MagicMock()
            mock_pad.GetAttribute.return_value = pcbnew.PAD_ATTRIB_PTH
            mock_pads.append(mock_pad)
        
        self.mock_board.GetPads.return_value = mock_pads
        
        # Run validation
        results = self.validator._validate_cost_optimization(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.COST and
            "Large board area" in r.message
            for r in results[pcbnew.GENERAL]
        ))
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.COST and
            "High layer count" in r.message
            for r in results[pcbnew.GENERAL]
        ))
        self.assertTrue(any(
            isinstance(r, OptimizationResult) and
            r.optimization_category == OptimizationCategory.COST and
            "High hole count" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_signal_integrity_optimization(self):
        """Test signal integrity optimization validation."""
        # Create mock high-speed signal track
        track = MagicMock(spec=pcbnew.PCB_TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetNetname.return_value = "DDR_CLK"
        track.GetWidth.return_value = 100000  # 0.1mm
        track.GetStart.return_value = MagicMock(x=0, y=0)
        track.GetLayer.return_value = pcbnew.F_Cu
        
        # Create mock ground zone
        zone = MagicMock()
        zone.GetNetname.return_value = "GND"
        zone.IsOnLayer.return_value = True
        
        self.mock_board.GetTracks.return_value = [track]
        self.mock_board.Zones.return_value = [zone]
        
        results = self.validator._validate_signal_integrity_optimization(self.mock_board)
        
        # Check for trace width warning
        self.assertTrue(any(
            result.message.startswith("High-speed signal DDR_CLK trace width") and
            result.optimization_category == OptimizationCategory.SIGNAL_INTEGRITY
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for ground plane reference warning
        zone.IsOnLayer.return_value = False
        results = self.validator._validate_signal_integrity_optimization(self.mock_board)
        self.assertTrue(any(
            result.message == "High-speed signal DDR_CLK lacks ground plane reference" and
            result.optimization_category == OptimizationCategory.SIGNAL_INTEGRITY
            for result in results[pcbnew.GENERAL]
        ))
    
    def test_emi_emc_optimization(self):
        """Test EMI/EMC optimization validation."""
        # Create mock ground zones
        zone1 = MagicMock()
        zone1.GetNetname.return_value = "GND"
        zone2 = MagicMock()
        zone2.GetNetname.return_value = "GND"
        
        # Create mock IC and decoupling cap
        ic = MagicMock()
        ic.GetReference.return_value = "U1"
        ic.GetPosition.return_value = MagicMock(x=0, y=0)
        
        cap = MagicMock()
        cap.GetReference.return_value = "C1"
        cap.GetNetname.return_value = "GND"
        cap.GetPosition.return_value = MagicMock(x=1000000, y=1000000)  # 1mm away
        
        self.mock_board.Zones.return_value = [zone1, zone2]
        self.mock_board.GetFootprints.return_value = [ic, cap]
        
        results = self.validator._validate_emi_emc_optimization(self.mock_board)
        
        # Check for ground plane stitching warning
        self.assertTrue(any(
            result.message.startswith("Insufficient ground plane stitching vias") and
            result.optimization_category == OptimizationCategory.EMI_EMC
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for decoupling warning
        self.assertTrue(any(
            result.message.startswith("Insufficient decoupling for U1") and
            result.optimization_category == OptimizationCategory.EMI_EMC
            for result in results[pcbnew.GENERAL]
        ))
    
    def test_dfm_optimization(self):
        """Test Design for Manufacturing optimization validation."""
        # Create mock pad with small annular ring
        pad = MagicMock()
        pad.GetName.return_value = "1"
        pad.GetSize.return_value = MagicMock(x=200000, y=200000)  # 0.2mm
        pad.GetDrillSize.return_value = MagicMock(x=190000, y=190000)  # 0.19mm
        pad.GetPosition.return_value = MagicMock(x=0, y=0)
        
        # Create mock footprint with small reference
        footprint = MagicMock()
        footprint.GetReference.return_value = "R1"
        footprint.GetPosition.return_value = MagicMock(x=0, y=0)
        footprint.Pads.return_value = [pad]
        ref = MagicMock()
        ref.GetTextSize.return_value = MagicMock(x=300000)  # 0.3mm
        ref.GetPosition.return_value = MagicMock(x=0, y=0)
        footprint.Reference.return_value = ref
        
        self.mock_board.GetPads.return_value = [pad]
        self.mock_board.GetFootprints.return_value = [footprint]
        
        results = self.validator._validate_dfm_optimization(self.mock_board)
        
        # Check for annular ring warning
        self.assertTrue(any(
            result.message.startswith("Small annular ring") and
            result.optimization_category == OptimizationCategory.DFM
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for reference size warning
        self.assertTrue(any(
            result.message.startswith("Small reference designator") and
            result.optimization_category == OptimizationCategory.DFM
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for polarity marking warning
        self.assertTrue(any(
            result.message.startswith("Missing polarity marking") and
            result.optimization_category == OptimizationCategory.DFM
            for result in results[pcbnew.GENERAL]
        ))
    
    def test_has_termination(self):
        """Test termination detection functionality."""
        # Create mock track
        track = MagicMock(spec=pcbnew.PCB_TRACK)
        track.GetNetname.return_value = "DDR_CLK"
        track.GetEnd.return_value = MagicMock(x=0, y=0)
        
        # Create mock termination resistor
        resistor = MagicMock()
        resistor.GetReference.return_value = "R1"
        resistor.GetNetname.return_value = "DDR_CLK"
        resistor.GetPosition.return_value = MagicMock(x=1000000, y=1000000)  # 1mm away
        
        self.mock_board.GetFootprints.return_value = [resistor]
        
        # Test termination detection
        self.assertTrue(self.validator._has_termination(track, self.mock_board))
        
        # Test with resistor too far away
        resistor.GetPosition.return_value = MagicMock(x=10000000, y=10000000)  # 10mm away
        self.assertFalse(self.validator._has_termination(track, self.mock_board))
        
        # Test with no resistor
        self.mock_board.GetFootprints.return_value = []
        self.assertFalse(self.validator._has_termination(track, self.mock_board))
    
    def test_audio_optimization(self):
        """Test audio optimization validation."""
        # Create mock balanced audio signal tracks
        track1 = MagicMock(spec=pcbnew.PCB_TRACK)
        track1.GetType.return_value = pcbnew.PCB_TRACE_T
        track1.GetNetname.return_value = "AUDIO_BAL+"
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        track1.GetLayer.return_value = pcbnew.F_Cu
        
        track2 = MagicMock(spec=pcbnew.PCB_TRACK)
        track2.GetType.return_value = pcbnew.PCB_TRACE_T
        track2.GetNetname.return_value = "AUDIO_BAL-"
        track2.GetStart.return_value = MagicMock(x=1000000, y=1000000)  # 1mm away
        track2.GetLayer.return_value = pcbnew.F_Cu
        
        # Create mock ground zone
        zone = MagicMock()
        zone.GetNetname.return_value = "GND"
        zone.IsOnLayer.return_value = True
        zone.GetPosition.return_value = MagicMock(x=0, y=0)
        
        # Create mock audio component
        component = MagicMock()
        component.GetReference.return_value = "U1"
        component.GetPosition.return_value = MagicMock(x=0, y=0)
        
        self.mock_board.GetTracks.return_value = [track1, track2]
        self.mock_board.Zones.return_value = [zone]
        self.mock_board.GetFootprints.return_value = [component]
        
        results = self.validator._validate_audio_optimization(self.mock_board)
        
        # Check for balanced pair spacing warning
        self.assertTrue(any(
            result.message.startswith("Balanced pair AUDIO_BAL+ spacing") and
            result.optimization_category == OptimizationCategory.AUDIO
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for ground plane reference warning
        zone.IsOnLayer.return_value = False
        results = self.validator._validate_audio_optimization(self.mock_board)
        self.assertTrue(any(
            result.message == "Audio signal AUDIO_BAL+ lacks ground plane reference" and
            result.optimization_category == OptimizationCategory.AUDIO
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for component ground plane warning
        zone.GetPosition.return_value = MagicMock(x=20000000, y=20000000)  # 20mm away
        results = self.validator._validate_audio_optimization(self.mock_board)
        self.assertTrue(any(
            result.message == "Audio component U1 lacks nearby ground plane" and
            result.optimization_category == OptimizationCategory.AUDIO
            for result in results[pcbnew.GENERAL]
        ))
    
    def test_power_quality_optimization(self):
        """Test power quality optimization validation."""
        # Create mock power tracks
        track1 = MagicMock(spec=pcbnew.PCB_TRACK)
        track1.GetType.return_value = pcbnew.PCB_TRACE_T
        track1.GetNetname.return_value = "VCC"
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        track1.GetEnd.return_value = MagicMock(x=60000000, y=0)  # 60mm long
        track1.GetWidth.return_value = 300000  # 0.3mm wide
        
        # Create mock components
        cap = MagicMock()
        cap.GetReference.return_value = "C1"
        cap.GetNetname.return_value = "VCC"
        
        ic = MagicMock()
        ic.GetReference.return_value = "U1"
        ic.GetNetname.return_value = "VCC"
        
        self.mock_board.GetTracks.return_value = [track1]
        self.mock_board.GetFootprints.return_value = [cap, ic]
        
        results = self.validator._validate_power_quality_optimization(self.mock_board)
        
        # Check for power trace width warning
        self.assertTrue(any(
            result.message.startswith("Power net VCC trace width") and
            result.optimization_category == OptimizationCategory.POWER_QUALITY
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for decoupling warning
        self.assertTrue(any(
            result.message.startswith("Power net VCC has insufficient decoupling") and
            result.optimization_category == OptimizationCategory.POWER_QUALITY
            for result in results[pcbnew.GENERAL]
        ))
    
    def test_thermal_management_optimization(self):
        """Test thermal management optimization validation."""
        # Create mock high-power component
        component = MagicMock()
        component.GetReference.return_value = "U1"
        component.GetPosition.return_value = MagicMock(x=0, y=0)
        
        # Create mock pad without thermal relief
        pad = MagicMock()
        pad.GetNetname.return_value = "VCC"
        pad.GetThermalSpokeWidth.return_value = 0
        component.Pads.return_value = [pad]
        
        # Create mock thermal vias
        via1 = MagicMock()
        via1.GetNetname.return_value = "VCC"
        via1.GetPosition.return_value = MagicMock(x=1000000, y=1000000)  # 1mm away
        
        via2 = MagicMock()
        via2.GetNetname.return_value = "VCC"
        via2.GetPosition.return_value = MagicMock(x=2000000, y=2000000)  # 2mm away
        
        # Create mock power zone
        zone = MagicMock()
        zone.GetNetname.return_value = "VCC"
        
        self.mock_board.GetFootprints.return_value = [component]
        self.mock_board.GetVias.return_value = [via1, via2]
        self.mock_board.Zones.return_value = [zone]
        self.mock_board.GetPads.return_value = [pad]
        
        results = self.validator._validate_thermal_management_optimization(self.mock_board)
        
        # Check for thermal relief warning
        self.assertTrue(any(
            result.message == "High-power component U1 lacks thermal relief" and
            result.optimization_category == OptimizationCategory.THERMAL_MANAGEMENT
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for thermal vias warning
        self.assertTrue(any(
            result.message.startswith("High-power component U1 has insufficient thermal vias") and
            result.optimization_category == OptimizationCategory.THERMAL_MANAGEMENT
            for result in results[pcbnew.GENERAL]
        ))
        
        # Check for thermal relief usage warning
        pad.GetThermalSpokeWidth.return_value = 100000  # 0.1mm
        results = self.validator._validate_thermal_management_optimization(self.mock_board)
        self.assertTrue(any(
            result.message.startswith("Power zone VCC has low thermal relief usage") and
            result.optimization_category == OptimizationCategory.THERMAL_MANAGEMENT
            for result in results[pcbnew.GENERAL]
        ))

if __name__ == '__main__':
    unittest.main() 