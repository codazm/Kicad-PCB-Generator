"""
Thermal Coupling Analysis for Audio PCB Design.

This module provides thermal coupling analysis including temperature effects on
component parasitics, thermal expansion effects, and power dissipation coupling.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import numpy as np

from ..base.base_analyzer import BaseAnalyzer
from ..base.results.analysis_result import AnalysisResult, AnalysisType, AnalysisSeverity
from ..base.base_config import BaseConfig

logger = logging.getLogger(__name__)

class ThermalEffectType(Enum):
    """Types of thermal effects on coupling."""
    TEMPERATURE_COEFFICIENT = "temperature_coefficient"
    THERMAL_EXPANSION = "thermal_expansion"
    POWER_DISSIPATION = "power_dissipation"
    THERMAL_GRADIENT = "thermal_gradient"

@dataclass
class ThermalModel:
    """Data structure for thermal coupling model parameters."""
    effect_type: ThermalEffectType
    temperature_factor: float  # Temperature-dependent factor
    expansion_factor: float  # Thermal expansion factor
    power_dissipation: float  # Power dissipation in W
    thermal_resistance: float  # Thermal resistance in °C/W
    coupling_effects: Dict[str, float]  # Component ID -> coupling effect

@dataclass
class ThermalCouplingConfigItem:
    """Configuration for thermal coupling analysis."""
    # Analysis parameters
    ambient_temperature: float = 25.0  # °C
    max_temperature: float = 85.0  # °C
    temperature_points: int = 20
    
    # Component-specific parameters
    component_thermal_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    power_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    expansion_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Analysis thresholds
    min_temperature_rise: float = 5.0  # °C
    max_temperature_rise: float = 60.0  # °C
    thermal_coupling_threshold: float = 0.1  # 10% coupling
    
    # Material properties
    pcb_thermal_conductivity: float = 0.3  # W/m·K (FR4)
    copper_thermal_conductivity: float = 400.0  # W/m·K
    air_thermal_conductivity: float = 0.024  # W/m·K

@dataclass
class ThermalCouplingAnalysisItem:
    """Analysis item for thermal coupling calculations."""
    id: str
    analysis_type: AnalysisType
    board: Any  # pcbnew.BOARD
    config: ThermalCouplingConfigItem
    thermal_models: Dict[str, ThermalModel] = field(default_factory=dict)

class ThermalCouplingAnalyzer(BaseAnalyzer[ThermalCouplingAnalysisItem]):
    """Thermal coupling analyzer for audio PCB design."""
    
    def __init__(self, config: Optional[ThermalCouplingConfigItem] = None):
        """Initialize the thermal coupling analyzer.
        
        Args:
            config: Configuration for thermal coupling analysis
        """
        super().__init__()
        self.config = config or ThermalCouplingConfigItem()
        self.logger = logging.getLogger(__name__)
        
        # Component-specific thermal models
        self._component_models = self._initialize_component_models()
        self._power_models = self._initialize_power_models()
        self._expansion_models = self._initialize_expansion_models()
    
    def analyze_thermal_coupling(self, board: Any) -> AnalysisResult:
        """Analyze thermal coupling for all components on the board.
        
        Args:
            board: KiCad board object
            
        Returns:
            AnalysisResult with thermal coupling data
        """
        try:
            # Create analysis item
            analysis_item = ThermalCouplingAnalysisItem(
                id="thermal_coupling_analysis",
                analysis_type=AnalysisType.CUSTOM,
                board=board,
                config=self.config
            )
            
            # Perform analysis
            result = self.analyze(analysis_item, AnalysisType.CUSTOM)
            
            if result.success and result.data:
                return result
            else:
                # Fallback to direct analysis
                return self._perform_direct_analysis(board)
                
        except Exception as e:
            self.logger.error(f"Error in thermal coupling analysis: {str(e)}")
            return AnalysisResult(
                success=False,
                analysis_type=AnalysisType.CUSTOM,
                message=f"Thermal coupling analysis failed: {str(e)}",
                severity=AnalysisSeverity.ERROR,
                errors=[str(e)]
            )
    
    def analyze_temperature_effects(self, board: Any, temperature: float) -> Dict[str, float]:
        """Analyze temperature effects on component parasitics.
        
        Args:
            board: KiCad board object
            temperature: Analysis temperature in °C
            
        Returns:
            Dictionary with temperature effect data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                
                # Calculate temperature effects
                temp_effects = self._calculate_temperature_effects(component, temperature)
                
                results[ref] = {
                    'temperature_factor': temp_effects['factor'],
                    'resistance_change': temp_effects['resistance'],
                    'capacitance_change': temp_effects['capacitance'],
                    'inductance_change': temp_effects['inductance']
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing temperature effects: {str(e)}")
            return {}
    
    def analyze_thermal_expansion(self, board: Any, temperature: float) -> Dict[str, float]:
        """Analyze thermal expansion effects on component coupling.
        
        Args:
            board: KiCad board object
            temperature: Analysis temperature in °C
            
        Returns:
            Dictionary with thermal expansion data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                
                # Calculate thermal expansion effects
                expansion_effects = self._calculate_thermal_expansion(component, temperature)
                
                results[ref] = {
                    'expansion_factor': expansion_effects['factor'],
                    'position_change': expansion_effects['position'],
                    'size_change': expansion_effects['size'],
                    'coupling_change': expansion_effects['coupling']
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing thermal expansion: {str(e)}")
            return {}
    
    def analyze_power_dissipation(self, board: Any) -> Dict[str, float]:
        """Analyze power dissipation and thermal coupling.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary with power dissipation data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                
                # Calculate power dissipation
                power_effects = self._calculate_power_dissipation(component)
                
                results[ref] = {
                    'power_dissipation': power_effects['power'],
                    'temperature_rise': power_effects['temperature_rise'],
                    'thermal_resistance': power_effects['thermal_resistance'],
                    'coupling_effect': power_effects['coupling']
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing power dissipation: {str(e)}")
            return {}
    
    def analyze_thermal_gradients(self, board: Any) -> Dict[str, float]:
        """Analyze thermal gradients and their effects on coupling.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary with thermal gradient data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            # Calculate board-wide thermal gradients
            gradients = self._calculate_board_thermal_gradients(board)
            
            for component in components:
                ref = component.GetReference()
                
                # Calculate local thermal gradient effects
                gradient_effects = self._calculate_local_thermal_gradient(component, gradients)
                
                results[ref] = {
                    'local_gradient': gradient_effects['gradient'],
                    'temperature_variation': gradient_effects['variation'],
                    'coupling_variation': gradient_effects['coupling']
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing thermal gradients: {str(e)}")
            return {}
    
    def _initialize_component_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize component-specific thermal models."""
        return {
            'resistor': {
                'temperature_coefficient': 100.0,  # ppm/°C
                'thermal_resistance': 50.0,  # °C/W
                'power_rating': 0.25,  # W
                'expansion_coefficient': 6.0e-6  # 1/°C
            },
            'capacitor': {
                'temperature_coefficient': 50.0,  # ppm/°C
                'thermal_resistance': 30.0,  # °C/W
                'power_rating': 0.1,  # W
                'expansion_coefficient': 8.0e-6  # 1/°C
            },
            'inductor': {
                'temperature_coefficient': 200.0,  # ppm/°C
                'thermal_resistance': 80.0,  # °C/W
                'power_rating': 0.5,  # W
                'expansion_coefficient': 5.0e-6  # 1/°C
            },
            'ic': {
                'temperature_coefficient': 300.0,  # ppm/°C
                'thermal_resistance': 20.0,  # °C/W
                'power_rating': 1.0,  # W
                'expansion_coefficient': 4.0e-6  # 1/°C
            }
        }
    
    def _initialize_power_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize power dissipation models."""
        return {
            'low_power': {
                'power_factor': 0.1,
                'thermal_efficiency': 0.8,
                'coupling_factor': 0.05
            },
            'medium_power': {
                'power_factor': 0.5,
                'thermal_efficiency': 0.7,
                'coupling_factor': 0.1
            },
            'high_power': {
                'power_factor': 1.0,
                'thermal_efficiency': 0.6,
                'coupling_factor': 0.2
            }
        }
    
    def _initialize_expansion_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize thermal expansion models."""
        return {
            'pcb': {
                'expansion_coefficient': 16.0e-6,  # 1/°C (FR4)
                'thickness': 1.6,  # mm
                'coupling_factor': 0.1
            },
            'copper': {
                'expansion_coefficient': 17.0e-6,  # 1/°C
                'thickness': 0.035,  # mm
                'coupling_factor': 0.05
            },
            'component': {
                'expansion_coefficient': 6.0e-6,  # 1/°C
                'thickness': 2.0,  # mm
                'coupling_factor': 0.15
            }
        }
    
    def _calculate_temperature_effects(self, component: Any, temperature: float) -> Dict[str, float]:
        """Calculate temperature effects on component parasitics."""
        try:
            ref = component.GetReference()
            component_type = self._determine_component_type(ref)
            
            # Get component model
            model = self._component_models.get(component_type, self._component_models['ic'])
            
            # Calculate temperature change from ambient
            delta_t = temperature - self.config.ambient_temperature
            
            # Calculate temperature factor
            temp_coeff = model['temperature_coefficient'] * 1e-6  # Convert ppm to per °C
            temp_factor = 1.0 + temp_coeff * delta_t
            
            # Calculate changes in parasitics
            resistance_change = temp_factor - 1.0
            capacitance_change = temp_factor - 1.0
            inductance_change = temp_factor - 1.0
            
            return {
                'factor': temp_factor,
                'resistance': resistance_change,
                'capacitance': capacitance_change,
                'inductance': inductance_change
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating temperature effects: {str(e)}")
            return {'factor': 1.0, 'resistance': 0.0, 'capacitance': 0.0, 'inductance': 0.0}
    
    def _calculate_thermal_expansion(self, component: Any, temperature: float) -> Dict[str, float]:
        """Calculate thermal expansion effects on component coupling."""
        try:
            ref = component.GetReference()
            component_type = self._determine_component_type(ref)
            
            # Get expansion model
            expansion_model = self._expansion_models['component']
            
            # Calculate temperature change
            delta_t = temperature - self.config.ambient_temperature
            
            # Calculate expansion factor
            expansion_coeff = expansion_model['expansion_coefficient']
            expansion_factor = 1.0 + expansion_coeff * delta_t
            
            # Get component geometry
            bbox = component.GetBoundingBox()
            width = bbox.GetWidth() / 1e6  # mm
            height = bbox.GetHeight() / 1e6  # mm
            
            # Calculate size changes
            size_change = expansion_factor - 1.0
            
            # Calculate position changes (simplified)
            position_change = size_change * 0.5  # Assume center expansion
            
            # Calculate coupling changes
            coupling_change = expansion_model['coupling_factor'] * size_change
            
            return {
                'factor': expansion_factor,
                'position': position_change,
                'size': size_change,
                'coupling': coupling_change
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating thermal expansion: {str(e)}")
            return {'factor': 1.0, 'position': 0.0, 'size': 0.0, 'coupling': 0.0}
    
    def _calculate_power_dissipation(self, component: Any) -> Dict[str, float]:
        """Calculate power dissipation and thermal effects."""
        try:
            ref = component.GetReference()
            component_type = self._determine_component_type(ref)
            
            # Get component model
            model = self._component_models.get(component_type, self._component_models['ic'])
            
            # Estimate power dissipation based on component type
            power_rating = model['power_rating']
            power_factor = self._estimate_power_factor(component_type)
            power_dissipation = power_rating * power_factor
            
            # Calculate temperature rise
            thermal_resistance = model['thermal_resistance']
            temperature_rise = power_dissipation * thermal_resistance
            
            # Calculate coupling effect
            coupling_effect = power_dissipation * 0.1  # Simplified coupling factor
            
            return {
                'power': power_dissipation,
                'temperature_rise': temperature_rise,
                'thermal_resistance': thermal_resistance,
                'coupling': coupling_effect
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating power dissipation: {str(e)}")
            return {'power': 0.1, 'temperature_rise': 5.0, 'thermal_resistance': 50.0, 'coupling': 0.01}
    
    def _calculate_board_thermal_gradients(self, board: Any) -> Dict[str, float]:
        """Calculate board-wide thermal gradients."""
        try:
            # Simplified thermal gradient calculation
            # In practice, this would require finite element analysis
            
            # Get board dimensions
            bbox = board.GetBoundingBox()
            width = bbox.GetWidth() / 1e6  # mm
            height = bbox.GetHeight() / 1e6  # mm
            
            # Calculate simplified gradients
            gradients = {
                'x_gradient': 5.0 / width,  # 5°C across width
                'y_gradient': 3.0 / height,  # 3°C across height
                'max_gradient': 10.0 / min(width, height)  # Max gradient
            }
            
            return gradients
            
        except Exception as e:
            self.logger.error(f"Error calculating board thermal gradients: {str(e)}")
            return {'x_gradient': 0.01, 'y_gradient': 0.01, 'max_gradient': 0.02}
    
    def _calculate_local_thermal_gradient(self, component: Any, gradients: Dict[str, float]) -> Dict[str, float]:
        """Calculate local thermal gradient effects for a component."""
        try:
            # Get component position
            pos = component.GetPosition()
            x = pos.x / 1e6  # mm
            y = pos.y / 1e6  # mm
            
            # Calculate local gradient
            local_gradient = gradients['x_gradient'] * x + gradients['y_gradient'] * y
            
            # Calculate temperature variation
            temperature_variation = local_gradient * 10.0  # 10mm characteristic length
            
            # Calculate coupling variation
            coupling_variation = temperature_variation * 0.01  # 1% per °C
            
            return {
                'gradient': local_gradient,
                'variation': temperature_variation,
                'coupling': coupling_variation
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating local thermal gradient: {str(e)}")
            return {'gradient': 0.01, 'variation': 0.1, 'coupling': 0.001}
    
    def _determine_component_type(self, ref: str) -> str:
        """Determine component type based on reference."""
        ref_upper = ref.upper()
        
        if ref_upper.startswith('R'):
            return 'resistor'
        elif ref_upper.startswith('C'):
            return 'capacitor'
        elif ref_upper.startswith('L'):
            return 'inductor'
        elif ref_upper.startswith('U') or ref_upper.startswith('IC'):
            return 'ic'
        else:
            return 'ic'  # Default
    
    def _estimate_power_factor(self, component_type: str) -> float:
        """Estimate power factor for a component type."""
        power_factors = {
            'resistor': 0.3,
            'capacitor': 0.1,
            'inductor': 0.4,
            'ic': 0.6
        }
        
        return power_factors.get(component_type, 0.5)
    
    def _perform_direct_analysis(self, board: Any) -> AnalysisResult:
        """Perform direct thermal coupling analysis."""
        try:
            # Analyze at typical operating temperature
            operating_temp = 50.0  # °C
            
            # Perform all analyses
            temp_effects = self.analyze_temperature_effects(board, operating_temp)
            expansion_effects = self.analyze_thermal_expansion(board, operating_temp)
            power_effects = self.analyze_power_dissipation(board)
            gradient_effects = self.analyze_thermal_gradients(board)
            
            # Combine results
            combined_results = {
                'temperature_effects': temp_effects,
                'thermal_expansion': expansion_effects,
                'power_dissipation': power_effects,
                'thermal_gradients': gradient_effects,
                'analysis_temperature': operating_temp
            }
            
            return AnalysisResult(
                success=True,
                analysis_type=AnalysisType.CUSTOM,
                message="Thermal coupling analysis completed",
                severity=AnalysisSeverity.INFO,
                data=combined_results
            )
            
        except Exception as e:
            self.logger.error(f"Error in direct analysis: {str(e)}")
            return AnalysisResult(
                success=False,
                analysis_type=AnalysisType.CUSTOM,
                message=f"Direct analysis failed: {str(e)}",
                severity=AnalysisSeverity.ERROR,
                errors=[str(e)]
            ) 