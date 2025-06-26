"""Audio circuit templates for KiCad Audio Designer."""
import logging
from typing import Dict, List, Optional, Any

from ...core.templates import TemplateBase, LayerStack, ZoneSettings, DesignVariant
from ...core.components import ComponentData

class AudioCircuitTemplate(TemplateBase):
    """Base template for audio circuits.
    
    This class provides common functionality for all audio circuit templates,
    including audio-specific layer stacks, zones, and design rules.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize audio circuit template.
        
        Args:
            base_path: Base path for template data
            logger: Optional logger instance
        """
        super().__init__(base_path, logger)
        
        # Set audio-specific layer stack
        self.layer_stack = LayerStack(
            name="Audio 4-Layer Stack",
            layers=["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
            thickness={
                "F.Cu": 0.035,
                "In1.Cu": 0.035,
                "In2.Cu": 0.035,
                "B.Cu": 0.035
            },
            material={
                "F.Cu": "Copper",
                "In1.Cu": "Copper",
                "In2.Cu": "Copper",
                "B.Cu": "Copper"
            },
            dielectric={
                "F.Cu": 0.1,
                "In1.Cu": 0.1,
                "In2.Cu": 0.1,
                "B.Cu": 0.1
            }
        )
        
        # Set audio-specific zones
        self.zones["GND"] = ZoneSettings(
            name="GND",
            layer="F.Cu",
            net="GND",
            priority=1,
            fill_mode="solid",
            thermal_gap=0.5,
            thermal_bridge_width=0.5,
            min_thickness=0.5,
            keep_islands=True,
            smoothing=True
        )
        
        # Set audio-specific design rules
        self.rules = {
            "clearance": 0.2,
            "track_width": {
                "signal": 0.2,
                "power": 0.5,
                "audio": 0.3
            },
            "via_diameter": 0.4,
            "via_drill": 0.2,
            "min_annular_ring": 0.15,
            "min_hole_size": 0.3,
            "min_clearance": 0.2,
            "min_track_width": 0.2,
            "min_via_diameter": 0.4,
            "min_via_drill": 0.2
        }

class PreamplifierTemplate(AudioCircuitTemplate):
    """Template for preamplifier circuits.
    
    This template provides a specialized configuration for preamplifier circuits,
    including common components and design rules.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize preamplifier template.
        
        Args:
            base_path: Base path for template data
            logger: Optional logger instance
        """
        super().__init__(base_path, logger)
        
        # Set template info
        self.name = "Preamplifier"
        self.description = "Template for preamplifier circuits"
        self.version = "1.0.0"
        
        # Add common components
        self._add_common_components()
        
        # Add common variants
        self._add_common_variants()
    
    def _add_common_components(self) -> None:
        """Add common preamplifier components."""
        # Input stage
        self.component_manager.add_component(ComponentData(
            id="R1",
            type="resistor",
            value="10k",
            footprint="R_0805_2012Metric",
            metadata={"tolerance": "1%", "power": "0.25W"}
        ))
        
        self.component_manager.add_component(ComponentData(
            id="C1",
            type="capacitor",
            value="100n",
            footprint="C_0805_2012Metric",
            metadata={"tolerance": "10%", "voltage": "50V"}
        ))
        
        # Op-amp
        self.component_manager.add_component(ComponentData(
            id="U1",
            type="opamp",
            value="NE5532",
            footprint="SOIC-8_3.9x4.9mm_P1.27mm",
            metadata={"type": "dual", "slew_rate": "9V/us"}
        ))
    
    def _add_common_variants(self) -> None:
        """Add common preamplifier variants."""
        # Standard variant
        self.variants["Standard"] = DesignVariant(
            name="Standard",
            description="Standard preamplifier configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["R1-1", "C1-1", "U1-4"],
                "VCC": ["U1-8"],
                "VEE": ["U1-4"],
                "IN": ["R1-2"],
                "OUT": ["U1-1"]
            },
            rules=self.rules
        )
        
        # High-gain variant
        self.variants["HighGain"] = DesignVariant(
            name="HighGain",
            description="High-gain preamplifier configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["R1-1", "C1-1", "U1-4"],
                "VCC": ["U1-8"],
                "VEE": ["U1-4"],
                "IN": ["R1-2"],
                "OUT": ["U1-1"]
            },
            rules=self.rules
        )

