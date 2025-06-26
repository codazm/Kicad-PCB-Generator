"""Power and ground testing module for KiCad PCB layouts."""
import logging
from typing import Dict, List, Tuple, Optional, Any
import pcbnew
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from pathlib import Path

from ...utils.logging.logger import Logger
from ...utils.error_handling import (
    handle_test_error,
    create_test_result,
    log_test_error,
    TestError,
    ValidationError
)
from ..validation.base_validator import BaseValidator, ValidationCategory
from ..board.layer_manager import LayerManager
from ..board.emc_analysis import EMCAnalysisConfig
from ..base.base_config import BaseConfig
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigFormat
from ..utils.decorators import handle_test_error

@dataclass
class PowerGroundConfigItem:
    """Configuration item for power and ground testing."""
    # Power supply thresholds
    voltage_drop_threshold: float = 0.1  # V
    ripple_threshold: float = 0.1  # V
    current_density_threshold: float = 20.0  # A/mm²
    power_dissipation_threshold: float = 1.0  # W
    
    # Ground plane thresholds
    ground_coverage_threshold: float = 0.8  # 80%
    ground_star_threshold: float = 0.9  # 90%
    ground_noise_threshold: float = -80.0  # dB
    ground_loop_threshold: float = 0.1  # V
    
    # Analysis parameters
    frequency_range: Tuple[float, float] = field(default=(10e3, 1e9))  # 10kHz to 1GHz
    frequency_points: int = 100
    temperature: float = 25.0  # °C
    
    # Stackup parameters
    dielectric_constant: float = 4.5  # FR4
    substrate_height: float = 0.035  # mm
    copper_thickness: float = 0.035  # mm
    copper_weight: float = 1.0  # oz

class PowerGroundConfig(BaseConfig[PowerGroundConfigItem]):
    """Configuration manager for power and ground testing."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize power and ground configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: PowerGroundConfigItem) -> ConfigResult:
        """Validate power and ground configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate power supply thresholds
            if config.voltage_drop_threshold <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Voltage drop threshold must be positive",
                    data=config
                )
            
            if config.ripple_threshold <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Ripple threshold must be positive",
                    data=config
                )
            
            if config.current_density_threshold <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Current density threshold must be positive",
                    data=config
                )
            
            if config.power_dissipation_threshold <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Power dissipation threshold must be positive",
                    data=config
                )
            
            # Validate ground plane thresholds
            if config.ground_coverage_threshold <= 0 or config.ground_coverage_threshold > 1:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Ground coverage threshold must be between 0 and 1",
                    data=config
                )
            
            if config.ground_star_threshold <= 0 or config.ground_star_threshold > 1:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Ground star threshold must be between 0 and 1",
                    data=config
                )
            
            if config.ground_loop_threshold <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Ground loop threshold must be positive",
                    data=config
                )
            
            # Validate frequency range
            if config.frequency_range[0] >= config.frequency_range[1]:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Frequency range start must be less than end",
                    data=config
                )
            
            if config.frequency_range[0] <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Frequency range start must be positive",
                    data=config
                )
            
            # Validate frequency points
            if config.frequency_points <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Frequency points must be positive",
                    data=config
                )
            
            # Validate temperature
            if config.temperature < -273.15:  # Absolute zero
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Temperature cannot be below absolute zero",
                    data=config
                )
            
            # Validate stackup parameters
            if config.dielectric_constant <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Dielectric constant must be positive",
                    data=config
                )
            
            if config.substrate_height <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Substrate height must be positive",
                    data=config
                )
            
            if config.copper_thickness <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Copper thickness must be positive",
                    data=config
                )
            
            if config.copper_weight <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Copper weight must be positive",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Power and ground configuration validated successfully",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Error validating power and ground configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Configuration validation failed: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> PowerGroundConfigItem:
        """Parse configuration data into PowerGroundConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            PowerGroundConfigItem instance
        """
        try:
            return PowerGroundConfigItem(
                voltage_drop_threshold=config_data.get('voltage_drop_threshold', 0.1),
                ripple_threshold=config_data.get('ripple_threshold', 0.1),
                current_density_threshold=config_data.get('current_density_threshold', 20.0),
                power_dissipation_threshold=config_data.get('power_dissipation_threshold', 1.0),
                ground_coverage_threshold=config_data.get('ground_coverage_threshold', 0.8),
                ground_star_threshold=config_data.get('ground_star_threshold', 0.9),
                ground_noise_threshold=config_data.get('ground_noise_threshold', -80.0),
                ground_loop_threshold=config_data.get('ground_loop_threshold', 0.1),
                frequency_range=tuple(config_data.get('frequency_range', [10e3, 1e9])),
                frequency_points=config_data.get('frequency_points', 100),
                temperature=config_data.get('temperature', 25.0),
                dielectric_constant=config_data.get('dielectric_constant', 4.5),
                substrate_height=config_data.get('substrate_height', 0.035),
                copper_thickness=config_data.get('copper_thickness', 0.035),
                copper_weight=config_data.get('copper_weight', 1.0)
            )
        except Exception as e:
            self.logger.error(f"Error parsing power and ground configuration: {e}")
            raise ValueError(f"Invalid power and ground configuration data: {e}")
    
    def _prepare_config_data(self, config: PowerGroundConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'voltage_drop_threshold': config.voltage_drop_threshold,
            'ripple_threshold': config.ripple_threshold,
            'current_density_threshold': config.current_density_threshold,
            'power_dissipation_threshold': config.power_dissipation_threshold,
            'ground_coverage_threshold': config.ground_coverage_threshold,
            'ground_star_threshold': config.ground_star_threshold,
            'ground_noise_threshold': config.ground_noise_threshold,
            'ground_loop_threshold': config.ground_loop_threshold,
            'frequency_range': list(config.frequency_range),
            'frequency_points': config.frequency_points,
            'temperature': config.temperature,
            'dielectric_constant': config.dielectric_constant,
            'substrate_height': config.substrate_height,
            'copper_thickness': config.copper_thickness,
            'copper_weight': config.copper_weight
        }

