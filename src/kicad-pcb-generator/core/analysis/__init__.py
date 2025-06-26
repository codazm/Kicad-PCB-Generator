"""
Analysis module for advanced PCB analysis capabilities.

This module provides enhanced analysis tools for physical coupling,
electromagnetic effects, and component-specific modeling.
"""

from .mutual_inductance import MutualInductanceAnalyzer
from .capacitive_coupling import CapacitiveCouplingAnalyzer
from .high_frequency_coupling import HighFrequencyCouplingAnalyzer
from .thermal_coupling import ThermalCouplingAnalyzer

__all__ = [
    'MutualInductanceAnalyzer',
    'CapacitiveCouplingAnalyzer', 
    'HighFrequencyCouplingAnalyzer',
    'ThermalCouplingAnalyzer'
] 
