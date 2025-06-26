"""
High-Frequency Physical Coupling Analysis for Audio PCB Design.

This module provides advanced high-frequency coupling analysis including proximity effects,
enhanced skin effect analysis, and radiation coupling for professional audio applications.
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

class CouplingType(Enum):
    """Types of high-frequency coupling."""
    PROXIMITY = "proximity"
    SKIN_EFFECT = "skin_effect"
    RADIATION = "radiation"
    DIELECTRIC = "dielectric"
    GROUND_COUPLING = "ground_coupling"

@dataclass
class HighFrequencyModel:
    """Data structure for high-frequency coupling model parameters."""
    coupling_type: CouplingType
    coupling_strength: float  # Coupling coefficient (0-1)
    frequency_dependence: Dict[float, float]  # Frequency -> coupling factor
    geometry_params: Dict[str, float]  # Geometry-specific parameters
    component_effects: Dict[str, float]  # Component ID -> effect strength

@dataclass
class HighFrequencyCouplingConfigItem:
    """Configuration for high-frequency coupling analysis."""
    # Analysis parameters
    frequency_range: Tuple[float, float] = field(default=(20000.0, 80000.0))  # 20kHz to 80kHz
    frequency_points: int = 50
    temperature: float = 25.0  # °C
    
    # Coupling parameters
    proximity_threshold: float = 0.1  # 10% coupling
    skin_effect_threshold: float = 0.05  # 5% effect
    radiation_threshold: float = 0.01  # 1% radiation
    dielectric_threshold: float = 0.02  # 2% dielectric loss
    
    # Audio-specific parameters
    audio_component_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    opamp_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    power_supply_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Analysis bands
    analysis_bands: List[Tuple[float, float]] = field(default_factory=lambda: [
        (20000.0, 30000.0),  # Low high-frequency
        (30000.0, 50000.0),  # Mid high-frequency
        (50000.0, 80000.0)   # High high-frequency
    ])

@dataclass
class HighFrequencyCouplingAnalysisItem:
    """Analysis item for high-frequency coupling calculations."""
    id: str
    analysis_type: AnalysisType
    board: Any  # pcbnew.BOARD
    config: HighFrequencyCouplingConfigItem
    coupling_models: Dict[str, HighFrequencyModel] = field(default_factory=dict)

class HighFrequencyCouplingAnalyzer(BaseAnalyzer[HighFrequencyCouplingAnalysisItem]):
    """High-frequency coupling analyzer for audio PCB design."""
    
    def __init__(self, config: Optional[HighFrequencyCouplingConfigItem] = None):
        """Initialize the high-frequency coupling analyzer.
        
        Args:
            config: Configuration for high-frequency coupling analysis
        """
        super().__init__()
        self.config = config or HighFrequencyCouplingConfigItem()
        self.logger = logging.getLogger(__name__)
        
        # Component-specific models
        self._audio_models = self._initialize_audio_models()
        self._opamp_models = self._initialize_opamp_models()
        self._power_models = self._initialize_power_models()
    
    def analyze_high_frequency_coupling(self, board: Any) -> AnalysisResult:
        """Analyze high-frequency coupling for all components on the board.
        
        Args:
            board: KiCad board object
            
        Returns:
            AnalysisResult with high-frequency coupling data
        """
        try:
            # Create analysis item
            analysis_item = HighFrequencyCouplingAnalysisItem(
                id="high_frequency_coupling_analysis",
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
            self.logger.error(f"Error in high-frequency coupling analysis: {str(e)}")
            return AnalysisResult(
                success=False,
                analysis_type=AnalysisType.CUSTOM,
                message=f"High-frequency coupling analysis failed: {str(e)}",
                severity=AnalysisSeverity.ERROR,
                errors=[str(e)]
            )
    
    def analyze_proximity_effects(self, board: Any, frequency: float) -> Dict[str, float]:
        """Analyze proximity effects between components at high frequencies.
        
        Args:
            board: KiCad board object
            frequency: Analysis frequency in Hz
            
        Returns:
            Dictionary with proximity effect data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                
                # Calculate proximity effects with nearby components
                proximity_effects = self._calculate_component_proximity_effects(
                    component, frequency
                )
                
                results[ref] = {
                    'total_proximity_effect': sum(proximity_effects.values()),
                    'max_proximity_effect': max(proximity_effects.values()) if proximity_effects else 0.0,
                    'affected_components': list(proximity_effects.keys())
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing proximity effects: {str(e)}")
            return {}
    
    def analyze_enhanced_skin_effects(self, board: Any, frequency: float) -> Dict[str, float]:
        """Analyze enhanced skin effects for audio components at high frequencies.
        
        Args:
            board: KiCad board object
            frequency: Analysis frequency in Hz
            
        Returns:
            Dictionary with skin effect data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                
                # Calculate enhanced skin effects
                skin_effect = self._calculate_enhanced_skin_effect(component, frequency)
                
                results[ref] = {
                    'skin_effect_factor': skin_effect['factor'],
                    'effective_resistance': skin_effect['resistance'],
                    'current_density': skin_effect['current_density']
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing enhanced skin effects: {str(e)}")
            return {}
    
    def analyze_radiation_coupling(self, board: Any, frequency: float) -> Dict[str, float]:
        """Analyze radiation coupling at high frequencies.
        
        Args:
            board: KiCad board object
            frequency: Analysis frequency in Hz
            
        Returns:
            Dictionary with radiation coupling data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                
                # Calculate radiation coupling
                radiation = self._calculate_radiation_coupling(component, frequency)
                
                results[ref] = {
                    'radiation_power': radiation['power'],
                    'radiation_efficiency': radiation['efficiency'],
                    'coupling_distance': radiation['distance']
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing radiation coupling: {str(e)}")
            return {}
    
    def analyze_opamp_coupling(self, board: Any, frequency: float) -> Dict[str, float]:
        """Analyze op-amp specific coupling effects at high frequencies.
        
        Args:
            board: KiCad board object
            frequency: Analysis frequency in Hz
            
        Returns:
            Dictionary with op-amp coupling data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                value = component.GetValue()
                
                # Check if component is an op-amp
                if self._is_opamp_component(ref, value):
                    coupling = self._calculate_opamp_coupling(component, frequency)
                    
                    results[ref] = {
                        'input_coupling': coupling['input'],
                        'output_coupling': coupling['output'],
                        'power_supply_coupling': coupling['power'],
                        'ground_coupling': coupling['ground']
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing op-amp coupling: {str(e)}")
            return {}
    
    def analyze_power_supply_coupling(self, board: Any, frequency: float) -> Dict[str, float]:
        """Analyze power supply coupling effects at high frequencies.
        
        Args:
            board: KiCad board object
            frequency: Analysis frequency in Hz
            
        Returns:
            Dictionary with power supply coupling data
        """
        try:
            results = {}
            components = board.GetFootprints()
            
            for component in components:
                ref = component.GetReference()
                
                # Check if component is power supply related
                if self._is_power_component(ref):
                    coupling = self._calculate_power_supply_coupling(component, frequency)
                    
                    results[ref] = {
                        'dc_coupling': coupling['dc'],
                        'ac_coupling': coupling['ac'],
                        'noise_coupling': coupling['noise'],
                        'ripple_coupling': coupling['ripple']
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing power supply coupling: {str(e)}")
            return {}
    
    def _initialize_audio_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize audio component models for high-frequency analysis."""
        return {
            'audio_capacitor': {
                'proximity_factor': 0.1,
                'skin_effect_factor': 0.05,
                'radiation_factor': 0.01,
                'frequency_dependence': 0.02
            },
            'audio_resistor': {
                'proximity_factor': 0.08,
                'skin_effect_factor': 0.03,
                'radiation_factor': 0.005,
                'frequency_dependence': 0.01
            },
            'audio_inductor': {
                'proximity_factor': 0.15,
                'skin_effect_factor': 0.1,
                'radiation_factor': 0.02,
                'frequency_dependence': 0.05
            }
        }
    
    def _initialize_opamp_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize op-amp models for high-frequency analysis."""
        return {
            'tl072': {
                'input_coupling': 0.02,
                'output_coupling': 0.03,
                'power_coupling': 0.05,
                'ground_coupling': 0.01,
                'frequency_dependence': 0.1
            },
            'ne5532': {
                'input_coupling': 0.015,
                'output_coupling': 0.025,
                'power_coupling': 0.04,
                'ground_coupling': 0.008,
                'frequency_dependence': 0.08
            },
            'opa2134': {
                'input_coupling': 0.01,
                'output_coupling': 0.02,
                'power_coupling': 0.03,
                'ground_coupling': 0.005,
                'frequency_dependence': 0.06
            }
        }
    
    def _initialize_power_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize power supply models for high-frequency analysis."""
        return {
            'regulator': {
                'dc_coupling': 0.05,
                'ac_coupling': 0.1,
                'noise_coupling': 0.02,
                'ripple_coupling': 0.03
            },
            'filter_capacitor': {
                'dc_coupling': 0.02,
                'ac_coupling': 0.08,
                'noise_coupling': 0.01,
                'ripple_coupling': 0.015
            },
            'power_trace': {
                'dc_coupling': 0.03,
                'ac_coupling': 0.06,
                'noise_coupling': 0.015,
                'ripple_coupling': 0.02
            }
        }
    
    def _calculate_component_proximity_effects(self, component: Any, frequency: float) -> Dict[str, float]:
        """Calculate proximity effects between a component and nearby components."""
        try:
            proximity_effects = {}
            all_components = component.GetBoard().GetFootprints()
            
            for other_component in all_components:
                if other_component == component:
                    continue
                
                # Calculate distance
                distance = self._calculate_component_distance(component, other_component)
                
                # Only consider nearby components (within 3mm for high-frequency effects)
                if distance < 3.0:
                    # Calculate proximity effect using simplified model
                    # Proximity effect increases with frequency and decreases with distance
                    base_effect = 0.1  # Base proximity effect
                    frequency_factor = math.log10(frequency / 20000.0)  # Normalized to 20kHz
                    distance_factor = math.exp(-distance / 1.0)  # Exponential decay
                    
                    proximity_effect = base_effect * frequency_factor * distance_factor
                    proximity_effects[other_component.GetReference()] = proximity_effect
            
            return proximity_effects
            
        except Exception as e:
            self.logger.error(f"Error calculating proximity effects: {str(e)}")
            return {}
    
    def _calculate_enhanced_skin_effect(self, component: Any, frequency: float) -> Dict[str, float]:
        """Calculate enhanced skin effect for a component."""
        try:
            # Enhanced skin effect calculation
            # Skin depth = sqrt(ρ / (π * μ * f))
            rho = 1.68e-8  # Copper resistivity
            mu = 4 * math.pi * 1e-7  # Permeability of free space
            
            skin_depth = math.sqrt(rho / (math.pi * mu * frequency))
            
            # Get component geometry
            bbox = component.GetBoundingBox()
            width = bbox.GetWidth() / 1e6  # mm
            height = bbox.GetHeight() / 1e6  # mm
            
            # Calculate effective resistance increase
            effective_area = width * height * 1e-6  # m²
            skin_area = 2 * math.pi * skin_depth * (width + height) * 1e-3  # m²
            
            if skin_area > 0:
                resistance_factor = effective_area / skin_area
            else:
                resistance_factor = 1.0
            
            # Calculate current density
            current_density = 1e6 / (skin_depth * 1e3)  # A/m²
            
            return {
                'factor': resistance_factor,
                'resistance': resistance_factor * 1e-3,  # mΩ
                'current_density': current_density
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced skin effect: {str(e)}")
            return {'factor': 1.0, 'resistance': 1e-3, 'current_density': 1e6}
    
    def _calculate_radiation_coupling(self, component: Any, frequency: float) -> Dict[str, float]:
        """Calculate radiation coupling for a component."""
        try:
            # Simplified radiation coupling calculation
            # Radiation power = k * f² * A * I²
            # where k is a constant, f is frequency, A is area, I is current
            
            bbox = component.GetBoundingBox()
            area = (bbox.GetWidth() * bbox.GetHeight()) / 1e12  # m²
            
            # Simplified constants
            k = 1e-12  # Radiation constant
            current = 0.01  # Assumed current (10mA)
            
            radiation_power = k * frequency * frequency * area * current * current
            
            # Radiation efficiency (simplified)
            efficiency = min(0.01, radiation_power / 1e-6)  # Max 1% efficiency
            
            # Coupling distance (simplified)
            distance = 0.1  # 10cm typical coupling distance
            
            return {
                'power': radiation_power,
                'efficiency': efficiency,
                'distance': distance
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating radiation coupling: {str(e)}")
            return {'power': 0.0, 'efficiency': 0.0, 'distance': 0.1}
    
    def _is_opamp_component(self, ref: str, value: str) -> bool:
        """Check if component is an op-amp."""
        ref_upper = ref.upper()
        value_upper = value.upper()
        
        opamp_identifiers = ['OP', 'OPA', 'TL', 'NE', 'LM', 'AD', 'LT']
        
        for identifier in opamp_identifiers:
            if identifier in ref_upper or identifier in value_upper:
                return True
        
        return False
    
    def _calculate_opamp_coupling(self, component: Any, frequency: float) -> Dict[str, float]:
        """Calculate op-amp specific coupling effects."""
        try:
            value = component.GetValue().upper()
            
            # Get op-amp model
            opamp_model = None
            for model_name in self._opamp_models:
                if model_name.upper() in value:
                    opamp_model = self._opamp_models[model_name]
                    break
            
            if opamp_model is None:
                # Use default model
                opamp_model = self._opamp_models['tl072']
            
            # Calculate frequency-dependent coupling
            freq_factor = 1.0 + opamp_model['frequency_dependence'] * math.log10(frequency / 20000.0)
            
            return {
                'input': opamp_model['input_coupling'] * freq_factor,
                'output': opamp_model['output_coupling'] * freq_factor,
                'power': opamp_model['power_coupling'] * freq_factor,
                'ground': opamp_model['ground_coupling'] * freq_factor
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating op-amp coupling: {str(e)}")
            return {'input': 0.02, 'output': 0.03, 'power': 0.05, 'ground': 0.01}
    
    def _is_power_component(self, ref: str) -> bool:
        """Check if component is power supply related."""
        ref_upper = ref.upper()
        
        power_identifiers = ['REG', 'VCC', 'VDD', 'GND', 'PWR', 'PSU']
        
        for identifier in power_identifiers:
            if identifier in ref_upper:
                return True
        
        return False
    
    def _calculate_power_supply_coupling(self, component: Any, frequency: float) -> Dict[str, float]:
        """Calculate power supply coupling effects."""
        try:
            ref = component.GetReference().upper()
            
            # Determine power component type
            if 'REG' in ref:
                model = self._power_models['regulator']
            elif 'C' in ref and ('DEC' in ref or 'FILTER' in ref):
                model = self._power_models['filter_capacitor']
            else:
                model = self._power_models['power_trace']
            
            # Calculate frequency-dependent coupling
            freq_factor = 1.0 + 0.1 * math.log10(frequency / 20000.0)
            
            return {
                'dc': model['dc_coupling'],
                'ac': model['ac_coupling'] * freq_factor,
                'noise': model['noise_coupling'] * freq_factor,
                'ripple': model['ripple_coupling'] * freq_factor
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating power supply coupling: {str(e)}")
            return {'dc': 0.05, 'ac': 0.1, 'noise': 0.02, 'ripple': 0.03}
    
    def _calculate_component_distance(self, comp1: Any, comp2: Any) -> float:
        """Calculate distance between two components."""
        try:
            pos1 = comp1.GetPosition()
            pos2 = comp2.GetPosition()
            
            dx = pos1.x - pos2.x
            dy = pos1.y - pos2.y
            
            return math.sqrt(dx*dx + dy*dy) / 1e6  # Convert to mm
            
        except Exception as e:
            self.logger.error(f"Error calculating component distance: {str(e)}")
            return float('inf')
    
    def _perform_direct_analysis(self, board: Any) -> AnalysisResult:
        """Perform direct high-frequency coupling analysis."""
        try:
            # Analyze at center frequency of the range
            center_freq = (self.config.frequency_range[0] + self.config.frequency_range[1]) / 2
            
            # Perform all analyses
            proximity_results = self.analyze_proximity_effects(board, center_freq)
            skin_effect_results = self.analyze_enhanced_skin_effects(board, center_freq)
            radiation_results = self.analyze_radiation_coupling(board, center_freq)
            opamp_results = self.analyze_opamp_coupling(board, center_freq)
            power_results = self.analyze_power_supply_coupling(board, center_freq)
            
            # Combine results
            combined_results = {
                'proximity_effects': proximity_results,
                'skin_effects': skin_effect_results,
                'radiation_coupling': radiation_results,
                'opamp_coupling': opamp_results,
                'power_supply_coupling': power_results,
                'analysis_frequency': center_freq
            }
            
            return AnalysisResult(
                success=True,
                analysis_type=AnalysisType.CUSTOM,
                message="High-frequency coupling analysis completed",
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