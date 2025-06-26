"""Unit tests for advanced DRC features."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import pcbnew
from kicad_pcb_generator.core.board.advanced_drc import (
    AdvancedDRCManager,
    RulePriority,
    RuleTemplate,
    RuleConflict
)
from kicad_pcb_generator.core.validation.validation_rule import (
    ValidationRule,
    RuleType,
    ValidationCategory,
    ValidationSeverity
)

class TestAdvancedDRCManager(unittest.TestCase):
    """Test cases for AdvancedDRCManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_board = Mock(spec=pcbnew.BOARD)
        self.drc_manager = AdvancedDRCManager(self.mock_board)
    
    def test_init_default_templates(self):
        """Test initialization of default templates."""
        # Check if default templates are created
        self.assertIn("track_width", self.drc_manager.templates)
        self.assertIn("via_size", self.drc_manager.templates)
        self.assertIn("clearance", self.drc_manager.templates)
        self.assertIn("impedance", self.drc_manager.templates)
        self.assertIn("thermal", self.drc_manager.templates)
        
        # Check template properties
        track_width_template = self.drc_manager.templates["track_width"]
        self.assertEqual(track_width_template.name, "Track Width")
        self.assertEqual(track_width_template.rule_type, RuleType.DESIGN_RULES)
        self.assertEqual(track_width_template.priority, RulePriority.HIGH)
    
    def test_create_rule_from_template(self):
        """Test creating a rule from a template."""
        # Create rule with default parameters
        rule = self.drc_manager.create_rule_from_template("track_width")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.rule_type, RuleType.DESIGN_RULES)
        self.assertEqual(rule.parameters["min_width"], 0.1)
        
        # Create rule with custom parameters
        rule = self.drc_manager.create_rule_from_template(
            "track_width",
            min_width=0.2,
            max_width=3.0
        )
        self.assertEqual(rule.parameters["min_width"], 0.2)
        self.assertEqual(rule.parameters["max_width"], 3.0)
        
        # Test with non-existent template
        rule = self.drc_manager.create_rule_from_template("non_existent")
        self.assertIsNone(rule)
    
    def test_add_rule(self):
        """Test adding a validation rule."""
        # Create a test rule
        rule = ValidationRule(
            rule_type=RuleType.DESIGN_RULES,
            category=ValidationCategory.DESIGN_RULES,
            enabled=True,
            parameters={"min_width": 0.1},
            thresholds={"min_width": 0.1},
            severity=ValidationSeverity.WARNING
        )
        
        # Add rule
        result = self.drc_manager.add_rule(rule)
        self.assertTrue(result)
        self.assertIn(rule.rule_type.name, self.drc_manager.rules)
        
        # Test adding conflicting rule
        conflicting_rule = ValidationRule(
            rule_type=RuleType.DESIGN_RULES,
            category=ValidationCategory.DESIGN_RULES,
            enabled=True,
            parameters={"min_width": 0.05},  # Smaller than existing rule
            thresholds={"min_width": 0.05},
            severity=ValidationSeverity.WARNING
        )
        
        result = self.drc_manager.add_rule(conflicting_rule)
        self.assertTrue(result)
        self.assertTrue(len(self.drc_manager.conflicts) > 0)
    
    def test_resolve_conflicts(self):
        """Test resolving rule conflicts."""
        # Add conflicting rules
        rule1 = ValidationRule(
            rule_type=RuleType.DESIGN_RULES,
            category=ValidationCategory.DESIGN_RULES,
            enabled=True,
            parameters={"min_width": 0.1},
            thresholds={"min_width": 0.1},
            severity=ValidationSeverity.WARNING
        )
        
        rule2 = ValidationRule(
            rule_type=RuleType.DESIGN_RULES,
            category=ValidationCategory.DESIGN_RULES,
            enabled=True,
            parameters={"min_width": 0.05},
            thresholds={"min_width": 0.05},
            severity=ValidationSeverity.WARNING
        )
        
        self.drc_manager.add_rule(rule1)
        self.drc_manager.add_rule(rule2)
        
        # Resolve conflicts
        self.drc_manager.resolve_conflicts()
        self.assertEqual(len(self.drc_manager.conflicts), 0)
        
        # Check if rule2 was updated to match rule1
        updated_rule = self.drc_manager.rules[RuleType.DESIGN_RULES.name]
        self.assertEqual(updated_rule.parameters["min_width"], 0.1)
    
    @patch('pcbnew.DRC')
    def test_validate_board(self, mock_drc):
        """Test board validation."""
        # Mock DRC results
        mock_drc_instance = Mock()
        mock_drc.return_value = mock_drc_instance
        mock_marker = Mock()
        mock_marker.GetLayer.return_value = 0
        mock_marker.GetMessage.return_value = "Test error"
        mock_marker.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_drc_instance.GetMarkers.return_value = [mock_marker]
        
        # Add a test rule
        rule = ValidationRule(
            rule_type=RuleType.DESIGN_RULES,
            category=ValidationCategory.DESIGN_RULES,
            enabled=True,
            parameters={"min_width": 0.1},
            thresholds={"min_width": 0.1},
            severity=ValidationSeverity.WARNING
        )
        self.drc_manager.add_rule(rule)
        
        # Run validation
        results = self.drc_manager.validate_board()
        
        # Check results
        self.assertIn("Edge.Cuts", results)
        self.assertIn(ValidationCategory.DESIGN_RULES, results)
    
    def test_calculate_distance(self):
        """Test distance calculation."""
        pos1 = pcbnew.VECTOR2I(0, 0)
        pos2 = pcbnew.VECTOR2I(1000000, 1000000)  # 1mm in both directions
        
        distance = self.drc_manager._calculate_distance(pos1, pos2)
        self.assertAlmostEqual(distance, 1.4142135623730951)  # sqrt(2)
    
    def test_calculate_track_resistance(self):
        """Test track resistance calculation."""
        length = 10.0  # 10mm
        width = 0.2    # 0.2mm
        
        resistance = self.drc_manager._calculate_track_resistance(length, width)
        self.assertGreater(resistance, 0)
    
    def test_calculate_track_impedance(self):
        """Test track impedance calculation."""
        mock_track = Mock(spec=pcbnew.TRACK)
        mock_track.GetWidth.return_value = 200000  # 0.2mm
        
        impedance = self.drc_manager._calculate_track_impedance(mock_track)
        self.assertGreater(impedance, 0)
    
    def test_calculate_crosstalk(self):
        """Test crosstalk calculation."""
        mock_track1 = Mock(spec=pcbnew.TRACK)
        mock_track2 = Mock(spec=pcbnew.TRACK)
        mock_track1.GetWidth.return_value = 200000  # 0.2mm
        mock_track2.GetWidth.return_value = 200000  # 0.2mm
        mock_track1.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        mock_track2.GetStart.return_value = pcbnew.VECTOR2I(1000000, 0)  # 1mm away
        
        crosstalk = self.drc_manager._calculate_crosstalk(mock_track1, mock_track2)
        self.assertLess(crosstalk, 0)  # Should be negative dB
    
    def test_calculate_zone_distance(self):
        """Test zone distance calculation."""
        mock_zone1 = Mock(spec=pcbnew.ZONE)
        mock_zone2 = Mock(spec=pcbnew.ZONE)
        
        # Mock zone outlines
        mock_outline1 = Mock()
        mock_outline2 = Mock()
        mock_outline1.PointCount.return_value = 2
        mock_outline2.PointCount.return_value = 2
        mock_outline1.CPoint.side_effect = [
            pcbnew.VECTOR2I(0, 0),
            pcbnew.VECTOR2I(1000000, 0)
        ]
        mock_outline2.CPoint.side_effect = [
            pcbnew.VECTOR2I(0, 1000000),
            pcbnew.VECTOR2I(1000000, 1000000)
        ]
        
        mock_zone1.GetOutline.return_value = mock_outline1
        mock_zone2.GetOutline.return_value = mock_outline2
        
        distance = self.drc_manager._calculate_zone_distance(mock_zone1, mock_zone2)
        self.assertAlmostEqual(distance, 1.0)  # 1mm
    
    def test_validate_design_rules(self):
        """Test design rules validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.DESIGN_RULES,
            category=ValidationCategory.DESIGN_RULES,
            enabled=True,
            parameters={
                "min_width": 0.1,
                "min_diameter": 0.2,
                "min_clearance": 0.1
            },
            thresholds={
                "min_width": 0.1,
                "min_diameter": 0.2,
                "min_clearance": 0.1
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock board settings
        mock_settings = Mock()
        mock_settings.GetTrackWidth.return_value = 50000  # 0.05mm
        mock_settings.GetViasMinSize.return_value = 100000  # 0.1mm
        mock_settings.GetMinClearance.return_value = 50000  # 0.05mm
        self.mock_board.GetDesignSettings.return_value = mock_settings
        
        # Run validation
        results = {}
        self.drc_manager._validate_design_rules(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.DESIGN_RULES, results)
        self.assertTrue(len(results[ValidationCategory.DESIGN_RULES]) > 0)
    
    def test_validate_component_placement(self):
        """Test component placement validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.COMPONENT_PLACEMENT,
            category=ValidationCategory.COMPONENT_PLACEMENT,
            enabled=True,
            parameters={
                "min_spacing": 1.0,
                "edge_clearance": 2.0
            },
            thresholds={
                "min_spacing": 1.0,
                "edge_clearance": 2.0
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock components
        mock_comp1 = Mock(spec=pcbnew.FOOTPRINT)
        mock_comp2 = Mock(spec=pcbnew.FOOTPRINT)
        mock_comp1.GetReference.return_value = "R1"
        mock_comp2.GetReference.return_value = "R2"
        mock_comp1.GetPosition.return_value = pcbnew.VECTOR2I(0, 0)
        mock_comp2.GetPosition.return_value = pcbnew.VECTOR2I(500000, 0)  # 0.5mm away
        
        self.mock_board.GetFootprints.return_value = [mock_comp1, mock_comp2]
        
        # Run validation
        results = {}
        self.drc_manager._validate_component_placement(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.COMPONENT_PLACEMENT, results)
        self.assertTrue(len(results[ValidationCategory.COMPONENT_PLACEMENT]) > 0)
    
    def test_validate_routing(self):
        """Test routing validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.ROUTING,
            category=ValidationCategory.ROUTING,
            enabled=True,
            parameters={
                "min_track_width": 0.1,
                "min_via_size": 0.2,
                "max_length": 100.0
            },
            thresholds={
                "min_track_width": 0.1,
                "min_via_size": 0.2,
                "max_length": 100.0
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock tracks and vias
        mock_track = Mock(spec=pcbnew.TRACK)
        mock_via = Mock(spec=pcbnew.VIA)
        mock_track.IsTrack.return_value = True
        mock_track.GetWidth.return_value = 50000  # 0.05mm
        mock_track.GetLength.return_value = 200000000  # 200mm
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        mock_via.GetWidth.return_value = 100000  # 0.1mm
        mock_via.GetPosition.return_value = pcbnew.VECTOR2I(0, 0)
        
        self.mock_board.GetTracks.return_value = [mock_track]
        self.mock_board.GetVias.return_value = [mock_via]
        
        # Run validation
        results = {}
        self.drc_manager._validate_routing(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.ROUTING, results)
        self.assertTrue(len(results[ValidationCategory.ROUTING]) > 0)
    
    def test_validate_manufacturing(self):
        """Test manufacturing validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.MANUFACTURING,
            category=ValidationCategory.MANUFACTURING,
            enabled=True,
            parameters={
                "min_feature_size": 0.1,
                "max_board_size": 100.0,
                "min_annular_ring": 0.1
            },
            thresholds={
                "min_feature_size": 0.1,
                "max_board_size": 100.0,
                "min_annular_ring": 0.1
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock board edges
        mock_bbox = Mock()
        mock_bbox.GetLeft.return_value = 0
        mock_bbox.GetRight.return_value = 200000000  # 200mm
        mock_bbox.GetTop.return_value = 0
        mock_bbox.GetBottom.return_value = 200000000  # 200mm
        self.mock_board.GetBoardEdgesBoundingBox.return_value = mock_bbox
        
        # Mock tracks and vias
        mock_track = Mock(spec=pcbnew.TRACK)
        mock_via = Mock(spec=pcbnew.VIA)
        mock_track.IsTrack.return_value = True
        mock_track.GetWidth.return_value = 50000  # 0.05mm
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        mock_via.GetWidth.return_value = 100000  # 0.1mm
        mock_via.GetDrill.return_value = 80000  # 0.08mm
        mock_via.GetPosition.return_value = pcbnew.VECTOR2I(0, 0)
        
        self.mock_board.GetTracks.return_value = [mock_track]
        self.mock_board.GetVias.return_value = [mock_via]
        
        # Run validation
        results = {}
        self.drc_manager._validate_manufacturing(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.MANUFACTURING, results)
        self.assertTrue(len(results[ValidationCategory.MANUFACTURING]) > 0)
    
    def test_validate_power(self):
        """Test power validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.POWER,
            category=ValidationCategory.POWER,
            enabled=True,
            parameters={
                "max_voltage_drop": 0.1,
                "max_current_density": 10.0
            },
            thresholds={
                "max_voltage_drop": 0.1,
                "max_current_density": 10.0
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock tracks
        mock_track = Mock(spec=pcbnew.TRACK)
        mock_track.IsTrack.return_value = True
        mock_track.GetLength.return_value = 1000000  # 1mm
        mock_track.GetWidth.return_value = 50000  # 0.05mm
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        
        self.mock_board.GetTracks.return_value = [mock_track]
        
        # Run validation
        results = {}
        self.drc_manager._validate_power(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.POWER, results)
        self.assertTrue(len(results[ValidationCategory.POWER]) > 0)
    
    def test_validate_ground(self):
        """Test ground validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.GROUND,
            category=ValidationCategory.GROUND,
            enabled=True,
            parameters={
                "min_coverage": 0.5,
                "max_via_spacing": 5.0
            },
            thresholds={
                "min_coverage": 0.5,
                "max_via_spacing": 5.0
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock zones and vias
        mock_zone = Mock(spec=pcbnew.ZONE)
        mock_zone.GetNetname.return_value = "GND"
        mock_zone.GetArea.return_value = 1000000000000  # 1000mm²
        
        mock_via1 = Mock(spec=pcbnew.VIA)
        mock_via2 = Mock(spec=pcbnew.VIA)
        mock_via1.GetNetname.return_value = "GND"
        mock_via2.GetNetname.return_value = "GND"
        mock_via1.GetPosition.return_value = pcbnew.VECTOR2I(0, 0)
        mock_via2.GetPosition.return_value = pcbnew.VECTOR2I(6000000, 0)  # 6mm away
        
        self.mock_board.Zones.return_value = [mock_zone]
        self.mock_board.GetVias.return_value = [mock_via1, mock_via2]
        
        # Mock board area
        mock_bbox = Mock()
        mock_bbox.GetLeft.return_value = 0
        mock_bbox.GetRight.return_value = 100000000  # 100mm
        mock_bbox.GetTop.return_value = 0
        mock_bbox.GetBottom.return_value = 100000000  # 100mm
        self.mock_board.GetBoardEdgesBoundingBox.return_value = mock_bbox
        
        # Run validation
        results = {}
        self.drc_manager._validate_ground(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.GROUND, results)
        self.assertTrue(len(results[ValidationCategory.GROUND]) > 0)
    
    def test_validate_signal(self):
        """Test signal validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.SIGNAL,
            category=ValidationCategory.SIGNAL,
            enabled=True,
            parameters={
                "target_impedance": 50.0,
                "tolerance": 5.0,
                "max_crosstalk": -20.0
            },
            thresholds={
                "min_impedance": 45.0,
                "max_impedance": 55.0,
                "max_crosstalk": -20.0
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock tracks
        mock_track1 = Mock(spec=pcbnew.TRACK)
        mock_track2 = Mock(spec=pcbnew.TRACK)
        mock_track1.IsTrack.return_value = True
        mock_track2.IsTrack.return_value = True
        mock_track1.GetWidth.return_value = 200000  # 0.2mm
        mock_track2.GetWidth.return_value = 200000  # 0.2mm
        mock_track1.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        mock_track2.GetStart.return_value = pcbnew.VECTOR2I(1000000, 0)  # 1mm away
        
        self.mock_board.GetTracks.return_value = [mock_track1, mock_track2]
        
        # Run validation
        results = {}
        self.drc_manager._validate_signal(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.SIGNAL, results)
        self.assertTrue(len(results[ValidationCategory.SIGNAL]) > 0)
    
    def test_validate_audio(self):
        """Test audio validation."""
        # Create test rule
        rule = ValidationRule(
            rule_type=RuleType.AUDIO,
            category=ValidationCategory.AUDIO,
            enabled=True,
            parameters={
                "max_signal_length": 50.0,
                "min_isolation": 2.0
            },
            thresholds={
                "max_signal_length": 50.0,
                "min_isolation": 2.0
            },
            severity=ValidationSeverity.WARNING
        )
        
        # Mock tracks and zones
        mock_track = Mock(spec=pcbnew.TRACK)
        mock_track.IsTrack.return_value = True
        mock_track.GetLength.return_value = 60000000  # 60mm
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        
        mock_zone1 = Mock(spec=pcbnew.ZONE)
        mock_zone2 = Mock(spec=pcbnew.ZONE)
        mock_zone1.GetNetname.return_value = "GND"
        mock_zone2.GetNetname.return_value = "GND"
        
        # Mock zone outlines
        mock_outline1 = Mock()
        mock_outline2 = Mock()
        mock_outline1.PointCount.return_value = 2
        mock_outline2.PointCount.return_value = 2
        mock_outline1.CPoint.side_effect = [
            pcbnew.VECTOR2I(0, 0),
            pcbnew.VECTOR2I(1000000, 0)
        ]
        mock_outline2.CPoint.side_effect = [
            pcbnew.VECTOR2I(0, 1500000),
            pcbnew.VECTOR2I(1000000, 1500000)
        ]
        
        mock_zone1.GetOutline.return_value = mock_outline1
        mock_zone2.GetOutline.return_value = mock_outline2
        
        self.mock_board.GetTracks.return_value = [mock_track]
        self.mock_board.Zones.return_value = [mock_zone1, mock_zone2]
        
        # Run validation
        results = {}
        self.drc_manager._validate_audio(rule, results)
        
        # Check results
        self.assertIn(ValidationCategory.AUDIO, results)
        self.assertTrue(len(results[ValidationCategory.AUDIO]) > 0)

if __name__ == '__main__':
    unittest.main() 
