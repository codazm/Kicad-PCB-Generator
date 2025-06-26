# Performance Optimization Guide

This guide covers the advanced performance optimization features of the KiCad PCB Generator, including memory optimization, resource management, caching strategies, and parallelization.

## Overview

The KiCad PCB Generator includes a comprehensive performance optimization system designed to handle large PCB designs efficiently while maintaining high accuracy for audio analysis. The system consists of four main components:

1. **Memory Optimizer**: Advanced memory management and leak detection
2. **Resource Manager**: Automatic resource lifecycle management
3. **Optimization Manager**: Caching, parallelization, and algorithm optimization
4. **Performance Manager**: Real-time monitoring and metrics

## Memory Optimization

### Memory Optimizer

The `MemoryOptimizer` provides advanced memory management capabilities:

```python
from kicad_pcb_generator.core.performance.memory_optimizer import MemoryOptimizer

# Initialize memory optimizer
memory_optimizer = MemoryOptimizer(
    enable_tracemalloc=True,      # Enable detailed memory tracking
    memory_threshold=100*1024*1024,  # 100MB warning threshold
    leak_threshold=10*1024*1024,     # 10MB leak detection threshold
    gc_threshold=1000               # Garbage collection threshold
)

# Start monitoring
memory_optimizer.start_monitoring(interval=1.0)

# Measure memory usage of a function
def expensive_operation():
    # Your expensive computation here
    return result

result = memory_optimizer.measure_memory(
    component_id="audio_analysis",
    operation="frequency_response",
    func=expensive_operation
)

# Get memory report
memory_report = memory_optimizer.get_memory_report()
print(f"Current memory: {memory_report['current_memory_mb']:.2f} MB")
print(f"Memory growth: {memory_report['memory_growth_mb']:.2f} MB")
print(f"Leak detections: {memory_report['leak_detections']}")

# Optimize memory
memory_optimizer.optimize_memory()

# Stop monitoring
memory_optimizer.stop_monitoring()
```

### Memory Leak Detection

The memory optimizer automatically detects potential memory leaks:

```python
# Memory leaks are automatically detected and reported
memory_report = memory_optimizer.get_memory_report()

if memory_report['leak_detections'] > 0:
    print("Potential memory leaks detected!")
    # Check the log for detailed leak information
```

### Garbage Collection Optimization

The memory optimizer includes intelligent garbage collection:

```python
# Optimize GC settings
memory_optimizer.gc_settings = {
    'threshold0': 700,   # Generation 0 threshold
    'threshold1': 10,    # Generation 1 threshold  
    'threshold2': 10     # Generation 2 threshold
}

# Force optimization
memory_optimizer.optimize_memory()
```

## Resource Management

### Resource Manager

The `ResourceManager` provides automatic resource lifecycle management:

```python
from kicad_pcb_generator.core.performance.resource_manager import ResourceManager, ResourceType

# Initialize resource manager
resource_manager = ResourceManager(
    temp_dir="/tmp/kicad_resources",
    max_temp_size=50*1024*1024,  # 50MB
    cleanup_interval=300.0,      # 5 minutes
    auto_cleanup=True
)

# Register a resource
resource_manager.register_resource(
    resource_id="temp_file_001",
    resource_type=ResourceType.FILE,
    path="/tmp/temp_file.txt",
    size=1024,
    cleanup_callback=lambda r: print(f"Cleaning up {r.resource_id}")
)

# Use temporary resources with context managers
with resource_manager.temporary_resource(
    ResourceType.FILE,
    prefix="analysis",
    suffix=".json"
) as resource:
    if resource and resource.path:
        # Write data to temporary file
        with open(resource.path, 'w') as f:
            json.dump(data, f)
        
        # Process the file
        result = process_file(resource.path)

# Get resource report
resource_report = resource_manager.get_resource_report()
print(f"Total resources: {resource_report['total_resources']}")
print(f"Total size: {resource_report['total_size_mb']:.2f} MB")

# Manual cleanup
cleaned_count = resource_manager.cleanup_resources()
print(f"Cleaned {cleaned_count} resources")
```

### Resource Types

The resource manager supports multiple resource types:

- **FILE**: Temporary files
- **DIRECTORY**: Temporary directories
- **MEMORY**: Memory allocations
- **THREAD**: Thread resources
- **NETWORK**: Network connections
- **DATABASE**: Database connections
- **CACHE**: Cache resources
- **TEMPORARY**: General temporary resources

## Caching and Optimization

### Optimization Manager

The `OptimizationManager` provides intelligent caching and parallelization:

