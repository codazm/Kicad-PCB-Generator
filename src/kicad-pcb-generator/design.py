"""Audio design rules for PCB layout."""
import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from ...config.audio_design_config import AudioDesignConfig


class SignalType(Enum):
    """Types of signals in audio circuits."""
    AUDIO = "audio"
    POWER = "power"
    DIGITAL = "digital"
    CONTROL = "control"


@dataclass
class SignalPath:
    """Audio signal path configuration."""
    type: SignalType
    min_width: float  # mm
    min_clearance: float  # mm
    max_length: float  # mm
    require_ground_plane: bool
    require_shielding: bool
    require_impedance_control: bool
    target_impedance: Optional[float] = None  # ohms


@dataclass
class PowerSupply:
    """Power supply configuration."""
    voltage: float
    max_current: float
    min_track_width: float  # mm
    min_clearance: float  # mm
    require_star_grounding: bool
    require_decoupling: bool
    decoupling_capacitors: List[Dict[str, Any]]


@dataclass
class Grounding:
    """Grounding configuration."""
    strategy: str  # "star", "plane", "hybrid"
    min_plane_width: float  # mm
    require_isolation: bool
    isolation_gap: float  # mm
    require_ferrite_beads: bool
    ferrite_bead_placement: List[Dict[str, Any]]


