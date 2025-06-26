"""Central footprint registry.

Provides a single source of truth mapping logical component *types* and optional
property hints (like pin count) to KiCad library IDs.  This avoids ad-hoc
`_FOOTPRINT_MAP` dicts scattered across importers or generators.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FootprintRegistry:
    """Singleton-style registry providing footprint lookup helpers."""

    # Base map for common components (SMD default)
    _BASE_MAP: Dict[str, str] = {
        # Basic passives
        "resistor": "Device:R_0603",
        "capacitor": "Device:C_0603",
        "inductor": "Device:L_0603",
        "diode": "Device:D_SOD-123",
        "led": "LED:LED_0603_1608Metric",
        
        # Power and ground
        "ground": "power:GND",
        "voltage": "power:VCC",
        "vcc": "power:VCC",
        "vee": "power:VEE",
        
        # Basic ICs
        "ic": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        "opamp": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        "comparator": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        
        # Transistors
        "transistor": "Package_TO_SOT_THT:TO-92_Inline",
        "bjt": "Package_TO_SOT_THT:TO-92_Inline",
        "jfet": "Package_TO_SOT_THT:TO-92_Inline",
        "mosfet": "Package_TO_SOT_THT:TO-220-3_Vertical",
        
        # Audio components
        "potentiometer": "Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Horizontal",
        "switch": "Button_Switch_THT:SW_SPST_SKQG_WithThreadedTerminal",
        "jack": "Connector_Audio:Jack_3.5mm_Stereo",
        "audio_jack": "Connector_Audio:Jack_3.5mm_Stereo",
        "xlr": "Connector_Audio:XLR-3_Male",
        "speaker": "Audio:Speaker_Pioneer_G-25MC",
        
        # Connectors
        "connector": "Connector_Generic:Conn_01x02",
        "header": "Connector_Generic:Conn_01x02",
        "terminal": "Connector_Generic:Conn_01x02",
        
        # Specialized audio components
        "ferrite_bead": "Inductor_SMD:L_0603_1608Metric",
        "crystal": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
        "oscillator": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
        "relay": "Relay_THT:Relay_SPDT_Schrack-RT1-FormA_RM5mm",
        "transformer": "Transformer_THT:Transformer_EI30-15_Vertical",
        
        # Logic and digital
        "logic": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        "flipflop": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        "counter": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        "shift_register": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        
        # Specialized ICs
        "timer": "Package_DIP:DIP-8_W7.62mm",
        "regulator": "Package_TO_SOT_THT:TO-220-3_Vertical",
        "dac": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        "adc": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        "vco": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        "vcf": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        "vca": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        
        # Tubes (vacuum tubes)
        "tube": "Package_THT:Socket_9-Pin_Octal",
        "triode": "Package_THT:Socket_9-Pin_Octal",
        "pentode": "Package_THT:Socket_9-Pin_Octal",
        
        # Mechanical
        "mounting_hole": "MountingHole:MountingHole_3.2mm_M3",
        "standoff": "MountingHole:MountingHole_3.2mm_M3",
    }

    # Through-hole / audio-centric overrides
    _TH_MAP: Dict[str, str] = {
        # Basic passives (through-hole)
        "resistor": "Device:R_Axial_L9.0mm_D3.0mm_P10.16mm_Horizontal",
        "capacitor": "Device:CP_Radial_D16.0mm_P7.50mm",
        "inductor": "Device:L_Radial_D10.0mm_P5.00mm",
        "diode": "Device:D_THT_D5.0mm_W2.5mm_P2.54mm",
        "led": "LED:LED_D5.0mm",
        
        # Audio components (through-hole preferred)
        "potentiometer": "Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Horizontal",
        "switch": "Button_Switch_THT:SW_SPST_SKQG_WithThreadedTerminal",
        "jack": "Connector_Audio:Jack_3.5mm_Stereo",
        "audio_jack": "Connector_Audio:Jack_3.5mm_Stereo",
        "xlr": "Connector_Audio:XLR-3_Male",
        "speaker": "Audio:Speaker_Pioneer_G-25MC",
        
        # Transistors (through-hole)
        "transistor": "Package_TO_SOT_THT:TO-92_Inline",
        "bjt": "Package_TO_SOT_THT:TO-92_Inline",
        "jfet": "Package_TO_SOT_THT:TO-92_Inline",
        "mosfet": "Package_TO_SOT_THT:TO-220-3_Vertical",
        
        # Connectors
        "connector": "Connector_Audio:Jack_3.5mm_Stereo",
        "header": "Connector_Generic:Conn_01x02",
        "terminal": "Connector_Generic:Conn_01x02",
        
        # Specialized components
        "ferrite_bead": "Inductor_THT:L_Axial_L12.0mm_D5.0mm_P15.00mm_Horizontal",
        "crystal": "Crystal:Crystal_HC49-U_Vertical",
        "oscillator": "Crystal:Crystal_HC49-U_Vertical",
        "relay": "Relay_THT:Relay_SPDT_Schrack-RT1-FormA_RM5mm",
        "transformer": "Transformer_THT:Transformer_EI30-15_Vertical",
        
        # Logic and digital (through-hole)
        "logic": "Package_DIP:DIP-14_W7.62mm",
        "flipflop": "Package_DIP:DIP-14_W7.62mm",
        "counter": "Package_DIP:DIP-16_W7.62mm",
        "shift_register": "Package_DIP:DIP-16_W7.62mm",
        
        # Specialized ICs (through-hole)
        "timer": "Package_DIP:DIP-8_W7.62mm",
        "regulator": "Package_TO_SOT_THT:TO-220-3_Vertical",
        "dac": "Package_DIP:DIP-8_W7.62mm",
        "adc": "Package_DIP:DIP-8_W7.62mm",
        "vco": "Package_DIP:DIP-16_W7.62mm",
        "vcf": "Package_DIP:DIP-16_W7.62mm",
        "vca": "Package_DIP:DIP-8_W7.62mm",
        
        # Op-amps (through-hole)
        "opamp": "Package_DIP:DIP-8_W7.62mm",
        "comparator": "Package_DIP:DIP-8_W7.62mm",
    }

    # Package map keyed by (type, property_key value)
    _PKG_MAP: Dict[tuple[str, str], str] = {
        # IC packages by pin count
        ("ic", "8"): "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        ("ic", "14"): "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        ("ic", "16"): "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        ("ic", "20"): "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
        ("ic", "24"): "Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm",
        ("ic", "28"): "Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm",
        
        # Op-amp packages
        ("opamp", "8"): "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        ("opamp", "14"): "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        ("opamp", "16"): "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        
        # Transistor packages
        ("transistor", "to92"): "Package_TO_SOT_THT:TO-92_Inline",
        ("transistor", "to220"): "Package_TO_SOT_THT:TO-220-3_Vertical",
        ("transistor", "sot23"): "Package_TO_SOT_SMD:SOT-23",
        ("transistor", "sot223"): "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        
        # Potentiometer packages
        ("potentiometer", "9mm"): "Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Horizontal",
        ("potentiometer", "16mm"): "Potentiometer_THT:Potentiometer_Alps_RK16K_Single_Horizontal",
        ("potentiometer", "24mm"): "Potentiometer_THT:Potentiometer_Alps_RK24K_Single_Horizontal",
        
        # Audio connector packages
        ("jack", "3.5mm"): "Connector_Audio:Jack_3.5mm_Stereo",
        ("jack", "6.35mm"): "Connector_Audio:Jack_6.35mm_Jack",
        ("jack", "xlr"): "Connector_Audio:XLR-3_Male",
        
        # Capacitor packages
        ("capacitor", "electrolytic"): "Device:CP_Radial_D16.0mm_P7.50mm",
        ("capacitor", "ceramic"): "Device:C_0805_2012Metric",
        ("capacitor", "film"): "Device:CP_Radial_D16.0mm_P7.50mm",
        ("capacitor", "tantalum"): "Device:C_1206_3216Metric",
        
        # Resistor packages
        ("resistor", "axial"): "Device:R_Axial_L9.0mm_D3.0mm_P10.16mm_Horizontal",
        ("resistor", "0805"): "Device:R_0805_2012Metric",
        ("resistor", "1206"): "Device:R_1206_3216Metric",
    }

    # Allow runtime registration
    _custom_map: Dict[str, str] = {}

    @classmethod
    def register(cls, key: str, lib_id: str) -> None:
        """Register or override a mapping at runtime."""
        cls._custom_map[key] = lib_id
        logger.debug("Registered custom footprint mapping %s -> %s", key, lib_id)

    # ------------------------------------------------------------------
    # Bulk-load helpers
    # ------------------------------------------------------------------

    @classmethod
    def load_from_file(cls, path: str | "Path") -> None:
        """Load additional mappings from a JSON/YAML file.

        The file should contain a simple object mapping *comp_type* → *lib_id*.
        Duplicate keys override previous mappings (including in the TH map).
        """
        from pathlib import Path
        import json
        import yaml

        p = Path(path)
        if not p.exists():
            logger.debug("Footprint override file not found: %s", p)
            return

        try:
            if p.suffix.lower() in {".yml", ".yaml"}:
                data = yaml.safe_load(p.read_text())
            else:
                data = json.loads(p.read_text())

            if not isinstance(data, dict):
                logger.warning("Footprint override file %s is not a dict", p)
                return

            for key, lib_id in data.items():
                if isinstance(key, str) and isinstance(lib_id, str):
                    cls.register(key.lower(), lib_id)
        except Exception as exc:
            logger.error("Failed to load footprint overrides from %s: %s", p, exc)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @classmethod
    def get_default_footprint(cls, comp_type: str, *, through_hole: bool = False) -> Optional[str]:
        """Return footprint libID for *comp_type*.

        Args:
            comp_type: Logical component kind (resistor, capacitor, opamp, etc.).
            through_hole: Prefer through-hole variant when available.
        """
        # Custom mapping has top priority
        if comp_type in cls._custom_map:
            return cls._custom_map[comp_type]

        if through_hole and comp_type in cls._TH_MAP:
            return cls._TH_MAP[comp_type]
        return cls._BASE_MAP.get(comp_type)

    @classmethod
    def get_ic_package(cls, pin_count: int) -> str:
        """Return package for IC with *pin_count* pins (falls back to base)."""
        return cls._PKG_MAP.get(("ic", str(pin_count)), cls._BASE_MAP["ic"])
    
    @classmethod
    def get_component_package(cls, comp_type: str, package_type: str) -> str:
        """Return specific package for component type and package variant.
        
        Args:
            comp_type: Component type (transistor, capacitor, etc.)
            package_type: Package variant (to92, to220, electrolytic, etc.)
        """
        return cls._PKG_MAP.get((comp_type, package_type), cls.get_default_footprint(comp_type))
    
    @classmethod
    def get_audio_component_footprint(cls, comp_type: str, *, through_hole: bool = True) -> Optional[str]:
        """Get footprint optimized for audio applications.
        
        Args:
            comp_type: Component type
            through_hole: Prefer through-hole components (default for audio)
        """
        return cls.get_default_footprint(comp_type, through_hole=through_hole)
    
    @classmethod
    def list_supported_components(cls) -> list[str]:
        """Return list of all supported component types."""
        all_components = set(cls._BASE_MAP.keys())
        all_components.update(cls._TH_MAP.keys())
        all_components.update(cls._custom_map.keys())
        return sorted(list(all_components)) 