```python
from kicad_pcb_generator.core.performance.optimization_manager import (
    OptimizationManager, OptimizationType
)

# Initialize optimization manager
optimization_manager = OptimizationManager(
    cache_dir="/tmp/kicad_cache",
    max_workers=8,
    enable_parallelization=True,
    enable_caching=True
)

# Apply caching optimization to a function
@optimization_manager.optimize_function(
    optimization_type=OptimizationType.CACHING,
    cache_key="audio_analysis"
)
def analyze_audio_performance(board):
    # Expensive audio analysis
    return analysis_results

# Apply parallelization optimization
@optimization_manager.optimize_function(
    optimization_type=OptimizationType.PARALLELIZATION,
    parallel=True
)
def parallel_processing(data_list):
    # Process data in parallel
    return processed_results

# Apply memory optimization
@optimization_manager.optimize_function(
    optimization_type=OptimizationType.MEMORY
)
def memory_intensive_operation(data):
    # Memory-intensive operation
    return result

# Apply multiple optimizations
optimized_function = optimization_manager.optimize_function(
    original_function,
    optimization_type=OptimizationType.CACHING,
    cache_key="my_function",
    parallel=True
)

# Get optimization report
optimization_report = optimization_manager.get_optimization_report()
print(f"Active optimizations: {optimization_report['active_optimizations']}")

# Get cache statistics
cache_stats = optimization_manager.get_cache_stats()
print(f"Cache hits: {cache_stats['memory_entries']}")
print(f"Cache size: {cache_stats['total_size_mb']:.2f} MB")

# Clear cache
optimization_manager.clear_cache()
```

### Caching Strategies

The optimization manager supports multiple caching strategies:

```python
# LRU (Least Recently Used) caching
config = OptimizationConfig(
    optimization_id="lru_cache",
    optimization_type=OptimizationType.CACHING,
    parameters={"strategy": "lru", "max_size": 1000}
)

# FIFO (First In, First Out) caching
config = OptimizationConfig(
    optimization_id="fifo_cache",
    optimization_type=OptimizationType.CACHING,
    parameters={"strategy": "fifo", "max_size": 1000}
)

# TTL (Time To Live) caching
config = OptimizationConfig(
    optimization_id="ttl_cache",
    optimization_type=OptimizationType.CACHING,
    cache_ttl=3600,  # 1 hour
    parameters={"strategy": "ttl"}
)
```

## Performance Monitoring

### Performance Manager

The `PerformanceManager` provides real-time performance monitoring:

```python
from kicad_pcb_generator.core.performance.performance_manager import PerformanceManager

# Initialize performance manager
performance_manager = PerformanceManager(
    max_workers=4,
    metrics_dir="performance_metrics"
)

# Start monitoring
performance_manager.start_monitoring(interval=1.0)

# Measure performance of a function
def expensive_operation():
    # Your expensive computation
    return result

result = performance_manager.measure_performance(
    component_id="audio_analysis",
    operation="thd_analysis",
    func=expensive_operation
)

# Get performance metrics
metrics = performance_manager.get_metrics(component_id="audio_analysis")
for metric in metrics:
    print(f"Operation: {metric.operation}")
    print(f"Execution time: {metric.execution_time:.3f}s")
    print(f"Memory usage: {metric.memory_usage / (1024*1024):.2f} MB")
    print(f"CPU usage: {metric.cpu_usage:.1f}%")

# Generate performance report
report = performance_manager.generate_report("audio_analysis")
print(f"Total operations: {report.summary['total_operations']}")
print(f"Average execution time: {report.summary['avg_execution_time']:.3f}s")
print(f"Recommendations: {report.recommendations}")

# Stop monitoring
performance_manager.stop_monitoring()
```

## Integration Examples

### Audio Analysis with Optimization

```python
from kicad_pcb_generator.audio.analysis.advanced_audio_analyzer import AdvancedAudioAnalyzer
from kicad_pcb_generator.core.performance import (
    MemoryOptimizer, ResourceManager, OptimizationManager, PerformanceManager
)

# Initialize all performance components
memory_optimizer = MemoryOptimizer(enable_tracemalloc=True)
resource_manager = ResourceManager(auto_cleanup=True)
optimization_manager = OptimizationManager(enable_caching=True, enable_parallelization=True)
performance_manager = PerformanceManager()

# Start monitoring
memory_optimizer.start_monitoring()
performance_manager.start_monitoring()

# Create optimized audio analyzer
analyzer = AdvancedAudioAnalyzer(
    board,
    memory_optimizer=memory_optimizer,
    resource_manager=resource_manager,
    optimization_manager=optimization_manager,
    performance_manager=performance_manager
)

# Perform comprehensive analysis
results = analyzer.analyze_audio_performance()

# Get performance reports
memory_report = memory_optimizer.get_memory_report()
resource_report = resource_manager.get_resource_report()
optimization_report = optimization_manager.get_optimization_report()
performance_report = performance_manager.generate_report("audio_analysis")

# Print results
print(f"THD+N: {results.thd_plus_n:.3f}%")
print(f"Memory used: {memory_report['current_memory_mb']:.2f} MB")
print(f"Cache hits: {optimization_report['cache_stats']['memory_entries']}")
print(f"Performance improvement: {performance_report.summary['avg_execution_time']:.3f}s")
```