class AudioDesignRules:
    """Audio design rules for PCB layout.
    
    This class defines design rules for audio PCB layouts,
    including signal paths, power supplies, and grounding strategies.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize audio design rules.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or "config/audio_design_rules.json"
        self.logger = logging.getLogger(__name__)
        
        # Initialize default configurations
        self.signal_paths: Dict[SignalType, SignalPath] = {}
        self.power_supplies: Dict[str, PowerSupply] = {}
        self.grounding: Optional[Grounding] = None
        self.component_placement: Dict[str, Dict[str, Any]] = {}
        self.noise_floor: Dict[str, float] = {}
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.logger.warning("Configuration file not found, using defaults")
                self._load_default_configuration()
                return
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Load signal path configurations
            signal_configs = config.get('signal_paths', {})
            for signal_type_str, signal_config in signal_configs.items():
                try:
                    signal_type = SignalType(signal_type_str)
                    self.signal_paths[signal_type] = SignalPath(
                        type=signal_type,
                        min_width=signal_config.get('min_width', 0.2),
                        min_clearance=signal_config.get('min_clearance', 0.2),
                        max_length=signal_config.get('max_length', 100.0),
                        require_ground_plane=signal_config.get('require_ground_plane', True),
                        require_shielding=signal_config.get('require_shielding', False),
                        require_impedance_control=signal_config.get('require_impedance_control', False),
                        target_impedance=signal_config.get('target_impedance')
                    )
                except ValueError as e:
                    self.logger.error("Invalid signal type in configuration: %s", signal_type_str)
                    continue
            
            # Load power supply configurations
            power_configs = config.get('power_supplies', {})
            for supply_name, supply_config in power_configs.items():
                self.power_supplies[supply_name] = PowerSupply(
                    voltage=supply_config.get('voltage', 12.0),
                    max_current=supply_config.get('max_current', 1.0),
                    min_track_width=supply_config.get('min_track_width', 0.5),
                    min_clearance=supply_config.get('min_clearance', 0.3),
                    require_star_grounding=supply_config.get('require_star_grounding', True),
                    require_decoupling=supply_config.get('require_decoupling', True),
                    decoupling_capacitors=supply_config.get('decoupling_capacitors', [])
                )
            
            # Load grounding configuration
            grounding_config = config.get('grounding', {})
            if grounding_config:
                self.grounding = Grounding(
                    strategy=grounding_config.get('strategy', 'star'),
                    min_plane_width=grounding_config.get('min_plane_width', 2.0),
                    require_isolation=grounding_config.get('require_isolation', True),
                    isolation_gap=grounding_config.get('isolation_gap', 0.5),
                    require_ferrite_beads=grounding_config.get('require_ferrite_beads', False),
                    ferrite_bead_placement=grounding_config.get('ferrite_bead_placement', [])
                )
            else:
                self.logger.error("Failed to load grounding configuration")
                raise ValueError("Grounding configuration not found")
            
            # Load component placement configurations
            self.component_placement = config.get('component_placement', {})
            
            # Load noise floor configurations
            noise_config = config.get('noise_floor', {})
            if noise_config:
                self.noise_floor = noise_config
            else:
                self.logger.error("Failed to load noise floor configuration")
                raise ValueError("Noise floor configuration not found")
            
            self.logger.info("Audio design rules configuration loaded successfully")
            
        except (FileNotFoundError, PermissionError) as e:
            self.logger.error("File access error loading configuration: %s", str(e))
            raise
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON in configuration file: %s", str(e))
            raise
        except (ValueError, KeyError) as e:
            self.logger.error("Configuration validation error: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error loading configuration: %s", str(e))
            raise
    
    def reload_configuration(self):
        """Reload configuration from file."""
        try:
            self._load_configuration()
            self.logger.info("Configuration reloaded successfully")
        except (FileNotFoundError, PermissionError, json.JSONDecodeError, ValueError, KeyError) as e:
            self.logger.error("Error reloading configuration: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error reloading configuration: %s", str(e))
            raise
    
    def update_signal_path_config(self, signal_type: SignalType, config_data: Dict[str, Any]):
        """Update signal path configuration.
        
        Args:
            signal_type: Type of signal
            config_data: New configuration data
        """
        try:
            result = self.config.update_signal_path_config(signal_type.value, config_data)
            if result.success:
                # Reload configuration
                self._load_configuration()
                self.logger.info(f"Updated signal path configuration for {signal_type.value}")
            else:
                self.logger.error(f"Failed to update signal path configuration: {result.message}")
                raise ValueError(result.message)
        except (ValueError, AttributeError) as e:
            self.logger.error("Error updating signal path configuration: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error updating signal path configuration: %s", str(e))
            raise
    
    def update_power_supply_config(self, supply_type: str, config_data: Dict[str, Any]):
        """Update power supply configuration.
        
        Args:
            supply_type: Type of power supply
            config_data: New configuration data
        """
        try:
            result = self.config.update_power_supply_config(supply_type, config_data)
            if result.success:
                # Reload configuration
                self._load_configuration()
                self.logger.info(f"Updated power supply configuration for {supply_type}")
            else:
                self.logger.error(f"Failed to update power supply configuration: {result.message}")
                raise ValueError(result.message)
        except (ValueError, AttributeError) as e:
            self.logger.error("Error updating power supply configuration: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error updating power supply configuration: %s", str(e))
            raise

    def validate_signal_path(self, path_type: SignalType, width: float, clearance: float, length: float) -> List[str]:
        """Validate a signal path against design rules.
        
        Args:
            path_type: Type of signal path
            width: Track width in mm
            clearance: Track clearance in mm
            length: Track length in mm
            
        Returns:
            List of validation errors
        """
        errors = []
        rules = self.signal_paths[path_type]
        
        if width < rules.min_width:
            errors.append(f"Signal path width {width}mm is less than minimum {rules.min_width}mm")
        
        if clearance < rules.min_clearance:
            errors.append(f"Signal path clearance {clearance}mm is less than minimum {rules.min_clearance}mm")
        
        if length > rules.max_length:
            errors.append(f"Signal path length {length}mm exceeds maximum {rules.max_length}mm")
        
        return errors
    
    def validate_power_supply(self, supply_type: str, width: float, clearance: float) -> List[str]:
        """Validate a power supply against design rules.
        
        Args:
            supply_type: Type of power supply
            width: Track width in mm
            clearance: Track clearance in mm
            
        Returns:
            List of validation errors
        """
        errors = []
        rules = self.power_supplies[supply_type]
        
        if width < rules.min_track_width:
            errors.append(f"Power supply width {width}mm is less than minimum {rules.min_track_width}mm")
        
        if clearance < rules.min_clearance:
            errors.append(f"Power supply clearance {clearance}mm is less than minimum {rules.min_clearance}mm")
        
        return errors
    
    def validate_grounding(self, plane_width: float, isolation_gap: float) -> List[str]:
        """Validate grounding against design rules.
        
        Args:
            plane_width: Ground plane width in mm
            isolation_gap: Isolation gap in mm
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if plane_width < self.grounding.min_plane_width:
            errors.append(f"Ground plane width {plane_width}mm is less than minimum {self.grounding.min_plane_width}mm")
        
        if self.grounding.require_isolation and isolation_gap < self.grounding.isolation_gap:
            errors.append(f"Isolation gap {isolation_gap}mm is less than minimum {self.grounding.isolation_gap}mm")
        
        return errors
    
    def validate_component_placement(self, component_type: str, distance: float, side: str) -> List[str]:
        """Validate component placement against design rules.
        
        Args:
            component_type: Type of component
            distance: Distance from board edge in mm
            side: Board side (left, right, top, bottom)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if component_type in self.component_placement:
            rules = self.component_placement[component_type]
            
            if distance < rules["min_distance"]:
                errors.append(f"Component distance {distance}mm is less than minimum {rules['min_distance']}mm")
            
            if side != rules["preferred_side"]:
                errors.append(f"Component side '{side}' is not preferred '{rules['preferred_side']}'")
        
        return errors
    
    def validate_noise_floor(self, section: str, noise_level: float) -> List[str]:
        """Validate noise floor against design rules.
        
        Args:
            section: Section name
            noise_level: Noise level in dB
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if section in self.noise_floor:
            max_noise = self.noise_floor[section]
            
            if noise_level > max_noise:
                errors.append(f"Noise level {noise_level}dB exceeds maximum {max_noise}dB for {section}")
        
        return errors
    
    def get_component_placement_guidelines(self, component_type: str) -> Dict[str, Any]:
        """Get component placement guidelines.
        
        Args:
            component_type: Type of component
            
        Returns:
            Component placement guidelines
        """
        return self.component_placement.get(component_type, {})
    
    def get_power_supply_guidelines(self, supply_type: str) -> Dict[str, Any]:
        """Get power supply guidelines.
        
        Args:
            supply_type: Type of power supply
            
        Returns:
            Power supply guidelines
        """
        if supply_type in self.power_supplies:
            supply = self.power_supplies[supply_type]
            return {
                "voltage": supply.voltage,
                "max_current": supply.max_current,
                "min_track_width": supply.min_track_width,
                "min_clearance": supply.min_clearance,
                "require_star_grounding": supply.require_star_grounding,
                "require_decoupling": supply.require_decoupling,
                "decoupling_capacitors": supply.decoupling_capacitors
            }
        return {}
    
    def get_grounding_guidelines(self) -> Dict[str, Any]:
        """Get grounding guidelines.
        
        Returns:
            Grounding guidelines
        """
        return {
            "strategy": self.grounding.strategy,
            "min_plane_width": self.grounding.min_plane_width,
            "require_isolation": self.grounding.require_isolation,
            "isolation_gap": self.grounding.isolation_gap,
            "require_ferrite_beads": self.grounding.require_ferrite_beads,
            "ferrite_bead_placement": self.grounding.ferrite_bead_placement
        } 
