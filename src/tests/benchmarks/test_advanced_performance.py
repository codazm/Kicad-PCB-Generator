"""
Advanced performance benchmarks for the KiCad PCB Generator.
"""

import unittest
import time
import psutil
import gc
import tempfile
import shutil
import json
import random
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Any, Tuple
import threading
import concurrent.futures
import multiprocessing

from kicad_pcb_generator.core.performance.memory_optimizer import MemoryOptimizer
from kicad_pcb_generator.core.performance.resource_manager import ResourceManager
from kicad_pcb_generator.core.performance.optimization_manager import OptimizationManager
from kicad_pcb_generator.core.performance.performance_manager import PerformanceManager


class TestAdvancedPerformance(unittest.TestCase):
    """Advanced performance tests for real-world scenarios."""
    
    def setUp(self):
        """Set up test cases."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results = {
            'large_dataset_processing': [],
            'concurrent_operations': [],
            'memory_intensive_workloads': [],
            'optimization_integration': [],
            'stress_testing': []
        }
        
        # Initialize all performance managers
        self.memory_optimizer = MemoryOptimizer(
            logger=None,
            enable_tracemalloc=True,
            memory_threshold=100 * 1024 * 1024,  # 100MB
            leak_threshold=10 * 1024 * 1024      # 10MB
        )
        
        self.resource_manager = ResourceManager(
            logger=None,
            temp_dir=str(self.temp_dir / "resources"),
            max_temp_size=50 * 1024 * 1024,  # 50MB
            cleanup_interval=5.0,
            auto_cleanup=True
        )
        
        self.optimization_manager = OptimizationManager(
            logger=None,
            cache_dir=str(self.temp_dir / "cache"),
            max_workers=multiprocessing.cpu_count(),
            enable_parallelization=True,
            enable_caching=True
        )
        
        self.performance_manager = PerformanceManager(
            logger=None,
            max_workers=4,
            metrics_dir=str(self.temp_dir / "metrics")
        )
        
        # Start monitoring
        self.memory_optimizer.start_monitoring(interval=1.0)
        self.performance_manager.start_monitoring(interval=1.0)
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop monitoring
        self.memory_optimizer.stop_monitoring()
        self.performance_manager.stop_monitoring()
        
        # Clean up managers
        self.memory_optimizer.optimize_memory()
        self.resource_manager.cleanup_resources()
        self.optimization_manager.clear_cache()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _generate_large_dataset(self, size: int = 10000) -> List[Dict[str, Any]]:
        """Generate a large dataset for testing.
        
        Args:
            size: Dataset size
            
        Returns:
            Large dataset
        """
        dataset = []
        for i in range(size):
            item = {
                'id': i,
                'name': f'Item_{i}',
                'data': [random.randint(1, 1000) for _ in range(100)],
                'metadata': {
                    'created': time.time(),
                    'category': random.choice(['A', 'B', 'C', 'D']),
                    'priority': random.randint(1, 10)
                }
            }
            dataset.append(item)
        return dataset
    
    def _measure_comprehensive_performance(
        self,
        func: callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Measure comprehensive performance metrics.
        
        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Comprehensive performance metrics
        """
        process = psutil.Process()
        
        # Collect garbage before measurement
        gc.collect()
        
        # Measure system metrics before
        memory_before = process.memory_info()
        cpu_before = process.cpu_percent()
        objects_before = len(gc.get_objects())
        
        # Measure execution time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Measure system metrics after
        memory_after = process.memory_info()
        cpu_after = process.cpu_percent()
        objects_after = len(gc.get_objects())
        
        return {
            'execution_time': end_time - start_time,
            'memory_rss_increase': memory_after.rss - memory_before.rss,
            'memory_vms_increase': memory_after.vms - memory_before.vms,
            'cpu_usage': (cpu_before + cpu_after) / 2,
            'object_increase': objects_after - objects_before,
            'result_size': len(str(result)) if result else 0,
            'result': result
        }
    
    def test_large_dataset_processing(self):
        """Test processing of large datasets with optimizations."""
        # Generate large dataset
        dataset = self._generate_large_dataset(5000)
        
        # Define processing function
        def process_dataset(data: List[Dict[str, Any]]) -> Dict[str, Any]:
            results = {
                'total_items': len(data),
                'categories': {},
                'priorities': {},
                'data_summary': {}
            }
            
            for item in data:
                # Count categories
                category = item['metadata']['category']
                results['categories'][category] = results['categories'].get(category, 0) + 1
                
                # Count priorities
                priority = item['metadata']['priority']
                results['priorities'][priority] = results['priorities'].get(priority, 0) + 1
                
                # Calculate data summary
                data_sum = sum(item['data'])
                results['data_summary'][item['id']] = data_sum
            
            return results
        
        # Apply optimizations
        optimized_process = self.optimization_manager.optimize_function(
            process_dataset,
            OptimizationType.CACHING,
            cache_key="large_dataset_processing"
        )
        
        # Measure performance with optimizations
        optimized_metrics = self._measure_comprehensive_performance(
            optimized_process,
            dataset
        )
        
        # Measure performance without optimizations
        unoptimized_metrics = self._measure_comprehensive_performance(
            process_dataset,
            dataset
        )
        
        # Store results
        self.results['large_dataset_processing'].extend([
            optimized_metrics['execution_time'],
            unoptimized_metrics['execution_time']
        ])
        
        # Verify optimizations provide benefits
        self.assertLess(
            optimized_metrics['execution_time'],
            unoptimized_metrics['execution_time'] * 0.8  # At least 20% improvement
        )
        
        # Verify memory usage is reasonable
        self.assertLess(
            optimized_metrics['memory_rss_increase'],
            100 * 1024 * 1024  # Less than 100MB increase
        )
        
        # Verify results are correct
        self.assertEqual(
            optimized_metrics['result']['total_items'],
            unoptimized_metrics['result']['total_items']
        )
    
    def test_concurrent_operations(self):
        """Test concurrent operations with resource management."""
        # Define concurrent operation
        def concurrent_operation(operation_id: int) -> Dict[str, Any]:
            # Create temporary resource
            with self.resource_manager.temporary_resource(
                ResourceType.FILE,
                prefix=f"concurrent_{operation_id}"
            ) as resource:
                # Write data to file
                if resource and resource.path:
                    data = {
                        'operation_id': operation_id,
                        'timestamp': time.time(),
                        'data': [random.randint(1, 100) for _ in range(100)]
                    }
                    
                    with open(resource.path, 'w') as f:
                        json.dump(data, f)
                    
                    # Read data back
                    with open(resource.path, 'r') as f:
                        read_data = json.load(f)
                    
                    return read_data
            
            return {'error': 'No resource available'}
        
        # Apply optimizations
        optimized_operation = self.optimization_manager.optimize_function(
            concurrent_operation,
            OptimizationType.PARALLELIZATION,
            parallel=True
        )
        
        # Run concurrent operations
        num_operations = 20
        results = []
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(optimized_operation, i)
                for i in range(num_operations)
            ]
            results = [f.result() for f in futures]
        
        concurrent_time = time.time() - start_time
        
        # Run sequential operations for comparison
        start_time = time.time()
        sequential_results = [concurrent_operation(i) for i in range(num_operations)]
        sequential_time = time.time() - start_time
        
        # Store results
        self.results['concurrent_operations'].extend([
            concurrent_time,
            sequential_time
        ])
        
        # Verify concurrent execution is faster
        self.assertLess(concurrent_time, sequential_time * 0.7)  # At least 30% faster
        
        # Verify all operations completed successfully
        self.assertEqual(len(results), num_operations)
        self.assertEqual(len(sequential_results), num_operations)
        
        # Verify results are consistent
        for i, (concurrent_result, sequential_result) in enumerate(zip(results, sequential_results)):
            self.assertEqual(
                concurrent_result.get('operation_id'),
                sequential_result.get('operation_id')
            )
    
    def test_memory_intensive_workloads(self):
        """Test memory-intensive workloads with optimization."""
        # Define memory-intensive operation
        def memory_intensive_workload(workload_size: int) -> List[List[int]]:
            # Create large data structures
            matrices = []
            for i in range(workload_size):
                matrix = [[random.randint(1, 100) for _ in range(100)] for _ in range(100)]
                matrices.append(matrix)
            
            # Perform matrix operations
            results = []
            for matrix in matrices:
                # Transpose matrix
                transposed = list(zip(*matrix))
                # Calculate row sums
                row_sums = [sum(row) for row in matrix]
                # Calculate column sums
                col_sums = [sum(col) for col in transposed]
                
                results.append({
                    'matrix_id': len(results),
                    'row_sums': row_sums,
                    'col_sums': col_sums
                })
            
            return results
        
        # Apply memory optimization
        optimized_workload = self.optimization_manager.optimize_function(
            memory_intensive_workload,
            OptimizationType.MEMORY
        )
        
        # Measure performance with different workload sizes
        workload_sizes = [10, 20, 30]
        
        for size in workload_sizes:
            # Measure with optimization
            optimized_metrics = self._measure_comprehensive_performance(
                optimized_workload,
                size
            )
            
            # Measure without optimization
            unoptimized_metrics = self._measure_comprehensive_performance(
                memory_intensive_workload,
                size
            )
            
            # Store results
            self.results['memory_intensive_workloads'].extend([
                optimized_metrics['memory_rss_increase'],
                unoptimized_metrics['memory_rss_increase']
            ])
            
            # Verify memory optimization reduces usage
            self.assertLessEqual(
                optimized_metrics['memory_rss_increase'],
                unoptimized_metrics['memory_rss_increase'] * 1.1  # Allow 10% overhead
            )
            
            # Verify results are correct
            self.assertEqual(
                len(optimized_metrics['result']),
                len(unoptimized_metrics['result'])
            )
    
    def test_optimization_integration(self):
        """Test integration of all optimization techniques."""
        # Define complex operation that benefits from multiple optimizations
        def complex_operation(data_size: int, iterations: int) -> Dict[str, Any]:
            results = {
                'processed_items': 0,
                'cache_hits': 0,
                'memory_usage': 0,
                'execution_times': []
            }
            
            # Generate data
            dataset = self._generate_large_dataset(data_size)
            
            for i in range(iterations):
                start_time = time.time()
                
                # Process dataset with caching
                processed_data = []
                for item in dataset:
                    # Simulate expensive computation
                    processed_item = {
                        'id': item['id'],
                        'processed_data': sum(item['data']) * 2,
                        'category': item['metadata']['category'],
                        'iteration': i
                    }
                    processed_data.append(processed_item)
                
                end_time = time.time()
                results['execution_times'].append(end_time - start_time)
                results['processed_items'] += len(processed_data)
            
            return results
        
        # Apply multiple optimizations
        optimized_complex = self.optimization_manager.optimize_function(
            complex_operation,
            OptimizationType.CACHING,
            cache_key="complex_operation"
        )
        
        # Apply memory optimization
        memory_optimized = self.optimization_manager.optimize_function(
            optimized_complex,
            OptimizationType.MEMORY
        )
        
        # Measure performance with all optimizations
        optimized_metrics = self._measure_comprehensive_performance(
            memory_optimized,
            1000,  # data_size
            5      # iterations
        )
        
        # Measure performance without optimizations
        unoptimized_metrics = self._measure_comprehensive_performance(
            complex_operation,
            1000,  # data_size
            5      # iterations
        )
        
        # Store results
        self.results['optimization_integration'].extend([
            optimized_metrics['execution_time'],
            unoptimized_metrics['execution_time']
        ])
        
        # Verify optimizations provide significant benefits
        improvement_ratio = unoptimized_metrics['execution_time'] / optimized_metrics['execution_time']
        self.assertGreater(improvement_ratio, 1.2)  # At least 20% improvement
        
        # Verify memory usage is controlled
        self.assertLess(
            optimized_metrics['memory_rss_increase'],
            150 * 1024 * 1024  # Less than 150MB increase
        )
        
        # Verify results are correct
        self.assertEqual(
            optimized_metrics['result']['processed_items'],
            unoptimized_metrics['result']['processed_items']
        )
    
    def test_stress_testing(self):
        """Test system under stress conditions."""
        # Define stress test operation
        def stress_operation(operation_id: int, duration: float) -> Dict[str, Any]:
            start_time = time.time()
            operations = 0
            memory_usage = 0
            
            while time.time() - start_time < duration:
                # Create temporary data
                temp_data = [random.randint(1, 1000) for _ in range(100)]
                
                # Perform computation
                result = sum(temp_data) * len(temp_data)
                
                # Create temporary file
                with self.resource_manager.temporary_resource(
                    ResourceType.FILE,
                    prefix=f"stress_{operation_id}_{operations}"
                ) as resource:
                    if resource and resource.path:
                        with open(resource.path, 'w') as f:
                            f.write(str(result))
                
                operations += 1
                memory_usage += len(temp_data) * 8  # Approximate memory usage
            
            return {
                'operation_id': operation_id,
                'operations_completed': operations,
                'memory_used': memory_usage,
                'duration': time.time() - start_time
            }
        
        # Apply optimizations
        optimized_stress = self.optimization_manager.optimize_function(
            stress_operation,
            OptimizationType.MEMORY
        )
        
        # Run stress test with multiple concurrent operations
        num_stress_operations = 5
        stress_duration = 2.0  # seconds
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_stress_operations) as executor:
            futures = [
                executor.submit(optimized_stress, i, stress_duration)
                for i in range(num_stress_operations)
            ]
            stress_results = [f.result() for f in futures]
        
        total_stress_time = time.time() - start_time
        
        # Store results
        self.results['stress_testing'].append(total_stress_time)
        
        # Verify stress test completed successfully
        self.assertEqual(len(stress_results), num_stress_operations)
        
        # Verify all operations completed
        total_operations = sum(result['operations_completed'] for result in stress_results)
        self.assertGreater(total_operations, 0)
        
        # Verify memory usage is controlled
        total_memory = sum(result['memory_used'] for result in stress_results)
        self.assertLess(total_memory, 500 * 1024 * 1024)  # Less than 500MB
        
        # Verify system remains stable
        process = psutil.Process()
        current_memory = process.memory_info().rss
        self.assertLess(current_memory, 1 * 1024 * 1024 * 1024)  # Less than 1GB
    
    def test_performance_monitoring_integration(self):
        """Test integration with performance monitoring."""
        # Define monitored operation
        def monitored_operation(operation_id: int) -> Dict[str, Any]:
            # Use performance manager to measure
            def inner_operation():
                time.sleep(0.1)  # Simulate work
                return {
                    'operation_id': operation_id,
                    'result': operation_id * 2,
                    'timestamp': time.time()
                }
            
            return self.performance_manager.measure_performance(
                component_id="test_component",
                operation=f"monitored_operation_{operation_id}",
                func=inner_operation
            )
        
        # Run multiple monitored operations
        for i in range(10):
            result = monitored_operation(i)
            self.assertIn('operation_id', result)
            self.assertEqual(result['result'], i * 2)
        
        # Get performance metrics
        metrics = self.performance_manager.get_metrics(component_id="test_component")
        self.assertGreater(len(metrics), 0)
        
        # Verify metrics contain expected data
        for metric in metrics:
            self.assertEqual(metric.component_id, "test_component")
            self.assertGreaterEqual(metric.execution_time, 0.1)
            self.assertGreaterEqual(metric.memory_usage, 0)
    
    def test_memory_leak_detection_advanced(self):
        """Test advanced memory leak detection."""
        # Start memory monitoring
        self.memory_optimizer.start_monitoring(interval=0.5)
        
        # Create potential memory leak scenario
        leaked_objects = []
        
        def leaky_operation(iteration: int):
            # Create objects that might leak
            large_data = [i for i in range(1000)]
            leaked_objects.append(large_data)
            
            # Simulate work
            time.sleep(0.01)
            
            return len(large_data)
        
        # Run leaky operations
        for i in range(10):
            leaky_operation(i)
            time.sleep(0.1)
        
        # Get memory report
        memory_report = self.memory_optimizer.get_memory_report()
        
        # Verify leak detection is working
        self.assertIn('leak_detections', memory_report)
        self.assertIn('current_memory_mb', memory_report)
        
        # Clean up leaked objects
        leaked_objects.clear()
        gc.collect()
        
        # Verify memory is reclaimed
        final_memory_report = self.memory_optimizer.get_memory_report()
        
        # Stop monitoring
        self.memory_optimizer.stop_monitoring()
    
    def test_resource_management_advanced(self):
        """Test advanced resource management scenarios."""
        # Create complex resource scenario
        resources = []
        
        # Create different types of resources
        for i in range(5):
            # File resource
            with self.resource_manager.temporary_resource(
                ResourceType.FILE,
                prefix=f"advanced_file_{i}"
            ) as file_resource:
                if file_resource and file_resource.path:
                    with open(file_resource.path, 'w') as f:
                        f.write(f"File {i} content")
                    resources.append(file_resource)
            
            # Directory resource
            with self.resource_manager.temporary_resource(
                ResourceType.DIRECTORY,
                prefix=f"advanced_dir_{i}"
            ) as dir_resource:
                if dir_resource and dir_resource.path:
                    # Create files in directory
                    for j in range(3):
                        file_path = Path(dir_resource.path) / f"file_{j}.txt"
                        with open(file_path, 'w') as f:
                            f.write(f"File {j} in directory {i}")
                    resources.append(dir_resource)
        
        # Get resource report
        resource_report = self.resource_manager.get_resource_report()
        
        # Verify resources are tracked
        self.assertGreater(resource_report['total_resources'], 0)
        self.assertIn('file', resource_report['type_counts'])
        self.assertIn('directory', resource_report['type_counts'])
        
        # Test cleanup
        cleaned_count = self.resource_manager.cleanup_resources()
        self.assertGreater(cleaned_count, 0)
        
        # Verify cleanup worked
        final_report = self.resource_manager.get_resource_report()
        self.assertLessEqual(final_report['total_resources'], resource_report['total_resources'])
    
    def test_comprehensive_performance_summary(self):
        """Generate comprehensive performance summary."""
        # Run all performance tests
        self.test_large_dataset_processing()
        self.test_concurrent_operations()
        self.test_memory_intensive_workloads()
        self.test_optimization_integration()
        self.test_stress_testing()
        
        # Generate comprehensive summary
        print("\n" + "="*60)
        print("COMPREHENSIVE PERFORMANCE SUMMARY")
        print("="*60)
        
        for category, results in self.results.items():
            if results:
                print(f"\n{category.upper()}:")
                print(f"  Measurements: {len(results)}")
                
                if len(results) >= 2:
                    # Calculate statistics
                    avg_result = mean(results)
                    median_result = median(results)
                    min_result = min(results)
                    max_result = max(results)
                    
                    if len(results) > 2:
                        std_result = stdev(results)
                        print(f"  Average: {avg_result:.4f}")
                        print(f"  Median:  {median_result:.4f}")
                        print(f"  Std Dev: {std_result:.4f}")
                        print(f"  Min:     {min_result:.4f}")
                        print(f"  Max:     {max_result:.4f}")
                    else:
                        print(f"  Values:  {results}")
        
        # Print system information
        print(f"\nSYSTEM INFORMATION:")
        print(f"  CPU Cores: {multiprocessing.cpu_count()}")
        print(f"  Memory:    {psutil.virtual_memory().total / (1024**3):.1f} GB")
        
        # Print optimization effectiveness
        print(f"\nOPTIMIZATION EFFECTIVENESS:")
        
        if self.results['large_dataset_processing']:
            improvement = (self.results['large_dataset_processing'][1] / 
                          self.results['large_dataset_processing'][0])
            print(f"  Large Dataset Processing: {improvement:.2f}x improvement")
        
        if self.results['concurrent_operations']:
            improvement = (self.results['concurrent_operations'][1] / 
                          self.results['concurrent_operations'][0])
            print(f"  Concurrent Operations: {improvement:.2f}x improvement")
        
        if self.results['optimization_integration']:
            improvement = (self.results['optimization_integration'][1] / 
                          self.results['optimization_integration'][0])
            print(f"  Optimization Integration: {improvement:.2f}x improvement")
        
        print("="*60)


if __name__ == '__main__':
    unittest.main() 