### Large Dataset Processing

```python
# Process large datasets efficiently
def process_large_dataset(dataset):
    # Apply multiple optimizations
    optimized_process = optimization_manager.optimize_function(
        process_dataset,
        optimization_type=OptimizationType.CACHING,
        cache_key="large_dataset_processing"
    )
    
    # Apply memory optimization
    memory_optimized = optimization_manager.optimize_function(
        optimized_process,
        optimization_type=OptimizationType.MEMORY
    )
    
    # Process with monitoring
    result = performance_manager.measure_performance(
        component_id="dataset_processing",
        operation="large_dataset",
        func=memory_optimized,
        dataset
    )
    
    return result

# Use temporary resources for large files
with resource_manager.temporary_resource(
    ResourceType.FILE,
    prefix="large_dataset",
    suffix=".json"
) as temp_file:
    if temp_file and temp_file.path:
        # Write large dataset to temporary file
        with open(temp_file.path, 'w') as f:
            json.dump(large_dataset, f)
        
        # Process the file
        result = process_large_dataset(temp_file.path)
```

## Best Practices

### Memory Management

1. **Use Memory Optimizer**: Always use the memory optimizer for expensive operations
2. **Monitor Memory Usage**: Set appropriate thresholds and monitor for leaks
3. **Optimize Garbage Collection**: Configure GC settings for your workload
4. **Clean Up Resources**: Use context managers for temporary resources

### Caching

1. **Choose Appropriate Cache Keys**: Use unique, deterministic cache keys
2. **Set TTL Values**: Configure appropriate time-to-live values
3. **Monitor Cache Performance**: Track hit rates and cache size
4. **Clear Cache When Needed**: Clear cache when data becomes stale

### Parallelization

1. **Identify Parallelizable Operations**: Look for independent operations
2. **Use Appropriate Pool Sizes**: Set worker counts based on CPU cores
3. **Handle Exceptions**: Properly handle exceptions in parallel operations
4. **Monitor Resource Usage**: Watch for resource contention

### Resource Management

1. **Use Context Managers**: Always use context managers for temporary resources
2. **Set Cleanup Intervals**: Configure appropriate cleanup intervals
3. **Monitor Resource Usage**: Track resource counts and sizes
4. **Handle Cleanup Errors**: Properly handle cleanup failures

## Performance Tuning

### Configuration Guidelines

```python
# For memory-intensive workloads
memory_optimizer = MemoryOptimizer(
    memory_threshold=200*1024*1024,  # 200MB
    leak_threshold=20*1024*1024,     # 20MB
    gc_threshold=500                 # Lower threshold
)

# For CPU-intensive workloads
optimization_manager = OptimizationManager(
    max_workers=multiprocessing.cpu_count(),
    enable_parallelization=True,
    enable_caching=True
)

# For I/O-intensive workloads
resource_manager = ResourceManager(
    cleanup_interval=60.0,  # More frequent cleanup
    auto_cleanup=True
)
```

### Monitoring and Debugging

```python
# Enable detailed monitoring
memory_optimizer = MemoryOptimizer(enable_tracemalloc=True)
performance_manager = PerformanceManager()

# Get detailed reports
memory_report = memory_optimizer.get_memory_report()
if memory_report['leak_detections'] > 0:
    print("Memory leaks detected - check logs for details")

performance_report = performance_manager.generate_report("component")
for recommendation in performance_report.recommendations:
    print(f"Recommendation: {recommendation}")
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check for memory leaks using the memory optimizer
   - Optimize garbage collection settings
   - Use memory optimization for expensive operations

2. **Slow Performance**
   - Enable caching for repeated operations
   - Use parallelization for independent operations
   - Monitor performance metrics for bottlenecks

3. **Resource Leaks**
   - Use resource manager context managers
   - Check cleanup intervals and thresholds
   - Monitor resource reports

4. **Cache Issues**
   - Verify cache keys are unique and deterministic
   - Check TTL settings
   - Monitor cache hit rates

### Debugging Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get comprehensive reports
memory_report = memory_optimizer.get_memory_report()
resource_report = resource_manager.get_resource_report()
optimization_report = optimization_manager.get_optimization_report()
performance_report = performance_manager.generate_report("all")

# Print detailed information
print("Memory Report:", json.dumps(memory_report, indent=2))
print("Resource Report:", json.dumps(resource_report, indent=2))
print("Optimization Report:", json.dumps(optimization_report, indent=2))
print("Performance Report:", json.dumps(performance_report.summary, indent=2))
```

This performance optimization system provides comprehensive tools for managing memory, resources, caching, and parallelization, ensuring optimal performance for even the most complex PCB designs and audio analysis tasks. 