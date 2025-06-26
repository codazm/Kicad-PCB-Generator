"""Modular Synthesizer-Specific Layout and Routing Rules for Audio PCBs."""
import logging
from typing import Any, List, Dict, Optional
import pcbnew

logger = logging.getLogger(__name__)

# Eurorack and modular synth standards
EURORACK_WIDTH_MM = 5.08  # HP unit
EURORACK_MAX_HEIGHT_MM = 128.5
POWER_HEADER_PINOUT = ["-12V", "GND", "GND", "+5V", "+12V"]
POWER_HEADER_FOOTPRINT = "PinHeader_2x5_P2.54mm_Vertical"

# Minimum trace widths (mm)
CV_TRACE_WIDTH = 0.3
AUDIO_TRACE_WIDTH = 0.4
POWER_TRACE_WIDTH = 0.6

# Standard front panel component spacing (mm)
JACK_SPACING = 3.5
POT_SPACING = 7.5
LED_SPACING = 5.0

class ModularSynthLayoutRules:
    """Encapsulates modular synth-specific layout and routing rules."""
    def __init__(self):
        self.width_mm = EURORACK_WIDTH_MM
        self.max_height_mm = EURORACK_MAX_HEIGHT_MM
        self.power_header_footprint = POWER_HEADER_FOOTPRINT
        self.power_header_pinout = POWER_HEADER_PINOUT
        self.cv_trace_width = CV_TRACE_WIDTH
        self.audio_trace_width = AUDIO_TRACE_WIDTH
        self.power_trace_width = POWER_TRACE_WIDTH
        self.jack_spacing = JACK_SPACING
        self.pot_spacing = POT_SPACING
        self.led_spacing = LED_SPACING

    def enforce_board_dimensions(self, board: pcbnew.BOARD) -> List[str]:
        """Ensure board dimensions comply with Eurorack standards.
        
        Args:
            board: KiCad board object
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        try:
            bbox = board.GetBoardEdgesBoundingBox()
            width = bbox.GetWidth() / 1e6  # mm
            height = bbox.GetHeight() / 1e6  # mm
            
            # Check height
            if height > self.max_height_mm:
                errors.append(f"Board height {height}mm exceeds Eurorack max {self.max_height_mm}mm")
            
            # Check width is multiple of HP
            hp_units = width / self.width_mm
            if not hp_units.is_integer():
                errors.append(f"Board width {width}mm is not a multiple of HP ({self.width_mm}mm)")
            
            # Check minimum width (2HP)
            if width < 2 * self.width_mm:
                errors.append(f"Board width {width}mm is less than minimum 2HP ({2 * self.width_mm}mm)")
            
            # Check maximum width (84HP)
            if width > 84 * self.width_mm:
                errors.append(f"Board width {width}mm exceeds maximum 84HP ({84 * self.width_mm}mm)")
            
            return errors
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error enforcing board dimensions: {str(e)}")
            return [f"Board data error: {str(e)}"]
        except Exception as e:
            logger.error(f"Unexpected error enforcing board dimensions: {str(e)}")
            return [f"Unexpected error: {str(e)}"]

    def validate_component_spacing(self, board: pcbnew.BOARD) -> List[str]:
        """Validate component spacing according to Eurorack standards.
        
        Args:
            board: KiCad board object
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        try:
            # Get all components
            components = board.GetFootprints()
            
            # Group components by type
            jacks = []
            pots = []
            leds = []
            
            for comp in components:
                ref = comp.GetReference()
                if "J" in ref:  # Jack
                    jacks.append(comp)
                elif "P" in ref:  # Potentiometer
                    pots.append(comp)
                elif "D" in ref:  # LED
                    leds.append(comp)
            
            # Check jack spacing
            for i, jack1 in enumerate(jacks):
                for jack2 in jacks[i+1:]:
                    pos1 = jack1.GetPosition()
                    pos2 = jack2.GetPosition()
                    distance = ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5 / 1e6  # mm
                    if distance < self.jack_spacing:
                        errors.append(f"Jack spacing {distance:.1f}mm is less than minimum {self.jack_spacing}mm")
            
            # Check pot spacing
            for i, pot1 in enumerate(pots):
                for pot2 in pots[i+1:]:
                    pos1 = pot1.GetPosition()
                    pos2 = pot2.GetPosition()
                    distance = ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5 / 1e6  # mm
                    if distance < self.pot_spacing:
                        errors.append(f"Pot spacing {distance:.1f}mm is less than minimum {self.pot_spacing}mm")
            
            # Check LED spacing
            for i, led1 in enumerate(leds):
                for led2 in leds[i+1:]:
                    pos1 = led1.GetPosition()
                    pos2 = led2.GetPosition()
                    distance = ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5 / 1e6  # mm
                    if distance < self.led_spacing:
                        errors.append(f"LED spacing {distance:.1f}mm is less than minimum {self.led_spacing}mm")
            
            return errors
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error validating component spacing: {str(e)}")
            return [f"Board data error: {str(e)}"]
        except Exception as e:
            logger.error(f"Unexpected error validating component spacing: {str(e)}")
            return [f"Unexpected error: {str(e)}"]

    def validate_power_connector(self, board: pcbnew.BOARD) -> List[str]:
        """Validate power connector placement and pinout.
        
        Args:
            board: KiCad board object
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        try:
            # Find power connector
            power_connector = None
            for comp in board.GetFootprints():
                if comp.GetReference().startswith("J") and comp.GetValue() == "POWER":
                    power_connector = comp
                    break
            
            if not power_connector:
                errors.append("Power connector not found")
                return errors
            
            # Check footprint
            if power_connector.GetFPID().GetFootprintName() != self.power_header_footprint:
                errors.append(f"Power connector footprint should be {self.power_header_footprint}")
            
            # Check pinout
            for i, pin in enumerate(power_connector.Pads()):
                net = pin.GetNetname()
                if net != self.power_header_pinout[i]:
                    errors.append(f"Power pin {i+1} should be {self.power_header_pinout[i]}, found {net}")
            
            return errors
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error validating power connector: {str(e)}")
            return [f"Board data error: {str(e)}"]
        except Exception as e:
            logger.error(f"Unexpected error validating power connector: {str(e)}")
            return [f"Unexpected error: {str(e)}"]

    def validate(self, board: pcbnew.BOARD) -> List[str]:
        """Run all modular synth-specific layout checks. Returns a list of error messages."""
        errors = []
        try:
            errors.extend(self.enforce_board_dimensions(board))
        except Exception as e:
            logger.error(f"Unexpected error in board dimension validation: {str(e)}")
            errors.append(f"Board dimension validation error: {str(e)}")
        try:
            errors.extend(self.validate_component_spacing(board))
        except Exception as e:
            logger.error(f"Unexpected error in component spacing validation: {str(e)}")
            errors.append(f"Component spacing validation error: {str(e)}")
        try:
            errors.extend(self.validate_power_connector(board))
        except Exception as e:
            logger.error(f"Unexpected error in power connector validation: {str(e)}")
            errors.append(f"Power connector validation error: {str(e)}")
        return errors 