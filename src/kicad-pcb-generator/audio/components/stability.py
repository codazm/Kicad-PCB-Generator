"""Stability and filtering components for audio circuits."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

from ...core.base.base_manager import BaseManager
from ...core.base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from ...config.stability_config import StabilityConfig

if TYPE_CHECKING:
    from ...core.base.results.analysis_result import AnalysisResult

class FilterType(Enum):
    """Types of filters for audio circuits."""
    LOW_PASS = "low_pass"
    HIGH_PASS = "high_pass"
    BAND_PASS = "band_pass"
    NOTCH = "notch"
    EMI = "emi"

@dataclass
class FilterSpec:
    """Specification for a filter component."""
    type: FilterType
    cutoff_freq: float  # Hz
    order: int
    ripple: Optional[float] = None  # dB
    attenuation: Optional[float] = None  # dB

@dataclass
class StabilityComponent:
    """Stability and filtering component for audio circuits."""
    reference: str
    value: str
    type: str  # e.g., "ferrite", "capacitor", "inductor"
    filter_spec: Optional[FilterSpec] = None
    position: Optional[Dict[str, float]] = None
    properties: Optional[Dict[str, Any]] = None

class StabilityManager(BaseManager[StabilityComponent]):
    """Manages stability and filtering components for audio circuits."""
    
    def __init__(self, config: Optional[StabilityConfig] = None):
        """Initialize the stability manager.
        
        Args:
            config: Optional stability configuration
        """
        super().__init__()
        self.config = config or StabilityConfig()
        
    def add_ferrite_bead(self, reference: str, impedance: float, current_rating: float) -> StabilityComponent:
        """Add a ferrite bead for EMI suppression."""
        try:
            # Get configuration values
            ferrite_config = self.config.get_ferrite_config()
            if ferrite_config is None:
                # Use default values if configuration is not available
                dc_resistance = 0.1  # Typical value
                frequency_range = "1MHz-1GHz"
            else:
                dc_resistance = ferrite_config.dc_resistance
                frequency_range = ferrite_config.frequency_range
            
            component = StabilityComponent(
                reference=reference,
                value=f"{impedance}Ω @ 100MHz",
                type="ferrite",
                properties={
                    "impedance": impedance,
                    "current_rating": current_rating,
                    "dc_resistance": dc_resistance,
                    "frequency_range": frequency_range
                }
            )
            # Use BaseManager's create method
            result = self.create(reference, component)
            if result.success:
                return component
            else:
                raise ValueError(f"Failed to add ferrite bead: {result.message}")
                
        except (ValueError, KeyError, AttributeError) as e:
            raise ValueError(f"Error adding ferrite bead: {str(e)}")
    
    def add_emc_filter(self, reference: str, filter_spec: FilterSpec) -> StabilityComponent:
        """Add an EMC filter for noise suppression."""
        try:
            emc_config = self.config.get_emc_filter_config()
            if emc_config is None:
                insertion_loss = -40.0
                voltage_rating = 250.0
                current_rating = 1.0
                temperature_range = "-40°C to +85°C"
            else:
                insertion_loss = emc_config.default_insertion_loss
                voltage_rating = emc_config.default_voltage_rating
                current_rating = emc_config.default_current_rating
                temperature_range = emc_config.temperature_range
            component = StabilityComponent(
                reference=reference,
                value=f"EMC Filter {filter_spec.type.value}",
                type="emc_filter",
                filter_spec=filter_spec,
                properties={
                    "insertion_loss": insertion_loss,
                    "voltage_rating": voltage_rating,
                    "current_rating": current_rating,
                    "temperature_range": temperature_range
                }
            )
            result = self.create(reference, component)
            if result.success:
                return component
            else:
                raise ValueError(f"Failed to add EMC filter: {result.message}")
        except (ValueError, KeyError, AttributeError) as e:
            raise ValueError(f"Error adding EMC filter: {str(e)}")
    
    def add_power_filter(self, reference: str, capacitance: float, voltage_rating: float) -> StabilityComponent:
        """Add a power supply filter capacitor."""
        try:
            power_config = self.config.get_power_filter_config()
            if power_config is None:
                cutoff_freq = 1e3
                order = 1
                esr = 0.01
                temp_coeff = "X7R"
            else:
                cutoff_freq = power_config.default_cutoff_freq
                order = power_config.default_order
                esr = power_config.default_esr
                temp_coeff = power_config.temperature_coefficient
            component = StabilityComponent(
                reference=reference,
                value=f"{capacitance}µF",
                type="capacitor",
                filter_spec=FilterSpec(
                    type=FilterType.LOW_PASS,
                    cutoff_freq=cutoff_freq,
                    order=order
                ),
                properties={
                    "capacitance": capacitance,
                    "voltage_rating": voltage_rating,
                    "esr": esr,
                    "temperature_coefficient": temp_coeff
                }
            )
            result = self.create(reference, component)
            if result.success:
                return component
            else:
                raise ValueError(f"Failed to add power filter: {result.message}")
        except (ValueError, KeyError, AttributeError) as e:
            raise ValueError(f"Error adding power filter: {str(e)}")
    
    def add_audio_filter(self, reference: str, filter_spec: FilterSpec) -> StabilityComponent:
        """Add an audio-specific filter."""
        try:
            audio_config = self.config.get_audio_filter_config()
            if audio_config is None:
                insertion_loss = -0.1
                impedance = 600.0
                distortion = 0.001
                temperature_range = "-40°C to +85°C"
            else:
                insertion_loss = audio_config.default_insertion_loss
                impedance = audio_config.default_impedance
                distortion = audio_config.default_distortion
                temperature_range = audio_config.temperature_range
            component = StabilityComponent(
                reference=reference,
                value=f"Audio Filter {filter_spec.type.value}",
                type="audio_filter",
                filter_spec=filter_spec,
                properties={
                    "insertion_loss": insertion_loss,
                    "impedance": impedance,
                    "distortion": distortion,
                    "temperature_range": temperature_range
                }
            )
            result = self.create(reference, component)
            if result.success:
                return component
            else:
                raise ValueError(f"Failed to add audio filter: {result.message}")
        except (ValueError, KeyError, AttributeError) as e:
            raise ValueError(f"Error adding audio filter: {str(e)}")
    
    def get_components(self) -> List[StabilityComponent]:
        """Get all stability and filtering components."""
        result = self.list_all()
        if result.success and result.data:
            return list(result.data.values())
        return []
    
    def get_component_by_reference(self, reference: str) -> Optional[StabilityComponent]:
        """Get a component by its reference."""
        result = self.read(reference)
        if result.success:
            return result.data
        return None
    
    def get_components_by_type(self, type: str) -> List[StabilityComponent]:
        """Get all components of a specific type."""
        components = self.get_components()
        return [c for c in components if c.type == type]
    
    def get_components_by_filter_type(self, filter_type: FilterType) -> List[StabilityComponent]:
        """Get all components with a specific filter type."""
        components = self.get_components()
        return [c for c in components if c.filter_spec and c.filter_spec.type == filter_type]
    
    def _validate_data(self, data: StabilityComponent) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.reference:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Component reference is required",
                    errors=["Component reference cannot be empty"]
                )
            
            if not data.value:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Component value is required",
                    errors=["Component value cannot be empty"]
                )
            
            if not data.type:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Component type is required",
                    errors=["Component type cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Stability component validation successful"
            )
        except (ValueError, KeyError, AttributeError) as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Stability component validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a stability component.
        
        Args:
            key: Component reference to clean up
        """
        # No specific cleanup currently required; kept for extensibility.
        self.logger.debug("StabilityManager cleanup called for component '%s'", key)
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache - no additional operations needed
        super()._clear_cache() 
