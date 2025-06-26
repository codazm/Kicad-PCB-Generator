# Performance Optimization API Reference

This document provides detailed API reference for the performance optimization system in the KiCad PCB Generator.

## Memory Optimizer

### MemoryOptimizer

Advanced memory management and leak detection system.

#### Constructor

```python
MemoryOptimizer(
    logger: Optional[logging.Logger] = None,
    enable_tracemalloc: bool = True,
    memory_threshold: int = 100 * 1024 * 1024,
    leak_threshold: int = 10 * 1024 * 1024,
    gc_threshold: int = 1000
)
```

**Parameters:**
- `logger`: Optional logger instance
- `enable_tracemalloc`: Enable tracemalloc for detailed memory tracking
- `memory_threshold`: Memory usage threshold for warnings (bytes)
- `leak_threshold`: Memory leak detection threshold (bytes)
- `gc_threshold`: Garbage collection threshold (objects)

#### Methods

##### start_monitoring(interval: float = 1.0)

Start memory monitoring.

**Parameters:**
- `interval`: Monitoring interval in seconds

##### stop_monitoring()

Stop memory monitoring.

##### measure_memory(component_id: str, operation: str, func: Callable, *args, **kwargs)

Measure memory usage of a function.

**Parameters:**
- `component_id`: Component identifier
- `operation`: Operation name
- `func`: Function to measure
- `*args`: Function arguments
- `**kwargs`: Function keyword arguments

**Returns:**
- Function result

##### optimize_memory()

Perform memory optimization.

##### get_memory_report() -> Dict[str, Any]

Get comprehensive memory report.

**Returns:**
- Memory report dictionary

#### Properties

- `gc_settings`: Garbage collection settings dictionary
- `thresholds`: Performance thresholds dictionary

### MemoryMetrics

Memory usage metrics for a component or operation.

```python
@dataclass
class MemoryMetrics:
    component_id: str
    operation: str
    memory_usage: int  # bytes
    memory_peak: int   # peak memory usage
    object_count: int  # number of objects
    gc_collections: int  # garbage collection count
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### MemoryLeak

Memory leak detection result.

```python
@dataclass
class MemoryLeak:
    component_id: str
    operation: str
    memory_increase: int  # bytes
    object_increase: int  # number of objects
    duration: float  # seconds
    severity: MemorySeverity
    timestamp: datetime
    details: str
    recommendations: List[str] = field(default_factory=list)
```

### MemorySeverity

Memory issue severity levels.

```python
class MemorySeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

## Resource Manager

### ResourceManager

Automatic resource lifecycle management system.

#### Constructor

```python
ResourceManager(
    logger: Optional[logging.Logger] = None,
    temp_dir: Optional[str] = None,
    max_temp_size: int = 100 * 1024 * 1024,
    cleanup_interval: float = 300.0,
    auto_cleanup: bool = True
)
```

**Parameters:**
- `logger`: Optional logger instance
- `temp_dir`: Temporary directory path
- `max_temp_size`: Maximum temporary file size (bytes)
- `cleanup_interval`: Automatic cleanup interval (seconds)
- `auto_cleanup`: Enable automatic cleanup

#### Methods

##### register_resource(resource_id: str, resource_type: ResourceType, path: Optional[str] = None, size: Optional[int] = None, cleanup_callback: Optional[Callable] = None, metadata: Optional[Dict[str, Any]] = None)

Register a new resource.

**Parameters:**
- `resource_id`: Unique resource identifier
- `resource_type`: Type of resource
- `path`: Resource path (for file/directory resources)
- `size`: Resource size in bytes
- `cleanup_callback`: Optional cleanup callback function
- `metadata`: Additional metadata

**Returns:**
- Manager result with resource information

##### unregister_resource(resource_id: str)

Unregister a resource.

**Parameters:**
- `resource_id`: Resource identifier

**Returns:**
- Manager result indicating success

##### get_resource(resource_id: str) -> Optional[Resource]

Get resource by ID.

**Parameters:**
- `resource_id`: Resource identifier

**Returns:**
- Resource object or None