class PowerAmplifierTemplate(AudioCircuitTemplate):
    """Template for power amplifier circuits.
    
    This template provides a specialized configuration for power amplifier circuits,
    including common components and design rules.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize power amplifier template.
        
        Args:
            base_path: Base path for template data
            logger: Optional logger instance
        """
        super().__init__(base_path, logger)
        
        # Set template info
        self.name = "Power Amplifier"
        self.description = "Template for power amplifier circuits"
        self.version = "1.0.0"
        
        # Add common components
        self._add_common_components()
        
        # Add common variants
        self._add_common_variants()
    
    def _add_common_components(self) -> None:
        """Add common power amplifier components."""
        # Input stage
        self.component_manager.add_component(ComponentData(
            id="R1",
            type="resistor",
            value="10k",
            footprint="R_1206_3216Metric",
            metadata={"tolerance": "1%", "power": "0.5W"}
        ))
        
        # Output stage
        self.component_manager.add_component(ComponentData(
            id="Q1",
            type="transistor",
            value="2N3055",
            footprint="TO-3",
            metadata={"type": "NPN", "power": "115W"}
        ))
        
        self.component_manager.add_component(ComponentData(
            id="Q2",
            type="transistor",
            value="MJ2955",
            footprint="TO-3",
            metadata={"type": "PNP", "power": "115W"}
        ))
    
    def _add_common_variants(self) -> None:
        """Add common power amplifier variants."""
        # Standard variant
        self.variants["Standard"] = DesignVariant(
            name="Standard",
            description="Standard power amplifier configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["R1-1", "Q1-2", "Q2-2"],
                "VCC": ["Q1-1"],
                "VEE": ["Q2-1"],
                "IN": ["R1-2"],
                "OUT": ["Q1-3", "Q2-3"]
            },
            rules=self.rules
        )
        
        # High-power variant
        self.variants["HighPower"] = DesignVariant(
            name="HighPower",
            description="High-power amplifier configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["R1-1", "Q1-2", "Q2-2"],
                "VCC": ["Q1-1"],
                "VEE": ["Q2-1"],
                "IN": ["R1-2"],
                "OUT": ["Q1-3", "Q2-3"]
            },
            rules=self.rules
        )

class EffectsPedalTemplate(AudioCircuitTemplate):
    """Template for effects pedal circuits.
    
    This template provides a specialized configuration for effects pedal circuits,
    including common components and design rules.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize effects pedal template.
        
        Args:
            base_path: Base path for template data
            logger: Optional logger instance
        """
        super().__init__(base_path, logger)
        
        # Set template info
        self.name = "Effects Pedal"
        self.description = "Template for effects pedal circuits"
        self.version = "1.0.0"
        
        # Add common components
        self._add_common_components()
        
        # Add common variants
        self._add_common_variants()
    
    def _add_common_components(self) -> None:
        """Add common effects pedal components."""
        # Input stage
        self.component_manager.add_component(ComponentData(
            id="R1",
            type="resistor",
            value="10k",
            footprint="R_0805_2012Metric",
            metadata={"tolerance": "1%", "power": "0.25W"}
        ))
        
        # Effect stage
        self.component_manager.add_component(ComponentData(
            id="U1",
            type="opamp",
            value="TL072",
            footprint="SOIC-8_3.9x4.9mm_P1.27mm",
            metadata={"type": "dual", "slew_rate": "13V/us"}
        ))
        
        # Output stage
        self.component_manager.add_component(ComponentData(
            id="C1",
            type="capacitor",
            value="100n",
            footprint="C_0805_2012Metric",
            metadata={"tolerance": "10%", "voltage": "50V"}
        ))
    
    def _add_common_variants(self) -> None:
        """Add common effects pedal variants."""
        # Standard variant
        self.variants["Standard"] = DesignVariant(
            name="Standard",
            description="Standard effects pedal configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["R1-1", "C1-1", "U1-4"],
                "VCC": ["U1-8"],
                "VEE": ["U1-4"],
                "IN": ["R1-2"],
                "OUT": ["U1-1"]
            },
            rules=self.rules
        )
        
        # Bypass variant
        self.variants["Bypass"] = DesignVariant(
            name="Bypass",
            description="Effects pedal with bypass configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["R1-1", "C1-1", "U1-4"],
                "VCC": ["U1-8"],
                "VEE": ["U1-4"],
                "IN": ["R1-2"],
                "OUT": ["U1-1"],
                "BYPASS": ["SW1-1", "SW1-2"]
            },
            rules=self.rules
        )

