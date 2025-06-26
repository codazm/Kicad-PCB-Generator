"""Power distribution management for KiCad PCB layouts."""
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any, TYPE_CHECKING
import pcbnew

from ..base.base_manager import BaseManager
from ..base.base_config import BaseConfig
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigSection
from ..audio.rules.design import PowerSupply
from ..audio.validation.audio_validator import AudioPCBValidator
from ..ai.analysis.power_integrity import PowerIntegrityAnalyzer, PowerNetwork, PowerRequirements
from ..ai.collectors.power_collector import PowerCollector

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

@dataclass
class PowerDistributionConfigItem:
    """Data structure for power distribution configuration items."""
    id: str
    min_trace_width: float = 0.5  # mm
    max_trace_width: float = 5.0  # mm
    min_clearance: float = 0.5  # mm
    max_clearance: float = 10.0  # mm
    max_voltage_drop: float = 0.1  # V
    decoupling_cap_distance: float = 2.0  # mm
    star_topology: bool = True
    power_planes: Dict = None
    current_capacity: Dict = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Initialize default values for nested dictionaries."""
        if self.power_planes is None:
            self.power_planes = {
                'enabled': True,
                'min_width': 2.0,  # mm
                'clearance': 0.5,  # mm
                'thermal_relief': True
            }
        if self.current_capacity is None:
            self.current_capacity = {
                'max_current': 5.0,  # A
                'temperature_rise': 10,  # °C
                'safety_factor': 1.5
            }

class PowerDistributionConfig(BaseConfig[PowerDistributionConfigItem]):
    """Configuration for power distribution optimization.
    
    Now inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "PowerDistributionConfig", config_path: Optional[str] = None):
        """Initialize power distribution configuration.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        self.set_default("min_trace_width", 0.5)
        self.set_default("max_trace_width", 5.0)
        self.set_default("min_clearance", 0.5)
        self.set_default("max_clearance", 10.0)
        self.set_default("max_voltage_drop", 0.1)
        self.set_default("decoupling_cap_distance", 2.0)
        self.set_default("star_topology", True)
        self.set_default("power_planes", {
            'enabled': True,
            'min_width': 2.0,
            'clearance': 0.5,
            'thermal_relief': True
        })
        self.set_default("current_capacity", {
            'max_current': 5.0,
            'temperature_rise': 10,
            'safety_factor': 1.5
        })
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        self.add_validation_rule("min_trace_width", {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "required": True
        })
        self.add_validation_rule("max_trace_width", {
            "type": "float",
            "min": 0.5,
            "max": 20.0,
            "required": True
        })
        self.add_validation_rule("min_clearance", {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "required": True
        })
        self.add_validation_rule("max_clearance", {
            "type": "float",
            "min": 0.5,
            "max": 50.0,
            "required": True
        })
        self.add_validation_rule("max_voltage_drop", {
            "type": "float",
            "min": 0.01,
            "max": 1.0,
            "required": True
        })
        self.add_validation_rule("decoupling_cap_distance", {
            "type": "float",
            "min": 0.5,
            "max": 10.0,
            "required": True
        })
        self.add_validation_rule("star_topology", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("power_planes", {
            "type": "dict",
            "required": True,
            "required_keys": ["enabled", "min_width", "clearance", "thermal_relief"]
        })
        self.add_validation_rule("current_capacity", {
            "type": "dict",
            "required": True,
            "required_keys": ["max_current", "temperature_rise", "safety_factor"]
        })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate power distribution configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "min_trace_width", "max_trace_width", "min_clearance", "max_clearance",
                "max_voltage_drop", "decoupling_cap_distance", "star_topology",
                "power_planes", "current_capacity"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} must be a number")
                elif rule.get("type") == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                elif rule.get("type") == "dict" and not isinstance(value, dict):
                    errors.append(f"Field {field} must be a dictionary")
                
                # Range validation for numbers
                if rule.get("type") == "float":
                    if rule.get("min") is not None and value < rule["min"]:
                        errors.append(f"Field {field} must be >= {rule['min']}")
                    if rule.get("max") is not None and value > rule["max"]:
                        errors.append(f"Field {field} must be <= {rule['max']}")
                
                # Dictionary validation
                if rule.get("type") == "dict" and isinstance(value, dict):
                    required_keys = rule.get("required_keys", [])
                    for key in required_keys:
                        if key not in value:
                            errors.append(f"Field {field} must contain key: {key}")
            
            # Validate trace width relationship
            if "min_trace_width" in config_data and "max_trace_width" in config_data:
                if config_data["min_trace_width"] >= config_data["max_trace_width"]:
                    errors.append("min_trace_width must be less than max_trace_width")
            
            # Validate clearance relationship
            if "min_clearance" in config_data and "max_clearance" in config_data:
                if config_data["min_clearance"] >= config_data["max_clearance"]:
                    errors.append("min_clearance must be less than max_clearance")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="Power distribution configuration validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="Power distribution configuration is valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating power distribution configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse power distribution configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create power distribution config item
            power_item = PowerDistributionConfigItem(
                id=config_data.get("id", "power_distribution_config"),
                min_trace_width=config_data.get("min_trace_width", 0.5),
                max_trace_width=config_data.get("max_trace_width", 5.0),
                min_clearance=config_data.get("min_clearance", 0.5),
                max_clearance=config_data.get("max_clearance", 10.0),
                max_voltage_drop=config_data.get("max_voltage_drop", 0.1),
                decoupling_cap_distance=config_data.get("decoupling_cap_distance", 2.0),
                star_topology=config_data.get("star_topology", True),
                power_planes=config_data.get("power_planes", {
                    'enabled': True,
                    'min_width': 2.0,
                    'clearance': 0.5,
                    'thermal_relief': True
                }),
                current_capacity=config_data.get("current_capacity", {
                    'max_current': 5.0,
                    'temperature_rise': 10,
                    'safety_factor': 1.5
                })
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="power_distribution_settings",
                data=config_data,
                description="Power distribution optimization configuration settings"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="Power distribution configuration parsed successfully",
                data=power_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing power distribution configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare power distribution configuration data for saving.
        
        Returns:
            Configuration data
        """
        power_section = self.get_section("power_distribution_settings")
        if power_section:
            return power_section.data
        
        # Return default configuration
        return {
            "id": "power_distribution_config",
            "min_trace_width": self.get_default("min_trace_width"),
            "max_trace_width": self.get_default("max_trace_width"),
            "min_clearance": self.get_default("min_clearance"),
            "max_clearance": self.get_default("max_clearance"),
            "max_voltage_drop": self.get_default("max_voltage_drop"),
            "decoupling_cap_distance": self.get_default("decoupling_cap_distance"),
            "star_topology": self.get_default("star_topology"),
            "power_planes": self.get_default("power_planes"),
            "current_capacity": self.get_default("current_capacity")
        }
    
    def create_power_distribution_config(self,
                                        min_trace_width: float = 0.5,
                                        max_trace_width: float = 5.0,
                                        min_clearance: float = 0.5,
                                        max_clearance: float = 10.0,
                                        max_voltage_drop: float = 0.1,
                                        decoupling_cap_distance: float = 2.0,
                                        star_topology: bool = True,
                                        power_planes: Optional[Dict] = None,
                                        current_capacity: Optional[Dict] = None) -> ConfigResult[PowerDistributionConfigItem]:
        """Create a new power distribution configuration.
        
        Args:
            min_trace_width: Minimum trace width in mm
            max_trace_width: Maximum trace width in mm
            min_clearance: Minimum clearance in mm
            max_clearance: Maximum clearance in mm
            max_voltage_drop: Maximum voltage drop in V
            decoupling_cap_distance: Decoupling capacitor distance in mm
            star_topology: Whether to use star topology
            power_planes: Power plane configuration
            current_capacity: Current capacity configuration
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"power_distribution_config_{len(self._config_history) + 1}",
                "min_trace_width": min_trace_width,
                "max_trace_width": max_trace_width,
                "min_clearance": min_clearance,
                "max_clearance": max_clearance,
                "max_voltage_drop": max_voltage_drop,
                "decoupling_cap_distance": decoupling_cap_distance,
                "star_topology": star_topology,
                "power_planes": power_planes or self.get_default("power_planes"),
                "current_capacity": current_capacity or self.get_default("current_capacity")
            }
            
            # Validate configuration
            validation_result = self._validate_config(config_data)
            if not validation_result.success:
                return validation_result
            
            # Parse configuration
            return self._parse_config(config_data)
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error creating power distribution configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )

@dataclass
class PowerDistributionItem:
    """Data structure for power distribution items."""
    net_name: str
    voltage: float
    max_current: float
    target_impedance: float
    frequency_range: Tuple[float, float]
    domains: List[str]
    decoupling_capacitors: List[str]
    trace_width: float
    zone_settings: Dict
    validation_status: str = "pending"
    optimization_status: str = "pending"
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.net_name:
            raise ValueError("net_name is required")
        if self.voltage <= 0:
            raise ValueError("voltage must be positive")
        if self.max_current <= 0:
            raise ValueError("max_current must be positive")
        if self.target_impedance <= 0:
            raise ValueError("target_impedance must be positive")

class PowerDistributionManager(BaseManager[PowerDistributionItem]):
    """Manages power distribution optimization for PCB layouts."""
    
    def __init__(self, board: pcbnew.BOARD, config: Optional[PowerDistributionConfig] = None):
        """Initialize the power distribution manager.
        
        Args:
            board: KiCad board object
            config: Optional configuration for power distribution
        """
        super().__init__()
        self.board = board
        self.config = config or PowerDistributionConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.validator = AudioPCBValidator()
        self.analyzer = PowerIntegrityAnalyzer()
        self.collector = PowerCollector()
        
        # Validate KiCad version
        self._validate_kicad_version()
    
    def _validate_data(self, data: PowerDistributionItem) -> ManagerResult:
        """Validate power distribution item data.
        
        Args:
            data: Power distribution item to validate
            
        Returns:
            Manager result
        """
        try:
            # Basic validation
            if not isinstance(data, PowerDistributionItem):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Data must be a PowerDistributionItem instance",
                    errors=["Invalid data type"]
                )
            
            # Validate net name
            if not data.net_name or not isinstance(data.net_name, str):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid net name",
                    errors=["net_name must be a non-empty string"]
                )
            
            # Validate voltage
            if data.voltage <= 0:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid voltage",
                    errors=["voltage must be positive"]
                )
            
            # Validate current
            if data.max_current <= 0:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid current",
                    errors=["max_current must be positive"]
                )
            
            # Validate impedance
            if data.target_impedance <= 0:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid impedance",
                    errors=["target_impedance must be positive"]
                )
            
            # Validate frequency range
            if len(data.frequency_range) != 2 or data.frequency_range[0] >= data.frequency_range[1]:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid frequency range",
                    errors=["frequency_range must be a tuple of (min, max) with min < max"]
                )
            
            # Validate trace width
            if data.trace_width < self.config.get_default("min_trace_width") or data.trace_width > self.config.get_default("max_trace_width"):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid trace width",
                    errors=[f"trace_width must be between {self.config.get_default('min_trace_width')} and {self.config.get_default('max_trace_width')} mm"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Power distribution item validation successful"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating power distribution item: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Validation error: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a power distribution item.
        
        Args:
            key: Key of the item to clean up
        """
        try:
            # Remove from analyzer if present
            if hasattr(self.analyzer, 'remove_power_network'):
                self.analyzer.remove_power_network(key)
            
            self.logger.debug(f"Cleaned up power distribution item: {key}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up power distribution item {key}: {e}")
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        if not hasattr(pcbnew, 'VERSION'):
            raise RuntimeError("KiCad version not found")
        version = pcbnew.VERSION
        if not version.startswith('9'):
            raise RuntimeError(f"KiCad version {version} not supported. Version 9.x required.")
    
    def add_power_network(self, net_name: str, voltage: float, max_current: float, 
                         target_impedance: float = 0.1, frequency_range: Tuple[float, float] = (0, 1e6),
                         domains: Optional[List[str]] = None, decoupling_capacitors: Optional[List[str]] = None) -> ManagerResult:
        """Add a power network to the manager.
        
        Args:
            net_name: Name of the power network
            voltage: Voltage of the network
            max_current: Maximum current of the network
            target_impedance: Target impedance for the network
            frequency_range: Frequency range for analysis
            domains: Power domains
            decoupling_capacitors: List of decoupling capacitors
            
        Returns:
            Manager result
        """
        try:
            # Calculate trace width
            trace_width = self._calculate_trace_width_for_current(max_current)
            
            # Create power distribution item
            item = PowerDistributionItem(
                net_name=net_name,
                voltage=voltage,
                max_current=max_current,
                target_impedance=target_impedance,
                frequency_range=frequency_range,
                domains=domains or [],
                decoupling_capacitors=decoupling_capacitors or [],
                trace_width=trace_width,
                zone_settings=self._get_default_zone_settings()
            )
            
            # Add to manager
            result = self.create(net_name, item)
            
            if result.success:
                # Add to analyzer
                network = PowerNetwork(
                    name=net_name,
                    voltage=voltage,
                    max_current=max_current,
                    target_impedance=target_impedance,
                    frequency_range=frequency_range,
                    domains=domains or [],
                    decoupling_capacitors=decoupling_capacitors or []
                )
                self.analyzer.add_power_network(net_name, network)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding power network {net_name}: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.CREATE,
                status=ManagerStatus.FAILED,
                message=f"Error adding power network: {e}",
                errors=[str(e)]
            )
    
    def optimize_power_distribution(self) -> Dict:
        """Optimize power distribution for the board.
        
        Returns:
            Dictionary containing optimization results
        """
        self.logger.info("Starting power distribution optimization...")
        
        # Collect power data
        power_data = self.collector.collect_power_data(self.board)
        
        # Analyze power integrity
        analysis_results = self._analyze_power_integrity(power_data)
        
        # Optimize power planes
        plane_results = self._optimize_power_planes()
        
        # Optimize power traces
        trace_results = self._optimize_power_traces()
        
        # Add decoupling capacitors
        decoupling_results = self._add_decoupling_capacitors()
        
        # Validate power distribution
        validation_results = self._validate_power_distribution()
        
        # Combine results
        results = {
            'analysis': analysis_results,
            'planes': plane_results,
            'traces': trace_results,
            'decoupling': decoupling_results,
            'validation': validation_results
        }
        
        self.logger.info("Power distribution optimization completed")
        return results
    
    def _calculate_trace_width_for_current(self, current: float) -> float:
        """Calculate required trace width for a given current.
        
        Args:
            current: Current in amperes
            
        Returns:
            Trace width in mm
        """
        # Using IPC-2221 formula for external layers
        width = (current * 0.048) / (self.config.get_default("current_capacity")['temperature_rise'] ** 0.44)
        
        # Apply safety factor
        width *= self.config.get_default("current_capacity")['safety_factor']
        
        # Ensure within limits
        return max(min(width, self.config.get_default("max_trace_width")), self.config.get_default("min_trace_width"))
    
    def _get_default_zone_settings(self) -> Dict:
        """Get default zone settings.
        
        Returns:
            Default zone settings dictionary
        """
        return {
            'enabled': self.config.get_default("power_planes")['enabled'],
            'min_width': self.config.get_default("power_planes")['min_width'],
            'clearance': self.config.get_default("power_planes")['clearance'],
            'thermal_relief': self.config.get_default("power_planes")['thermal_relief']
        }
    
    def _analyze_power_integrity(self, power_data: Dict) -> Dict:
        """Analyze power integrity of the board.
        
        Args:
            power_data: Power data collected from the board
            
        Returns:
            Dictionary containing analysis results
        """
        results = {}
        
        # Analyze each power network
        for net_name, net_data in power_data.get('networks', {}).items():
            network = PowerNetwork(
                name=net_name,
                voltage=net_data.get('voltage', 0),
                max_current=net_data.get('max_current', 0),
                target_impedance=net_data.get('target_impedance', 0.1),
                frequency_range=(0, 1e6),  # Default frequency range
                domains=net_data.get('domains', []),
                decoupling_capacitors=net_data.get('decoupling_capacitors', [])
            )
            
            # Add network to analyzer
            self.analyzer.add_power_network(net_name, network)
            
            # Analyze network
            results[net_name] = self.analyzer.optimize_power_network(
                net_name,
                network.target_impedance,
                network.frequency_range
            )
        
        return results
    
    def _optimize_power_planes(self) -> Dict:
        """Optimize power planes on the board.
        
        Returns:
            Dictionary containing optimization results
        """
        results = {
            'created_planes': [],
            'modified_planes': [],
            'errors': []
        }
        
        try:
            # Get power nets
            power_nets = [net for net in self.board.GetNetsByName().values()
                         if self._is_power_net(net.GetNetname())]
            
            for net in power_nets:
                # Create or modify power plane
                zone = self._get_or_create_power_zone(net)
                if zone:
                    # Optimize zone settings
                    self._optimize_zone_settings(zone)
                    results['modified_planes'].append(net.GetNetname())
                else:
                    results['errors'].append(f"Failed to create power plane for {net.GetNetname()}")
            
            # Refresh board
            self.board.BuildConnectivity()
            
        except Exception as e:
            self.logger.error(f"Error optimizing power planes: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    def _optimize_power_traces(self) -> Dict:
        """Optimize power traces on the board.
        
        Returns:
            Dictionary containing optimization results
        """
        results = {
            'modified_traces': [],
            'errors': []
        }
        
        try:
            # Get power tracks
            power_tracks = [track for track in self.board.GetTracks()
                          if self._is_power_track(track)]
            
            for track in power_tracks:
                # Calculate required width
                required_width = self._calculate_trace_width(track)
                
                # Update track width if needed
                if track.GetWidth() < required_width:
                    track.SetWidth(int(required_width * 1e6))  # Convert to nm
                    results['modified_traces'].append(track.GetNetname())
            
            # Refresh board
            self.board.BuildConnectivity()
            
        except Exception as e:
            self.logger.error(f"Error optimizing power traces: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    def _add_decoupling_capacitors(self) -> Dict:
        """Add decoupling capacitors to the board.
        
        Returns:
            Dictionary containing optimization results
        """
        results = {
            'added_capacitors': [],
            'errors': []
        }
        
        try:
            # Get power components
            power_components = [comp for comp in self.board.GetFootprints()
                              if self._is_power_component(comp)]
            
            for comp in power_components:
                # Add decoupling capacitors
                caps = self._add_component_decoupling(comp)
                if caps:
                    results['added_capacitors'].extend(caps)
            
            # Refresh board
            self.board.BuildConnectivity()
            
        except Exception as e:
            self.logger.error(f"Error adding decoupling capacitors: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    def _validate_power_distribution(self) -> Dict:
        """Validate power distribution on the board.
        
        Returns:
            Dictionary containing validation results
        """
        return self.validator._validate_power_distribution(self.board)
    
    def _is_power_net(self, net_name: str) -> bool:
        """Check if a net is a power net."""
        return any(p in net_name.upper() for p in ['VCC', 'VDD', 'VSS', 'POWER'])
    
    def _is_power_track(self, track: pcbnew.TRACK) -> bool:
        """Check if a track is a power track."""
        return self._is_power_net(track.GetNetname())
    
    def _is_power_component(self, comp: pcbnew.FOOTPRINT) -> bool:
        """Check if a component is a power component."""
        value = comp.GetValue().lower()
        ref = comp.GetReference()
        return any(p in value for p in ['reg', 'ldo', 'dc-dc', 'filter']) or ref.startswith('U')
    
    def _get_or_create_power_zone(self, net: pcbnew.NETINFO_ITEM) -> Optional[pcbnew.ZONE]:
        """Get or create a power zone for a net."""
        # Check for existing zone
        for zone in self.board.Zones():
            if zone.GetNetname() == net.GetNetname():
                return zone
        
        # Create new zone
        try:
            zone = pcbnew.ZONE(self.board)
            zone.SetNet(net)
            zone.SetLayer(self.board.GetLayerID("Power"))
            zone.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
            zone.SetMinThickness(int(self.config.get_default("power_planes")['min_width'] * 1e6))
            zone.SetClearance(int(self.config.get_default("power_planes")['clearance'] * 1e6))
            
            # Add zone to board
            self.board.Add(zone)
            return zone
            
        except Exception as e:
            self.logger.error(f"Error creating power zone: {str(e)}")
            return None
    
    def _optimize_zone_settings(self, zone: pcbnew.ZONE) -> None:
        """Optimize settings for a power zone."""
        # Set thermal relief
        if self.config.get_default("power_planes")['thermal_relief']:
            zone.SetThermalReliefGap(int(0.5 * 1e6))  # 0.5mm
            zone.SetThermalReliefCopperBridge(int(0.3 * 1e6))  # 0.3mm
            zone.SetThermalReliefSpokeCount(4)
        
        # Set other settings
        zone.SetMinThickness(int(self.config.get_default("power_planes")['min_width'] * 1e6))
        zone.SetClearance(int(self.config.get_default("power_planes")['clearance'] * 1e6))
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        zone.SetPriority(1)
        
        # Rebuild zone
        zone.Rebuild()
    
    def _calculate_trace_width(self, track: pcbnew.TRACK) -> float:
        """Calculate required trace width for a power track."""
        # Get current from net
        net = track.GetNet()
        current = self._get_net_current(net)
        
        # Calculate width based on current
        # Using IPC-2221 formula for external layers
        width = (current * 0.048) / (self.config.get_default("current_capacity")['temperature_rise'] ** 0.44)
        
        # Apply safety factor
        width *= self.config.get_default("current_capacity")['safety_factor']
        
        # Ensure within limits
        return max(min(width, self.config.get_default("max_trace_width")), self.config.get_default("min_trace_width"))
    
    def _get_net_current(self, net: pcbnew.NETINFO_ITEM) -> float:
        """Get current for a net."""
        # This is a simplified implementation
        # In practice, this should be calculated based on component requirements
        return 1.0  # Default to 1A
    
    def _add_component_decoupling(self, comp: pcbnew.FOOTPRINT) -> List[str]:
        """Add decoupling capacitors for a component."""
        added_caps = []
        
        try:
            # Get power pins
            power_pins = [pad for pad in comp.Pads() if self._is_power_net(pad.GetNetname())]
            
            for pin in power_pins:
                # Add decoupling capacitors
                for cap_value in ['100n', '10u']:
                    cap = self._create_decoupling_capacitor(cap_value, pin)
                    if cap:
                        added_caps.append(cap.GetReference())
            
        except Exception as e:
            self.logger.error(f"Error adding decoupling capacitors: {str(e)}")
        
        return added_caps
    
    def _create_decoupling_capacitor(self, value: str, power_pin: pcbnew.PAD) -> Optional[pcbnew.FOOTPRINT]:
        """Create a decoupling capacitor near a power pin."""
        try:
            # Create capacitor footprint
            cap = pcbnew.FOOTPRINT(self.board)
            cap.SetValue(value)
            cap.SetReference(f"C{self.board.GetFootprintCount() + 1}")
            
            # Set position near power pin
            pos = power_pin.GetPosition()
            cap.SetPosition(pos)
            
            # Add to board
            self.board.Add(cap)
            return cap
            
        except Exception as e:
            self.logger.error(f"Error creating decoupling capacitor: {str(e)}")
            return None 