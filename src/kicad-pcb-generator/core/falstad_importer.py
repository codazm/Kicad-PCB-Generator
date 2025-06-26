"""Falstad schematic importer.

Converts Falstad circuit-sim JSON export to either:
1. A lightweight Netlist object (preferred for headless PCB generation).
2. A stub .kicad_sch file so KiCad GUI tooling can open it (optional).

The implementation purposefully avoids external libs.  It performs only
sanity-checks required by the existing unit-tests.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .components.footprint_registry import FootprintRegistry
from .netlist.parser import FootprintData, PadConnection, NetData, Netlist

logger = logging.getLogger(__name__)

__all__ = ["FalstadImporter", "FalstadImportError"]


class FalstadImportError(Exception):
    """Raised when Falstad import fails."""


class FalstadImporter:
    """Importer for Falstad simulator JSON files."""

    # Component type to reference prefix mapping
    _REF_PREFIXES = {
        # Basic passives
        "resistor": "R",
        "capacitor": "C",
        "inductor": "L",
        "diode": "D",
        "led": "LED",
        
        # Power and ground
        "ground": "GND",
        "voltage": "V",
        "vcc": "VCC",
        "vee": "VEE",
        
        # Basic ICs
        "ic": "U",
        "opamp": "U",
        "comparator": "U",
        
        # Transistors
        "transistor": "Q",
        "bjt": "Q",
        "jfet": "Q",
        "mosfet": "Q",
        
        # Audio components
        "potentiometer": "RV",
        "switch": "SW",
        "jack": "J",
        "audio_jack": "J",
        "xlr": "XLR",
        "speaker": "SPK",
        
        # Connectors
        "connector": "CON",
        "header": "H",
        "terminal": "T",
        
        # Specialized audio components
        "ferrite_bead": "FB",
        "crystal": "XTAL",
        "oscillator": "OSC",
        "relay": "RLY",
        "transformer": "T",
        
        # Logic and digital
        "logic": "U",
        "flipflop": "U",
        "counter": "U",
        "shift_register": "U",
        
        # Specialized ICs
        "timer": "U",
        "regulator": "REG",
        "dac": "U",
        "adc": "U",
        "vco": "U",
        "vcf": "U",
        "vca": "U",
        
        # Tubes (vacuum tubes)
        "tube": "V",
        "triode": "V",
        "pentode": "V",
        
        # Mechanical
        "mounting_hole": "MH",
        "standoff": "ST",
    }

    # Pin mapping for common components
    _PIN_MAPPINGS = {
        # Transistors (BJT, JFET, MOSFET)
        "transistor": {
            "bjt": {"1": "E", "2": "B", "3": "C"},  # Emitter, Base, Collector
            "jfet": {"1": "S", "2": "G", "3": "D"},  # Source, Gate, Drain
            "mosfet": {"1": "S", "2": "G", "3": "D"},  # Source, Gate, Drain
            "default": {"1": "1", "2": "2", "3": "3"}
        },
        
        # Op-amps
        "opamp": {
            "8": {"1": "OUT", "2": "IN-", "3": "IN+", "4": "V-", "5": "NC", "6": "NC", "7": "NC", "8": "V+"},
            "14": {"1": "OUT1", "2": "IN1-", "3": "IN1+", "4": "V-", "5": "IN2+", "6": "IN2-", "7": "OUT2", 
                   "8": "OUT3", "9": "IN3-", "10": "IN3+", "11": "V+", "12": "IN4+", "13": "IN4-", "14": "OUT4"},
            "default": {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8"}
        },
        
        # Potentiometers
        "potentiometer": {
            "3": {"1": "1", "2": "W", "3": "3"},  # Terminal 1, Wiper, Terminal 3
            "default": {"1": "1", "2": "2", "3": "3"}
        },
        
        # Audio connectors
        "jack": {
            "3.5mm": {"1": "TIP", "2": "RING", "3": "SLEEVE"},
            "6.35mm": {"1": "TIP", "2": "RING", "3": "SLEEVE"},
            "xlr": {"1": "GND", "2": "HOT", "3": "COLD"},
            "default": {"1": "1", "2": "2", "3": "3"}
        },
        
        # Diodes
        "diode": {
            "default": {"1": "A", "2": "K"}  # Anode, Cathode
        },
        
        # LEDs
        "led": {
            "default": {"1": "A", "2": "K"}  # Anode, Cathode
        },
        
        # Relays
        "relay": {
            "5": {"1": "COIL+", "2": "COIL-", "3": "COM", "4": "NO", "5": "NC"},
            "default": {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}
        },
        
        # Transformers
        "transformer": {
            "6": {"1": "PRI1", "2": "PRI2", "3": "SEC1", "4": "SEC2", "5": "CT1", "6": "CT2"},
            "4": {"1": "PRI1", "2": "PRI2", "3": "SEC1", "4": "SEC2"},
            "default": {"1": "1", "2": "2", "3": "3", "4": "4"}
        }
    }

    def import_schematic(
        self,
        falstad_path: str | Path,
        output_dir: str | Path,
        *,
        strict: bool = True,
    ) -> str:
        """Convert Falstad JSON into a KiCad schematic file and return its path."""
        falstad_path = Path(falstad_path)
        if not falstad_path.exists():
            raise FalstadImportError(f"Falstad file '{falstad_path}' not found")

        try:
            data = json.loads(falstad_path.read_text())
        except json.JSONDecodeError as exc:
            raise FalstadImportError("Invalid JSON") from exc

        # Basic structural validation
        if "elements" not in data or "wires" not in data:
            raise FalstadImportError("Missing required fields 'elements' or 'wires'")

        netlist = self.to_netlist(data, strict=strict)

        # Produce stub schematic file with reference list (for tests / GUI)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        sch_path = out_dir / f"falstad_{uuid.uuid4().hex[:8]}.kicad_sch"
        lines = ["(kicad_sch (version 20211027) (generator FalstadImporter)"]
        for fp in netlist.footprints:
            lines.append(f"  (symbol {fp.lib_id} (property \"Reference\" \"{fp.ref}\"))")
        lines.append(")")
        sch_path.write_text("\n".join(lines))
        return str(sch_path)

    # ---------------------------------------------------------------------
    # JSON → Netlist
    # ---------------------------------------------------------------------

    def to_netlist(self, data: Dict[str, Any], *, strict: bool = True) -> Netlist:
        """Convert Falstad JSON dict to internal Netlist representation."""
        footprints: List[FootprintData] = []
        nets: Dict[str, NetData] = {}

        for idx, elem in enumerate(data.get("elements", [])):
            etype = elem.get("type")
            
            # Check if component type is supported
            if not self._is_component_supported(etype):
                if strict:
                    raise FalstadImportError(f"Unsupported component type '{etype}' @index {idx}")
                else:
                    logger.warning("Skipping unsupported component type %s", etype)
                    continue

            # Create footprint data
            footprint_data = self._create_footprint_data(elem, idx)
            if footprint_data:
                footprints.append(footprint_data)
                
                # Add pad connections to nets
                for pc in footprint_data.pad_connections:
                    nets.setdefault(pc.net_name, NetData(name=pc.net_name, connected_pads=[])).connected_pads.append(
                        f"{footprint_data.ref}-{pc.pad_name}"
                    )

        return Netlist(footprints=footprints, nets=list(nets.values()))

    def _is_component_supported(self, comp_type: str) -> bool:
        """Check if component type is supported."""
        return (comp_type in self._REF_PREFIXES or 
                FootprintRegistry.get_default_footprint(comp_type) is not None)

    def _create_footprint_data(self, elem: Dict[str, Any], idx: int) -> Optional[FootprintData]:
        """Create footprint data for an element."""
        etype = elem.get("type")
        props = elem.get("properties", {})
        
        # Get reference prefix and create reference
        ref_prefix = self._REF_PREFIXES.get(etype, "U")
        ref = f"{ref_prefix}{idx + 1}"
        
        # Get component value
        value = elem.get("value", "")
        
        # Get footprint
        lib_id = self._get_footprint_lib_id(elem)
        if not lib_id:
            logger.warning(f"No footprint found for component type '{etype}'")
            return None
        
        # Create pad connections
        pad_connections = self._create_pad_connections(elem, idx)
        
        return FootprintData(
            ref=ref,
            value=value,
            lib_id=lib_id,
            pad_connections=pad_connections
        )

    def _get_footprint_lib_id(self, elem: Dict[str, Any]) -> Optional[str]:
        """Get footprint library ID for an element."""
        etype = elem.get("type")
        props = elem.get("properties", {})
        
        # Check for package override
        pkg_override = props.get("package")
        if pkg_override:
            return pkg_override
        
        # Get default footprint
        footprint = FootprintRegistry.get_default_footprint(etype)
        if footprint:
            return footprint
        
        # Handle special cases
        if etype == "ic":
            pin_count = int(props.get("pins", 14))
            return FootprintRegistry.get_ic_package(pin_count)
        
        return None

    def _create_pad_connections(self, elem: Dict[str, Any], idx: int) -> List[PadConnection]:
        """Create pad connections for an element."""
        etype = elem.get("type")
        props = elem.get("properties", {})
        
        # Handle ICs with variable pin counts
        if etype == "ic":
            pin_count = int(props.get("pins", 14))
            return [
                PadConnection(pad_name=str(pin), net_name=f"N{idx}_{pin}")
                for pin in range(1, pin_count + 1)
            ]
        
        # Handle op-amps
        if etype == "opamp":
            pin_count = int(props.get("pins", 8))
            pin_mapping = self._PIN_MAPPINGS.get("opamp", {}).get(str(pin_count), 
                                                                self._PIN_MAPPINGS["opamp"]["default"])
            return [
                PadConnection(pad_name=pin_mapping.get(str(pin), str(pin)), net_name=f"N{idx}_{pin}")
                for pin in range(1, pin_count + 1)
            ]
        
        # Handle transistors
        if etype in ["transistor", "bjt", "jfet", "mosfet"]:
            transistor_type = props.get("transistor_type", "bjt")
            pin_mapping = self._PIN_MAPPINGS.get("transistor", {}).get(transistor_type, 
                                                                      self._PIN_MAPPINGS["transistor"]["default"])
            return [
                PadConnection(pad_name=pin_mapping.get(str(pin), str(pin)), net_name=f"N{idx}_{pin}")
                for pin in range(1, 4)  # Most transistors have 3 pins
            ]
        
        # Handle potentiometers
        if etype == "potentiometer":
            pin_mapping = self._PIN_MAPPINGS.get("potentiometer", {}).get("3", 
                                                                         self._PIN_MAPPINGS["potentiometer"]["default"])
            return [
                PadConnection(pad_name=pin_mapping.get(str(pin), str(pin)), net_name=f"N{idx}_{pin}")
                for pin in range(1, 4)  # 3-terminal potentiometer
            ]
        
        # Handle audio connectors
        if etype in ["jack", "audio_jack", "xlr"]:
            connector_type = props.get("connector_type", "3.5mm")
            pin_mapping = self._PIN_MAPPINGS.get("jack", {}).get(connector_type, 
                                                                self._PIN_MAPPINGS["jack"]["default"])
            return [
                PadConnection(pad_name=pin_mapping.get(str(pin), str(pin)), net_name=f"N{idx}_{pin}")
                for pin in range(1, 4)  # Most audio connectors have 3 pins
            ]
        
        # Handle diodes and LEDs
        if etype in ["diode", "led"]:
            pin_mapping = self._PIN_MAPPINGS.get(etype, {}).get("default", {"1": "1", "2": "2"})
            return [
                PadConnection(pad_name=pin_mapping.get(str(pin), str(pin)), net_name=f"N{idx}_{pin}")
                for pin in range(1, 3)  # 2-terminal devices
            ]
        
        # Handle relays
        if etype == "relay":
            pin_count = int(props.get("pins", 5))
            pin_mapping = self._PIN_MAPPINGS.get("relay", {}).get(str(pin_count), 
                                                                 self._PIN_MAPPINGS["relay"]["default"])
            return [
                PadConnection(pad_name=pin_mapping.get(str(pin), str(pin)), net_name=f"N{idx}_{pin}")
                for pin in range(1, pin_count + 1)
            ]
        
        # Handle transformers
        if etype == "transformer":
            pin_count = int(props.get("pins", 4))
            pin_mapping = self._PIN_MAPPINGS.get("transformer", {}).get(str(pin_count), 
                                                                       self._PIN_MAPPINGS["transformer"]["default"])
            return [
                PadConnection(pad_name=pin_mapping.get(str(pin), str(pin)), net_name=f"N{idx}_{pin}")
                for pin in range(1, pin_count + 1)
            ]
        
        # Default 2-terminal components
        if etype in ["resistor", "capacitor", "inductor", "ferrite_bead"]:
            return [
                PadConnection(pad_name="1", net_name=f"N{idx}_A"),
                PadConnection(pad_name="2", net_name=f"N{idx}_B"),
            ]
        
        # Default 3-terminal components
        if etype in ["switch", "timer", "regulator"]:
            return [
                PadConnection(pad_name=str(pin), net_name=f"N{idx}_{pin}")
                for pin in range(1, 4)
            ]
        
        # Default for other components
        return [
            PadConnection(pad_name="1", net_name=f"N{idx}_A"),
            PadConnection(pad_name="2", net_name=f"N{idx}_B"),
        ]

    def get_supported_components(self) -> List[str]:
        """Get list of supported component types."""
        return list(self._REF_PREFIXES.keys()) 