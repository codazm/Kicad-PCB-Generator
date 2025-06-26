"""Safety validation functionality for KiCad PCB Generator.

This module provides safety-focused validation features while maintaining compatibility
with KiCad 9 and avoiding duplication of native functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pcbnew
import math
from pcbnew import BOARD, PCB_TRACE_T, FOOTPRINT, ZONE, PCB_VIA_T

from .enhanced_validator import EnhancedValidator
from .enhanced_features import EnhancedFeaturesMixin
from .base_validator import ValidationCategory, ValidationResult

class SafetyCategory(Enum):
    """Categories for safety validation."""
    ELECTRICAL = "electrical"
    THERMAL = "thermal"
    MECHANICAL = "mechanical"
    COMPONENT = "component"
    AUDIO = "audio"
    EMI_EMC = "emi_emc"
    MODULAR = "modular"

@dataclass
class SafetyResult(ValidationResult):
    """Safety validation result with additional metadata."""
    safety_category: SafetyCategory
    current_value: Optional[float] = None
    safety_limit: Optional[float] = None
    safety_margin: Optional[float] = None

class SafetyValidator(EnhancedValidator):
    """Safety-focused validation functionality.
    
    This class adds safety-specific validation features while maintaining compatibility
    with KiCad 9 and leveraging native functionality where possible.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the safety validator.
        
        Args:
            logger: Optional logger instance
        """
        super().__init__(logger)
        
        # Define safety standards
        self._safety_standards = {
            "min_trace_width": 0.2,      # Minimum trace width (mm)
            "min_hole_size": 0.3,        # Minimum hole size (mm)
            "min_pad_size": 0.5,         # Minimum pad size (mm)
            "min_clearance": 0.2,        # Minimum clearance between traces (mm)
            "max_current_density": 20,   # Maximum current density (A/mm²)
            "max_temperature": 85,       # Maximum component temperature (°C)
            "min_ground_coverage": 0.7,  # Minimum ground plane coverage ratio
            "min_power_trace_width": 0.5 # Minimum power trace width (mm)
        }
        
        # Define audio-specific safety standards
        self._audio_standards = {
            "balanced_pair_spacing": 0.5,  # Minimum spacing between balanced pairs (mm)
            "ground_plane_coverage": 0.8,  # Minimum ground plane coverage for audio
            "cv_ground_separation": 1.0,   # Minimum separation between CV and ground (mm)
            "audio_ground_separation": 1.5, # Minimum separation between audio and ground (mm)
            "power_ground_separation": 2.0, # Minimum separation between power and ground (mm)
            "cv_audio_separation": 2.0,     # Minimum separation between CV and audio (mm)
            "cv_power_separation": 2.5,     # Minimum separation between CV and power (mm)
            "audio_power_separation": 3.0,  # Minimum separation between audio and power (mm)
            "cv_shielding_coverage": 0.8,   # Minimum CV shielding coverage ratio
            "audio_shielding_coverage": 0.9, # Minimum audio shielding coverage ratio
            "power_shielding_coverage": 0.7, # Minimum power shielding coverage ratio
            "cv_crosstalk_threshold": 0.1,   # Maximum CV crosstalk ratio
            "audio_crosstalk_threshold": 0.05 # Maximum audio crosstalk ratio
        }
        
        self._safety_cache: Dict[str, Any] = {}
        
        # Safety limits and margins
        self._voltage_clearance_limits = {
            "LV": 0.5,    # Low voltage (<50V): 0.5mm
            "MV": 1.0,    # Medium voltage (50-150V): 1.0mm
            "HV": 2.0,    # High voltage (150-300V): 2.0mm
            "EHV": 3.0    # Extra high voltage (>300V): 3.0mm
        }
        
        self._thermal_limits = {
            "IC": 85.0,   # IC junction temperature limit
            "PWR": 100.0, # Power component temperature limit
            "PASSIVE": 125.0  # Passive component temperature limit
        }
        
        self._derating_factors = {
            "R": 0.7,     # Resistor derating factor
            "C": 0.8,     # Capacitor derating factor
            "L": 0.7,     # Inductor derating factor
            "IC": 0.8,    # IC derating factor
            "PWR": 0.7    # Power component derating factor
        }
        
        # Modular synth-specific standards
        self._modular_standards = {
            "eurorack_width": 5.08,           # Standard Eurorack width (mm)
            "eurorack_height": 128.5,         # Standard Eurorack height (mm)
            "power_header_spacing": 2.54,     # Power header pin spacing (mm)
            "jack_spacing": 3.5,              # Standard jack spacing (mm)
            "pot_spacing": 7.5,               # Standard pot spacing (mm)
            "led_spacing": 5.0,               # LED spacing (mm)
            "cv_range": (-10.0, 10.0),        # Standard CV range (V)
            "audio_level": 10.0,              # Standard audio level (Vpp)
            "power_rail_clearance": 1.0,      # Minimum clearance to power rails (mm)
            "front_panel_clearance": 2.0,     # Minimum clearance to front panel (mm)
            "mounting_hole_diameter": 3.2,    # Standard mounting hole diameter (mm)
            "mounting_hole_clearance": 5.0,   # Minimum clearance around mounting holes (mm)
            "power_connector_clearance": 3.0,  # Minimum clearance around power connector (mm)
            "jack_clearance": 2.0,            # Minimum clearance around jacks (mm)
            "pot_clearance": 3.0,             # Minimum clearance around pots (mm)
            "led_clearance": 1.0,             # Minimum clearance around LEDs (mm)
            "cv_trace_width": 0.3,            # Minimum CV trace width (mm)
            "audio_trace_width": 0.4,         # Minimum audio trace width (mm)
            "power_trace_width": 0.6,         # Minimum power trace width (mm)
            "ground_trace_width": 0.5,        # Minimum ground trace width (mm)
            "cv_decoupling_distance": 3.0,    # Maximum distance to CV decoupling cap (mm)
            "audio_decoupling_distance": 5.0,  # Maximum distance to audio decoupling cap (mm)
            "power_decoupling_distance": 7.0,  # Maximum distance to power decoupling cap (mm)
            "cv_power_separation": 2.5,       # Minimum separation between CV and power (mm)
            "audio_power_separation": 3.0,    # Minimum separation between audio and power (mm)
            "cv_shielding_coverage": 0.8,     # Minimum CV shielding coverage ratio
            "audio_shielding_coverage": 0.9,  # Minimum audio shielding coverage ratio
            "power_shielding_coverage": 0.7,  # Minimum power shielding coverage ratio
            "cv_crosstalk_threshold": 0.1,    # Maximum CV crosstalk ratio
            "audio_crosstalk_threshold": 0.05 # Maximum audio crosstalk ratio
        }
    
    def validate_board(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate a PCB board with safety focus.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results by category
        """
        # Get enhanced validation results
        results = super().validate_board(board)
        
        # Add safety-specific validation results
        results.update(self._validate_electrical_safety(board))
        results.update(self._validate_thermal_safety(board))
        results.update(self._validate_mechanical_safety(board))
        results.update(self._validate_component_safety(board))
        results.update(self._validate_audio_safety(board))
        results.update(self._validate_emi_emc_safety(board))
        results.update(self._validate_modular_safety(board))
        
        return results
    
    def _validate_electrical_safety(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate electrical safety aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check high-voltage clearances using KiCad's native clearance checking
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net:
                    continue
                
                # Determine voltage level from net name
                voltage_level = self._get_voltage_level(net)
                if not voltage_level:
                    continue
                
                min_clearance = self._voltage_clearance_limits[voltage_level]
                
                # Use KiCad's native clearance checking
                clearance = board.GetDesignSettings().GetMinClearanceValue()
                if clearance < min_clearance:
                    pos = track.GetStart()
                    results[ValidationCategory.GENERAL].append(SafetyResult(
                        category=ValidationCategory.GENERAL,
                        safety_category=SafetyCategory.ELECTRICAL,
                        message=f"Clearance for {net} ({clearance}mm) below safety limit ({min_clearance}mm)",
                        severity="error",
                        location=(pos.x/1e6, pos.y/1e6),
                        net_name=net,
                        current_value=clearance,
                        safety_limit=min_clearance,
                        safety_margin=((min_clearance - clearance) / min_clearance) * 100
                    ))
            
            # Check power trace widths
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net or not any(keyword in net.upper() for keyword in ["PWR", "VCC", "VDD", "GND"]):
                    continue
                
                width = track.GetWidth() / 1e6  # Convert to mm
                min_width = self._safety_standards["min_power_trace_width"]
                
                if width < min_width:
                    pos = track.GetStart()
                    results[ValidationCategory.GENERAL].append(SafetyResult(
                        category=ValidationCategory.GENERAL,
                        safety_category=SafetyCategory.ELECTRICAL,
                        message=f"Power trace {net} width ({width:.2f}mm) below safety limit ({min_width}mm)",
                        severity="error",
                        location=(pos.x/1e6, pos.y/1e6),
                        net_name=net,
                        current_value=width,
                        safety_limit=min_width,
                        safety_margin=((min_width - width) / min_width) * 100
                    ))
            
            # Check decoupling capacitor placement
            for footprint in board.GetFootprints():
                if not footprint.GetReference().startswith("C"):
                    continue
                
                if any(keyword in footprint.GetValue().upper() for keyword in ["DECOUPL", "BYPASS"]):
                    # Count nearby decoupling caps
                    decoupling_caps = self._count_decoupling_caps(board, footprint)
                    if decoupling_caps < 2:  # Minimum 2 decoupling caps per IC
                        pos = footprint.GetPosition()
                        results[ValidationCategory.GENERAL].append(SafetyResult(
                            category=ValidationCategory.GENERAL,
                            safety_category=SafetyCategory.ELECTRICAL,
                            message=f"Insufficient decoupling for {footprint.GetReference()} ({decoupling_caps} caps)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=footprint.GetReference(),
                            current_value=float(decoupling_caps),
                            safety_limit=2.0,
                            safety_margin=((2.0 - decoupling_caps) / 2.0) * 100
                        ))
        
        except (pcbnew.PCB_IO_ERROR, pcbnew.PCB_PARSE_ERROR) as e:
            self.logger.error(f"PCB I/O error in electrical safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"PCB I/O error in electrical safety validation: {str(e)}",
                "error"
            ))
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error in electrical safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Data processing error in electrical safety validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in electrical safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in electrical safety validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_thermal_safety(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate thermal safety aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check high-power components
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if not ref:
                    continue
                
                # Determine component type and thermal limits
                component_type = self._get_component_type(ref)
                if not component_type:
                    continue
                
                thermal_limit = self._thermal_limits.get(component_type)
                if not thermal_limit:
                    continue
                
                # Check for thermal relief
                has_thermal_relief = False
                for pad in footprint.Pads():
                    if pad.GetNetname() in ["GND", "PWR", "VCC", "VDD"]:
                        if pad.GetThermalSpokeWidth() > 0:
                            has_thermal_relief = True
                            break
                
                if not has_thermal_relief:
                    pos = footprint.GetPosition()
                    results[ValidationCategory.GENERAL].append(SafetyResult(
                        category=ValidationCategory.GENERAL,
                        safety_category=SafetyCategory.THERMAL,
                        message=f"High-power component {ref} lacks thermal relief",
                        severity="error",
                        location=(pos.x/1e6, pos.y/1e6),
                        component_ref=ref,
                        safety_limit=1.0,  # 1.0mm minimum thermal relief
                        safety_margin=0.0
                    ))
                
                # Check component spacing for thermal management
                for other in board.GetFootprints():
                    if other == footprint:
                        continue
                    
                    if self._get_component_type(other.GetReference()) in ["IC", "PWR"]:
                        distance = self._calculate_component_distance(footprint, other)
                        if distance < 5.0:  # Minimum 5mm spacing between high-power components
                            pos = footprint.GetPosition()
                            results[ValidationCategory.GENERAL].append(SafetyResult(
                                category=ValidationCategory.GENERAL,
                                safety_category=SafetyCategory.THERMAL,
                                message=f"High-power components {ref} and {other.GetReference()} too close ({distance:.1f}mm)",
                                severity="warning",
                                location=(pos.x/1e6, pos.y/1e6),
                                component_ref=ref,
                                current_value=distance,
                                safety_limit=5.0,
                                safety_margin=((5.0 - distance) / 5.0) * 100
                            ))
        
        except (pcbnew.PCB_IO_ERROR, pcbnew.PCB_PARSE_ERROR) as e:
            self.logger.error(f"PCB I/O error in thermal safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"PCB I/O error in thermal safety validation: {str(e)}",
                "error"
            ))
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error in thermal safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Data processing error in thermal safety validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in thermal safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in thermal safety validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_mechanical_safety(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate mechanical safety aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check board edge clearance
            edge_clearance = board.GetDesignSettings().GetEdgeClearance()
            if edge_clearance < 0.5:  # Minimum 0.5mm edge clearance
                results[ValidationCategory.GENERAL].append(SafetyResult(
                    category=ValidationCategory.GENERAL,
                    safety_category=SafetyCategory.MECHANICAL,
                    message=f"Board edge clearance ({edge_clearance}mm) below safety limit (0.5mm)",
                    severity="warning",
                    current_value=edge_clearance,
                    safety_limit=0.5,
                    safety_margin=((0.5 - edge_clearance) / 0.5) * 100
                ))
            
            # Check mounting hole clearance
            for footprint in board.GetFootprints():
                if footprint.GetReference().startswith("MH"):  # Mounting hole
                    for pad in footprint.Pads():
                        clearance = pad.GetClearance()
                        if clearance < 1.0:  # Minimum 1.0mm mounting hole clearance
                            pos = footprint.GetPosition()
                            results[ValidationCategory.GENERAL].append(SafetyResult(
                                category=ValidationCategory.GENERAL,
                                safety_category=SafetyCategory.MECHANICAL,
                                message=f"Mounting hole {footprint.GetReference()} clearance ({clearance}mm) below safety limit",
                                severity="warning",
                                location=(pos.x/1e6, pos.y/1e6),
                                component_ref=footprint.GetReference(),
                                current_value=clearance,
                                safety_limit=1.0,
                                safety_margin=((1.0 - clearance) / 1.0) * 100
                            ))
        
        except (pcbnew.PCB_IO_ERROR, pcbnew.PCB_PARSE_ERROR) as e:
            self.logger.error(f"PCB I/O error in mechanical safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"PCB I/O error in mechanical safety validation: {str(e)}",
                "error"
            ))
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error in mechanical safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Data processing error in mechanical safety validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in mechanical safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in mechanical safety validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_component_safety(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate component safety aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check component derating
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if not ref:
                    continue
                
                component_type = self._get_component_type(ref)
                if not component_type:
                    continue
                
                derating_factor = self._derating_factors.get(component_type)
                if not derating_factor:
                    continue
                
                # Get component value and power rating
                value = self._get_component_value(footprint)
                if not value:
                    continue
                
                power_rating = self._get_power_rating(footprint)
                if not power_rating:
                    continue
                
                # Check derating
                if power_rating < value * derating_factor:
                    pos = footprint.GetPosition()
                    results[ValidationCategory.GENERAL].append(SafetyResult(
                        category=ValidationCategory.GENERAL,
                        safety_category=SafetyCategory.COMPONENT,
                        message=f"Component {ref} power rating ({power_rating}W) below safety margin",
                        severity="error",
                        location=(pos.x/1e6, pos.y/1e6),
                        component_ref=ref,
                        current_value=power_rating,
                        safety_limit=value * derating_factor,
                        safety_margin=((value * derating_factor - power_rating) / (value * derating_factor)) * 100
                    ))
        
        except (pcbnew.PCB_IO_ERROR, pcbnew.PCB_PARSE_ERROR) as e:
            self.logger.error(f"PCB I/O error in component safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"PCB I/O error in component safety validation: {str(e)}",
                "error"
            ))
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error in component safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Data processing error in component safety validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in component safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in component safety validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_audio_safety(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate audio-specific safety aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check balanced signal pairs
            balanced_pairs = self._find_balanced_pairs(board)
            for track1, track2 in balanced_pairs:
                distance = self._calculate_track_distance(track1, track2)
                min_spacing = self._audio_standards["balanced_pair_spacing"]
                
                if distance < min_spacing:
                    pos = track1.GetStart()
                    results[ValidationCategory.GENERAL].append(SafetyResult(
                        category=ValidationCategory.GENERAL,
                        safety_category=SafetyCategory.AUDIO,
                        message=f"Balanced pair spacing ({distance:.2f}mm) below audio standard ({min_spacing}mm)",
                        severity="warning",
                        location=(pos.x/1e6, pos.y/1e6),
                        current_value=distance,
                        safety_limit=min_spacing,
                        safety_margin=((min_spacing - distance) / min_spacing) * 100
                    ))
            
            # Check ground plane coverage
            board_area = self._calculate_board_area(board)
            ground_area = self._calculate_ground_area(board)
            ground_coverage = ground_area / board_area if board_area > 0 else 0.0
            
            min_coverage = self._audio_standards["ground_plane_coverage"]
            if ground_coverage < min_coverage:
                results[ValidationCategory.GENERAL].append(SafetyResult(
                    category=ValidationCategory.GENERAL,
                    safety_category=SafetyCategory.AUDIO,
                    message=f"Ground plane coverage ({ground_coverage:.1%}) below audio standard ({min_coverage:.1%})",
                    severity="warning",
                    current_value=ground_coverage,
                    safety_limit=min_coverage,
                    safety_margin=((min_coverage - ground_coverage) / min_coverage) * 100
                ))
            
            # Check CV and audio signal separation
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net:
                    continue
                
                # Check CV signal separation
                if "CV" in net.upper():
                    for other in board.GetTracks():
                        if other == track or other.GetType() != pcbnew.PCB_TRACE_T:
                            continue
                        
                        other_net = other.GetNetname()
                        if not other_net:
                            continue
                        
                        if "GND" in other_net.upper():
                            distance = self._calculate_track_distance(track, other)
                            min_separation = self._audio_standards["cv_ground_separation"]
                            
                            if distance < min_separation:
                                pos = track.GetStart()
                                results[ValidationCategory.GENERAL].append(SafetyResult(
                                    category=ValidationCategory.GENERAL,
                                    safety_category=SafetyCategory.AUDIO,
                                    message=f"CV signal {net} too close to ground ({distance:.2f}mm)",
                                    severity="warning",
                                    location=(pos.x/1e6, pos.y/1e6),
                                    net_name=net,
                                    current_value=distance,
                                    safety_limit=min_separation,
                                    safety_margin=((min_separation - distance) / min_separation) * 100
                                ))
                
                # Check audio signal separation
                elif any(keyword in net.upper() for keyword in ["AUDIO", "SIG", "IN", "OUT"]):
                    for other in board.GetTracks():
                        if other == track or other.GetType() != pcbnew.PCB_TRACE_T:
                            continue
                        
                        other_net = other.GetNetname()
                        if not other_net:
                            continue
                        
                        if "GND" in other_net.upper():
                            distance = self._calculate_track_distance(track, other)
                            min_separation = self._audio_standards["audio_ground_separation"]
                            
                            if distance < min_separation:
                                pos = track.GetStart()
                                results[ValidationCategory.GENERAL].append(SafetyResult(
                                    category=ValidationCategory.GENERAL,
                                    safety_category=SafetyCategory.AUDIO,
                                    message=f"Audio signal {net} too close to ground ({distance:.2f}mm)",
                                    severity="warning",
                                    location=(pos.x/1e6, pos.y/1e6),
                                    net_name=net,
                                    current_value=distance,
                                    safety_limit=min_separation,
                                    safety_margin=((min_separation - distance) / min_separation) * 100
                                ))
            
            # Check decoupling capacitor placement for audio components
            for footprint in board.GetFootprints():
                if not footprint.GetReference().startswith("C"):
                    continue
                
                if any(keyword in footprint.GetValue().upper() for keyword in ["DECOUPL", "BYPASS"]):
                    # Count nearby decoupling caps
                    decoupling_caps = self._count_decoupling_caps(board, footprint)
                    if decoupling_caps < 2:  # Minimum 2 decoupling caps per IC
                        pos = footprint.GetPosition()
                        results[ValidationCategory.GENERAL].append(SafetyResult(
                            category=ValidationCategory.GENERAL,
                            safety_category=SafetyCategory.AUDIO,
                            message=f"Insufficient decoupling for {footprint.GetReference()} ({decoupling_caps} caps)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=footprint.GetReference(),
                            current_value=float(decoupling_caps),
                            safety_limit=2.0,
                            safety_margin=((2.0 - decoupling_caps) / 2.0) * 100
                        ))
        
        except (pcbnew.PCB_IO_ERROR, pcbnew.PCB_PARSE_ERROR) as e:
            self.logger.error(f"PCB I/O error in audio safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"PCB I/O error in audio safety validation: {str(e)}",
                "error"
            ))
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error in audio safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Data processing error in audio safety validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in audio safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in audio safety validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_emi_emc_safety(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate EMI/EMC safety aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check ground plane stitching
            ground_zones = [zone for zone in board.Zones() if zone.GetNetname() == "GND"]
            if len(ground_zones) > 1:
                stitching_vias = [via for via in board.GetVias() if via.GetNetname() == "GND"]
                
                # Check via spacing
                for i, via1 in enumerate(stitching_vias):
                    for via2 in stitching_vias[i+1:]:
                        pos1, pos2 = via1.GetPosition(), via2.GetPosition()
                        distance = math.sqrt(
                            ((pos1.x - pos2.x) / 1e6) ** 2 +
                            ((pos1.y - pos2.y) / 1e6) ** 2
                        )
                        
                        if distance > self._safety_standards["ground_stitching_distance"]:
                            results[ValidationCategory.GENERAL].append(SafetyResult(
                                category=ValidationCategory.GENERAL,
                                safety_category=SafetyCategory.EMI_EMC,
                                message=f"Ground stitching via spacing ({distance:.2f}mm) exceeds limit",
                                severity="warning",
                                location=(pos1.x/1e6, pos1.y/1e6),
                                current_value=distance,
                                safety_limit=self._safety_standards["ground_stitching_distance"],
                                safety_margin=((self._safety_standards["ground_stitching_distance"] - distance) / 
                                             self._safety_standards["ground_stitching_distance"]) * 100
                            ))
            
            # Check RF trace shielding
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net or not any(keyword in net.upper() for keyword in ["RF", "ANT", "WIFI", "BT"]):
                    continue
                
                # Check for ground plane shielding
                layer = track.GetLayer()
                has_shielding = False
                shielding_coverage = 0.0
                
                for zone in board.Zones():
                    if zone.GetNetname() == "GND":
                        if zone.IsOnLayer(layer - 1) or zone.IsOnLayer(layer + 1):
                            has_shielding = True
                            # Calculate shielding coverage
                            shielding_coverage = self._calculate_shielding_coverage(track, zone)
                
                if not has_shielding or shielding_coverage < self._safety_standards["shielding_coverage"]:
                    pos = track.GetStart()
                    results[ValidationCategory.GENERAL].append(SafetyResult(
                        category=ValidationCategory.GENERAL,
                        safety_category=SafetyCategory.EMI_EMC,
                        message=f"RF signal {net} has insufficient shielding ({shielding_coverage:.2%})",
                        severity="warning",
                        location=(pos.x/1e6, pos.y/1e6),
                        net_name=net,
                        current_value=shielding_coverage,
                        safety_limit=self._safety_standards["shielding_coverage"],
                        safety_margin=((self._safety_standards["shielding_coverage"] - shielding_coverage) / 
                                     self._safety_standards["shielding_coverage"]) * 100,
                        shielding_effectiveness=shielding_coverage
                    ))
            
            # Check clock trace isolation
            for track in board.GetTracks():
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net = track.GetNetname()
                if not net or not any(keyword in net.upper() for keyword in ["CLK", "OSC", "XTAL"]):
                    continue
                
                # Check distance to other traces
                for other in board.GetTracks():
                    if other == track or other.GetType() != pcbnew.PCB_TRACE_T:
                        continue
                    
                    distance = self._calculate_track_distance(track, other)
                    if distance < self._safety_standards["clock_trace_spacing"]:
                        pos = track.GetStart()
                        results[ValidationCategory.GENERAL].append(SafetyResult(
                            category=ValidationCategory.GENERAL,
                            safety_category=SafetyCategory.EMI_EMC,
                            message=f"Clock trace {net} too close to {other.GetNetname()} ({distance:.2f}mm)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            net_name=net,
                            current_value=distance,
                            safety_limit=self._safety_standards["clock_trace_spacing"],
                            safety_margin=((self._safety_standards["clock_trace_spacing"] - distance) / 
                                         self._safety_standards["clock_trace_spacing"]) * 100,
                            crosstalk=self._calculate_crosstalk(track, other)
                        ))
            
            # Check filter capacitor placement
            for footprint in board.GetFootprints():
                if not footprint.GetReference().startswith("C"):
                    continue
                
                if any(keyword in footprint.GetValue().upper() for keyword in ["FILTER", "EMI"]):
                    pos = footprint.GetPosition()
                    # Check distance to power pins
                    min_distance = float('inf')
                    for other in board.GetFootprints():
                        if any(keyword in other.GetReference().upper() for keyword in ["U", "IC"]):
                            distance = self._calculate_component_distance(footprint, other)
                            min_distance = min(min_distance, distance)
                    
                    if min_distance > self._safety_standards["filter_cap_distance"]:
                        results[ValidationCategory.GENERAL].append(SafetyResult(
                            category=ValidationCategory.GENERAL,
                            safety_category=SafetyCategory.EMI_EMC,
                            message=f"Filter capacitor {footprint.GetReference()} too far from IC ({min_distance:.2f}mm)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=footprint.GetReference(),
                            current_value=min_distance,
                            safety_limit=self._safety_standards["filter_cap_distance"],
                            safety_margin=((self._safety_standards["filter_cap_distance"] - min_distance) / 
                                         self._safety_standards["filter_cap_distance"]) * 100
                        ))
        
        except (pcbnew.PCB_IO_ERROR, pcbnew.PCB_PARSE_ERROR) as e:
            self.logger.error(f"PCB I/O error in EMI/EMC safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"PCB I/O error in EMI/EMC safety validation: {str(e)}",
                "error"
            ))
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error in EMI/EMC safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Data processing error in EMI/EMC safety validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in EMI/EMC safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in EMI/EMC safety validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _validate_modular_safety(self, board: pcbnew.BOARD) -> Dict[ValidationCategory, List[ValidationResult]]:
        """Validate modular synth-specific safety aspects.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of validation results
        """
        results = {ValidationCategory.GENERAL: []}
        
        try:
            # Check Eurorack dimensions
            box = board.GetBoardEdgesBoundingBox()
            width = box.GetWidth() / 1e6
            height = box.GetHeight() / 1e6
            
            if width != self._modular_standards["eurorack_width"]:
                results[ValidationCategory.GENERAL].append(SafetyResult(
                    category=ValidationCategory.GENERAL,
                    safety_category=SafetyCategory.MODULAR,
                    message=f"Module width ({width:.2f}mm) does not match Eurorack standard",
                    severity="error",
                    current_value=width,
                    safety_limit=self._modular_standards["eurorack_width"],
                    safety_margin=((self._modular_standards["eurorack_width"] - width) / 
                                 self._modular_standards["eurorack_width"]) * 100
                ))
            
            if height > self._modular_standards["eurorack_height"]:
                results[ValidationCategory.GENERAL].append(SafetyResult(
                    category=ValidationCategory.GENERAL,
                    safety_category=SafetyCategory.MODULAR,
                    message=f"Module height ({height:.2f}mm) exceeds Eurorack standard",
                    severity="error",
                    current_value=height,
                    safety_limit=self._modular_standards["eurorack_height"],
                    safety_margin=((self._modular_standards["eurorack_height"] - height) / 
                                 self._modular_standards["eurorack_height"]) * 100
                ))
            
            # Check power connector placement
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if not ref or not any(keyword in ref.upper() for keyword in ["PWR", "CONN", "HEADER"]):
                    continue
                
                # Check distance to board edge
                pos = footprint.GetPosition()
                edge_distance = min(
                    pos.x/1e6,  # Distance to left edge
                    (board.GetBoardEdgesBoundingBox().GetWidth() - pos.x)/1e6,  # Distance to right edge
                    pos.y/1e6,  # Distance to top edge
                    (board.GetBoardEdgesBoundingBox().GetHeight() - pos.y)/1e6   # Distance to bottom edge
                )
                
                if edge_distance < self._modular_standards["power_connector_clearance"]:
                    results[ValidationCategory.GENERAL].append(SafetyResult(
                        category=ValidationCategory.GENERAL,
                        safety_category=SafetyCategory.MODULAR,
                        message=f"Power connector {ref} too close to board edge ({edge_distance:.2f}mm)",
                        severity="warning",
                        location=(pos.x/1e6, pos.y/1e6),
                        component_ref=ref,
                        current_value=edge_distance,
                        safety_limit=self._modular_standards["power_connector_clearance"],
                        safety_margin=((self._modular_standards["power_connector_clearance"] - edge_distance) / 
                                     self._modular_standards["power_connector_clearance"]) * 100
                    ))
            
            # Check jack spacing
            jacks = [f for f in board.GetFootprints() if "JACK" in f.GetReference().upper()]
            for i, jack1 in enumerate(jacks):
                for jack2 in jacks[i+1:]:
                    distance = self._calculate_component_distance(jack1, jack2)
                    if distance < self._modular_standards["jack_spacing"]:
                        pos = jack1.GetPosition()
                        results[ValidationCategory.GENERAL].append(SafetyResult(
                            category=ValidationCategory.GENERAL,
                            safety_category=SafetyCategory.MODULAR,
                            message=f"Jacks {jack1.GetReference()} and {jack2.GetReference()} too close ({distance:.2f}mm)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=jack1.GetReference(),
                            current_value=distance,
                            safety_limit=self._modular_standards["jack_spacing"],
                            safety_margin=((self._modular_standards["jack_spacing"] - distance) / 
                                         self._modular_standards["jack_spacing"]) * 100
                        ))
            
            # Check pot spacing
            pots = [f for f in board.GetFootprints() if "POT" in f.GetReference().upper()]
            for i, pot1 in enumerate(pots):
                for pot2 in pots[i+1:]:
                    distance = self._calculate_component_distance(pot1, pot2)
                    if distance < self._modular_standards["pot_spacing"]:
                        pos = pot1.GetPosition()
                        results[ValidationCategory.GENERAL].append(SafetyResult(
                            category=ValidationCategory.GENERAL,
                            safety_category=SafetyCategory.MODULAR,
                            message=f"Pots {pot1.GetReference()} and {pot2.GetReference()} too close ({distance:.2f}mm)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=pot1.GetReference(),
                            current_value=distance,
                            safety_limit=self._modular_standards["pot_spacing"],
                            safety_margin=((self._modular_standards["pot_spacing"] - distance) / 
                                         self._modular_standards["pot_spacing"]) * 100
                        ))
            
            # Check LED spacing
            leds = [f for f in board.GetFootprints() if "LED" in f.GetReference().upper()]
            for i, led1 in enumerate(leds):
                for led2 in leds[i+1:]:
                    distance = self._calculate_component_distance(led1, led2)
                    if distance < self._modular_standards["led_spacing"]:
                        pos = led1.GetPosition()
                        results[ValidationCategory.GENERAL].append(SafetyResult(
                            category=ValidationCategory.GENERAL,
                            safety_category=SafetyCategory.MODULAR,
                            message=f"LEDs {led1.GetReference()} and {led2.GetReference()} too close ({distance:.2f}mm)",
                            severity="warning",
                            location=(pos.x/1e6, pos.y/1e6),
                            component_ref=ref,
                            current_value=distance,
                            safety_limit=self._modular_standards["led_spacing"],
                            safety_margin=((self._modular_standards["led_spacing"] - distance) / 
                                         self._modular_standards["led_spacing"]) * 100
                        ))
        
        except (pcbnew.PCB_IO_ERROR, pcbnew.PCB_PARSE_ERROR) as e:
            self.logger.error(f"PCB I/O error in modular safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"PCB I/O error in modular safety validation: {str(e)}",
                "error"
            ))
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error in modular safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Data processing error in modular safety validation: {str(e)}",
                "error"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error in modular safety validation: {str(e)}")
            results[ValidationCategory.GENERAL].append(ValidationResult(
                ValidationCategory.GENERAL,
                f"Unexpected error in modular safety validation: {str(e)}",
                "error"
            ))
        
        return results
    
    def _find_balanced_pairs(self, board: pcbnew.BOARD) -> List[Tuple[pcbnew.PCB_TRACK, pcbnew.PCB_TRACK]]:
        """Find balanced signal pairs.
        
        Args:
            board: KiCad board object
            
        Returns:
            List of balanced signal pairs
        """
        pairs = []
        tracks = [t for t in board.GetTracks() if t.GetType() == pcbnew.PCB_TRACE_T]
        
        for i, track1 in enumerate(tracks):
            net1 = track1.GetNetname()
            if not net1:
                continue
            
            # Look for matching pair
            for track2 in tracks[i+1:]:
                net2 = track2.GetNetname()
                if not net2:
                    continue
                
                # Check for balanced pair naming convention
                if (net1.endswith("+") and net2.endswith("-") and
                    net1[:-1] == net2[:-1]):
                    pairs.append((track1, track2))
        
        return pairs
    
    def _calculate_board_area(self, board: pcbnew.BOARD) -> float:
        """Calculate total board area.
        
        Args:
            board: KiCad board object
            
        Returns:
            Board area in mm²
        """
        box = board.GetBoardEdgesBoundingBox()
        return (box.GetWidth() / 1e6) * (box.GetHeight() / 1e6)
    
    def _calculate_ground_area(self, board: pcbnew.BOARD) -> float:
        """Calculate total ground plane area.
        
        Args:
            board: KiCad board object
            
        Returns:
            Ground plane area in mm²
        """
        total_area = 0.0
        for zone in board.Zones():
            if zone.GetNetname() == "GND":
                # Approximate area using bounding box
                box = zone.GetBoundingBox()
                total_area += (box.GetWidth() / 1e6) * (box.GetHeight() / 1e6)
        return total_area
    
    def _calculate_track_distance(self, track1: pcbnew.PCB_TRACK, track2: pcbnew.PCB_TRACK) -> float:
        """Calculate minimum distance between tracks.
        
        Args:
            track1: First track
            track2: Second track
            
        Returns:
            Minimum distance in mm
        """
        pos1 = track1.GetStart()
        pos2 = track2.GetStart()
        
        return math.sqrt(
            ((pos1.x - pos2.x) / 1e6) ** 2 +
            ((pos1.y - pos2.y) / 1e6) ** 2
        )
    
    def _calculate_shielding_coverage(self, track: pcbnew.PCB_TRACK, zone: pcbnew.ZONE) -> float:
        """Calculate shielding coverage for a track.
        
        Args:
            track: Track object
            zone: Ground zone object
            
        Returns:
            Shielding coverage ratio (0.0 to 1.0)
        """
        # This is a simplified calculation
        # In practice, you would need to consider the actual track path and zone shape
        track_pos = track.GetStart()
        zone_box = zone.GetBoundingBox()
        
        # Check if track is within zone bounds
        if (zone_box.GetLeft() <= track_pos.x <= zone_box.GetRight() and
            zone_box.GetTop() <= track_pos.y <= zone_box.GetBottom()):
            return 1.0
        
        return 0.0
    
    def _calculate_crosstalk(self, track1: pcbnew.PCB_TRACK, track2: pcbnew.PCB_TRACK) -> float:
        """Calculate crosstalk between tracks.
        
        Args:
            track1: First track
            track2: Second track
            
        Returns:
            Crosstalk ratio (0.0 to 1.0)
        """
        # This is a simplified calculation
        # In practice, you would need to consider:
        # - Track length
        # - Parallel length
        # - Dielectric properties
        # - Signal rise time
        distance = self._calculate_track_distance(track1, track2)
        return 1.0 / (1.0 + distance)  # Simplified inverse distance model
    
    def _get_voltage_level(self, net_name: str) -> Optional[str]:
        """Get voltage level from net name.
        
        Args:
            net_name: Net name
            
        Returns:
            Voltage level or None if not found
        """
        net_name = net_name.upper()
        if any(keyword in net_name for keyword in ["HV", "AC", "MAINS"]):
            return "HV"
        elif any(keyword in net_name for keyword in ["MV", "PWR", "VCC", "VDD"]):
            return "MV"
        elif any(keyword in net_name for keyword in ["LV", "SIG", "AUDIO"]):
            return "LV"
        return None
    
    def _get_component_type(self, ref: str) -> Optional[str]:
        """Get component type from reference.
        
        Args:
            ref: Component reference
            
        Returns:
            Component type or None if not found
        """
        ref = ref.upper()
        if ref.startswith("R"):
            return "R"
        elif ref.startswith("C"):
            return "C"
        elif ref.startswith("L"):
            return "L"
        elif ref.startswith("U"):
            return "IC"
        elif ref.startswith("Q"):
            return "PWR"
        return None
    
    def _get_component_value(self, footprint: pcbnew.FOOTPRINT) -> Optional[float]:
        """Get component value.
        
        Args:
            footprint: Component footprint
            
        Returns:
            Component value or None if not found
        """
        try:
            value = footprint.GetValue()
            if not value:
                return None
            
            # Extract numeric value
            value = value.replace("R", "").replace("k", "000").replace("M", "000000")
            value = value.replace("pF", "").replace("nF", "000").replace("uF", "000000")
            value = value.replace("uH", "").replace("mH", "000").replace("H", "000000")
            
            return float(value)
        except Exception:
            return None
    
    def _get_power_rating(self, footprint: pcbnew.FOOTPRINT) -> Optional[float]:
        """Get component power rating.
        
        Args:
            footprint: Component footprint
            
        Returns:
            Power rating in watts or None if not found
        """
        try:
            value = self._get_component_value(footprint)
            if value is None:
                return None
            
            ref = footprint.GetReference()
            if ref.startswith("R"):
                return value * 0.1  # Assume 0.1W per ohm
            elif ref.startswith("C"):
                return value * 0.01  # Assume 0.01W per farad
            elif ref.startswith("L"):
                return value * 0.001  # Assume 0.001W per henry
            return None
        except Exception:
            return None
    
    def _calculate_component_distance(self, comp1: pcbnew.FOOTPRINT, comp2: pcbnew.FOOTPRINT) -> float:
        """Calculate distance between components.
        
        Args:
            comp1: First component
            comp2: Second component
            
        Returns:
            Distance in millimeters
        """
        pos1 = comp1.GetPosition()
        pos2 = comp2.GetPosition()
        
        return math.sqrt(
            ((pos1.x - pos2.x) / 1e6) ** 2 +
            ((pos1.y - pos2.y) / 1e6) ** 2
        )
    
    def _count_decoupling_caps(self, board: pcbnew.BOARD, target: Any) -> int:
        """Count decoupling capacitors near target.
        
        Args:
            board: KiCad board object
            target: Target object (zone or track)
            
        Returns:
            Number of decoupling capacitors
        """
        count = 0
        
        if isinstance(target, pcbnew.ZONE):
            pos = target.GetPosition()
        elif isinstance(target, pcbnew.PCB_TRACK):
            pos = target.GetStart()
        else:
            return 0
        
        for footprint in board.GetFootprints():
            if not footprint.GetReference().startswith("C"):
                continue
            
            if footprint.GetNetname() == "GND":
                other_pos = footprint.GetPosition()
                distance = math.sqrt(
                    ((pos.x - other_pos.x) / 1e6) ** 2 +
                    ((pos.y - other_pos.y) / 1e6) ** 2
                )
                
                if distance < 5.0:  # Within 5mm
                    count += 1
        
        return count 