##### list_resources(resource_type: Optional[ResourceType] = None) -> List[Resource]

List all resources, optionally filtered by type.

**Parameters:**
- `resource_type`: Optional resource type filter

**Returns:**
- List of resources

##### cleanup_resources(resource_type: Optional[ResourceType] = None) -> int

Clean up resources.

**Parameters:**
- `resource_type`: Optional resource type to clean up

**Returns:**
- Number of resources cleaned up

##### get_resource_report() -> Dict[str, Any]

Get comprehensive resource report.

**Returns:**
- Resource report dictionary

##### temporary_resource(resource_type: ResourceType, prefix: str = "temp", suffix: str = "", cleanup: bool = True)

Context manager for temporary resources.

**Parameters:**
- `resource_type`: Type of temporary resource
- `prefix`: File prefix
- `suffix`: File suffix
- `cleanup`: Whether to clean up on exit

**Yields:**
- Resource object

### Resource

Resource information.

```python
@dataclass
class Resource:
    resource_id: str
    resource_type: ResourceType
    path: Optional[str] = None
    size: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    status: ResourceStatus = ResourceStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    cleanup_callback: Optional[Callable] = None
```

### ResourceType

Types of resources that can be managed.

```python
class ResourceType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    MEMORY = "memory"
    THREAD = "thread"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    TEMPORARY = "temporary"
```

### ResourceStatus

Resource status.

```python
class ResourceStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CLEANED = "cleaned"
```

## Optimization Manager

### OptimizationManager

Advanced performance optimization with caching and parallelization.

#### Constructor

```python
OptimizationManager(
    logger: Optional[logging.Logger] = None,
    cache_dir: Optional[str] = None,
    max_workers: int = None,
    enable_parallelization: bool = True,
    enable_caching: bool = True
)
```

**Parameters:**
- `logger`: Optional logger instance
- `cache_dir`: Cache directory path
- `max_workers`: Maximum number of worker threads/processes
- `enable_parallelization`: Enable parallel processing
- `enable_caching`: Enable caching optimizations

#### Methods

##### register_optimization(config: OptimizationConfig)

Register an optimization configuration.

**Parameters:**
- `config`: Optimization configuration

**Returns:**
- Manager result with configuration

##### get_optimization(optimization_id: str) -> Optional[OptimizationConfig]

Get optimization configuration.

**Parameters:**
- `optimization_id`: Optimization identifier

**Returns:**
- Optimization configuration or None

##### enable_optimization(optimization_id: str) -> bool

Enable an optimization.

**Parameters:**
- `optimization_id`: Optimization identifier

**Returns:**
- True if optimization was enabled

##### disable_optimization(optimization_id: str) -> bool

Disable an optimization.

**Parameters:**
- `optimization_id`: Optimization identifier

**Returns:**
- True if optimization was disabled

##### optimize_function(func: Callable[..., T], optimization_type: OptimizationType, cache_key: Optional[str] = None, parallel: bool = False, **kwargs)

Apply optimizations to a function.

**Parameters:**
- `func`: Function to optimize
- `optimization_type`: Type of optimization to apply
- `cache_key`: Optional cache key for caching optimization
- `parallel`: Whether to enable parallel execution
- `**kwargs`: Additional optimization parameters

**Returns:**
- Optimized function

##### get_cache_stats() -> Dict[str, Any]

Get cache statistics.

**Returns:**
- Cache statistics dictionary

##### clear_cache()

Clear all cache entries.

##### get_optimization_report() -> Dict[str, Any]

Get comprehensive optimization report.

**Returns:**
- Optimization report dictionary

### OptimizationConfig

Optimization configuration.

```python
@dataclass
class OptimizationConfig:
    optimization_id: str
    optimization_type: OptimizationType
    enabled: bool = True
    priority: int = 1  # Higher number = higher priority
    max_workers: int = 4
    cache_size: int = 1000
    cache_ttl: int = 3600  # seconds
    parameters: Dict[str, Any] = field(default_factory=dict)
```

### OptimizationType

Types of optimizations.

