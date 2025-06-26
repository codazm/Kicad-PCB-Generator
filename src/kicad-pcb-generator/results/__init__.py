"""
Standardized result structures for the KiCad PCB Generator.
"""

from .analysis_result import AnalysisResult
from .optimization_result import OptimizationResult, OptimizationStrategy
from .config_result import ConfigResult, ConfigFormat, ConfigSection
from .manager_result import ManagerResult

__all__ = [
    'AnalysisResult',
    'OptimizationResult',
    'OptimizationStrategy', 
    'ConfigResult',
    'ConfigFormat',
    'ConfigSection',
    'ManagerResult'
] 
