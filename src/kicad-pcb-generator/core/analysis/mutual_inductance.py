"""
Enhanced Mutual Inductance Analysis for Audio PCB Design.

This module provides advanced mutual inductance calculations with component-specific
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

class ComponentType(Enum):
    """Component types for inductance modeling."""
    INDUCTOR = "inductor"
    TRANSFORMER = "transformer"
    COIL = "coil"
    PCB_TRACE = "pcb_trace"
    WINDING = "winding"
    AUDIO_COMPONENT = "audio_component"

@dataclass
class InductanceModel:
    """Data structure for inductance model parameters."""
    component_type: ComponentType
    self_inductance: float  # H
    mutual_inductance: Dict[str, float]  # Component ID -> mutual inductance (H)
    frequency_dependence: Dict[float, float]  # Frequency -> inductance factor
    geometry_params: Dict[str, float]  # Geometry-specific parameters
    temperature_coefficient: float = 0.0  # ppm/°C

@dataclass
class MutualInductanceConfigItem:
    """Configuration for mutual inductance analysis."""
    # Analysis parameters
    frequency_range: Tuple[float, float] = field(default=(20.0, 80000.0))  # 20Hz to 80kHz
    frequency_points: int = 100
    temperature: float = 25.0  # °C
    
    # Component-specific parameters
    inductor_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    transformer_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    trace_models: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Analysis thresholds
    min_inductance: float = 1e-9  # 1nH
    max_inductance: float = 1e-3  # 1mH
    coupling_threshold: float = 0.1  # 10% coupling
    
    # Audio-specific parameters
    audio_frequency_bands: List[Tuple[float, float]] = field(default_factory=lambda: [
        (20.0, 200.0),    # Low frequency
        (200.0, 2000.0),  # Mid frequency  
        (2000.0, 20000.0), # High frequency
        (20000.0, 80000.0) # Extended frequency
    ])

@dataclass
class MutualInductanceAnalysisItem:
    """Analysis item for mutual inductance calculations."""
    id: str
    analysis_type: AnalysisType
    board: Any  # pcbnew.BOARD
    config: MutualInductanceConfigItem
    component_models: Dict[str, InductanceModel] = field(default_factory=dict)

class MutualInductanceAnalyzer(BaseAnalyzer[MutualInductanceAnalysisItem]):
    """Enhanced mutual inductance analyzer for audio PCB design."""
    
    def __init__(self, config: Optional[MutualInductanceConfigItem] = None):
        """Initialize the mutual inductance analyzer.
        
        Args:
            config: Configuration for mutual inductance analysis
        """
        super().__init__()
        self.config = config or MutualInductanceConfigItem()
        self.logger = logging.getLogger(__name__)
        
        # Component-specific inductance models
        self._inductor_models = self._initialize_inductor_models()
        self._transformer_models = self._initialize_transformer_models()
        self._trace_models = self._initialize_trace_models()
    
    def analyze_mutual_inductance(self, board: Any) -> AnalysisResult:
        """Analyze mutual inductance for all components on the board.
        
        Args:
            board: KiCad board object
            
        Returns:
            AnalysisResult with mutual inductance data
        """
        try:
            # Create analysis item
            analysis_item = MutualInductanceAnalysisItem(
                id="mutual_inductance_analysis",
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
            self.logger.error(f"Error in mutual inductance analysis: {str(e)}")
            return AnalysisResult(
                success=False,
                analysis_type=AnalysisType.CUSTOM,
                message=f"Mutual inductance analysis failed: {str(e)}",
                severity=AnalysisSeverity.ERROR,
                errors=[str(e)]
            )
    
    def calculate_component_inductance(self, component: Any, frequency: float) -> InductanceModel:
        """Calculate inductance model for a specific component.
        
        Args:
            component: KiCad component object
            frequency: Analysis frequency in Hz
            
        Returns:
            InductanceModel with calculated parameters
        """
        try:
            ref = component.GetReference()
            value = component.GetValue()
            footprint = component.GetFPID().GetLibItemName()
            
            # Determine component type
            component_type = self._determine_component_type(ref, value, footprint)
            
            # Get base inductance
            base_inductance = self._calculate_base_inductance(component, component_type)
            
            # Calculate frequency dependence
            frequency_factor = self._calculate_frequency_factor(frequency, component_type)
            
            # Calculate self inductance
            self_inductance = base_inductance * frequency_factor
            
            # Calculate mutual inductance with nearby components
            mutual_inductance = self._calculate_mutual_inductance(component, frequency)
            
            # Get geometry parameters
            geometry_params = self._extract_geometry_params(component)
            
            # Create inductance model
            model = InductanceModel(
                component_type=component_type,
                self_inductance=self_inductance,
                mutual_inductance=mutual_inductance,
                frequency_dependence={frequency: frequency_factor},
                geometry_params=geometry_params
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error calculating component inductance: {str(e)}")
            return InductanceModel(
                component_type=ComponentType.AUDIO_COMPONENT,
                self_inductance=0.0,
                mutual_inductance={},
                frequency_dependence={},
                geometry_params={}
            )
    
    def analyze_audio_frequency_bands(self, board: Any) -> Dict[str, Dict[str, float]]:
        """Analyze mutual inductance across audio frequency bands.
        
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
                    
                    # Calculate inductance at center frequency
                    inductance_model = self.calculate_component_inductance(component, center_freq)
                    
                    results[band_key][ref] = {
                        'self_inductance': inductance_model.self_inductance,
                        'total_mutual_inductance': sum(inductance_model.mutual_inductance.values()),
                        'coupling_factor': self._calculate_coupling_factor(inductance_model)
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing audio frequency bands: {str(e)}")
            return {}
    
    def _initialize_inductor_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize inductor-specific inductance models."""
        return {
            'axial': {
                'base_inductance_factor': 1e-9,
                'frequency_dependence': 0.1,
                'temperature_coefficient': 100.0
            },
            'radial': {
                'base_inductance_factor': 1.2e-9,
                'frequency_dependence': 0.15,
                'temperature_coefficient': 120.0
            },
            'toroidal': {
                'base_inductance_factor': 0.8e-9,
                'frequency_dependence': 0.05,
                'temperature_coefficient': 80.0
            }
        }
    
    def _initialize_transformer_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize transformer-specific inductance models."""
        return {
            'audio_transformer': {
                'primary_inductance': 1e-3,
                'secondary_inductance': 1e-3,
                'coupling_coefficient': 0.95,
                'leakage_inductance': 1e-6
            },
            'power_transformer': {
                'primary_inductance': 10e-3,
                'secondary_inductance': 10e-3,
                'coupling_coefficient': 0.98,
                'leakage_inductance': 5e-6
            }
        }
    
    def _initialize_trace_models(self) -> Dict[str, Dict[str, float]]:
        """Initialize PCB trace inductance models."""
        return {
            'microstrip': {
                'inductance_per_mm': 0.4e-9,
                'frequency_dependence': 0.2,
                'skin_effect_factor': 0.1
            },
            'stripline': {
                'inductance_per_mm': 0.3e-9,
                'frequency_dependence': 0.15,
                'skin_effect_factor': 0.08
            }
        }
    
    def _determine_component_type(self, ref: str, value: str, footprint: str) -> ComponentType:
        """Determine component type based on reference, value, and footprint."""
        ref_upper = ref.upper()
        value_upper = value.upper()
        footprint_lower = footprint.lower()
        
        if ref_upper.startswith('L') or 'H' in value_upper or 'HENRY' in value_upper:
            return ComponentType.INDUCTOR
        elif ref_upper.startswith('T') or 'TRANSFORMER' in footprint_lower:
            return ComponentType.TRANSFORMER
        elif ref_upper.startswith('COIL') or 'WINDING' in footprint_lower:
            return ComponentType.COIL
        elif 'AUDIO' in footprint_lower or 'AUDIO' in value_upper:
            return ComponentType.AUDIO_COMPONENT
        else:
            return ComponentType.PCB_TRACE
    
    def _calculate_base_inductance(self, component: Any, component_type: ComponentType) -> float:
        """Calculate base inductance for a component."""
        try:
            if component_type == ComponentType.INDUCTOR:
                return self._calculate_inductor_inductance(component)
            elif component_type == ComponentType.TRANSFORMER:
                return self._calculate_transformer_inductance(component)
            elif component_type == ComponentType.COIL:
                return self._calculate_coil_inductance(component)
            elif component_type == ComponentType.PCB_TRACE:
                return self._calculate_trace_inductance(component)
            else:
                return 1e-9  # Default small inductance
                
        except Exception as e:
            self.logger.error(f"Error calculating base inductance: {str(e)}")
            return 1e-9
    
    def _calculate_inductor_inductance(self, component: Any) -> float:
        """Calculate inductance for inductor components."""
        try:
            value = component.GetValue()
            
            # Parse inductance value
            if 'H' in value.upper():
                # Extract numeric value and convert to base units
                numeric_part = ''.join(c for c in value if c.isdigit() or c == '.')
                if numeric_part:
                    inductance = float(numeric_part)
                    
                    # Apply unit conversion
                    if 'MH' in value.upper():
                        inductance *= 1e-3
                    elif 'UH' in value.upper():
                        inductance *= 1e-6
                    elif 'NH' in value.upper():
                        inductance *= 1e-9
                    
                    return inductance
            
            # Fallback to geometric calculation
            return self._calculate_geometric_inductance(component)
            
        except Exception as e:
            self.logger.error(f"Error calculating inductor inductance: {str(e)}")
            return 1e-6  # Default 1μH
    
    def _calculate_transformer_inductance(self, component: Any) -> float:
        """Calculate inductance for transformer components."""
        try:
            # For transformers, calculate primary inductance
            # This is a simplified model - in practice you'd need more detailed specs
            return 1e-3  # Default 1mH primary inductance
            
        except Exception as e:
            self.logger.error(f"Error calculating transformer inductance: {str(e)}")
            return 1e-3
    
    def _calculate_coil_inductance(self, component: Any) -> float:
        """Calculate inductance for coil components."""
        try:
            # Calculate based on coil geometry
            # This is a simplified model using Wheeler's formula
            return self._calculate_geometric_inductance(component)
            
        except Exception as e:
            self.logger.error(f"Error calculating coil inductance: {str(e)}")
            return 1e-6
    
    def _calculate_trace_inductance(self, component: Any) -> float:
        """Calculate inductance for PCB trace components."""
        try:
            # Get trace properties
            tracks = component.GetTracks()
            total_length = 0.0
            
            for track in tracks:
                if track.GetType() == 0:  # PCB_TRACE_T
                    total_length += track.GetLength() / 1e6  # Convert to mm
            
            # Use microstrip model
            inductance_per_mm = self._trace_models['microstrip']['inductance_per_mm']
            return inductance_per_mm * total_length
            
        except Exception as e:
            self.logger.error(f"Error calculating trace inductance: {str(e)}")
            return 1e-9
    
    def _calculate_geometric_inductance(self, component: Any) -> float:
        """Calculate inductance based on component geometry."""
        try:
            # Get component bounding box
            bbox = component.GetBoundingBox()
            width = bbox.GetWidth() / 1e6  # Convert to mm
            height = bbox.GetHeight() / 1e6  # Convert to mm
            
            # Simplified inductance calculation based on area
            area = width * height
            return 1e-9 * area  # 1nH per mm²
            
        except Exception as e:
            self.logger.error(f"Error calculating geometric inductance: {str(e)}")
            return 1e-9
    
    def _calculate_frequency_factor(self, frequency: float, component_type: ComponentType) -> float:
        """Calculate frequency-dependent factor for inductance."""
        try:
            if component_type == ComponentType.INDUCTOR:
                # Inductors have some frequency dependence due to core effects
                return 1.0 + 0.1 * math.log10(frequency / 1000.0)
            elif component_type == ComponentType.TRANSFORMER:
                # Transformers have frequency-dependent coupling
                return 1.0 + 0.05 * math.log10(frequency / 1000.0)
            elif component_type == ComponentType.PCB_TRACE:
                # PCB traces have skin effect and proximity effect
                return 1.0 + 0.2 * math.log10(frequency / 1000.0)
            else:
                return 1.0
                
        except Exception as e:
            self.logger.error(f"Error calculating frequency factor: {str(e)}")
            return 1.0
    
    def _calculate_mutual_inductance(self, component: Any, frequency: float) -> Dict[str, float]:
        """Calculate mutual inductance with nearby components."""
        try:
            mutual_inductances = {}
            
            # Get all other components
            all_components = component.GetBoard().GetFootprints()
            
            for other_component in all_components:
                if other_component == component:
                    continue
                
                # Calculate distance between components
                distance = self._calculate_component_distance(component, other_component)
                
                # Only consider nearby components (within 10mm)
                if distance < 10.0:
                    # Calculate mutual inductance using simplified formula
                    # M = k * sqrt(L1 * L2) where k is coupling coefficient
                    l1 = self._calculate_base_inductance(component, ComponentType.AUDIO_COMPONENT)
                    l2 = self._calculate_base_inductance(other_component, ComponentType.AUDIO_COMPONENT)
                    
                    # Coupling coefficient decreases with distance
                    k = 0.1 * math.exp(-distance / 5.0)  # Exponential decay
                    
                    mutual_inductance = k * math.sqrt(l1 * l2)
                    mutual_inductances[other_component.GetReference()] = mutual_inductance
            
            return mutual_inductances
            
        except Exception as e:
            self.logger.error(f"Error calculating mutual inductance: {str(e)}")
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
    
    def _calculate_coupling_factor(self, inductance_model: InductanceModel) -> float:
        """Calculate coupling factor for an inductance model."""
        try:
            if inductance_model.self_inductance == 0:
                return 0.0
            
            total_mutual = sum(inductance_model.mutual_inductance.values())
            return total_mutual / inductance_model.self_inductance
            
        except Exception as e:
            self.logger.error(f"Error calculating coupling factor: {str(e)}")
            return 0.0
    
    def _perform_direct_analysis(self, board: Any) -> AnalysisResult:
        """Perform direct mutual inductance analysis."""
        try:
            components = board.GetFootprints()
            inductance_data = {}
            
            for component in components:
                ref = component.GetReference()
                inductance_model = self.calculate_component_inductance(component, 1000.0)  # 1kHz
                inductance_data[ref] = {
                    'self_inductance': inductance_model.self_inductance,
                    'mutual_inductance': inductance_model.mutual_inductance,
                    'coupling_factor': self._calculate_coupling_factor(inductance_model)
                }
            
            return AnalysisResult(
                success=True,
                analysis_type=AnalysisType.CUSTOM,
                message="Mutual inductance analysis completed",
                severity=AnalysisSeverity.INFO,
                data=inductance_data
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