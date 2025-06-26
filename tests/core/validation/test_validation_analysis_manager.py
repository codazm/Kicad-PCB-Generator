"""Tests for the validation analysis manager module."""

import unittest
from unittest.mock import MagicMock, patch
import pcbnew
import math

from kicad_pcb_generator.core.validation.validation_analysis_manager import (
    ValidationAnalysisManager,
    ValidationAnalysisResult
)
from kicad_pcb_generator.core.validation.base_validator import (
    ValidationResult,
    ValidationSeverity,
    ValidationCategory
)
from kicad_pcb_generator.analysis.analysis_manager import (
    AnalysisResult,
    AnalysisType
)

class TestValidationAnalysisManager(unittest.TestCase):
    """Test cases for the ValidationAnalysisManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_board = MagicMock(spec=pcbnew.BOARD)
        self.mock_board.GetFileName.return_value = "test_board.kicad_pcb"
        
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
        
        # Create manager instance
        self.manager = ValidationAnalysisManager(self.mock_board)
    
    def test_initialization(self):
        """Test initialization of the manager."""
        self.assertIsNotNone(self.manager.base_validator)
        self.assertIsNotNone(self.manager.board_validator)
        self.assertIsNotNone(self.manager.realtime_validator)
        self.assertIsNotNone(self.manager.audio_validator)
        self.assertIsNotNone(self.manager.analysis_manager)
        self.assertIsNotNone(self.manager.layout_optimizer)
        self.assertIsNotNone(self.manager.design_assistant)
    
    def test_validate_and_analyze(self):
        """Test validate_and_analyze method."""
        # Mock validation results
        mock_validation = ValidationResult(
            id="test_validation",
            category=ValidationCategory.DESIGN_RULES,
            severity=ValidationSeverity.WARNING,
            message="Test validation message",
            location=(0.0, 0.0),
            component="U1"
        )
        
        # Mock analysis results
        mock_analysis = AnalysisResult(
            type=AnalysisType.SIGNAL_INTEGRITY,
            severity="warning",
            message="Test analysis message",
            location=(0.0, 0.0),
            component="U1"
        )
        
        # Mock validator and analyzer
        self.manager.base_validator.validate = MagicMock(return_value=[mock_validation])
        self.manager.analysis_manager.analyze_signal_integrity = MagicMock(return_value=[mock_analysis])
        
        # Run validation and analysis
        results = self.manager.validate_and_analyze()
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ValidationAnalysisResult)
        self.assertEqual(results[0].validation_result, mock_validation)
        self.assertEqual(results[0].analysis_result, mock_analysis)
        self.assertIsNotNone(results[0].optimization_score)
        self.assertIsNotNone(results[0].ai_recommendation)
    
    def test_results_match(self):
        """Test _results_match method."""
        # Create matching results
        validation = ValidationResult(
            id="test",
            category=ValidationCategory.DESIGN_RULES,
            severity=ValidationSeverity.WARNING,
            message="Test",
            location=(1.0, 1.0),
            component="U1"
        )
        
        analysis = AnalysisResult(
            type=AnalysisType.SIGNAL_INTEGRITY,
            severity="warning",
            message="Test",
            location=(1.0, 1.0),
            component="U1"
        )
        
        # Test matching
        self.assertTrue(self.manager._results_match(validation, analysis))
        
        # Test non-matching location
        analysis.location = (2.0, 2.0)
        self.assertFalse(self.manager._results_match(validation, analysis))
        
        # Test non-matching component
        analysis.location = (1.0, 1.0)
        analysis.component = "U2"
        self.assertFalse(self.manager._results_match(validation, analysis))
    
    def test_calculate_optimization_score(self):
        """Test _calculate_optimization_score method."""
        # Create test results
        validation = ValidationResult(
            id="test",
            category=ValidationCategory.DESIGN_RULES,
            severity=ValidationSeverity.WARNING,
            message="Test",
            location=(1.0, 1.0),
            component="U1"
        )
        
        analysis = AnalysisResult(
            type=AnalysisType.SIGNAL_INTEGRITY,
            severity="warning",
            message="Test",
            location=(1.0, 1.0),
            component="U1"
        )
        
        # Test with warning severity
        score = self.manager._calculate_optimization_score(validation, analysis)
        self.assertAlmostEqual(score, 0.375)  # 0.5 * 0.75
        
        # Test with error severity
        validation.severity = ValidationSeverity.ERROR
        score = self.manager._calculate_optimization_score(validation, analysis)
        self.assertAlmostEqual(score, 0.0)  # 0.0 * 0.75
        
        # Test with info severity
        validation.severity = ValidationSeverity.INFO
        score = self.manager._calculate_optimization_score(validation, analysis)
        self.assertAlmostEqual(score, 0.75)  # 1.0 * 0.75
    
    def test_get_ai_recommendation(self):
        """Test _get_ai_recommendation method."""
        # Create test results
        validation = ValidationResult(
            id="test",
            category=ValidationCategory.DESIGN_RULES,
            severity=ValidationSeverity.WARNING,
            message="Test",
            location=(1.0, 1.0),
            component="U1"
        )
        
        analysis = AnalysisResult(
            type=AnalysisType.SIGNAL_INTEGRITY,
            severity="warning",
            message="Test",
            location=(1.0, 1.0),
            component="U1"
        )
        
        # Mock design assistant
        self.manager.design_assistant.get_recommendation = MagicMock(
            return_value={"action": "test_action"}
        )
        
        # Get recommendation
        recommendation = self.manager._get_ai_recommendation(
            validation,
            analysis,
            0.5
        )
        
        # Verify recommendation
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation["action"], "test_action")
    
    def test_cleanup(self):
        """Test cleanup method."""
        # Run cleanup
        self.manager.cleanup()
        
        # Verify caches are cleared
        self.assertEqual(len(self.manager._validation_cache), 0)
        self.assertEqual(len(self.manager._analysis_cache), 0)
        self.assertEqual(len(self.manager._optimization_cache), 0)
        
        # Verify thread pool is shut down
        self.assertTrue(self.manager.executor._shutdown) 