"""
Enhanced Capacitive Coupling Analysis for Audio PCB Design.

This module provides advanced capacitive coupling calculations with component-specific
models and frequency-dependent analysis for professional audio applications.
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

class CapacitorType(Enum):
    """Capacitor types for coupling analysis."""
    DECOUPLING = "decoupling"
    COUPLING = "coupling"
    FILTER = "filter"
    AUDIO = "audio"
    HIGH_FREQUENCY = "high_frequency"
    PCB_TRACE = "pcb_trace"

@dataclass
class CapacitanceModel:
    """Data structure for capacitance model parameters."""
    capacitor_type: CapacitorType
    self_capacitance: float  # F
    parasitic_capacitance: Dict[str, float]  # Component ID -> parasitic capacitance (F)
    frequency_dependence: Dict[float, float]  # Frequency -> capacitance factor
    geometry_params: Dict[str, float]  # Geometry-specific parameters
    temperature_coefficient: float = 0.0  # ppm/°C

@dataclass
class CapacitiveCouplingConfigItem:
    """Configuration for capacitive coupling analysis."""
    # Analysis parameters
    frequency_range: Tuple[float, float] = field(default=(20.0, 80000.0))  # 20Hz to 80kHz
    frequency_points: int = 100
    temperature: float = 25.0  # °C
    
    # Component-specific parameters
    capacitor_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    trace_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    audio_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Analysis thresholds
    min_capacitance: float = 1e-15  # 1fF
    max_capacitance: float = 1e-6   # 1μF
    coupling_threshold: float = 0.1  # 10% coupling
    
    # Audio-specific parameters
    audio_frequency_bands: List[Tuple[float, float]] = field(default_factory=lambda: [
        (20.0, 200.0),    # Low frequency
        (200.0, 2000.0),  # Mid frequency  
        (2000.0, 20000.0), # High frequency
        (20000.0, 80000.0) # Extended frequency
    ])

@dataclass
class CapacitiveCouplingAnalysisItem:
    """Analysis item for capacitive coupling calculations."""
    id: str
    analysis_type: AnalysisType
    board: Any  # pcbnew.BOARD
    config: CapacitiveCouplingConfigItem
    component_models: Dict[str, CapacitanceModel] = field(default_factory=dict)

class CapacitiveCouplingAnalyzer(BaseAnalyzer[CapacitiveCouplingAnalysisItem]):
    """Enhanced capacitive coupling analyzer for audio PCB design."""
    
    def __init__(self, config: Optional[CapacitiveCouplingConfigItem] = None):
        """Initialize the capacitive coupling analyzer.
        
        Args:
            config: Configuration for capacitive coupling analysis
        """
        super().__init__()
        self.config = config or CapacitiveCouplingConfigItem()
        self.logger = logging.getLogger(__name__)
        
        # Component-specific capacitance models
        self._capacitor_models = self._initialize_capacitor_models()
        self._trace_models = self._initialize_trace_models()
        self._audio_models = self._initialize_audio_models()
    
    def analyze_capacitive_coupling(self, board: Any) -> AnalysisResult:
        """Analyze capacitive coupling for all components on the board.
        
        Args:
            board: KiCad board object
            
        Returns:
            AnalysisResult with capacitive coupling data
        """
        try:
            # Create analysis item
            analysis_item = CapacitiveCouplingAnalysisItem(
                id="capacitive_coupling_analysis",
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
            self.logger.error(f"Error in capacitive coupling analysis: {str(e)}")
            return AnalysisResult(
                success=False,
                analysis_type=AnalysisType.CUSTOM,
                message=f"Capacitive coupling analysis failed: {str(e)}",
                severity=AnalysisSeverity.ERROR,
                errors=[str(e)]
            )
    
    def calculate_component_capacitance(self, component: Any, frequency: float) -> CapacitanceModel:
        """Calculate capacitance model for a specific component.
        
        Args:
            component: KiCad component object
            frequency: Analysis frequency in Hz
            
        Returns:
            CapacitanceModel with calculated parameters
        """
        try:
            ref = component.GetReference()
            value = component.GetValue()
            footprint = component.GetFPID().GetLibItemName()
            
            # Determine component type
            component_type = self._determine_component_type(ref, value, footprint)
            
            # Get base capacitance
            base_capacitance = self._calculate_base_capacitance(component, component_type)
            
            # Calculate frequency dependence
            frequency_factor = self._calculate_frequency_factor(frequency, component_type)
            
            # Calculate self capacitance
            self_capacitance = base_capacitance * frequency_factor
            
            # Calculate parasitic capacitance with nearby components
            parasitic_capacitance = self._calculate_parasitic_capacitance(component, frequency)
            
            # Get geometry parameters
            geometry_params = self._extract_geometry_params(component)
            
            # Create capacitance model
            model = CapacitanceModel(
                capacitor_type=component_type,
                self_capacitance=self_capacitance,
                parasitic_capacitance=parasitic_capacitance,
                frequency_dependence={frequency: frequency_factor},
                geometry_params=geometry_params
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error calculating component capacitance: {str(e)}")
            return CapacitanceModel(
                capacitor_type=CapacitorType.AUDIO,
                self_capacitance=0.0,
                parasitic_capacitance={},
                frequency_dependence={},
                geometry_params={}
            )
    
    def analyze_audio_frequency_bands(self, board: Any) -> Dict[str, Dict[str, float]]:
        """Analyze capacitive coupling across audio frequency bands.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary with frequency band analysis results
        """
        try:
            results = {}
            
            for band_name, (f_min, f_max) in enumerate(self.config.audio_frequency_bands):
                band_key = f"band_{band_name+1}_{f_min:.0f}Hz_{f_max:.0f}Hz"
                results[band_key] = {}
                
                # Analyze at center frequency of each band
                center_freq = math.sqrt(f_min * f_max)
                
                # Get all components
                components = board.GetFootprints()
                
                for component in components:
                    ref = component.GetReference()
                    
                    # Calculate capacitance at center frequency
                    capacitance_model = self.calculate_component_capacitance(component, center_freq)
                    
                    results[band_key][ref] = {
                        'self_capacitance': capacitance_model.self_capacitance,
                        'total_parasitic_capacitance': sum(capacitance_model.parasitic_capacitance.values()),
                        'coupling_factor': self._calculate_coupling_factor(capacitance_model)
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing audio frequency bands: {str(e)}")
            return {}
    
    def analyze_high_frequency_effects(self, board: Any) -> Dict[str, float]:
        """Analyze high-frequency capacitive effects for audio applications.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary with high-frequency analysis results
        """
        try:
            results = {}
            
            # Analyze at high frequencies (20kHz-80kHz)
            high_freqs = [20000.0, 40000.0, 60000.0, 80000.0]
            
            for freq in high_freqs:
                freq_key = f"{freq/1000:.0f}kHz"
                results[freq_key] = {}
                
                components = board.GetFootprints()
                
                for component in components:
                    ref = component.GetReference()
                    capacitance_model = self.calculate_component_capacitance(component, freq)
                    
                    # Calculate high-frequency effects
                    skin_effect = self._calculate_skin_effect(freq, component)
                    proximity_effect = self._calculate_proximity_effect(freq, component)
                    dielectric_loss = self._calculate_dielectric_loss(freq, component)
                    
                    results[freq_key][ref] = {
                        'effective_capacitance': capacitance_model.self_capacitance,
                        'skin_effect_factor': skin_effect,
                        'proximity_effect_factor': proximity_effect,
                        'dielectric_loss_factor': dielectric_loss
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing high-frequency effects: {str(e)}")
            return {}
    
    def _initialize_capacitor_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize capacitor-specific capacitance models."""
        return {
            'ceramic': {
                'base_capacitance_factor': 1.0,
                'frequency_dependence': 0.05,
                'temperature_coefficient': 50.0,
                'parasitic_factor': 0.01
            },
            'electrolytic': {
                'base_capacitance_factor': 1.2,
                'frequency_dependence': 0.1,
                'temperature_coefficient': 100.0,
                'parasitic_factor': 0.02
            },
            'film': {
                'base_capacitance_factor': 0.9,
                'frequency_dependence': 0.02,
                'temperature_coefficient': 30.0,
                'parasitic_factor': 0.005
            },
            'audio': {
                'base_capacitance_factor': 0.8,
                'frequency_dependence': 0.01,
                'temperature_coefficient': 20.0,
                'parasitic_factor': 0.003
            }
        }
    
    def _initialize_trace_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize PCB trace capacitance models."""
        return {
            'microstrip': {
                'capacitance_per_mm': 0.1e-12,  # 0.1pF/mm
                'frequency_dependence': 0.1,
                'substrate_factor': 4.5  # FR4 dielectric constant
            },
            'stripline': {
                'capacitance_per_mm': 0.15e-12,  # 0.15pF/mm
                'frequency_dependence': 0.08,
                'substrate_factor': 4.5
            },
            'coplanar': {
                'capacitance_per_mm': 0.08e-12,  # 0.08pF/mm
                'frequency_dependence': 0.12,
                'substrate_factor': 4.5
            }
        }
    
    def _initialize_audio_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize audio-specific capacitance models."""
        return {
            'audio_coupling': {
                'base_capacitance_factor': 0.7,
                'frequency_dependence': 0.005,
                'temperature_coefficient': 15.0,
                'parasitic_factor': 0.002
            },
            'audio_filter': {
                'base_capacitance_factor': 0.8,
                'frequency_dependence': 0.01,
                'temperature_coefficient': 25.0,
                'parasitic_factor': 0.004
            },
            'audio_decoupling': {
                'base_capacitance_factor': 1.0,
                'frequency_dependence': 0.02,
                'temperature_coefficient': 40.0,
                'parasitic_factor': 0.008
            }
        }
    
    def _determine_component_type(self, ref: str, value: str, footprint: str) -> CapacitorType:
        """Determine component type based on reference, value, and footprint."""
        ref_upper = ref.upper()
        value_upper = value.upper()
        footprint_lower = footprint.lower()
        
        if ref_upper.startswith('C'):
            if 'DEC' in ref_upper or 'DECOUPLING' in footprint_lower:
                return CapacitorType.DECOUPLING
            elif 'COUP' in ref_upper or 'COUPLING' in footprint_lower:
                return CapacitorType.COUPLING
            elif 'FILTER' in footprint_lower or 'FILTER' in value_upper:
                return CapacitorType.FILTER
            elif 'AUDIO' in footprint_lower or 'AUDIO' in value_upper:
                return CapacitorType.AUDIO
            elif 'HF' in value_upper or 'HIGH_FREQ' in footprint_lower:
                return CapacitorType.HIGH_FREQUENCY
            else:
                return CapacitorType.AUDIO  # Default for audio applications
        else:
            return CapacitorType.PCB_TRACE
    
    def _calculate_base_capacitance(self, component: Any, component_type: CapacitorType) -> float:
        """Calculate base capacitance for a component."""
        try:
            if component_type in [CapacitorType.DECOUPLING, CapacitorType.COUPLING, 
                                CapacitorType.FILTER, CapacitorType.AUDIO, CapacitorType.HIGH_FREQUENCY]:
                return self._calculate_capacitor_capacitance(component)
            elif component_type == CapacitorType.PCB_TRACE:
                return self._calculate_trace_capacitance(component)
            else:
                return 1e-12  # Default 1pF
                
        except Exception as e:
            self.logger.error(f"Error calculating base capacitance: {str(e)}")
            return 1e-12
    
    def _calculate_capacitor_capacitance(self, component: Any) -> float:
        """Calculate capacitance for capacitor components."""
        try:
            value = component.GetValue()
            
            # Parse capacitance value
            if 'F' in value.upper():
                # Extract numeric value and convert to base units
                numeric_part = ''.join(c for c in value if c.isdigit() or c == '.')
                if numeric_part:
                    capacitance = float(numeric_part)
                    
                    # Apply unit conversion
                    if 'MF' in value.upper() or 'MFD' in value.upper():
                        capacitance *= 1e-3
                    elif 'UF' in value.upper() or 'MFD' in value.upper():
                        capacitance *= 1e-6
                    elif 'NF' in value.upper():
                        capacitance *= 1e-9
                    elif 'PF' in value.upper():
                        capacitance *= 1e-12
                    
                    return capacitance
            
            # Fallback to geometric calculation
            return self._calculate_geometric_capacitance(component)
            
        except Exception as e:
            self.logger.error(f"Error calculating capacitor capacitance: {str(e)}")
            return 1e-9  # Default 1nF
    
    def _calculate_trace_capacitance(self, component: Any) -> float:
        """Calculate capacitance for PCB trace components."""
        try:
            # Get trace properties
            tracks = component.GetTracks()
            total_length = 0.0
            
            for track in tracks:
                if track.GetType() == 0:  # PCB_TRACE_T
                    total_length += track.GetLength() / 1e6  # Convert to mm
            
            # Use microstrip model
            capacitance_per_mm = self._trace_models['microstrip']['capacitance_per_mm']
            return capacitance_per_mm * total_length
            
        except Exception as e:
            self.logger.error(f"Error calculating trace capacitance: {str(e)}")
            return 1e-12
    
    def _calculate_geometric_capacitance(self, component: Any) -> float:
        """Calculate capacitance based on component geometry."""
        try:
            # Get component bounding box
            bbox = component.GetBoundingBox()
            width = bbox.GetWidth() / 1e6  # Convert to mm
            height = bbox.GetHeight() / 1e6  # Convert to mm
            
            # Simplified capacitance calculation based on area
            area = width * height
            return 1e-12 * area  # 1pF per mm²
            
        except Exception as e:
            self.logger.error(f"Error calculating geometric capacitance: {str(e)}")
            return 1e-12
    
    def _calculate_frequency_factor(self, frequency: float, component_type: CapacitorType) -> float:
        """Calculate frequency-dependent factor for capacitance."""
        try:
            if component_type == CapacitorType.HIGH_FREQUENCY:
                # High-frequency capacitors have frequency-dependent behavior
                return 1.0 + 0.05 * math.log10(frequency / 1000.0)
            elif component_type == CapacitorType.AUDIO:
                # Audio capacitors have minimal frequency dependence
                return 1.0 + 0.01 * math.log10(frequency / 1000.0)
            elif component_type == CapacitorType.PCB_TRACE:
                # PCB traces have frequency-dependent effects
                return 1.0 + 0.1 * math.log10(frequency / 1000.0)
            else:
                return 1.0
                
        except Exception as e:
            self.logger.error(f"Error calculating frequency factor: {str(e)}")
            return 1.0
    
    def _calculate_parasitic_capacitance(self, component: Any, frequency: float) -> Dict[str, float]:
        """Calculate parasitic capacitance with nearby components."""
        try:
            parasitic_capacitances = {}
            
            # Get all other components
            all_components = component.GetBoard().GetFootprints()
            
            for other_component in all_components:
                if other_component == component:
                    continue
                
                # Calculate distance between components
                distance = self._calculate_component_distance(component, other_component)
                
                # Only consider nearby components (within 5mm)
                if distance < 5.0:
                    # Calculate parasitic capacitance using simplified formula
                    # C_parasitic = ε₀ * εᵣ * A / d
                    area = self._calculate_coupling_area(component, other_component)
                    
                    # Effective dielectric constant (air + substrate)
                    epsilon_eff = 2.5  # Simplified value
                    
                    # Parasitic capacitance
                    parasitic_capacitance = 8.85e-12 * epsilon_eff * area / (distance * 1e-3)
                    parasitic_capacitances[other_component.GetReference()] = parasitic_capacitance
            
            return parasitic_capacitances
            
        except Exception as e:
            self.logger.error(f"Error calculating parasitic capacitance: {str(e)}")
            return {}
    
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
    
    def _calculate_coupling_area(self, comp1: Any, comp2: Any) -> float:
        """Calculate coupling area between two components."""
        try:
            bbox1 = comp1.GetBoundingBox()
            bbox2 = comp2.GetBoundingBox()
            
            # Simplified coupling area calculation
            area1 = (bbox1.GetWidth() * bbox1.GetHeight()) / 1e12  # m²
            area2 = (bbox2.GetWidth() * bbox2.GetHeight()) / 1e12  # m²
            
            # Use smaller area as coupling area
            return min(area1, area2)
            
        except Exception as e:
            self.logger.error(f"Error calculating coupling area: {str(e)}")
            return 1e-6  # Default 1mm²
    
    def _extract_geometry_params(self, component: Any) -> Dict[str, float]:
        """Extract geometry parameters from component."""
        try:
            bbox = component.GetBoundingBox()
            
            return {
                'width': bbox.GetWidth() / 1e6,  # mm
                'height': bbox.GetHeight() / 1e6,  # mm
                'area': (bbox.GetWidth() * bbox.GetHeight()) / 1e12,  # m²
                'x': component.GetPosition().x / 1e6,  # mm
                'y': component.GetPosition().y / 1e6   # mm
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting geometry parameters: {str(e)}")
            return {}
    
    def _calculate_coupling_factor(self, capacitance_model: CapacitanceModel) -> float:
        """Calculate coupling factor for a capacitance model."""
        try:
            if capacitance_model.self_capacitance == 0:
                return 0.0
            
            total_parasitic = sum(capacitance_model.parasitic_capacitance.values())
            return total_parasitic / capacitance_model.self_capacitance
            
        except Exception as e:
            self.logger.error(f"Error calculating coupling factor: {str(e)}")
            return 0.0
    
    def _calculate_skin_effect(self, frequency: float, component: Any) -> float:
        """Calculate skin effect factor for high-frequency analysis."""
        try:
            # Simplified skin effect calculation
            # Skin depth = sqrt(ρ / (π * μ * f))
            # For copper: ρ = 1.68e-8 Ω·m, μ = 4πe-7 H/m
            rho = 1.68e-8  # Copper resistivity
            mu = 4 * math.pi * 1e-7  # Permeability of free space
            
            skin_depth = math.sqrt(rho / (math.pi * mu * frequency))
            
            # Get component size
            bbox = component.GetBoundingBox()
            width = bbox.GetWidth() / 1e6  # mm
            
            # Skin effect factor (simplified)
            return min(1.0, skin_depth / (width * 1e-3))
            
        except Exception as e:
            self.logger.error(f"Error calculating skin effect: {str(e)}")
            return 1.0
    
    def _calculate_proximity_effect(self, frequency: float, component: Any) -> float:
        """Calculate proximity effect factor for high-frequency analysis."""
        try:
            # Simplified proximity effect calculation
            # Proximity effect increases with frequency
            return 1.0 + 0.1 * math.log10(frequency / 1000.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating proximity effect: {str(e)}")
            return 1.0
    
    def _calculate_dielectric_loss(self, frequency: float, component: Any) -> float:
        """Calculate dielectric loss factor for high-frequency analysis."""
        try:
            # Simplified dielectric loss calculation
            # Dielectric loss increases with frequency
            return 1.0 + 0.05 * math.log10(frequency / 1000.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating dielectric loss: {str(e)}")
            return 1.0
    
    def _perform_direct_analysis(self, board: Any) -> AnalysisResult:
        """Perform direct capacitive coupling analysis."""
        try:
            components = board.GetFootprints()
            capacitance_data = {}
            
            for component in components:
                ref = component.GetReference()
                capacitance_model = self.calculate_component_capacitance(component, 1000.0)  # 1kHz
                capacitance_data[ref] = {
                    'self_capacitance': capacitance_model.self_capacitance,
                    'parasitic_capacitance': capacitance_model.parasitic_capacitance,
                    'coupling_factor': self._calculate_coupling_factor(capacitance_model)
                }
            
            return AnalysisResult(
                success=True,
                analysis_type=AnalysisType.CUSTOM,
                message="Capacitive coupling analysis completed",
                severity=AnalysisSeverity.INFO,
                data=capacitance_data
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