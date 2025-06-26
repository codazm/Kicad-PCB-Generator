"""Tests for the PerformanceManager class."""

import unittest
import time
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import threading
from unittest.mock import Mock, patch

from kicad_pcb_generator.core.performance.performance_manager import (
    PerformanceManager,
    PerformanceMetrics,
    PerformanceReport,
    PerformanceSeverity
)

class TestPerformanceManager(unittest.TestCase):
    """Test cases for the PerformanceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for metrics
        self.test_dir = tempfile.mkdtemp()
        self.manager = PerformanceManager(metrics_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.manager.stop_monitoring()
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test PerformanceManager initialization."""
        self.assertIsNotNone(self.manager.logger)
        self.assertEqual(self.manager.max_workers, 4)
        self.assertEqual(self.manager.metrics_dir, self.test_dir)
        self.assertFalse(self.manager._monitoring)
        self.assertIsNone(self.manager._monitor_thread)
        self.assertEqual(len(self.manager._metrics), 0)
        self.assertEqual(len(self.manager._reports), 0)
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping performance monitoring."""
        # Start monitoring
        self.manager.start_monitoring(interval=0.1)
        self.assertTrue(self.manager._monitoring)
        self.assertIsNotNone(self.manager._monitor_thread)
        self.assertTrue(self.manager._monitor_thread.is_alive())
        
        # Wait for some metrics
        time.sleep(0.3)
        
        # Stop monitoring
        self.manager.stop_monitoring()
        self.assertFalse(self.manager._monitoring)
        self.assertIsNone(self.manager._monitor_thread)
        
        # Check metrics
        metrics = self.manager.get_metrics(component_id="system")
        self.assertGreater(len(metrics), 0)
    
    def test_measure_performance(self):
        """Test measuring performance of a function."""
        def test_function(x, y):
            time.sleep(0.1)
            return x + y
        
        # Measure performance
        result = self.manager.measure_performance(
            component_id="test",
            operation="test_function",
            func=test_function,
            x=1,
            y=2
        )
        
        # Check result
        self.assertEqual(result, 3)
        
        # Check metrics
        metrics = self.manager.get_metrics(component_id="test")
        self.assertEqual(len(metrics), 1)
        
        metric = metrics[0]
        self.assertEqual(metric.component_id, "test")
        self.assertEqual(metric.operation, "test_function")
        self.assertGreaterEqual(metric.execution_time, 0.1)
        self.assertGreaterEqual(metric.memory_usage, 0)
        self.assertGreaterEqual(metric.cpu_usage, 0)
    
    def test_threshold_checking(self):
        """Test checking performance thresholds."""
        # Create metrics exceeding thresholds
        metrics = PerformanceMetrics(
            component_id="test",
            operation="test_operation",
            execution_time=11.0,  # Exceeds critical threshold
            memory_usage=2 * 1024 * 1024 * 1024,  # Exceeds critical threshold
            cpu_usage=96.0,  # Exceeds critical threshold
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Check thresholds
        with patch.object(self.manager, '_log_performance_issue') as mock_log:
            self.manager._check_thresholds(metrics)
            
            # Check that critical issues were logged
            self.assertEqual(mock_log.call_count, 3)
            calls = mock_log.call_args_list
            self.assertEqual(calls[0][0][1], PerformanceSeverity.CRITICAL)
            self.assertEqual(calls[1][0][1], PerformanceSeverity.CRITICAL)
            self.assertEqual(calls[2][0][1], PerformanceSeverity.CRITICAL)
    
    def test_metrics_storage(self):
        """Test storing and retrieving metrics."""
        # Create test metrics
        metrics = [
            PerformanceMetrics(
                component_id="test",
                operation=f"operation_{i}",
                execution_time=i * 0.1,
                memory_usage=i * 1024 * 1024,
                cpu_usage=i * 10.0,
                timestamp=datetime.now() - timedelta(minutes=i),
                metadata={"test": i}
            )
            for i in range(5)
        ]
        
        # Store metrics
        for metric in metrics:
            self.manager._store_metrics(metric)
        
        # Check metrics in memory
        stored_metrics = self.manager.get_metrics(component_id="test")
        self.assertEqual(len(stored_metrics), 5)
        
        # Check metrics in file
        metrics_files = os.listdir(self.test_dir)
        self.assertEqual(len(metrics_files), 1)
        
        # Check metrics filtering
        filtered_metrics = self.manager.get_metrics(
            component_id="test",
            start_time=datetime.now() - timedelta(minutes=2),
            end_time=datetime.now()
        )
        self.assertEqual(len(filtered_metrics), 3)
    
    def test_report_generation(self):
        """Test generating performance reports."""
        # Create test metrics
        metrics = [
            PerformanceMetrics(
                component_id="test",
                operation=f"operation_{i}",
                execution_time=i * 0.1,
                memory_usage=i * 1024 * 1024,
                cpu_usage=i * 10.0,
                timestamp=datetime.now() - timedelta(minutes=i),
                metadata={"test": i}
            )
            for i in range(5)
        ]
        
        # Store metrics
        for metric in metrics:
            self.manager._store_metrics(metric)
        
        # Generate report
        report = self.manager.generate_report("test")
        
        # Check report
        self.assertEqual(report.component_id, "test")
        self.assertEqual(len(report.metrics), 5)
        self.assertIn('total_operations', report.summary)
        self.assertIn('average_execution_time', report.summary)
        self.assertIn('average_memory_usage', report.summary)
        self.assertIn('average_cpu_usage', report.summary)
        self.assertGreater(len(report.recommendations), 0)
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        # Create and store test metrics
        metrics = [
            PerformanceMetrics(
                component_id=f"test_{i}",
                operation="test_operation",
                execution_time=0.1,
                memory_usage=1024 * 1024,
                cpu_usage=10.0,
                timestamp=datetime.now(),
                metadata={}
            )
            for i in range(3)
        ]
        
        for metric in metrics:
            self.manager._store_metrics(metric)
        
        # Clear specific component metrics
        self.manager.clear_metrics(component_id="test_0")
        self.assertEqual(len(self.manager.get_metrics(component_id="test_0")), 0)
        self.assertEqual(len(self.manager.get_metrics(component_id="test_1")), 1)
        
        # Clear all metrics
        self.manager.clear_metrics()
        self.assertEqual(len(self.manager.get_metrics()), 0)
    
    def test_clear_reports(self):
        """Test clearing reports."""
        # Create and store test reports
        for i in range(3):
            report = PerformanceReport(
                component_id=f"test_{i}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                metrics=[],
                summary={},
                recommendations=[]
            )
            self.manager._reports[f"test_{i}"] = report
        
        # Clear specific component report
        self.manager.clear_reports(component_id="test_0")
        self.assertNotIn("test_0", self.manager._reports)
        self.assertIn("test_1", self.manager._reports)
        
        # Clear all reports
        self.manager.clear_reports()
        self.assertEqual(len(self.manager._reports), 0)
    
    def test_concurrent_operations(self):
        """Test concurrent performance measurements."""
        def test_function(x):
            time.sleep(0.1)
            return x * 2
        
        # Create multiple threads
        threads = []
        results = []
        
        def thread_function(i):
            result = self.manager.measure_performance(
                component_id="test",
                operation=f"operation_{i}",
                func=test_function,
                x=i
            )
            results.append(result)
        
        # Start threads
        for i in range(5):
            thread = threading.Thread(target=thread_function, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(results), 5)
        self.assertEqual(results, [0, 2, 4, 6, 8])
        
        # Check metrics
        metrics = self.manager.get_metrics(component_id="test")
        self.assertEqual(len(metrics), 5)
    
    def test_error_handling(self):
        """Test error handling in performance monitoring."""
        # Test invalid metrics directory
        with self.assertRaises(Exception):
            PerformanceManager(metrics_dir="/invalid/path")
        
        # Test invalid function
        with self.assertRaises(Exception):
            self.manager.measure_performance(
                component_id="test",
                operation="invalid_function",
                func=lambda: 1/0
            )
        
        # Test invalid report generation
        with self.assertRaises(ValueError):
            self.manager.generate_report("nonexistent_component")
    
    def test_recommendations(self):
        """Test generating performance recommendations."""
        # Create metrics with poor performance
        metrics = [
            PerformanceMetrics(
                component_id="test",
                operation="slow_operation",
                execution_time=2.0,  # Exceeds warning threshold
                memory_usage=200 * 1024 * 1024,  # Exceeds warning threshold
                cpu_usage=60.0,  # Exceeds warning threshold
                timestamp=datetime.now(),
                metadata={}
            )
            for _ in range(5)
        ]
        
        # Generate recommendations
        summary = {
            'average_execution_time': 2.0,
            'average_memory_usage': 200 * 1024 * 1024,
            'average_cpu_usage': 60.0
        }
        
        recommendations = self.manager._generate_recommendations(metrics, summary)
        
        # Check recommendations
        self.assertEqual(len(recommendations), 3)
        self.assertTrue(any("execution time" in r for r in recommendations))
        self.assertTrue(any("memory usage" in r for r in recommendations))
        self.assertTrue(any("CPU usage" in r for r in recommendations)) 
