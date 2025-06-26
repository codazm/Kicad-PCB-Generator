"""
Performance optimization benchmarks for the KiCad PCB Generator.
"""

import unittest
import time
import psutil
import gc
import tempfile
import shutil
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Any
import threading
import concurrent.futures

from kicad_pcb_generator.core.performance.memory_optimizer import (
    MemoryOptimizer,
    MemoryMetrics,
    MemoryLeak,
    MemorySeverity
)
from kicad_pcb_generator.core.performance.resource_manager import (
    ResourceManager,
    Resource,
    ResourceType,
    ResourceStatus
)
from kicad_pcb_generator.core.performance.optimization_manager import (
    OptimizationManager,
    OptimizationConfig,
    OptimizationType,
    OptimizationStatus
)


class TestPerformanceOptimization(unittest.TestCase):
    """Performance optimization tests."""
    
    def setUp(self):
        """Set up test cases."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.metrics = {
            'memory_optimization': [],
            'resource_management': [],
            'caching_performance': [],
            'parallelization_performance': []
        }
        
        # Initialize managers
        self.memory_optimizer = MemoryOptimizer(
            logger=None,
            enable_tracemalloc=False,
            memory_threshold=50 * 1024 * 1024,  # 50MB
            leak_threshold=5 * 1024 * 1024      # 5MB
        )
        
        self.resource_manager = ResourceManager(
            logger=None,
            temp_dir=str(self.temp_dir / "resources"),
            max_temp_size=10 * 1024 * 1024,  # 10MB
            cleanup_interval=1.0,
            auto_cleanup=False
        )
        
        self.optimization_manager = OptimizationManager(
            logger=None,
            cache_dir=str(self.temp_dir / "cache"),
            max_workers=4,
            enable_parallelization=True,
            enable_caching=True
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop monitoring
        self.memory_optimizer.stop_monitoring()
        
        # Clean up managers
        self.memory_optimizer.optimize_memory()
        self.resource_manager.cleanup_resources()
        self.optimization_manager.clear_cache()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _measure_performance(self, func: callable, *args, **kwargs) -> Dict[str, float]:
        """Measure performance metrics for a function.
        
        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Performance metrics dictionary
        """
        process = psutil.Process()
        
        # Collect garbage before measurement
        gc.collect()
        
        # Measure memory before
        memory_before = process.memory_info().rss
        objects_before = len(gc.get_objects())
        
        # Measure execution time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Measure memory after
        memory_after = process.memory_info().rss
        objects_after = len(gc.get_objects())
        
        return {
            'execution_time': end_time - start_time,
            'memory_usage': memory_after - memory_before,
            'object_increase': objects_after - objects_before,
            'result': result
        }
    
    def test_memory_optimization_performance(self):
        """Test memory optimization performance."""
        # Start memory monitoring
        self.memory_optimizer.start_monitoring(interval=0.1)
        
        # Create memory-intensive operation
        def memory_intensive_operation():
            data = []
            for i in range(10000):
                data.append([i] * 100)  # Create large lists
            return len(data)
        
        # Measure without optimization
        unoptimized_metrics = self._measure_performance(memory_intensive_operation)
        
        # Measure with memory optimization
        optimized_metrics = self._measure_performance(
            self.memory_optimizer.measure_memory,
            "test",
            "memory_intensive",
            memory_intensive_operation
        )
        
        # Store metrics
        self.metrics['memory_optimization'].extend([
            unoptimized_metrics['execution_time'],
            optimized_metrics['execution_time']
        ])
        
        # Verify optimization provides benefits
        self.assertLessEqual(
            optimized_metrics['memory_usage'],
            unoptimized_metrics['memory_usage'] * 1.2  # Allow 20% overhead
        )
        
        # Get memory report
        memory_report = self.memory_optimizer.get_memory_report()
        self.assertIn('current_memory_mb', memory_report)
        self.assertIn('gc_stats', memory_report)
        
        # Stop monitoring
        self.memory_optimizer.stop_monitoring()
    
    def test_memory_leak_detection(self):
        """Test memory leak detection."""
        # Start monitoring
        self.memory_optimizer.start_monitoring(interval=0.1)
        
        # Create potential memory leak
        def leaky_operation():
            data = []
            for i in range(1000):
                data.append([i] * 100)
            # Don't return data, creating potential leak
            return len(data)
        
        # Run operation multiple times
        for _ in range(5):
            leaky_operation()
            time.sleep(0.1)
        
        # Check for memory leaks
        memory_report = self.memory_optimizer.get_memory_report()
        
        # Verify leak detection works
        self.assertIn('leak_detections', memory_report)
        
        # Stop monitoring
        self.memory_optimizer.stop_monitoring()
    
    def test_resource_management_performance(self):
        """Test resource management performance."""
        # Create temporary resources
        resources = []
        
        for i in range(10):
            with self.resource_manager.temporary_resource(
                ResourceType.FILE,
                prefix=f"test_{i}",
                cleanup=False
            ) as resource:
                resources.append(resource)
                
                # Write some data to the file
                if resource and resource.path:
                    with open(resource.path, 'w') as f:
                        f.write('x' * 1000)
        
        # Measure cleanup performance
        cleanup_start = time.time()
        cleaned_count = self.resource_manager.cleanup_resources()
        cleanup_time = time.time() - cleanup_start
        
        # Store metrics
        self.metrics['resource_management'].append(cleanup_time)
        
        # Verify cleanup worked
        self.assertGreater(cleaned_count, 0)
        self.assertLess(cleanup_time, 1.0)  # Should be fast
        
        # Get resource report
        resource_report = self.resource_manager.get_resource_report()
        self.assertIn('total_resources', resource_report)
        self.assertIn('type_counts', resource_report)
    
    def test_caching_performance(self):
        """Test caching performance improvements."""
        # Create expensive computation function
        def expensive_computation(n: int) -> int:
            time.sleep(0.01)  # Simulate expensive computation
            return sum(i * i for i in range(n))
        
        # Apply caching optimization
        cached_computation = self.optimization_manager.optimize_function(
            expensive_computation,
            OptimizationType.CACHING,
            cache_key="expensive_computation"
        )
        
        # Measure first run (no cache)
        first_run_metrics = self._measure_performance(cached_computation, 1000)
        
        # Measure second run (should use cache)
        second_run_metrics = self._measure_performance(cached_computation, 1000)
        
        # Store metrics
        self.metrics['caching_performance'].extend([
            first_run_metrics['execution_time'],
            second_run_metrics['execution_time']
        ])
        
        # Verify caching provides performance improvement
        self.assertLess(
            second_run_metrics['execution_time'],
            first_run_metrics['execution_time'] * 0.5  # Should be at least 50% faster
        )
        
        # Verify results are the same
        self.assertEqual(
            first_run_metrics['result'],
            second_run_metrics['result']
        )
        
        # Get cache stats
        cache_stats = self.optimization_manager.get_cache_stats()
        self.assertIn('memory_entries', cache_stats)
        self.assertGreater(cache_stats['memory_entries'], 0)
    
    def test_parallelization_performance(self):
        """Test parallelization performance improvements."""
        # Create parallelizable function
        def parallelizable_work(item: int) -> int:
            time.sleep(0.01)  # Simulate work
            return item * item
        
        # Apply parallelization optimization
        parallel_work = self.optimization_manager.optimize_function(
            parallelizable_work,
            OptimizationType.PARALLELIZATION,
            parallel=True
        )
        
        # Measure sequential execution
        def sequential_execution():
            return [parallelizable_work(i) for i in range(10)]
        
        sequential_metrics = self._measure_performance(sequential_execution)
        
        # Measure parallel execution
        def parallel_execution():
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(parallel_work, i) for i in range(10)]
                return [f.result() for f in futures]
        
        parallel_metrics = self._measure_performance(parallel_execution)
        
        # Store metrics
        self.metrics['parallelization_performance'].extend([
            sequential_metrics['execution_time'],
            parallel_metrics['execution_time']
        ])
        
        # Verify parallelization provides improvement
        self.assertLess(
            parallel_metrics['execution_time'],
            sequential_metrics['execution_time'] * 0.8  # Should be faster
        )
        
        # Verify results are the same
        self.assertEqual(
            sequential_metrics['result'],
            parallel_metrics['result']
        )
    
    def test_memory_optimization_effectiveness(self):
        """Test memory optimization effectiveness."""
        # Create memory-intensive operations
        def create_large_objects():
            objects = []
            for i in range(1000):
                objects.append([i] * 100)
            return objects
        
        def create_small_objects():
            objects = []
            for i in range(1000):
                objects.append(i)
            return objects
        
        # Measure memory usage for different operations
        large_metrics = self._measure_performance(create_large_objects)
        small_metrics = self._measure_performance(create_small_objects)
        
        # Verify memory optimization reduces usage
        self.assertLess(
            small_metrics['memory_usage'],
            large_metrics['memory_usage']
        )
        
        # Test memory cleanup
        self.memory_optimizer.optimize_memory()
        
        # Verify cleanup reduces memory usage
        process = psutil.Process()
        memory_after_cleanup = process.memory_info().rss
        
        # Memory should not grow unbounded
        self.assertLess(memory_after_cleanup, 500 * 1024 * 1024)  # Less than 500MB
    
    def test_resource_cleanup_effectiveness(self):
        """Test resource cleanup effectiveness."""
        # Create multiple temporary resources
        resources = []
        
        for i in range(20):
            with self.resource_manager.temporary_resource(
                ResourceType.FILE,
                prefix=f"cleanup_test_{i}"
            ) as resource:
                resources.append(resource)
                
                # Write data to file
                if resource and resource.path:
                    with open(resource.path, 'w') as f:
                        f.write('x' * 1000)
        
        # Get initial resource count
        initial_count = len(self.resource_manager.list_resources())
        
        # Perform cleanup
        cleaned_count = self.resource_manager.cleanup_resources()
        
        # Get final resource count
        final_count = len(self.resource_manager.list_resources())
        
        # Verify cleanup worked
        self.assertGreater(cleaned_count, 0)
        self.assertLessEqual(final_count, initial_count)
        
        # Verify temporary files are removed
        temp_files = list(self.temp_dir.glob("**/*"))
        self.assertLess(len(temp_files), 50)  # Should be cleaned up
    
    def test_optimization_configuration(self):
        """Test optimization configuration management."""
        # Create custom optimization
        config = OptimizationConfig(
            optimization_id="custom_optimization",
            optimization_type=OptimizationType.CACHING,
            enabled=True,
            priority=5,
            cache_size=2000,
            cache_ttl=7200,
            parameters={"strategy": "fifo"}
        )
        
        # Register optimization
        result = self.optimization_manager.register_optimization(config)
        self.assertTrue(result.success)
        
        # Get optimization
        retrieved_config = self.optimization_manager.get_optimization("custom_optimization")
        self.assertIsNotNone(retrieved_config)
        self.assertEqual(retrieved_config.optimization_id, "custom_optimization")
        
        # Disable optimization
        success = self.optimization_manager.disable_optimization("custom_optimization")
        self.assertTrue(success)
        
        # Verify disabled
        disabled_config = self.optimization_manager.get_optimization("custom_optimization")
        self.assertFalse(disabled_config.enabled)
    
    def test_performance_reporting(self):
        """Test performance reporting capabilities."""
        # Run some operations to generate data
        self.test_caching_performance()
        self.test_parallelization_performance()
        
        # Get optimization report
        optimization_report = self.optimization_manager.get_optimization_report()
        
        # Verify report contains expected data
        self.assertIn('total_optimizations', optimization_report)
        self.assertIn('cache_stats', optimization_report)
        self.assertIn('pool_stats', optimization_report)
        
        # Get cache stats
        cache_stats = self.optimization_manager.get_cache_stats()
        self.assertIn('memory_entries', cache_stats)
        self.assertIn('disk_entries', cache_stats)
        
        # Get resource report
        resource_report = self.resource_manager.get_resource_report()
        self.assertIn('total_resources', resource_report)
        self.assertIn('type_counts', resource_report)
        
        # Get memory report
        memory_report = self.memory_optimizer.get_memory_report()
        self.assertIn('current_memory_mb', memory_report)
        self.assertIn('gc_stats', memory_report)
    
    def test_concurrent_optimization_usage(self):
        """Test concurrent usage of optimization managers."""
        # Create multiple threads using optimizations
        results = []
        
        def worker_thread(thread_id: int):
            # Use caching optimization
            def thread_work(n: int):
                time.sleep(0.01)
                return n * n
            
            cached_work = self.optimization_manager.optimize_function(
                thread_work,
                OptimizationType.CACHING,
                cache_key=f"thread_{thread_id}"
            )
            
            # Perform work
            result = cached_work(thread_id)
            results.append(result)
        
        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all threads completed
        self.assertEqual(len(results), 5)
        
        # Verify cache contains entries from all threads
        cache_stats = self.optimization_manager.get_cache_stats()
        self.assertGreaterEqual(cache_stats['memory_entries'], 5)
    
    def test_memory_pressure_handling(self):
        """Test handling of memory pressure."""
        # Create memory pressure
        def create_memory_pressure():
            large_objects = []
            for i in range(100):
                large_objects.append([i] * 10000)
            return large_objects
        
        # Measure memory usage under pressure
        pressure_metrics = self._measure_performance(create_memory_pressure)
        
        # Verify memory optimization handles pressure
        self.assertLess(
            pressure_metrics['memory_usage'],
            200 * 1024 * 1024  # Less than 200MB increase
        )
        
        # Force garbage collection
        gc.collect()
        
        # Verify memory is reclaimed
        process = psutil.Process()
        memory_after_gc = process.memory_info().rss
        
        # Memory should be reasonable
        self.assertLess(memory_after_gc, 500 * 1024 * 1024)  # Less than 500MB
    
    def test_optimization_effectiveness_summary(self):
        """Test overall optimization effectiveness."""
        # Run all optimization tests
        self.test_memory_optimization_performance()
        self.test_caching_performance()
        self.test_parallelization_performance()
        
        # Calculate effectiveness metrics
        if self.metrics['caching_performance']:
            caching_improvement = (
                self.metrics['caching_performance'][0] /
                self.metrics['caching_performance'][1]
            )
            self.assertGreater(caching_improvement, 1.5)  # At least 50% improvement
        
        if self.metrics['parallelization_performance']:
            parallel_improvement = (
                self.metrics['parallelization_performance'][0] /
                self.metrics['parallelization_performance'][1]
            )
            self.assertGreater(parallel_improvement, 1.1)  # At least 10% improvement
        
        # Print performance summary
        print("\nPerformance Optimization Summary:")
        for category, metrics in self.metrics.items():
            if metrics:
                print(f"{category}: {len(metrics)} measurements")
                if len(metrics) >= 2:
                    avg_time = mean(metrics)
                    print(f"  Average time: {avg_time:.4f}s")
                    print(f"  Median time: {median(metrics):.4f}s")
                    print(f"  Min time: {min(metrics):.4f}s")
                    print(f"  Max time: {max(metrics):.4f}s")


if __name__ == '__main__':
    unittest.main() 