```python
class OptimizationType(Enum):
    CACHING = "caching"
    PARALLELIZATION = "parallelization"
    ALGORITHM = "algorithm"
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"
```

### OptimizationStatus

Optimization status.

```python
class OptimizationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
```

### OptimizationResult

Optimization result.

```python
@dataclass
class OptimizationResult:
    optimization_id: str
    optimization_type: OptimizationType
    status: OptimizationStatus
    performance_improvement: float  # percentage
    execution_time: float
    memory_saved: int  # bytes
    timestamp: datetime
    details: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Performance Manager

### PerformanceManager

Real-time performance monitoring and metrics collection.

#### Constructor

```python
PerformanceManager(
    logger: Optional[logging.Logger] = None,
    max_workers: int = 4,
    metrics_dir: str = "performance_metrics"
)
```

**Parameters:**
- `logger`: Optional logger instance
- `max_workers`: Maximum number of worker threads
- `metrics_dir`: Directory to store performance metrics

#### Methods

##### start_monitoring(interval: float = 1.0)

Start performance monitoring.

**Parameters:**
- `interval`: Monitoring interval in seconds

##### stop_monitoring()

Stop performance monitoring.

##### measure_performance(component_id: str, operation: str, func: Callable, *args, **kwargs)

Measure performance of a function.

**Parameters:**
- `component_id`: Component identifier
- `operation`: Operation name
- `func`: Function to measure
- `*args`: Function arguments
- `**kwargs`: Function keyword arguments

**Returns:**
- Function result

##### get_metrics(component_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[PerformanceMetrics]

Get performance metrics.

**Parameters:**
- `component_id`: Component ID
- `start_time`: Optional start time
- `end_time`: Optional end time

**Returns:**
- List of performance metrics

##### generate_report(component_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> PerformanceReport

Generate a performance report.

**Parameters:**
- `component_id`: Component ID
- `start_time`: Optional start time
- `end_time`: Optional end time

**Returns:**
- Performance report

### PerformanceMetrics

Performance metrics for a component or operation.

```python
@dataclass
class PerformanceMetrics:
    component_id: str
    operation: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    metadata: Dict[str, Any]
```

### PerformanceReport

Performance report with summary and recommendations.

```python
@dataclass
class PerformanceReport:
    component_id: str
    start_time: datetime
    end_time: datetime
    metrics: List[PerformanceMetrics]
    summary: Dict[str, float]
    recommendations: List[str]
```

### PerformanceSeverity

Performance issue severity levels.

```python
class PerformanceSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

## Integration Examples

### Complete Performance Optimization Setup

```python
from kicad_pcb_generator.core.performance import (
    MemoryOptimizer, ResourceManager, OptimizationManager, PerformanceManager,
    OptimizationType
)

# Initialize all performance components
memory_optimizer = MemoryOptimizer(
    enable_tracemalloc=True,
    memory_threshold=200*1024*1024,  # 200MB
    leak_threshold=20*1024*1024      # 20MB
)

resource_manager = ResourceManager(
    temp_dir="/tmp/kicad_resources",
    max_temp_size=100*1024*1024,  # 100MB
    cleanup_interval=300.0,       # 5 minutes
    auto_cleanup=True
)

optimization_manager = OptimizationManager(
    cache_dir="/tmp/kicad_cache",
    max_workers=8,
    enable_parallelization=True,
    enable_caching=True
)

performance_manager = PerformanceManager(
    max_workers=4,
    metrics_dir="performance_metrics"
)

# Start monitoring
memory_optimizer.start_monitoring(interval=1.0)
performance_manager.start_monitoring(interval=1.0)

# Define optimized function
@optimization_manager.optimize_function(
    optimization_type=OptimizationType.CACHING,
    cache_key="audio_analysis"
)
def analyze_audio_performance(board):
    # Expensive audio analysis
    return analysis_results

# Use with resource management
with resource_manager.temporary_resource(
    ResourceType.FILE,
    prefix="audio_analysis",
    suffix=".json"
) as temp_file:
    if temp_file and temp_file.path:
        # Write analysis data
        with open(temp_file.path, 'w') as f:
            json.dump(data, f)
        
        # Perform optimized analysis
        result = performance_manager.measure_performance(
            component_id="audio_analysis",
            operation="comprehensive_analysis",
            func=analyze_audio_performance,
            board
        )

# Get comprehensive reports
memory_report = memory_optimizer.get_memory_report()
resource_report = resource_manager.get_resource_report()
optimization_report = optimization_manager.get_optimization_report()
performance_report = performance_manager.generate_report("audio_analysis")

# Stop monitoring
memory_optimizer.stop_monitoring()
performance_manager.stop_monitoring()
```

