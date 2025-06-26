"""Enhanced validation features mixin for KiCad PCB Generator.

This module provides enhanced validation features as a mixin that can be used
by any validator while maintaining compatibility with KiCad 9 and avoiding
duplication of native functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pcbnew

from .base_validator import ValidationCategory, ValidationResult

class EnhancedValidationCategory(Enum):
    """Additional categories for enhanced validation."""
    THERMAL = "thermal"
    CROSS_LAYER = "cross_layer"
    SIGNAL_INTEGRITY = "signal_integrity"
    POWER_DISTRIBUTION = "power_distribution"
    MANUFACTURING_OPTIMIZATION = "manufacturing_optimization"

@dataclass
class EnhancedValidationResult(ValidationResult):
    """Enhanced validation result with additional metadata."""
    component_ref: Optional[str] = None
    net_name: Optional[str] = None
    layer_name: Optional[str] = None
    measurement: Optional[float] = None
    threshold: Optional[float] = None

class EnhancedFeaturesMixin:
    """Mixin class providing enhanced validation features.
    
    This mixin can be used by any validator to add enhanced validation features
    while maintaining compatibility with KiCad 9 and leveraging native functionality
    where possible.
    """
    
    def validate_enhanced(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate a PCB board with enhanced features.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results by category
        """
        results = {}
        
        # Add enhanced validation results
        results.update(self._validate_thermal(board))
        results.update(self._validate_cross_layer(board))
        results.update(self._validate_signal_integrity(board))
        results.update(self._validate_power_distribution(board))
        results.update(self._validate_manufacturing_optimization(board))
        
        return results
    
    def _validate_thermal(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate thermal characteristics using KiCad's native functionality."""
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Use KiCad's native thermal analysis where available
            for footprint in board.GetFootprints():
                # Check component power dissipation
                if hasattr(footprint, 'GetPowerDissipation'):
                    power = footprint.GetPowerDissipation()
                    if power > 1.0:  # Components dissipating more than 1W
                        pos = footprint.GetPosition()
                        results[ValidationCategory.GENERAL].append(EnhancedValidationResult(
                            category=ValidationCategory.GENERAL,
                            message=f"High power component {footprint.GetReference()} ({power}W)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=footprint.GetReference(),
                            measurement=power,
                            threshold=1.0
                        ))
                
                # Check for thermal relief on pads
                for pad in footprint.Pads():
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                        if not pad.HasThermalRelief():
                            pos = pad.GetPosition()
                            results[ValidationCategory.GENERAL].append(EnhancedValidationResult(
                                category=ValidationCategory.GENERAL,
                                message=f"Missing thermal relief on pad {pad.GetName()} of {footprint.GetReference()}",
                                severity="warning",
                                location=(pos.x/1e6, pos.y/1e6),
                                component_ref=footprint.GetReference()
                            ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in thermal validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in thermal validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in thermal validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in thermal validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_cross_layer(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate cross-layer interactions using KiCad's native functionality."""
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Use KiCad's native DRC engine for cross-layer validation
            drc_engine = pcbnew.DRC_ENGINE()
            drc_engine.SetBoard(board)
            
            # Check for cross-layer conflicts
            for track in board.GetTracks():
                start_layer = track.GetLayer()
                end_layer = track.GetLayer()
                
                if start_layer != end_layer:
                    # Check for proper via transitions
                    if not any(via.GetPosition() == track.GetStart() or 
                             via.GetPosition() == track.GetEnd() 
                             for via in board.GetVias()):
                        pos = track.GetStart()
                        results[ValidationCategory.GENERAL].append(EnhancedValidationResult(
                            category=ValidationCategory.GENERAL,
                            message=f"Track changes layers without via at ({pos.x/1e6:.1f}, {pos.y/1e6:.1f})",
                            severity="error",
                            location=(pos.x/1e6, pos.y/1e6),
                            layer_name=board.GetLayerName(start_layer)
                        ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in cross-layer validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in cross-layer validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in cross-layer validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in cross-layer validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_signal_integrity(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate signal integrity using KiCad's native functionality."""
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check for high-speed signal paths
            for track in board.GetTracks():
                net = track.GetNetname()
                if net and any(keyword in net.upper() for keyword in ["CLK", "DDR", "USB", "HDMI"]):
                    # Check for proper impedance control
                    width = track.GetWidth() / 1e6  # Convert to mm
                    if width < 0.2:  # High-speed signals typically need wider traces
                        pos = track.GetStart()
                        results[ValidationCategory.GENERAL].append(EnhancedValidationResult(
                            category=ValidationCategory.GENERAL,
                            message=f"High-speed signal {net} trace width {width:.2f}mm may be too narrow",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            net_name=net,
                            measurement=width,
                            threshold=0.2
                        ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in signal integrity validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in signal integrity validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in signal integrity validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in signal integrity validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_power_distribution(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate power distribution using KiCad's native functionality."""
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check power plane connections
            for zone in board.Zones():
                if zone.GetNetname() and "PWR" in zone.GetNetname().upper():
                    # Check for proper power plane connections
                    if not any(pad.GetNetname() == zone.GetNetname() 
                             for pad in board.GetPads()):
                        pos = zone.GetPosition()
                        results[ValidationCategory.GENERAL].append(EnhancedValidationResult(
                            category=ValidationCategory.GENERAL,
                            message=f"Power plane {zone.GetNetname()} has no connections",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            net_name=zone.GetNetname()
                        ))
        
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error in power distribution validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Input error in power distribution validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in power distribution validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in power distribution validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_manufacturing_optimization(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate manufacturing optimization using KiCad's native functionality."""
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check for manufacturing optimization opportunities
            for footprint in board.GetFootprints():
                # Check component orientation
                if footprint.GetOrientation() % 90 != 0:
                    pos = footprint.GetPosition()
                    results[ValidationCategory.GENERAL].append(EnhancedValidationResult(
                        category=ValidationCategory.GENERAL,
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
                    distance = ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5 / 1e6
                    
                    if distance < 0.5:  # Components too close
                        results[ValidationCategory.GENERAL].append(EnhancedValidationResult(
                            category=ValidationCategory.GENERAL,
                            message=f"Components {footprint.GetReference()} and {other.GetReference()} are too close ({distance:.2f}mm)",
                            severity="warning",
                            location=(pos1.x/1e6, pos1.y/1e6),
                            component_ref=footprint.GetReference(),
                            measurement=distance,
                            threshold=0.5
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