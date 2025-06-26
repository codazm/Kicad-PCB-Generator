"""
Unified Analysis Configuration Manager

This module provides comprehensive configuration management for all analysis parameters,
combining signal integrity, thermal, EMI, power distribution, audio performance, noise, frequency response, AI, and cost analysis.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.base.base_config import BaseConfig


@dataclass
class SignalIntegrityConfigItem:
    """Data structure for signal integrity analysis parameters."""
    min_track_width: float
    max_track_length: float
    max_track_angle: float
    min_clearance: float
    max_impedance_mismatch: float
    max_crosstalk: float
    max_reflection: float
    description: str


@dataclass
class ThermalConfigItem:
    """Data structure for thermal analysis parameters."""
    min_thermal_pad_size: float
    max_component_density_radius: float
    max_nearby_components: int
    thermal_pad_threshold: float
    high_density_threshold: float
    max_temperature_rise: float
    thermal_resistance_factor: float
    description: str


@dataclass
class EMIConfigItem:
    """Data structure for EMI analysis parameters."""
    max_parallel_length: float
    max_track_angle: float
    min_isolation_distance: float
    max_emission_level: float
    max_susceptibility: float
    shielding_effectiveness: float
    description: str


@dataclass
class PowerDistributionConfigItem:
    """Data structure for power distribution analysis parameters."""
    min_power_track_width: float
    max_voltage_drop: float
    min_power_plane_coverage: float
    max_current_density: float
    power_net_prefixes: List[str]
    high_current_threshold: float
    description: str


@dataclass
class AudioPerformanceConfigItem:
    """Data structure for audio performance analysis parameters."""
    min_snr: float
    max_noise_floor: float
    max_distortion: float
    min_bandwidth: float
    max_bandwidth: float
    max_phase_shift: float
    min_impedance: float
    max_impedance: float
    description: str


@dataclass
class NoiseAnalysisConfigItem:
    """Data structure for noise analysis parameters."""
    default_signal_level: float
    thermal_noise_factor: float
    crosstalk_threshold: float
    power_supply_noise_factor: float
    ground_noise_factor: float
    min_distance_threshold: float
    description: str


@dataclass
class FrequencyResponseConfigItem:
    """Data structure for frequency response analysis parameters."""
    min_frequency: float
    max_frequency: float
    frequency_step: float
    min_response_flatness: float
    max_phase_variation: float
    min_bandwidth_efficiency: float
    description: str


@dataclass
class AIAnalysisConfigItem:
    """Data structure for AI analysis parameters."""
    feature_weights: Dict[str, float]
    recommendation_threshold: float
    analysis_depth: int
    description: str


@dataclass
class CostAnalysisConfigItem:
    """Data structure for cost analysis parameters."""
    cost_threshold: float
    yield_impact_threshold: float
    sensitive_area_radius: float
    min_component_spacing: float
    description: str


@dataclass
class ValidationConfigItem:
    """Data structure for validation settings."""
    check_signal_integrity: bool
    check_thermal: bool
    check_emi: bool
    check_power_distribution: bool
    check_audio_performance: bool
    check_noise: bool
    check_frequency_response: bool
    check_ai_analysis: bool
    check_cost_analysis: bool
    description: str


@dataclass
class ThresholdsConfigItem:
    """Data structure for analysis severity thresholds."""
    warning_severity: float
    error_severity: float
    info_severity: float
    critical_severity: float
    description: str


@dataclass
class UnitsConfigItem:
    """Data structure for analysis units."""
    distance: str
    angle: str
    temperature: str
    voltage: str
    current: str
    power: str
    frequency: str
    impedance: str
    cost: str
    description: str


@dataclass
class AnalysisManagerConfigItem:
    """Data structure for unified analysis manager configuration."""
    signal_integrity: SignalIntegrityConfigItem
    thermal: ThermalConfigItem
    emi: EMIConfigItem
    power_distribution: PowerDistributionConfigItem
    audio_performance: AudioPerformanceConfigItem
    noise_analysis: NoiseAnalysisConfigItem
    frequency_response: FrequencyResponseConfigItem
    ai_analysis: AIAnalysisConfigItem
    cost_analysis: CostAnalysisConfigItem
    validation: ValidationConfigItem
    thresholds: ThresholdsConfigItem
    units: UnitsConfigItem
    description: str


class AnalysisManagerConfig(BaseConfig[AnalysisManagerConfigItem]):
    """Unified configuration manager for all analysis parameters."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the unified analysis manager configuration.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "analysis_manager_config.json"
        
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
    
    def _validate_config(self, config_data: dict) -> bool:
        """Validate configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            True if configuration is valid
        """
        try:
            if "analysis_manager" not in config_data:
                self.logger.error("Missing 'analysis_manager' section in configuration")
                return False
            
            config = config_data["analysis_manager"]
            
            # Validate signal integrity
            if "signal_integrity" not in config:
                self.logger.error("Missing 'signal_integrity' section in analysis_manager")
                return False
            
            si = config["signal_integrity"]
            if si["min_track_width"] <= 0:
                self.logger.error("Minimum track width must be positive")
                return False
            
            if si["max_track_length"] <= 0:
                self.logger.error("Maximum track length must be positive")
                return False
            
            if si["max_track_angle"] <= 0 or si["max_track_angle"] > 90:
                self.logger.error("Maximum track angle must be between 0 and 90 degrees")
                return False
            
            if si["max_crosstalk"] < 0 or si["max_crosstalk"] > 1:
                self.logger.error("Maximum crosstalk must be between 0 and 1")
                return False
            
            # Validate thermal
            if "thermal" not in config:
                self.logger.error("Missing 'thermal' section in analysis_manager")
                return False
            
            thermal = config["thermal"]
            if thermal["min_thermal_pad_size"] <= 0:
                self.logger.error("Minimum thermal pad size must be positive")
                return False
            
            if thermal["max_component_density_radius"] <= 0:
                self.logger.error("Maximum component density radius must be positive")
                return False
            
            if thermal["max_nearby_components"] <= 0:
                self.logger.error("Maximum nearby components must be positive")
                return False
            
            # Validate EMI
            if "emi" not in config:
                self.logger.error("Missing 'emi' section in analysis_manager")
                return False
            
            emi = config["emi"]
            if emi["max_parallel_length"] <= 0:
                self.logger.error("Maximum parallel length must be positive")
                return False
            
            if emi["max_track_angle"] <= 0 or emi["max_track_angle"] > 90:
                self.logger.error("Maximum track angle must be between 0 and 90 degrees")
                return False
            
            if emi["min_isolation_distance"] <= 0:
                self.logger.error("Minimum isolation distance must be positive")
                return False
            
            # Validate power distribution
            if "power_distribution" not in config:
                self.logger.error("Missing 'power_distribution' section in analysis_manager")
                return False
            
            power = config["power_distribution"]
            if power["min_power_track_width"] <= 0:
                self.logger.error("Minimum power track width must be positive")
                return False
            
            if power["max_voltage_drop"] <= 0:
                self.logger.error("Maximum voltage drop must be positive")
                return False
            
            if power["min_power_plane_coverage"] < 0 or power["min_power_plane_coverage"] > 1:
                self.logger.error("Minimum power plane coverage must be between 0 and 1")
                return False
            
            if power["max_current_density"] <= 0:
                self.logger.error("Maximum current density must be positive")
                return False
            
            if not power["power_net_prefixes"]:
                self.logger.error("Power net prefixes cannot be empty")
                return False
            
            # Validate audio performance
            if "audio_performance" not in config:
                self.logger.error("Missing 'audio_performance' section in analysis_manager")
                return False
            
            audio = config["audio_performance"]
            if audio["min_snr"] <= 0:
                self.logger.error("Minimum SNR must be positive")
                return False
            
            if audio["max_noise_floor"] >= 0:
                self.logger.error("Maximum noise floor must be negative")
                return False
            
            if audio["max_distortion"] < 0 or audio["max_distortion"] > 1:
                self.logger.error("Maximum distortion must be between 0 and 1")
                return False
            
            if audio["min_bandwidth"] <= 0:
                self.logger.error("Minimum bandwidth must be positive")
                return False
            
            if audio["max_bandwidth"] <= audio["min_bandwidth"]:
                self.logger.error("Maximum bandwidth must be greater than minimum")
                return False
            
            # Validate noise analysis
            if "noise_analysis" not in config:
                self.logger.error("Missing 'noise_analysis' section in analysis_manager")
                return False
            
            noise = config["noise_analysis"]
            if noise["default_signal_level"] <= 0:
                self.logger.error("Default signal level must be positive")
                return False
            
            if noise["thermal_noise_factor"] <= 0:
                self.logger.error("Thermal noise factor must be positive")
                return False
            
            if noise["crosstalk_threshold"] <= 0:
                self.logger.error("Crosstalk threshold must be positive")
                return False
            
            if noise["min_distance_threshold"] <= 0:
                self.logger.error("Minimum distance threshold must be positive")
                return False
            
            # Validate frequency response
            if "frequency_response" not in config:
                self.logger.error("Missing 'frequency_response' section in analysis_manager")
                return False
            
            freq = config["frequency_response"]
            if freq["min_frequency"] <= 0:
                self.logger.error("Minimum frequency must be positive")
                return False
            
            if freq["max_frequency"] <= freq["min_frequency"]:
                self.logger.error("Maximum frequency must be greater than minimum")
                return False
            
            if freq["frequency_step"] <= 0:
                self.logger.error("Frequency step must be positive")
                return False
            
            if freq["min_response_flatness"] < 0 or freq["min_response_flatness"] > 1:
                self.logger.error("Minimum response flatness must be between 0 and 1")
                return False
            
            # Validate AI analysis
            if "ai_analysis" not in config:
                self.logger.error("Missing 'ai_analysis' section in analysis_manager")
                return False
            
            ai = config["ai_analysis"]
            if not ai["feature_weights"]:
                self.logger.error("Feature weights cannot be empty")
                return False
            
            if ai["recommendation_threshold"] < 0 or ai["recommendation_threshold"] > 1:
                self.logger.error("Recommendation threshold must be between 0 and 1")
                return False
            
            if ai["analysis_depth"] <= 0:
                self.logger.error("Analysis depth must be positive")
                return False
            
            # Validate cost analysis
            if "cost_analysis" not in config:
                self.logger.error("Missing 'cost_analysis' section in analysis_manager")
                return False
            
            cost = config["cost_analysis"]
            if cost["cost_threshold"] <= 0:
                self.logger.error("Cost threshold must be positive")
                return False
            
            if cost["yield_impact_threshold"] <= 0:
                self.logger.error("Yield impact threshold must be positive")
                return False
            
            if cost["sensitive_area_radius"] <= 0:
                self.logger.error("Sensitive area radius must be positive")
                return False
            
            if cost["min_component_spacing"] <= 0:
                self.logger.error("Minimum component spacing must be positive")
                return False
            
            # Validate validation settings
            if "validation" not in config:
                self.logger.error("Missing 'validation' section in analysis_manager")
                return False
            
            # Validate thresholds
            if "thresholds" not in config:
                self.logger.error("Missing 'thresholds' section in analysis_manager")
                return False
            
            thresholds = config["thresholds"]
            if thresholds["warning_severity"] < 0 or thresholds["warning_severity"] > 1:
                self.logger.error("Warning severity must be between 0 and 1")
                return False
            
            if thresholds["error_severity"] < 0 or thresholds["error_severity"] > 1:
                self.logger.error("Error severity must be between 0 and 1")
                return False
            
            if thresholds["info_severity"] < 0 or thresholds["info_severity"] > 1:
                self.logger.error("Info severity must be between 0 and 1")
                return False
            
            if thresholds["critical_severity"] < 0 or thresholds["critical_severity"] > 1:
                self.logger.error("Critical severity must be between 0 and 1")
                return False
            
            # Validate units
            if "units" not in config:
                self.logger.error("Missing 'units' section in analysis_manager")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating analysis manager configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: dict) -> AnalysisManagerConfigItem:
        """Parse configuration data into structured format.
        
        Args:
            config_data: Raw configuration data
            
        Returns:
            Parsed configuration item
        """
        try:
            config = config_data["analysis_manager"]
            
            # Parse signal integrity
            si_config = config["signal_integrity"]
            signal_integrity = SignalIntegrityConfigItem(
                min_track_width=si_config["min_track_width"],
                max_track_length=si_config["max_track_length"],
                max_track_angle=si_config["max_track_angle"],
                min_clearance=si_config["min_clearance"],
                max_impedance_mismatch=si_config["max_impedance_mismatch"],
                max_crosstalk=si_config["max_crosstalk"],
                max_reflection=si_config["max_reflection"],
                description=si_config["description"]
            )
            
            # Parse thermal
            thermal_config = config["thermal"]
            thermal = ThermalConfigItem(
                min_thermal_pad_size=thermal_config["min_thermal_pad_size"],
                max_component_density_radius=thermal_config["max_component_density_radius"],
                max_nearby_components=thermal_config["max_nearby_components"],
                thermal_pad_threshold=thermal_config["thermal_pad_threshold"],
                high_density_threshold=thermal_config["high_density_threshold"],
                max_temperature_rise=thermal_config["max_temperature_rise"],
                thermal_resistance_factor=thermal_config["thermal_resistance_factor"],
                description=thermal_config["description"]
            )
            
            # Parse EMI
            emi_config = config["emi"]
            emi = EMIConfigItem(
                max_parallel_length=emi_config["max_parallel_length"],
                max_track_angle=emi_config["max_track_angle"],
                min_isolation_distance=emi_config["min_isolation_distance"],
                max_emission_level=emi_config["max_emission_level"],
                max_susceptibility=emi_config["max_susceptibility"],
                shielding_effectiveness=emi_config["shielding_effectiveness"],
                description=emi_config["description"]
            )
            
            # Parse power distribution
            power_config = config["power_distribution"]
            power_distribution = PowerDistributionConfigItem(
                min_power_track_width=power_config["min_power_track_width"],
                max_voltage_drop=power_config["max_voltage_drop"],
                min_power_plane_coverage=power_config["min_power_plane_coverage"],
                max_current_density=power_config["max_current_density"],
                power_net_prefixes=power_config["power_net_prefixes"],
                high_current_threshold=power_config["high_current_threshold"],
                description=power_config["description"]
            )
            
            # Parse audio performance
            audio_config = config["audio_performance"]
            audio_performance = AudioPerformanceConfigItem(
                min_snr=audio_config["min_snr"],
                max_noise_floor=audio_config["max_noise_floor"],
                max_distortion=audio_config["max_distortion"],
                min_bandwidth=audio_config["min_bandwidth"],
                max_bandwidth=audio_config["max_bandwidth"],
                max_phase_shift=audio_config["max_phase_shift"],
                min_impedance=audio_config["min_impedance"],
                max_impedance=audio_config["max_impedance"],
                description=audio_config["description"]
            )
            
            # Parse noise analysis
            noise_config = config["noise_analysis"]
            noise_analysis = NoiseAnalysisConfigItem(
                default_signal_level=noise_config["default_signal_level"],
                thermal_noise_factor=noise_config["thermal_noise_factor"],
                crosstalk_threshold=noise_config["crosstalk_threshold"],
                power_supply_noise_factor=noise_config["power_supply_noise_factor"],
                ground_noise_factor=noise_config["ground_noise_factor"],
                min_distance_threshold=noise_config["min_distance_threshold"],
                description=noise_config["description"]
            )
            
            # Parse frequency response
            freq_config = config["frequency_response"]
            frequency_response = FrequencyResponseConfigItem(
                min_frequency=freq_config["min_frequency"],
                max_frequency=freq_config["max_frequency"],
                frequency_step=freq_config["frequency_step"],
                min_response_flatness=freq_config["min_response_flatness"],
                max_phase_variation=freq_config["max_phase_variation"],
                min_bandwidth_efficiency=freq_config["min_bandwidth_efficiency"],
                description=freq_config["description"]
            )
            
            # Parse AI analysis
            ai_config = config["ai_analysis"]
            ai_analysis = AIAnalysisConfigItem(
                feature_weights=ai_config["feature_weights"],
                recommendation_threshold=ai_config["recommendation_threshold"],
                analysis_depth=ai_config["analysis_depth"],
                description=ai_config["description"]
            )
            
            # Parse cost analysis
            cost_config = config["cost_analysis"]
            cost_analysis = CostAnalysisConfigItem(
                cost_threshold=cost_config["cost_threshold"],
                yield_impact_threshold=cost_config["yield_impact_threshold"],
                sensitive_area_radius=cost_config["sensitive_area_radius"],
                min_component_spacing=cost_config["min_component_spacing"],
                description=cost_config["description"]
            )
            
            # Parse validation
            validation_config = config["validation"]
            validation = ValidationConfigItem(
                check_signal_integrity=validation_config["check_signal_integrity"],
                check_thermal=validation_config["check_thermal"],
                check_emi=validation_config["check_emi"],
                check_power_distribution=validation_config["check_power_distribution"],
                check_audio_performance=validation_config["check_audio_performance"],
                check_noise=validation_config["check_noise"],
                check_frequency_response=validation_config["check_frequency_response"],
                check_ai_analysis=validation_config["check_ai_analysis"],
                check_cost_analysis=validation_config["check_cost_analysis"],
                description=validation_config["description"]
            )
            
            # Parse thresholds
            thresholds_config = config["thresholds"]
            thresholds = ThresholdsConfigItem(
                warning_severity=thresholds_config["warning_severity"],
                error_severity=thresholds_config["error_severity"],
                info_severity=thresholds_config["info_severity"],
                critical_severity=thresholds_config["critical_severity"],
                description=thresholds_config["description"]
            )
            
            # Parse units
            units_config = config["units"]
            units = UnitsConfigItem(
                distance=units_config["distance"],
                angle=units_config["angle"],
                temperature=units_config["temperature"],
                voltage=units_config["voltage"],
                current=units_config["current"],
                power=units_config["power"],
                frequency=units_config["frequency"],
                impedance=units_config["impedance"],
                cost=units_config["cost"],
                description=units_config["description"]
            )
            
            return AnalysisManagerConfigItem(
                signal_integrity=signal_integrity,
                thermal=thermal,
                emi=emi,
                power_distribution=power_distribution,
                audio_performance=audio_performance,
                noise_analysis=noise_analysis,
                frequency_response=frequency_response,
                ai_analysis=ai_analysis,
                cost_analysis=cost_analysis,
                validation=validation,
                thresholds=thresholds,
                units=units,
                description=config.get("description", "Analysis manager configuration")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing analysis manager configuration: {str(e)}")
            raise
    
    def _prepare_config_data(self, config_item: AnalysisManagerConfigItem) -> dict:
        """Prepare configuration item for serialization.
        
        Args:
            config_item: Configuration item to serialize
            
        Returns:
            Dictionary representation of configuration
        """
        try:
            # Convert signal integrity
            signal_integrity = {
                "min_track_width": config_item.signal_integrity.min_track_width,
                "max_track_length": config_item.signal_integrity.max_track_length,
                "max_track_angle": config_item.signal_integrity.max_track_angle,
                "min_clearance": config_item.signal_integrity.min_clearance,
                "max_impedance_mismatch": config_item.signal_integrity.max_impedance_mismatch,
                "max_crosstalk": config_item.signal_integrity.max_crosstalk,
                "max_reflection": config_item.signal_integrity.max_reflection,
                "description": config_item.signal_integrity.description
            }
            
            # Convert thermal
            thermal = {
                "min_thermal_pad_size": config_item.thermal.min_thermal_pad_size,
                "max_component_density_radius": config_item.thermal.max_component_density_radius,
                "max_nearby_components": config_item.thermal.max_nearby_components,
                "thermal_pad_threshold": config_item.thermal.thermal_pad_threshold,
                "high_density_threshold": config_item.thermal.high_density_threshold,
                "max_temperature_rise": config_item.thermal.max_temperature_rise,
                "thermal_resistance_factor": config_item.thermal.thermal_resistance_factor,
                "description": config_item.thermal.description
            }
            
            # Convert EMI
            emi = {
                "max_parallel_length": config_item.emi.max_parallel_length,
                "max_track_angle": config_item.emi.max_track_angle,
                "min_isolation_distance": config_item.emi.min_isolation_distance,
                "max_emission_level": config_item.emi.max_emission_level,
                "max_susceptibility": config_item.emi.max_susceptibility,
                "shielding_effectiveness": config_item.emi.shielding_effectiveness,
                "description": config_item.emi.description
            }
            
            # Convert power distribution
            power_distribution = {
                "min_power_track_width": config_item.power_distribution.min_power_track_width,
                "max_voltage_drop": config_item.power_distribution.max_voltage_drop,
                "min_power_plane_coverage": config_item.power_distribution.min_power_plane_coverage,
                "max_current_density": config_item.power_distribution.max_current_density,
                "power_net_prefixes": config_item.power_distribution.power_net_prefixes,
                "high_current_threshold": config_item.power_distribution.high_current_threshold,
                "description": config_item.power_distribution.description
            }
            
            # Convert audio performance
            audio_performance = {
                "min_snr": config_item.audio_performance.min_snr,
                "max_noise_floor": config_item.audio_performance.max_noise_floor,
                "max_distortion": config_item.audio_performance.max_distortion,
                "min_bandwidth": config_item.audio_performance.min_bandwidth,
                "max_bandwidth": config_item.audio_performance.max_bandwidth,
                "max_phase_shift": config_item.audio_performance.max_phase_shift,
                "min_impedance": config_item.audio_performance.min_impedance,
                "max_impedance": config_item.audio_performance.max_impedance,
                "description": config_item.audio_performance.description
            }
            
            # Convert noise analysis
            noise_analysis = {
                "default_signal_level": config_item.noise_analysis.default_signal_level,
                "thermal_noise_factor": config_item.noise_analysis.thermal_noise_factor,
                "crosstalk_threshold": config_item.noise_analysis.crosstalk_threshold,
                "power_supply_noise_factor": config_item.noise_analysis.power_supply_noise_factor,
                "ground_noise_factor": config_item.noise_analysis.ground_noise_factor,
                "min_distance_threshold": config_item.noise_analysis.min_distance_threshold,
                "description": config_item.noise_analysis.description
            }
            
            # Convert frequency response
            frequency_response = {
                "min_frequency": config_item.frequency_response.min_frequency,
                "max_frequency": config_item.frequency_response.max_frequency,
                "frequency_step": config_item.frequency_response.frequency_step,
                "min_response_flatness": config_item.frequency_response.min_response_flatness,
                "max_phase_variation": config_item.frequency_response.max_phase_variation,
                "min_bandwidth_efficiency": config_item.frequency_response.min_bandwidth_efficiency,
                "description": config_item.frequency_response.description
            }
            
            # Convert AI analysis
            ai_analysis = {
                "feature_weights": config_item.ai_analysis.feature_weights,
                "recommendation_threshold": config_item.ai_analysis.recommendation_threshold,
                "analysis_depth": config_item.ai_analysis.analysis_depth,
                "description": config_item.ai_analysis.description
            }
            
            # Convert cost analysis
            cost_analysis = {
                "cost_threshold": config_item.cost_analysis.cost_threshold,
                "yield_impact_threshold": config_item.cost_analysis.yield_impact_threshold,
                "sensitive_area_radius": config_item.cost_analysis.sensitive_area_radius,
                "min_component_spacing": config_item.cost_analysis.min_component_spacing,
                "description": config_item.cost_analysis.description
            }
            
            # Convert validation
            validation = {
                "check_signal_integrity": config_item.validation.check_signal_integrity,
                "check_thermal": config_item.validation.check_thermal,
                "check_emi": config_item.validation.check_emi,
                "check_power_distribution": config_item.validation.check_power_distribution,
                "check_audio_performance": config_item.validation.check_audio_performance,
                "check_noise": config_item.validation.check_noise,
                "check_frequency_response": config_item.validation.check_frequency_response,
                "check_ai_analysis": config_item.validation.check_ai_analysis,
                "check_cost_analysis": config_item.validation.check_cost_analysis,
                "description": config_item.validation.description
            }
            
            # Convert thresholds
            thresholds = {
                "warning_severity": config_item.thresholds.warning_severity,
                "error_severity": config_item.thresholds.error_severity,
                "info_severity": config_item.thresholds.info_severity,
                "critical_severity": config_item.thresholds.critical_severity,
                "description": config_item.thresholds.description
            }
            
            # Convert units
            units = {
                "distance": config_item.units.distance,
                "angle": config_item.units.angle,
                "temperature": config_item.units.temperature,
                "voltage": config_item.units.voltage,
                "current": config_item.units.current,
                "power": config_item.units.power,
                "frequency": config_item.units.frequency,
                "impedance": config_item.units.impedance,
                "cost": config_item.units.cost,
                "description": config_item.units.description
            }
            
            return {
                "analysis_manager": {
                    "signal_integrity": signal_integrity,
                    "thermal": thermal,
                    "emi": emi,
                    "power_distribution": power_distribution,
                    "audio_performance": audio_performance,
                    "noise_analysis": noise_analysis,
                    "frequency_response": frequency_response,
                    "ai_analysis": ai_analysis,
                    "cost_analysis": cost_analysis,
                    "validation": validation,
                    "thresholds": thresholds,
                    "units": units,
                    "description": config_item.description
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing analysis manager configuration: {str(e)}")
            raise
    
    def get_signal_integrity_config(self) -> Optional[SignalIntegrityConfigItem]:
        """Get signal integrity configuration.
        
        Returns:
            Signal integrity configuration
        """
        try:
            config = self.get_config()
            return config.signal_integrity
        except Exception as e:
            self.logger.error(f"Error getting signal integrity configuration: {str(e)}")
            return None
    
    def get_thermal_config(self) -> Optional[ThermalConfigItem]:
        """Get thermal configuration.
        
        Returns:
            Thermal configuration
        """
        try:
            config = self.get_config()
            return config.thermal
        except Exception as e:
            self.logger.error(f"Error getting thermal configuration: {str(e)}")
            return None
    
    def get_emi_config(self) -> Optional[EMIConfigItem]:
        """Get EMI configuration.
        
        Returns:
            EMI configuration
        """
        try:
            config = self.get_config()
            return config.emi
        except Exception as e:
            self.logger.error(f"Error getting EMI configuration: {str(e)}")
            return None
    
    def get_power_distribution_config(self) -> Optional[PowerDistributionConfigItem]:
        """Get power distribution configuration.
        
        Returns:
            Power distribution configuration
        """
        try:
            config = self.get_config()
            return config.power_distribution
        except Exception as e:
            self.logger.error(f"Error getting power distribution configuration: {str(e)}")
            return None
    
    def get_audio_performance_config(self) -> Optional[AudioPerformanceConfigItem]:
        """Get audio performance configuration.
        
        Returns:
            Audio performance configuration
        """
        try:
            config = self.get_config()
            return config.audio_performance
        except Exception as e:
            self.logger.error(f"Error getting audio performance configuration: {str(e)}")
            return None
    
    def get_noise_analysis_config(self) -> Optional[NoiseAnalysisConfigItem]:
        """Get noise analysis configuration.
        
        Returns:
            Noise analysis configuration
        """
        try:
            config = self.get_config()
            return config.noise_analysis
        except Exception as e:
            self.logger.error(f"Error getting noise analysis configuration: {str(e)}")
            return None
    
    def get_frequency_response_config(self) -> Optional[FrequencyResponseConfigItem]:
        """Get frequency response configuration.
        
        Returns:
            Frequency response configuration
        """
        try:
            config = self.get_config()
            return config.frequency_response
        except Exception as e:
            self.logger.error(f"Error getting frequency response configuration: {str(e)}")
            return None
    
    def get_ai_analysis_config(self) -> Optional[AIAnalysisConfigItem]:
        """Get AI analysis configuration.
        
        Returns:
            AI analysis configuration
        """
        try:
            config = self.get_config()
            return config.ai_analysis
        except Exception as e:
            self.logger.error(f"Error getting AI analysis configuration: {str(e)}")
            return None
    
    def get_cost_analysis_config(self) -> Optional[CostAnalysisConfigItem]:
        """Get cost analysis configuration.
        
        Returns:
            Cost analysis configuration
        """
        try:
            config = self.get_config()
            return config.cost_analysis
        except Exception as e:
            self.logger.error(f"Error getting cost analysis configuration: {str(e)}")
            return None
    
    def get_validation_config(self) -> Optional[ValidationConfigItem]:
        """Get validation configuration.
        
        Returns:
            Validation configuration
        """
        try:
            config = self.get_config()
            return config.validation
        except Exception as e:
            self.logger.error(f"Error getting validation configuration: {str(e)}")
            return None
    
    def get_thresholds_config(self) -> Optional[ThresholdsConfigItem]:
        """Get thresholds configuration.
        
        Returns:
            Thresholds configuration
        """
        try:
            config = self.get_config()
            return config.thresholds
        except Exception as e:
            self.logger.error(f"Error getting thresholds configuration: {str(e)}")
            return None
    
    def get_units_config(self) -> Optional[UnitsConfigItem]:
        """Get units configuration.
        
        Returns:
            Units configuration
        """
        try:
            config = self.get_config()
            return config.units
        except Exception as e:
            self.logger.error(f"Error getting units configuration: {str(e)}")
            return None 