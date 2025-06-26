"""
Performance benchmarks for the validation system.
"""

import unittest
import time
import cProfile
import pstats
import io
import os
from typing import Dict, Any, List
from statistics import mean
import psutil
import gc

import pcbnew
from kicad_pcb_generator.core.validation.base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
    ValidationCategory
)
from kicad_pcb_generator.core.validation.validation_analysis_manager import ValidationAnalysisManager
from kicad_pcb_generator.audio.validation.audio_validator import AudioValidator
from kicad_pcb_generator.core.validation.real_time_validator import RealTimeValidator

class TestValidationPerformance(unittest.TestCase):
    """Performance tests for validation system."""
    
    def setUp(self):
        """Set up test cases."""
        self.test_boards = self._load_test_boards()
        self.analysis_manager = ValidationAnalysisManager(pcbnew.GetBoard())
        self.audio_validator = AudioValidator()
        self.realtime_validator = RealTimeValidator()
        
        # Performance metrics
        self.metrics = {
            'validation_times': [],
            'memory_usage': [],
            'cpu_usage': []
        }
    
    def _load_test_boards(self) -> Dict[str, str]:
        """Load test boards of different sizes."""
        test_data_dir = os.path.join(
            os.path.dirname(__file__),
            '..', 'e2e', 'test_data'
        )
        
        return {
            'small': os.path.join(test_data_dir, 'valid_audio_pcb.kicad_pcb'),
            'medium': os.path.join(test_data_dir, 'invalid_component_placement.kicad_pcb'),
            'large': os.path.join(test_data_dir, 'invalid_manufacturing.kicad_pcb')
        }
    
    def _measure_performance(self, func, *args, **kwargs) -> Dict[str, float]:
        """Measure performance metrics for a function."""
        process = psutil.Process()
        
        # Measure memory before
        memory_before = process.memory_info().rss
        
        # Measure CPU before
        cpu_before = process.cpu_percent()
        
        # Run function with timing
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Measure memory after
        memory_after = process.memory_info().rss
        
        # Measure CPU after
        cpu_after = process.cpu_percent()
        
        return {
            'execution_time': end_time - start_time,
            'memory_usage': memory_after - memory_before,
            'cpu_usage': (cpu_before + cpu_after) / 2,
            'result': result
        }
    
    def test_validation_speed(self):
        """Test validation speed with different board sizes."""
        for board_name, board_path in self.test_boards.items():
            board = pcbnew.LoadBoard(board_path)
            
            # Test base validation
            base_metrics = self._measure_performance(
                self.analysis_manager.base_validator.validate,
                board
            )
            
            # Test audio validation
            audio_metrics = self._measure_performance(
                self.audio_validator.validate,
                board
            )
            
            # Test real-time validation
            realtime_metrics = self._measure_performance(
                self.realtime_validator.validate,
                board
            )
            
            # Store metrics
            self.metrics['validation_times'].extend([
                base_metrics['execution_time'],
                audio_metrics['execution_time'],
                realtime_metrics['execution_time']
            ])
            
            # Verify performance requirements
            self.assertLess(base_metrics['execution_time'], 1.0)  # Base validation < 1s
            self.assertLess(audio_metrics['execution_time'], 2.0)  # Audio validation < 2s
            self.assertLess(realtime_metrics['execution_time'], 0.5)  # Real-time validation < 0.5s
    
    def test_memory_usage(self):
        """Test memory usage during validation."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Run validation on largest board
        board = pcbnew.LoadBoard(self.test_boards['large'])
        self.analysis_manager.validate_and_analyze(board)
        
        profiler.disable()
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        # Verify memory usage
        stats = s.getvalue()
        self.assertNotIn('MemoryError', stats)
        self.assertNotIn('OutOfMemory', stats)
        
        # Check memory growth
        process = psutil.Process()
        memory_usage = process.memory_info().rss
        self.assertLess(memory_usage, 500 * 1024 * 1024)  # Less than 500MB
    
    def test_concurrent_validation(self):
        """Test concurrent validation performance."""
        import concurrent.futures
        
        board = pcbnew.LoadBoard(self.test_boards['large'])
        
        # Run validations in parallel
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self.analysis_manager.base_validator.validate, board),
                executor.submit(self.audio_validator.validate, board),
                executor.submit(self.realtime_validator.validate, board)
            ]
            results = [f.result() for f in futures]
        
        parallel_time = time.time() - start_time
        
        # Run validations sequentially
        start_time = time.time()
        self.analysis_manager.base_validator.validate(board)
        self.audio_validator.validate(board)
        self.realtime_validator.validate(board)
        sequential_time = time.time() - start_time
        
        # Parallel should be faster
        self.assertLess(parallel_time, sequential_time)
    
    def test_validation_caching(self):
        """Test validation caching performance."""
        board = pcbnew.LoadBoard(self.test_boards['medium'])
        
        # First run (no cache)
        first_metrics = self._measure_performance(
            self.analysis_manager.validate_and_analyze,
            board
        )
        
        # Second run (should use cache)
        second_metrics = self._measure_performance(
            self.analysis_manager.validate_and_analyze,
            board
        )
        
        # Cached run should be faster
        self.assertLess(
            second_metrics['execution_time'],
            first_metrics['execution_time']
        )
    
    def test_large_board_performance(self):
        """Test performance with large boards."""
        board = pcbnew.LoadBoard(self.test_boards['large'])
        
        # Run validation with timeout
        metrics = self._measure_performance(
            self.analysis_manager.validate_and_analyze,
            board
        )
        
        # Verify performance
        self.assertLess(metrics['execution_time'], 5.0)  # Less than 5 seconds
        self.assertLess(metrics['memory_usage'], 100 * 1024 * 1024)  # Less than 100MB increase
    
    def test_memory_cleanup(self):
        """Test memory cleanup after validation."""
        import gc
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Run multiple validations
        for _ in range(5):
            board = pcbnew.LoadBoard(self.test_boards['medium'])
            self.analysis_manager.validate_and_analyze(board)
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory usage should not grow unbounded
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # Less than 50MB increase
    
    def test_validation_metrics(self):
        """Test validation metrics collection."""
        board = pcbnew.LoadBoard(self.test_boards['medium'])
        
        # Run validation
        self.analysis_manager.validate_and_analyze(board)
        
        # Get metrics
        metrics = self.analysis_manager.get_metrics()
        
        # Verify metrics
        self.assertIn('validation_count', metrics)
        self.assertIn('average_validation_time', metrics)
        self.assertIn('success_rate', metrics)
        self.assertIn('error_rate', metrics)
        
        # Check metric values
        self.assertGreater(metrics['validation_count'], 0)
        self.assertLess(metrics['average_validation_time'], 1.0)
        self.assertGreaterEqual(metrics['success_rate'], 0.0)
        self.assertLessEqual(metrics['success_rate'], 1.0)
    
    def tearDown(self):
        """Clean up after tests."""
        # Print performance summary
        if self.metrics['validation_times']:
            print("\nPerformance Summary:")
            print(f"Average validation time: {mean(self.metrics['validation_times']):.3f}s")
            print(f"Max validation time: {max(self.metrics['validation_times']):.3f}s")
            print(f"Min validation time: {min(self.metrics['validation_times']):.3f}s")
        
        # Clear caches
        self.analysis_manager.clear_cache()
        self.audio_validator.clear_cache()
        self.realtime_validator.clear_cache() 