class AudioInterfaceTemplate(AudioCircuitTemplate):
    """Template for audio interface circuits.
    
    This template provides a specialized configuration for audio interface circuits,
    including common components and design rules.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize audio interface template.
        
        Args:
            base_path: Base path for template data
            logger: Optional logger instance
        """
        super().__init__(base_path, logger)
        
        # Set template info
        self.name = "Audio Interface"
        self.description = "Template for audio interface circuits"
        self.version = "1.0.0"
        
        # Add common components
        self._add_common_components()
        
        # Add common variants
        self._add_common_variants()
    
    def _add_common_components(self) -> None:
        """Add common audio interface components."""
        # Input stage
        self.component_manager.add_component(ComponentData(
            id="U1",
            type="adc",
            value="PCM1808",
            footprint="SOIC-20_7.5x12.8mm_P1.27mm",
            metadata={"type": "24-bit", "sample_rate": "96kHz"}
        ))
        
        # Output stage
        self.component_manager.add_component(ComponentData(
            id="U2",
            type="dac",
            value="PCM5102",
            footprint="SOIC-20_7.5x12.8mm_P1.27mm",
            metadata={"type": "24-bit", "sample_rate": "96kHz"}
        ))
        
        # USB interface
        self.component_manager.add_component(ComponentData(
            id="U3",
            type="usb_controller",
            value="CP2102",
            footprint="QFN-28_5x5mm_P0.5mm",
            metadata={"type": "USB-UART", "speed": "12Mbps"}
        ))
        
        # Power supply
        self.component_manager.add_component(ComponentData(
            id="U4",
            type="regulator",
            value="LM317",
            footprint="TO-220-3_Vertical",
            metadata={"type": "adjustable", "current": "1.5A"}
        ))
    
    def _add_common_variants(self) -> None:
        """Add common audio interface variants."""
        # Standard variant
        self.variants["Standard"] = DesignVariant(
            name="Standard",
            description="Standard audio interface configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["U1-10", "U2-10", "U3-14", "U4-2"],
                "VCC": ["U1-20", "U2-20", "U3-28", "U4-3"],
                "USB_D+": ["U3-15"],
                "USB_D-": ["U3-16"],
                "AUDIO_IN": ["U1-1"],
                "AUDIO_OUT": ["U2-1"]
            },
            rules=self.rules
        )
        
        # Pro variant
        self.variants["Pro"] = DesignVariant(
            name="Pro",
            description="Professional audio interface configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["U1-10", "U2-10", "U3-14", "U4-2"],
                "VCC": ["U1-20", "U2-20", "U3-28", "U4-3"],
                "USB_D+": ["U3-15"],
                "USB_D-": ["U3-16"],
                "AUDIO_IN": ["U1-1"],
                "AUDIO_OUT": ["U2-1"],
                "MIDI_IN": ["U3-1"],
                "MIDI_OUT": ["U3-2"]
            },
            rules=self.rules
        )

class MixingConsoleTemplate(AudioCircuitTemplate):
    """Template for mixing console circuits.
    
    This template provides a specialized configuration for mixing console circuits,
    including common components and design rules.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize mixing console template.
        
        Args:
            base_path: Base path for template data
            logger: Optional logger instance
        """
        super().__init__(base_path, logger)
        
        # Set template info
        self.name = "Mixing Console"
        self.description = "Template for mixing console circuits"
        self.version = "1.0.0"
        
        # Add common components
        self._add_common_components()
        
        # Add common variants
        self._add_common_variants()
    
    def _add_common_components(self) -> None:
        """Add common mixing console components."""
        # Input channel
        self.component_manager.add_component(ComponentData(
            id="U1",
            type="opamp",
            value="NE5532",
            footprint="SOIC-8_3.9x4.9mm_P1.27mm",
            metadata={"type": "dual", "slew_rate": "9V/us"}
        ))
        
        # Fader
        self.component_manager.add_component(ComponentData(
            id="R1",
            type="potentiometer",
            value="10k",
            footprint="Potentiometer_Alps_RK09K_Single_Vertical",
            metadata={"type": "linear", "tolerance": "20%"}
        ))
        
        # EQ section
        self.component_manager.add_component(ComponentData(
            id="U2",
            type="opamp",
            value="TL072",
            footprint="SOIC-8_3.9x4.9mm_P1.27mm",
            metadata={"type": "dual", "slew_rate": "13V/us"}
        ))
        
        # Master section
        self.component_manager.add_component(ComponentData(
            id="U3",
            type="opamp",
            value="NE5532",
            footprint="SOIC-8_3.9x4.9mm_P1.27mm",
            metadata={"type": "dual", "slew_rate": "9V/us"}
        ))
    
    def _add_common_variants(self) -> None:
        """Add common mixing console variants."""
        # Standard variant
        self.variants["Standard"] = DesignVariant(
            name="Standard",
            description="Standard mixing console configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["U1-4", "U2-4", "U3-4"],
                "VCC": ["U1-8", "U2-8", "U3-8"],
                "VEE": ["U1-4", "U2-4", "U3-4"],
                "CH_IN": ["U1-3"],
                "CH_OUT": ["U1-1"],
                "EQ_IN": ["U2-3"],
                "EQ_OUT": ["U2-1"],
                "MASTER_IN": ["U3-3"],
                "MASTER_OUT": ["U3-1"]
            },
            rules=self.rules
        )
        
        # Professional variant
        self.variants["Professional"] = DesignVariant(
            name="Professional",
            description="Professional mixing console configuration",
            components=self.component_manager.get_components(),
            nets={
                "GND": ["U1-4", "U2-4", "U3-4"],
                "VCC": ["U1-8", "U2-8", "U3-8"],
                "VEE": ["U1-4", "U2-4", "U3-4"],
                "CH_IN": ["U1-3"],
                "CH_OUT": ["U1-1"],
                "EQ_IN": ["U2-3"],
                "EQ_OUT": ["U2-1"],
                "MASTER_IN": ["U3-3"],
                "MASTER_OUT": ["U3-1"],
                "AUX_SEND": ["U1-7"],
                "AUX_RETURN": ["U2-5"]
            },
            rules=self.rules
        ) 
