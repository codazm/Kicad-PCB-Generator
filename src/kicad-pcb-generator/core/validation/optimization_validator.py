"""Optimization validation functionality for KiCad PCB Generator.

This module provides optimization-focused validation features while maintaining
compatibility with KiCad 9 and leveraging native functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pcbnew
import math

from .enhanced_validator import EnhancedValidator, EnhancedValidationCategory, EnhancedValidationResult

class ValidationPriority(Enum):
    """Priority levels for validation results."""
    CRITICAL = 1  # Safety and reliability issues
    HIGH = 2      # Signal integrity and power distribution
    MEDIUM = 3    # EMI/EMC and thermal management
    LOW = 4       # Manufacturing and cost optimization

class OptimizationCategory(Enum):
    """Categories for optimization validation."""
    SAFETY = "Safety"
    SIGNAL_INTEGRITY = "Signal Integrity"
    POWER_DISTRIBUTION = "Power Distribution"
    EMI_EMC = "EMI/EMC"
    THERMAL = "Thermal"
    MANUFACTURING = "Manufacturing"
    COST = "Cost"
    AUDIO = "Audio"

@dataclass
class OptimizationResult(EnhancedValidationResult):
    """Optimization validation result with additional metadata."""
    optimization_category: OptimizationCategory
    priority: ValidationPriority
    current_value: Optional[float] = None
    optimal_value: Optional[float] = None
    improvement_potential: Optional[float] = None
    cost_impact: Optional[float] = None
    frequency: Optional[float] = None
    impedance: Optional[float] = None
    crosstalk: Optional[float] = None
    noise_level: Optional[float] = None
    power_quality: Optional[float] = None
    thermal_impact: Optional[float] = None
    safety_margin: Optional[float] = None
    reliability_factor: Optional[float] = None

class OptimizationValidator(EnhancedValidator):
    """Optimization-focused validation functionality.
    
    This class adds optimization-specific validation features while maintaining
    compatibility with KiCad 9 and leveraging native functionality where possible.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the optimization validator.
        
        Args:
            logger: Optional logger instance
        """
        super().__init__(logger)
        self._optimization_cache: Dict[str, Any] = {}
    
    def validate_board(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate a PCB board with optimization focus.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results by category
        """
        # Get enhanced validation results
        results = super().validate_board(board)
        
        # Add optimization-specific validation results in priority order
        results.update(self._validate_safety_and_reliability(board))
        results.update(self._validate_signal_integrity_optimization(board))
        results.update(self._validate_power_distribution_optimization(board))
        results.update(self._validate_emi_emc_optimization(board))
        results.update(self._validate_thermal_optimization(board))
        results.update(self._validate_manufacturing_optimization(board))
        results.update(self._validate_cost_optimization(board))
        results.update(self._validate_audio_optimization(board))
        
        return results

    def _validate_safety_and_reliability(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate safety and reliability aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check high-voltage clearances
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net or not any(keyword in net.upper() for keyword in ["HV", "AC", "MAINS"]):
                    continue
                
                # Check clearance to other tracks
                for other in board.GetTracks():
                    if other == track:
                        continue
                    
                    if other.GetType() != pcbnew.PCB_TRACE_T:
                        continue
                    
                    # Calculate clearance
                    pos1 = track.GetStart()
                    pos2 = other.GetStart()
                    distance = math.sqrt(
                        ((pos1.x - pos2.x) / 1e6) ** 2 +
                        ((pos1.y - pos2.y) / 1e6) ** 2
                    )
                    
                    # Minimum clearance based on voltage
                    min_clearance = 2.0  # 2mm for high voltage
                    if distance < min_clearance:
                        results[ValidationCategory.GENERAL].append(OptimizationResult(
                            category=EnhancedValidationCategory.GENERAL,
                            optimization_category=OptimizationCategory.SAFETY,
                            priority=ValidationPriority.CRITICAL,
                            message=f"High-voltage track {net} clearance ({distance:.2f}mm) below safety margin",
                            severity="error",
                            location=(pos1.x/1e6, pos1.y/1e6),
                            net_name=net,
                            current_value=distance,
                            optimal_value=min_clearance,
                            improvement_potential=((min_clearance - distance) / min_clearance) * 100,
                            safety_margin=((min_clearance - distance) / min_clearance) * 100
                        ))
            
            # Check component derating
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["R", "C", "L"]):
                    # Check power rating
                    value = self._get_component_value(footprint)
                    if value:
                        power_rating = self._get_power_rating(footprint)
                        if power_rating:
                            # Calculate derating factor
                            derating_factor = 0.7  # 70% of rated power
                            if power_rating < value * derating_factor:
                                pos = footprint.GetPosition()
                                results[ValidationCategory.GENERAL].append(OptimizationResult(
                                    category=EnhancedValidationCategory.GENERAL,
                                    optimization_category=OptimizationCategory.SAFETY,
                                    priority=ValidationPriority.CRITICAL,
                                    message=f"Component {ref} power rating ({power_rating}W) below safety margin",
                                    severity="error",
                                    location=(pos.x/1e6, pos.y/1e6),
                                    component_ref=ref,
                                    current_value=power_rating,
                                    optimal_value=value * derating_factor,
                                    improvement_potential=((value * derating_factor - power_rating) / (value * derating_factor)) * 100,
                                    safety_margin=((value * derating_factor - power_rating) / (value * derating_factor)) * 100
                                ))
            
            # Check thermal safety
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["U", "IC", "Q", "REG"]):
                    # Check for thermal relief
                    has_thermal_relief = False
                    for pad in footprint.Pads():
                        if pad.GetNetname() in ["GND", "PWR", "VCC", "VDD"]:
                            if pad.GetThermalSpokeWidth() > 0:
                                has_thermal_relief = True
                                break
                    
                    if not has_thermal_relief:
                        pos = footprint.GetPosition()
                        results[ValidationCategory.GENERAL].append(OptimizationResult(
                            category=EnhancedValidationCategory.GENERAL,
                            optimization_category=OptimizationCategory.SAFETY,
                            priority=ValidationPriority.CRITICAL,
                            message=f"High-power component {ref} lacks thermal relief",
                            severity="error",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=ref
                        ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in safety and reliability validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in safety and reliability validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in safety and reliability validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in safety and reliability validation: {str(e)}",
                "error"
            ))
        
        return results

    def _get_component_value(self, footprint: pcbnew.FOOTPRINT) -> Optional[float]:
        """Get the value of a component.
        
        Args:
            footprint: Component footprint
            
        Returns:
            Component value or None if not found
        """
        try:
            # Extract value from component reference
            ref = footprint.GetReference()
            if ref.startswith("R"):
                # Resistor value
                return float(footprint.GetValue().replace("R", "").replace("k", "000").replace("M", "000000"))
            elif ref.startswith("C"):
                # Capacitor value
                return float(footprint.GetValue().replace("pF", "").replace("nF", "000").replace("uF", "000000"))
            elif ref.startswith("L"):
                # Inductor value
                return float(footprint.GetValue().replace("uH", "").replace("mH", "000").replace("H", "000000"))
            return None
        except Exception:
            return None

    def _get_power_rating(self, footprint: pcbnew.FOOTPRINT) -> Optional[float]:
        """Get the power rating of a component.
        
        Args:
            footprint: Component footprint
            
        Returns:
            Power rating in watts or None if not found
        """
        try:
            # Extract power rating from component value
            value = self._get_component_value(footprint)
            if value is None:
                return None
            
            ref = footprint.GetReference()
            if ref.startswith("R"):
                # Resistor power rating
                return value * 0.1  # Assume 0.1W per ohm
            elif ref.startswith("C"):
                # Capacitor power rating
                return value * 0.01  # Assume 0.01W per farad
            elif ref.startswith("L"):
                # Inductor power rating
                return value * 0.001  # Assume 0.001W per henry
            return None
        except Exception:
            return None

    def _validate_signal_integrity_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate signal integrity optimization.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check high-speed signal paths
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net or not any(keyword in net.upper() for keyword in ["CLK", "DDR", "USB", "HDMI", "AUDIO"]):
                    continue
                
                # Check impedance control
                width = track.GetWidth() / 1e6  # Convert to mm
                optimal_width = 0.2  # Optimal width for high-speed signals
                
                if width < optimal_width:
                    pos = track.GetStart()
                    results[ValidationCategory.GENERAL].append(OptimizationResult(
                        category=EnhancedValidationCategory.GENERAL,
                        optimization_category=OptimizationCategory.SIGNAL_INTEGRITY,
                        priority=ValidationPriority.HIGH,
                        message=f"High-speed signal {net} trace width ({width:.2f}mm) below optimal",
                        severity="warning",
                        location=(pos.x/1e6, pos.y/1e6),
                        net_name=net,
                        current_value=width,
                        optimal_value=optimal_width,
                        improvement_potential=((optimal_width - width) / optimal_width) * 100
                    ))
                
                # Check for proper termination
                if not self._has_termination(track, board):
                    pos = track.GetStart()
                    results[ValidationCategory.GENERAL].append(OptimizationResult(
                        category=EnhancedValidationCategory.GENERAL,
                        optimization_category=OptimizationCategory.SIGNAL_INTEGRITY,
                        priority=ValidationPriority.HIGH,
                        message=f"High-speed signal {net} lacks proper termination",
                        severity="warning",
                        location=(pos.x/1e6, pos.y/1e6),
                        net_name=net
                    ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in signal integrity optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in signal integrity optimization validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in signal integrity optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in signal integrity optimization validation: {str(e)}",
                "error"
            ))
        
        return results

    def _validate_power_distribution_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate power distribution optimization.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check power plane connections
            for zone in board.Zones():
                if zone.GetNetname() and "PWR" in zone.GetNetname().upper():
                    # Check for proper power plane connections
                    connection_count = sum(1 for pad in board.GetPads() 
                                         if pad.GetNetname() == zone.GetNetname())
                    
                    if connection_count < 2:  # Need at least 2 connections for redundancy
                        pos = zone.GetPosition()
                        results[ValidationCategory.GENERAL].append(OptimizationResult(
                            category=EnhancedValidationCategory.GENERAL,
                            optimization_category=OptimizationCategory.POWER_DISTRIBUTION,
                            priority=ValidationPriority.HIGH,
                            message=f"Power plane {zone.GetNetname()} has insufficient connections ({connection_count})",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            net_name=zone.GetNetname(),
                            current_value=connection_count,
                            optimal_value=2,
                            improvement_potential=((2 - connection_count) / 2) * 100
                        ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in power distribution optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in power distribution optimization validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in power distribution optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in power distribution optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_emi_emc_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate EMI/EMC optimization.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check for balanced differential pairs
            differential_pairs = self._find_differential_pairs(board)
            
            for pair in differential_pairs:
                # Check pair spacing
                track1, track2 = pair
                pos1 = track1.GetStart()
                pos2 = track2.GetStart()
                spacing = math.sqrt(
                    ((pos1.x - pos2.x) / 1e6) ** 2 +
                    ((pos1.y - pos2.y) / 1e6) ** 2
                )
                
                optimal_spacing = 0.1  # 0.1mm optimal spacing for differential pairs
                if spacing > optimal_spacing * 2:  # Allow some tolerance
                    results[ValidationCategory.GENERAL].append(OptimizationResult(
                        category=EnhancedValidationCategory.GENERAL,
                        optimization_category=OptimizationCategory.EMI_EMC,
                        priority=ValidationPriority.MEDIUM,
                        message=f"Differential pair spacing ({spacing:.2f}mm) above optimal",
                        severity="warning",
                        location=(pos1.x/1e6, pos1.y/1e6),
                        current_value=spacing,
                        optimal_value=optimal_spacing,
                        improvement_potential=((spacing - optimal_spacing) / spacing) * 100
                    ))
            
            # Check for ground plane coverage
            ground_area = self._calculate_ground_area(board)
            board_area = self._calculate_board_area(board)
            ground_coverage = (ground_area / board_area) * 100
            
            optimal_coverage = 80.0  # 80% optimal ground coverage
            if ground_coverage < optimal_coverage:
                results[ValidationCategory.GENERAL].append(OptimizationResult(
                    category=EnhancedValidationCategory.GENERAL,
                    optimization_category=OptimizationCategory.EMI_EMC,
                    priority=ValidationPriority.MEDIUM,
                    message=f"Ground plane coverage ({ground_coverage:.1f}%) below optimal",
                    severity="warning",
                    current_value=ground_coverage,
                    optimal_value=optimal_coverage,
                    improvement_potential=((optimal_coverage - ground_coverage) / optimal_coverage) * 100
                ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in EMI/EMC optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in EMI/EMC optimization validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in EMI/EMC optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in EMI/EMC optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_thermal_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate thermal optimization.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check component spacing for thermal management
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["U", "IC", "Q", "REG"]):
                    # Check for nearby high-power components
                    for other in board.GetFootprints():
                        if other == footprint:
                            continue
                        
                        if any(keyword in other.GetReference().upper() for keyword in ["U", "IC", "Q", "REG"]):
                            pos1 = footprint.GetPosition()
                            pos2 = other.GetPosition()
                            distance = math.sqrt(
                                ((pos1.x - pos2.x) / 1e6) ** 2 +
                                ((pos1.y - pos2.y) / 1e6) ** 2
                            )
                            
                            min_spacing = 5.0  # 5mm minimum spacing between high-power components
                            if distance < min_spacing:
                                results[ValidationCategory.GENERAL].append(OptimizationResult(
                                    category=EnhancedValidationCategory.GENERAL,
                                    optimization_category=OptimizationCategory.THERMAL,
                                    priority=ValidationPriority.MEDIUM,
                                    message=f"High-power components {ref} and {other.GetReference()} too close ({distance:.1f}mm)",
                                    severity="warning",
                                    location=(pos1.x/1e6, pos1.y/1e6),
                                    component_ref=ref,
                                    current_value=distance,
                                    optimal_value=min_spacing,
                                    improvement_potential=((min_spacing - distance) / min_spacing) * 100,
                                    thermal_impact=((min_spacing - distance) / min_spacing) * 100
                                ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in thermal optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in thermal optimization validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in thermal optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in thermal optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_manufacturing_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate manufacturing optimization.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check component orientation
            for footprint in board.GetFootprints():
                orientation = footprint.GetOrientation()
                if orientation % 90 != 0:
                    pos = footprint.GetPosition()
                    results[ValidationCategory.GENERAL].append(OptimizationResult(
                        category=EnhancedValidationCategory.GENERAL,
                        optimization_category=OptimizationCategory.MANUFACTURING,
                        priority=ValidationPriority.LOW,
                        message=f"Component {footprint.GetReference()} has non-orthogonal orientation",
                        severity="info",
                        location=(pos.x/1e6, pos.y/1e6),
                        component_ref=footprint.GetReference()
                    ))
                
                # Check for proper component spacing
                for other in board.GetFootprints():
                    if other == footprint:
                        continue
                    
                    pos1 = footprint.GetPosition()
                    pos2 = other.GetPosition()
                    distance = math.sqrt(
                        ((pos1.x - pos2.x) / 1e6) ** 2 +
                        ((pos1.y - pos2.y) / 1e6) ** 2
                    )
                    
                    min_spacing = 0.5  # 0.5mm minimum component spacing
                    if distance < min_spacing:
                        results[ValidationCategory.GENERAL].append(OptimizationResult(
                            category=EnhancedValidationCategory.GENERAL,
                            optimization_category=OptimizationCategory.MANUFACTURING,
                            priority=ValidationPriority.LOW,
                            message=f"Components {footprint.GetReference()} and {other.GetReference()} too close ({distance:.2f}mm)",
                            severity="warning",
                            location=(pos1.x/1e6, pos1.y/1e6),
                            component_ref=footprint.GetReference(),
                            current_value=distance,
                            optimal_value=min_spacing,
                            improvement_potential=((min_spacing - distance) / min_spacing) * 100
                        ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in manufacturing optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in manufacturing optimization validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in manufacturing optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in manufacturing optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_cost_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate cost optimization.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check for expensive components
            expensive_components = []
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["U", "IC", "Q"]):
                    # Estimate component cost (simplified)
                    cost = self._estimate_component_cost(footprint)
                    if cost > 10.0:  # Components costing more than $10
                        expensive_components.append((ref, cost))
            
            if len(expensive_components) > 5:  # More than 5 expensive components
                results[ValidationCategory.GENERAL].append(OptimizationResult(
                    category=EnhancedValidationCategory.GENERAL,
                    optimization_category=OptimizationCategory.COST,
                    priority=ValidationPriority.LOW,
                    message=f"Board has {len(expensive_components)} expensive components",
                    severity="info",
                    current_value=len(expensive_components),
                    optimal_value=5,
                    improvement_potential=((len(expensive_components) - 5) / len(expensive_components)) * 100,
                    cost_impact=sum(cost for _, cost in expensive_components)
                ))
            
            # Check for redundant components
            redundant_count = self._count_redundant_components(board)
            if redundant_count > 0:
                results[ValidationCategory.GENERAL].append(OptimizationResult(
                    category=EnhancedValidationCategory.GENERAL,
                    optimization_category=OptimizationCategory.COST,
                    priority=ValidationPriority.LOW,
                    message=f"Board has {redundant_count} potentially redundant components",
                    severity="info",
                    current_value=redundant_count,
                    optimal_value=0,
                    improvement_potential=100.0 if redundant_count > 0 else 0.0
                ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in cost optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in cost optimization validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in cost optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in cost optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_audio_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate audio-specific optimization.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check audio signal paths
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net or not any(keyword in net.upper() for keyword in ["AUDIO", "IN", "OUT", "SIG"]):
                    continue
                
                # Check for proper audio routing
                width = track.GetWidth() / 1e6  # Convert to mm
                optimal_width = 0.15  # Optimal width for audio signals
                
                if width < optimal_width:
                    pos = track.GetStart()
                    results[ValidationCategory.GENERAL].append(OptimizationResult(
                        category=EnhancedValidationCategory.GENERAL,
                        optimization_category=OptimizationCategory.AUDIO,
                        priority=ValidationPriority.HIGH,
                        message=f"Audio signal {net} trace width ({width:.2f}mm) below optimal",
                        severity="warning",
                        location=(pos.x/1e6, pos.y/1e6),
                        net_name=net,
                        current_value=width,
                        optimal_value=optimal_width,
                        improvement_potential=((optimal_width - width) / optimal_width) * 100
                    ))
                
                # Check for crosstalk with other audio signals
                for other in board.GetTracks():
                    if other == track:
                        continue
                    
                    if other.GetType() != pcbnew.PCB_TRACE_T:
                        continue
                    
                    other_net = other.GetNetname()
                    if other_net and any(keyword in other_net.upper() for keyword in ["AUDIO", "IN", "OUT", "SIG"]):
                        # Calculate crosstalk
                        crosstalk = self._calculate_crosstalk(track, other)
                        if crosstalk > 0.1:  # Crosstalk above 10%
                            pos = track.GetStart()
                            results[ValidationCategory.GENERAL].append(OptimizationResult(
                                category=EnhancedValidationCategory.GENERAL,
                                optimization_category=OptimizationCategory.AUDIO,
                                priority=ValidationPriority.HIGH,
                                message=f"High crosstalk ({crosstalk:.1%}) between audio signals {net} and {other_net}",
                                severity="warning",
                                location=(pos.x/1e6, pos.y/1e6),
                                net_name=net,
                                current_value=crosstalk * 100,
                                optimal_value=10.0,
                                improvement_potential=((crosstalk - 0.1) / crosstalk) * 100,
                                crosstalk=crosstalk * 100
                            ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in audio optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in audio optimization validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in audio optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in audio optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_power_quality_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate power quality optimization opportunities.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Analyze power distribution
            power_nets = {}
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net or not any(keyword in net.upper() for keyword in ["PWR", "VCC", "VDD"]):
                    continue
                
                if net not in power_nets:
                    power_nets[net] = {
                        "length": 0,
                        "width": 0,
                        "decoupling_caps": 0,
                        "connections": 0
                    }
                
                # Accumulate track length
                start = track.GetStart()
                end = track.GetEnd()
                length = math.sqrt(
                    ((end.x - start.x) / 1e6) ** 2 +
                    ((end.y - start.y) / 1e6) ** 2
                )
                power_nets[net]["length"] += length
                
                # Track minimum width
                width = track.GetWidth() / 1e6  # Convert to mm
                if power_nets[net]["width"] == 0 or width < power_nets[net]["width"]:
                    power_nets[net]["width"] = width
            
            # Analyze decoupling and connections
            for footprint in board.GetFootprints():
                net = footprint.GetNetname()
                if not net or net not in power_nets:
                    continue
                
                if footprint.GetReference().startswith("C"):
                    power_nets[net]["decoupling_caps"] += 1
                else:
                    power_nets[net]["connections"] += 1
            
            # Validate power distribution
            for net, data in power_nets.items():
                # Check power trace width
                if data["length"] > 50 and data["width"] < 0.5:  # Long power traces should be wide
                    results[ValidationCategory.GENERAL].append(OptimizationResult(
                        category=EnhancedValidationCategory.GENERAL,
                        optimization_category=OptimizationCategory.POWER_QUALITY,
                        message=f"Power net {net} trace width ({data['width']:.2f}mm) may be too narrow for length {data['length']:.1f}mm",
                        severity="warning",
                        current_value=data["width"],
                        optimal_value=0.5,
                        improvement_potential=((0.5 - data["width"]) / 0.5) * 100
                    ))
                
                # Check decoupling
                if data["connections"] > 0 and data["decoupling_caps"] < data["connections"] / 2:
                    results[ValidationCategory.GENERAL].append(OptimizationResult(
                        category=EnhancedValidationCategory.GENERAL,
                        optimization_category=OptimizationCategory.POWER_QUALITY,
                        message=f"Power net {net} has insufficient decoupling ({data['decoupling_caps']} caps for {data['connections']} connections)",
                        severity="warning",
                        current_value=float(data["decoupling_caps"]),
                        optimal_value=float(data["connections"] / 2),
                        improvement_potential=((data["connections"] / 2 - data["decoupling_caps"]) / (data["connections"] / 2)) * 100
                    ))
        
        except Exception as e:
            self.logger.error(f"Error in power quality optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Error in power quality optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_thermal_management_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate thermal management optimization opportunities.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Analyze high-power components
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["U", "IC", "Q", "REG"]):
                    # Check for thermal relief
                    has_thermal_relief = False
                    for pad in footprint.Pads():
                        if pad.GetNetname() in ["GND", "PWR", "VCC", "VDD"]:
                            if pad.GetThermalSpokeWidth() > 0:
                                has_thermal_relief = True
                                break
                    
                    if not has_thermal_relief:
                        pos = footprint.GetPosition()
                        results[ValidationCategory.GENERAL].append(OptimizationResult(
                            category=EnhancedValidationCategory.GENERAL,
                            optimization_category=OptimizationCategory.THERMAL_MANAGEMENT,
                            message=f"High-power component {ref} lacks thermal relief",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=ref
                        ))
                    
                    # Check for nearby thermal vias
                    thermal_vias = 0
                    pos = footprint.GetPosition()
                    for via in board.GetVias():
                        if via.GetNetname() in ["GND", "PWR", "VCC", "VDD"]:
                            via_pos = via.GetPosition()
                            distance = math.sqrt(
                                ((pos.x - via_pos.x) / 1e6) ** 2 +
                                ((pos.y - via_pos.y) / 1e6) ** 2
                            )
                            if distance < 5.0:  # Within 5mm
                                thermal_vias += 1
                    
                    if thermal_vias < 4:  # At least 4 thermal vias
                        results[ValidationCategory.GENERAL].append(OptimizationResult(
                            category=EnhancedValidationCategory.GENERAL,
                            optimization_category=OptimizationCategory.THERMAL_MANAGEMENT,
                            message=f"High-power component {ref} has insufficient thermal vias ({thermal_vias})",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=ref,
                            current_value=float(thermal_vias),
                            optimal_value=4.0,
                            improvement_potential=((4.0 - thermal_vias) / 4.0) * 100
                        ))
            
            # Check for proper thermal zone coverage
            for zone in board.Zones():
                if zone.GetNetname() in ["GND", "PWR", "VCC", "VDD"]:
                    # Check for thermal relief usage
                    thermal_relief_count = 0
                    total_pads = 0
                    for pad in board.GetPads():
                        if pad.GetNetname() == zone.GetNetname():
                            total_pads += 1
                            if pad.GetThermalSpokeWidth() > 0:
                                thermal_relief_count += 1
                    
                    if total_pads > 0:
                        thermal_relief_ratio = thermal_relief_count / total_pads
                        if thermal_relief_ratio < 0.8:  # At least 80% thermal relief usage
                            results[ValidationCategory.GENERAL].append(OptimizationResult(
                                category=EnhancedValidationCategory.GENERAL,
                                optimization_category=OptimizationCategory.THERMAL_MANAGEMENT,
                                message=f"Power zone {zone.GetNetname()} has low thermal relief usage ({thermal_relief_ratio:.1%})",
                                severity="warning",
                                current_value=thermal_relief_ratio,
                                optimal_value=0.8,
                                improvement_potential=((0.8 - thermal_relief_ratio) / 0.8) * 100
                            ))
        
        except Exception as e:
            self.logger.error(f"Error in thermal management optimization validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Error in thermal management optimization validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _has_termination(self, track: pcbnew.PCB_TRACK, board: pcbnew.BOARD) -> bool:
        """Check if a track has proper termination.
        
        Args:
            track: Track to check
            board: KiCad board object
            
        Returns:
            True if track has termination, False otherwise
        """
        try:
            # Check for termination resistor
            net = track.GetNetname()
            if not net:
                return False
            
            # Look for termination resistor in the net
            for footprint in board.GetFootprints():
                if footprint.GetNetname() == net and "R" in footprint.GetReference():
                    # Check if resistor is at the end of the track
                    pos = footprint.GetPosition()
                    track_end = track.GetEnd()
                    distance = math.sqrt(
                        ((pos.x - track_end.x) / 1e6) ** 2 +
                        ((pos.y - track_end.y) / 1e6) ** 2
                    )
                    if distance < 5.0:  # Within 5mm of track end
                        return True
            
            return False
        
        except Exception:
            return False 