### Memory Optimization Example

```python
# Memory-intensive operation with optimization
def memory_intensive_operation(data_size: int):
    # Create large data structures
    matrices = []
    for i in range(data_size):
        matrix = [[i + j for j in range(100)] for _ in range(100)]
        matrices.append(matrix)
    
    # Perform matrix operations
    results = []
    for matrix in matrices:
        # Transpose matrix
        transposed = list(zip(*matrix))
        # Calculate row sums
        row_sums = [sum(row) for row in matrix]
        results.append({
            'matrix_id': len(results),
            'row_sums': row_sums
        })
    
    return results

# Apply memory optimization
optimized_operation = optimization_manager.optimize_function(
    memory_intensive_operation,
    optimization_type=OptimizationType.MEMORY
)

# Measure memory usage
result = memory_optimizer.measure_memory(
    component_id="matrix_operations",
    operation="large_matrix_processing",
    func=optimized_operation,
    50  # data_size
)

# Get memory report
memory_report = memory_optimizer.get_memory_report()
print(f"Memory used: {memory_report['current_memory_mb']:.2f} MB")
print(f"Memory growth: {memory_report['memory_growth_mb']:.2f} MB")
```

### Caching Example

```python
# Expensive computation with caching
def expensive_computation(n: int, complexity: str = "high"):
    import time
    time.sleep(0.1)  # Simulate expensive computation
    
    if complexity == "high":
        return sum(i * i * i for i in range(n))
    else:
        return sum(i * i for i in range(n))

# Apply caching optimization
cached_computation = optimization_manager.optimize_function(
    expensive_computation,
    optimization_type=OptimizationType.CACHING,
    cache_key="expensive_computation"
)

# First run (no cache)
start_time = time.time()
result1 = cached_computation(1000, "high")
first_run_time = time.time() - start_time

# Second run (should use cache)
start_time = time.time()
result2 = cached_computation(1000, "high")
second_run_time = time.time() - start_time

# Verify caching worked
assert result1 == result2
assert second_run_time < first_run_time * 0.5  # At least 50% faster

# Get cache statistics
cache_stats = optimization_manager.get_cache_stats()
print(f"Cache hits: {cache_stats['memory_entries']}")
print(f"Cache size: {cache_stats['total_size_mb']:.2f} MB")
```

### Parallelization Example

```python
# Parallelizable operation
def parallel_work(item: int) -> int:
    import time
    time.sleep(0.01)  # Simulate work
    return item * item

# Apply parallelization optimization
parallel_work_optimized = optimization_manager.optimize_function(
    parallel_work,
    optimization_type=OptimizationType.PARALLELIZATION,
    parallel=True
)

# Sequential execution
def sequential_execution():
    return [parallel_work(i) for i in range(100)]

# Parallel execution
def parallel_execution():
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(parallel_work_optimized, i) for i in range(100)]
        return [f.result() for f in futures]

# Measure performance
sequential_time = performance_manager.measure_performance(
    component_id="parallel_test",
    operation="sequential",
    func=sequential_execution
)

parallel_time = performance_manager.measure_performance(
    component_id="parallel_test",
    operation="parallel",
    func=parallel_execution
)

# Verify parallelization provides improvement
assert parallel_time < sequential_time * 0.8  # At least 20% faster
```

This API reference provides comprehensive documentation for all performance optimization features in the KiCad PCB Generator, enabling developers to effectively use the advanced performance capabilities for optimal PCB design and audio analysis performance. 