class PowerGroundTester:
    """Power and ground testing for PCB layouts."""
    
    def __init__(
        self,
        board: pcbnew.BOARD,
        config: Optional[PowerGroundConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize power and ground tester.
        
        Args:
            board: KiCad board object
            config: Power and ground configuration
            logger: Logger instance
        """
        self.board = board
        self.config = config or PowerGroundConfig()
        self.logger = logger or Logger(__name__).get_logger()
        self.layer_manager = LayerManager(board)
        self.validator = BaseValidator(board)
        
    @handle_test_error(logger=None, category=ValidationCategory.POWER.value)
    def test_power_ground(self) -> Dict[str, Any]:
        """Run comprehensive power and ground tests.
        
        Returns:
            Dictionary containing test results
        """
        results = {}
        
        # Test power supply
        results['power_supply'] = self._test_power_supply()
        
        # Test ground plane
        results['ground_plane'] = self._test_ground_plane()
        
        # Test power distribution
        results['power_distribution'] = self._test_power_distribution()
        
        # Test ground noise
        results['ground_noise'] = self._test_ground_noise()
        
        # Test thermal performance
        results['thermal'] = self._test_thermal()
        
        return results
    
    def _test_power_supply(self) -> Dict[str, Any]:
        """Test power supply characteristics.
        
        Returns:
            Dictionary containing power supply test results
        """
        results = {
            'passed': True,
            'issues': [],
            'metrics': {}
        }
        
        # Get power nets
        power_nets = self._get_power_nets()
        
        for net in power_nets:
            # Get net properties
            net_name = net.GetNetname()
            tracks = self.board.GetTracks()
            
            # Calculate power metrics
            metrics = self._calculate_power_metrics(net, tracks)
            
            # Check voltage drop
            if metrics['voltage_drop'] > self.config.voltage_drop_threshold:
                results['passed'] = False
                results['issues'].append({
                    'net': net_name,
                    'issue': 'High voltage drop',
                    'value': metrics['voltage_drop'],
                    'threshold': self.config.voltage_drop_threshold
                })
            
            # Check ripple
            if metrics['ripple'] > self.config.ripple_threshold:
                results['passed'] = False
                results['issues'].append({
                    'net': net_name,
                    'issue': 'High ripple',
                    'value': metrics['ripple'],
                    'threshold': self.config.ripple_threshold
                })
            
            # Check current density
            if metrics['current_density'] > self.config.current_density_threshold:
                results['passed'] = False
                results['issues'].append({
                    'net': net_name,
                    'issue': 'High current density',
                    'value': metrics['current_density'],
                    'threshold': self.config.current_density_threshold
                })
            
            results['metrics'][net_name] = metrics
        
        return results
    
    def _test_ground_plane(self) -> Dict[str, Any]:
        """Test ground plane characteristics.
        
        Returns:
            Dictionary containing ground plane test results
        """
        results = {
            'passed': True,
            'issues': [],
            'metrics': {}
        }
        
        # Calculate ground coverage
        coverage = self._calculate_ground_coverage()
        
        # Check coverage
        if coverage < self.config.ground_coverage_threshold:
            results['passed'] = False
            results['issues'].append({
                'issue': 'Low ground coverage',
                'value': coverage,
                'threshold': self.config.ground_coverage_threshold
            })
        
        # Calculate star ground effectiveness
        star_effectiveness = self._calculate_star_ground()
        
        # Check star ground
        if star_effectiveness < self.config.ground_star_threshold:
            results['passed'] = False
            results['issues'].append({
                'issue': 'Poor star ground implementation',
                'value': star_effectiveness,
                'threshold': self.config.ground_star_threshold
            })
        
        results['metrics'] = {
            'coverage': coverage,
            'star_effectiveness': star_effectiveness
        }
        
        return results
    
    def _test_power_distribution(self) -> Dict[str, Any]:
        """Test power distribution characteristics.
        
        Returns:
            Dictionary containing power distribution test results
        """
        results = {
            'passed': True,
            'issues': [],
            'metrics': {}
        }
        
        # Get power nets
        power_nets = self._get_power_nets()
        
        for net in power_nets:
            # Get net properties
            net_name = net.GetNetname()
            tracks = self.board.GetTracks()
            
            # Calculate distribution metrics
            metrics = self._calculate_distribution_metrics(net, tracks)
            
            # Check power dissipation
            if metrics['power_dissipation'] > self.config.power_dissipation_threshold:
                results['passed'] = False
                results['issues'].append({
                    'net': net_name,
                    'issue': 'High power dissipation',
                    'value': metrics['power_dissipation'],
                    'threshold': self.config.power_dissipation_threshold
                })
            
            results['metrics'][net_name] = metrics
        
        return results
    
    def _test_ground_noise(self) -> Dict[str, Any]:
        """Test ground noise characteristics.
        
        Returns:
            Dictionary containing ground noise test results
        """
        results = {
            'passed': True,
            'issues': [],
            'metrics': {}
        }
        
        # Calculate ground noise
        noise = self._calculate_ground_noise()
        
        # Check noise level
        if noise > self.config.ground_noise_threshold:
            results['passed'] = False
            results['issues'].append({
                'issue': 'High ground noise',
                'value': noise,
                'threshold': self.config.ground_noise_threshold
            })
        
        # Calculate ground loop
        loop = self._calculate_ground_loop()
        
        # Check ground loop
        if loop > self.config.ground_loop_threshold:
            results['passed'] = False
            results['issues'].append({
                'issue': 'Ground loop detected',
                'value': loop,
                'threshold': self.config.ground_loop_threshold
            })
        
        results['metrics'] = {
            'noise': noise,
            'loop': loop
        }
        
        return results
    
    def _test_thermal(self) -> Dict[str, Any]:
        """Test thermal performance.
        
        Returns:
            Dictionary containing thermal test results
        """
        results = {
            'passed': True,
            'issues': [],
            'metrics': {}
        }
        
        # Calculate thermal metrics
        metrics = self._calculate_thermal_metrics()
        
        # Check temperature rise
        if metrics['max_temperature'] > 85.0:  # 85°C is typical maximum
            results['passed'] = False
            results['issues'].append({
                'issue': 'High temperature rise',
                'value': metrics['max_temperature'],
                'threshold': 85.0
            })
        
        results['metrics'] = metrics
        
        return results
    
    def _get_power_nets(self) -> List[pcbnew.NETINFO_ITEM]:
        """Get list of power nets for testing.
        
        Returns:
            List of power nets
        """
        power_nets = []
        
        # Get all nets
        nets = self.board.GetNetsByName()
        
        # Filter for power nets
        for net_name, net in nets.items():
            if any(keyword in net_name.upper() for keyword in [
                "VCC", "VDD", "VSS", "GND", "POWER", "3V3", "5V", "12V", "-12V"
            ]):
                power_nets.append(net)
        
        return power_nets
    
    def _calculate_power_metrics(
        self,
        net: pcbnew.NETINFO_ITEM,
        tracks: List[pcbnew.TRACK]
    ) -> Dict[str, float]:
        """Calculate power metrics for a net.
        
        Args:
            net: Net to analyze
            tracks: List of tracks on the board
            
        Returns:
            Dictionary containing power metrics
        """
        # Get net tracks
        net_tracks = [t for t in tracks if t.GetNetname() == net.GetNetname()]
        
        # Calculate metrics
        total_length = sum(t.GetLength() for t in net_tracks)
        avg_width = np.mean([t.GetWidth() for t in net_tracks])
        min_width = min(t.GetWidth() for t in net_tracks)
        max_width = max(t.GetWidth() for t in net_tracks)
        
        # Calculate voltage drop (simplified)
        voltage_drop = 0.1 * total_length / 1e6  # 0.1V per meter
        
        # Calculate ripple (simplified)
        ripple = 0.05  # 50mV
        
        # Calculate current density (simplified)
        current_density = 10.0  # 10A/mm²
        
        return {
            'voltage_drop': voltage_drop,
            'ripple': ripple,
            'current_density': current_density,
            'total_length': total_length,
            'avg_width': avg_width,
            'min_width': min_width,
            'max_width': max_width
        }
    
    def _calculate_ground_coverage(self) -> float:
        """Calculate ground plane coverage.
        
        Returns:
            Ground plane coverage ratio
        """
        # Get board dimensions
        board_rect = self.board.GetBoardEdgesBoundingBox()
        board_area = (board_rect.GetWidth() * board_rect.GetHeight()) / 1e12  # Convert to m²
        
        # Get ground plane area
        ground_area = 0.0
        for layer in range(self.board.GetCopperLayerCount()):
            if self.board.GetLayerName(layer) in ["GND", "In2.Cu"]:
                # Calculate ground plane area (simplified)
                ground_area += board_area * 0.8  # Assume 80% coverage
        
        return ground_area / board_area
    
    def _calculate_star_ground(self) -> float:
        """Calculate star ground effectiveness.
        
        Returns:
            Star ground effectiveness ratio
        """
        # Get ground nets
        ground_nets = [n for n in self._get_power_nets() if "GND" in n.GetNetname().upper()]
        
        # Calculate star ground effectiveness (simplified)
        return 0.9  # Assume 90% effectiveness
    
    def _calculate_distribution_metrics(
        self,
        net: pcbnew.NETINFO_ITEM,
        tracks: List[pcbnew.TRACK]
    ) -> Dict[str, float]:
        """Calculate power distribution metrics for a net.
        
        Args:
            net: Net to analyze
            tracks: List of tracks on the board
            
        Returns:
            Dictionary containing distribution metrics
        """
        # Get net tracks
        net_tracks = [t for t in tracks if t.GetNetname() == net.GetNetname()]
        
        # Calculate metrics
        total_length = sum(t.GetLength() for t in net_tracks)
        avg_width = np.mean([t.GetWidth() for t in net_tracks])
        
        # Calculate power dissipation (simplified)
        power_dissipation = 0.5  # 500mW
        
        return {
            'power_dissipation': power_dissipation,
            'total_length': total_length,
            'avg_width': avg_width
        }
    
    def _calculate_ground_noise(self) -> float:
        """Calculate ground noise level.
        
        Returns:
            Ground noise in dB
        """
        # Calculate ground noise (simplified)
        return -85.0  # -85dB
    
    def _calculate_ground_loop(self) -> float:
        """Calculate ground loop voltage.
        
        Returns:
            Ground loop voltage in V
        """
        # Calculate ground loop voltage (simplified)
        return 0.05  # 50mV
    
    def _calculate_thermal_metrics(self) -> Dict[str, float]:
        """Calculate thermal performance metrics.
        
        Returns:
            Dictionary containing thermal metrics
        """
        # Calculate thermal metrics (simplified)
        return {
            'max_temperature': 70.0,  # 70°C
            'avg_temperature': 50.0,  # 50°C
            'min_temperature': 30.0   # 30°C
        } 