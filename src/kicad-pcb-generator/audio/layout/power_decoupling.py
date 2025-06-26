"""Power supply decoupling optimization for audio circuits."""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pcbnew
import math

logger = logging.getLogger(__name__)

@dataclass
class DecouplingResult:
    """Result of decoupling optimization."""
    success: bool
    placed_capacitors: List[pcbnew.FOOTPRINT] = None
    power_rail_optimizations: List[Dict[str, Any]] = None
    voltage_drop_analysis: Dict[str, float] = None
    errors: List[str] = None

@dataclass
class PowerRailAnalysis:
    """Analysis of power rail characteristics."""
    rail_name: str
    current_draw: float  # Amperes
    voltage_drop: float  # Volts
    resistance: float  # Ohms
    track_width: float  # mm
    recommended_width: float  # mm
    decoupling_caps: int
    recommended_caps: int

class PowerDecouplingOptimizer:
    """Optimizes power supply decoupling for audio applications."""
    
    def __init__(self):
        """Initialize the power decoupling optimizer."""
        # Audio-specific decoupling parameters
        self.max_decoupling_distance = 3.0  # mm - maximum distance for decoupling caps
        self.min_capacitance_per_rail = 10.0  # µF - minimum capacitance per power rail
        self.recommended_cap_values = [0.1, 1.0, 10.0, 100.0]  # µF - standard decoupling values
        self.max_voltage_drop = 0.1  # V - maximum acceptable voltage drop
        self.min_track_width = 0.2  # mm - minimum power track width
        
    def optimize_decoupling(self, board: pcbnew.BOARD) -> DecouplingResult:
        """Optimize decoupling capacitor placement and power rail design.
        
        Args:
            board: KiCad board object
            
        Returns:
            DecouplingResult with optimization results
        """
        try:
            # Analyze power rails
            power_analysis = self._analyze_power_rails(board)
            
            # Optimize decoupling capacitor placement
            placed_caps = self._optimize_decoupling_placement(board, power_analysis)
            
            # Optimize power rail routing
            rail_optimizations = self._optimize_power_rails(board, power_analysis)
            
            # Analyze voltage drop
            voltage_drop_analysis = self._analyze_voltage_drop(board, power_analysis)
            
            return DecouplingResult(
                success=True,
                placed_capacitors=placed_caps,
                power_rail_optimizations=rail_optimizations,
                voltage_drop_analysis=voltage_drop_analysis,
                errors=[]
            )
            
        except Exception as e:
            return DecouplingResult(
                success=False,
                errors=[f"Error optimizing decoupling: {str(e)}"]
            )

    def place_decoupling_capacitors(self, board: pcbnew.BOARD, opamp_footprints: List[pcbnew.FOOTPRINT]) -> List[pcbnew.FOOTPRINT]:
        """Place decoupling capacitors optimally near op-amps.
        
        Args:
            board: KiCad board object
            opamp_footprints: List of op-amp footprints
            
        Returns:
            List of placed decoupling capacitor footprints
        """
        placed_caps = []
        
        try:
            for opamp in opamp_footprints:
                # Find power pins
                power_pins = self._find_power_pins(opamp)
                
                for pin in power_pins:
                    # Place decoupling capacitors near each power pin
                    caps = self._place_caps_near_pin(board, pin, opamp)
                    placed_caps.extend(caps)
            
            return placed_caps
            
        except Exception as e:
            print(f"Error placing decoupling capacitors: {e}")
            return []

    def optimize_power_rail_widths(self, board: pcbnew.BOARD) -> List[Dict[str, Any]]:
        """Optimize power rail track widths based on current requirements.
        
        Args:
            board: KiCad board object
            
        Returns:
            List of optimization recommendations
        """
        optimizations = []
        
        try:
            # Find power tracks
            power_tracks = self._find_power_tracks(board)
            
            for track in power_tracks:
                # Calculate required width based on current
                current = self._estimate_track_current(track)
                required_width = self._calculate_required_width(current)
                current_width = track.GetWidth() / 1e6  # Convert to mm
                
                if required_width > current_width:
                    optimizations.append({
                        "track": track,
                        "current_width": current_width,
                        "required_width": required_width,
                        "current": current,
                        "action": "increase_width"
                    })
            
            return optimizations
            
        except Exception as e:
            print(f"Error optimizing power rail widths: {e}")
            return []

    def analyze_power_supply_rejection(self, board: pcbnew.BOARD) -> Dict[str, float]:
        """Analyze power supply rejection ratio (PSRR) characteristics.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary with PSRR analysis results
        """
        psrr_analysis = {}
        
        try:
            # Find op-amps
            opamps = [f for f in board.GetFootprints() if f.GetReference().startswith("U")]
            
            for opamp in opamps:
                # Calculate PSRR based on decoupling and layout
                psrr = self._calculate_psrr(opamp, board)
                psrr_analysis[opamp.GetReference()] = psrr
            
            return psrr_analysis
            
        except Exception as e:
            print(f"Error analyzing PSRR: {e}")
            return {}

    # --- Helper methods ---
    def _analyze_power_rails(self, board: pcbnew.BOARD) -> List[PowerRailAnalysis]:
        """Analyze power rail characteristics."""
        power_rails = []
        
        try:
            # Find power nets
            power_nets = {}
            for net in board.GetNets():
                net_name = net.GetNetname().upper()
                if any(keyword in net_name for keyword in ["VCC", "VDD", "V+", "V-", "POWER"]):
                    power_nets[net_name] = {
                        "current_draw": 0.0,
                        "tracks": [],
                        "components": []
                    }
            
            # Analyze each power rail
            for net_name, rail_data in power_nets.items():
                # Find tracks for this net
                for track in board.GetTracks():
                    if track.GetNet().GetNetname().upper() == net_name:
                        rail_data["tracks"].append(track)
                
                # Find components connected to this net
                for footprint in board.GetFootprints():
                    for pad in footprint.GetPads():
                        if pad.GetNetname().upper() == net_name:
                            rail_data["components"].append(footprint)
                            # Estimate current draw
                            rail_data["current_draw"] += self._estimate_component_current(footprint)
                
                # Calculate rail characteristics
                if rail_data["tracks"]:
                    avg_width = sum(t.GetWidth() for t in rail_data["tracks"]) / len(rail_data["tracks"]) / 1e6
                    resistance = self._calculate_track_resistance(rail_data["tracks"])
                    voltage_drop = rail_data["current_draw"] * resistance
                    decoupling_caps = len([c for c in rail_data["components"] if c.GetReference().startswith("C")])
                    
                    power_rails.append(PowerRailAnalysis(
                        rail_name=net_name,
                        current_draw=rail_data["current_draw"],
                        voltage_drop=voltage_drop,
                        resistance=resistance,
                        track_width=avg_width,
                        recommended_width=self._calculate_required_width(rail_data["current_draw"]),
                        decoupling_caps=decoupling_caps,
                        recommended_caps=max(1, int(rail_data["current_draw"] * 10))  # 1 cap per 100mA
                    ))
            
            return power_rails
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error analyzing power rails: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error analyzing power rails: {str(e)}")
            return []

    def _optimize_decoupling_placement(self, board: pcbnew.BOARD, power_analysis: List[PowerRailAnalysis]) -> List[pcbnew.FOOTPRINT]:
        """Optimize placement of decoupling capacitors."""
        placed_caps = []
        
        try:
            for rail in power_analysis:
                # Find components on this rail
                rail_components = []
                for footprint in board.GetFootprints():
                    for pad in footprint.GetPads():
                        if pad.GetNetname().upper() == rail.rail_name:
                            rail_components.append(footprint)
                
                # Place additional decoupling if needed
                current_caps = rail.decoupling_caps
                needed_caps = rail.recommended_caps - current_caps
                
                for i in range(needed_caps):
                    # Place near highest current component
                    if rail_components:
                        target_component = max(rail_components, 
                                             key=lambda c: self._estimate_component_current(c))
                        cap = self._create_decoupling_capacitor(board, target_component, rail.rail_name)
                        if cap:
                            placed_caps.append(cap)
            
            return placed_caps
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error optimizing decoupling placement: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error optimizing decoupling placement: {str(e)}")
            return []

    def _optimize_power_rails(self, board: pcbnew.BOARD, power_analysis: List[PowerRailAnalysis]) -> List[Dict[str, Any]]:
        """Optimize power rail routing."""
        optimizations = []
        
        try:
            for rail in power_analysis:
                if rail.voltage_drop > self.max_voltage_drop:
                    # Voltage drop too high - need wider tracks
                    optimizations.append({
                        "rail": rail.rail_name,
                        "issue": "high_voltage_drop",
                        "current_drop": rail.voltage_drop,
                        "max_drop": self.max_voltage_drop,
                        "action": "increase_track_width",
                        "recommended_width": rail.recommended_width
                    })
                
                if rail.decoupling_caps < rail.recommended_caps:
                    # Need more decoupling capacitors
                    optimizations.append({
                        "rail": rail.rail_name,
                        "issue": "insufficient_decoupling",
                        "current_caps": rail.decoupling_caps,
                        "recommended_caps": rail.recommended_caps,
                        "action": "add_decoupling_caps"
                    })
            
            return optimizations
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error optimizing power rails: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error optimizing power rails: {str(e)}")
            return []

    def _analyze_voltage_drop(self, board: pcbnew.BOARD, power_analysis: List[PowerRailAnalysis]) -> Dict[str, float]:
        """Analyze voltage drop across power rails."""
        voltage_drops = {}
        
        try:
            for rail in power_analysis:
                voltage_drops[rail.rail_name] = rail.voltage_drop
            
            return voltage_drops
            
        except Exception as e:
            print(f"Error analyzing voltage drop: {e}")
            return {}

    def _find_power_pins(self, opamp: pcbnew.FOOTPRINT) -> List[pcbnew.PAD]:
        """Find power supply pins on an op-amp."""
        power_pins = []
        
        try:
            for pad in opamp.GetPads():
                pad_name = pad.GetName().upper()
                if pad_name in ("VCC", "VDD", "V+", "V-", "VSS"):
                    power_pins.append(pad)
            
            return power_pins
            
        except Exception as e:
            print(f"Error finding power pins: {e}")
            return []

    def _place_caps_near_pin(self, board: pcbnew.BOARD, pin: pcbnew.PAD, opamp: pcbnew.FOOTPRINT) -> List[pcbnew.FOOTPRINT]:
        """Place decoupling capacitors near a power pin."""
        placed_caps = []
        
        try:
            pin_pos = pin.GetPosition()
            opamp_pos = opamp.GetPosition()
            
            # Place capacitors in a pattern around the pin
            for i, cap_value in enumerate(self.recommended_cap_values):
                # Calculate position offset
                offset_x = int(2 * 1e6)  # 2mm offset
                offset_y = int(i * 3 * 1e6)  # 3mm spacing between caps
                
                cap_pos = pcbnew.VECTOR2I(
                    pin_pos.x + offset_x,
                    pin_pos.y + offset_y
                )
                
                # Create decoupling capacitor
                cap = self._create_decoupling_capacitor_at_position(board, cap_pos, cap_value, pin.GetNetname())
                if cap:
                    placed_caps.append(cap)
            
            return placed_caps
            
        except Exception as e:
            print(f"Error placing caps near pin: {e}")
            return []

    def _create_decoupling_capacitor(self, board: pcbnew.BOARD, target_component: pcbnew.FOOTPRINT, net_name: str) -> Optional[pcbnew.FOOTPRINT]:
        """Create a decoupling capacitor near a target component."""
        try:
            # Calculate position near component
            comp_pos = target_component.GetPosition()
            offset = int(3 * 1e6)  # 3mm offset
            
            cap_pos = pcbnew.VECTOR2I(
                comp_pos.x + offset,
                comp_pos.y + offset
            )
            
            # Create capacitor with 0.1µF value (standard decoupling)
            return self._create_decoupling_capacitor_at_position(board, cap_pos, 0.1, net_name)
            
        except Exception as e:
            print(f"Error creating decoupling capacitor: {e}")
            return None

    def _create_decoupling_capacitor_at_position(self, board: pcbnew.BOARD, position: pcbnew.VECTOR2I, value: float, net_name: str) -> Optional[pcbnew.FOOTPRINT]:
        """Create a decoupling capacitor at a specific position."""
        try:
            # Create footprint
            cap = pcbnew.FOOTPRINT(board)
            cap.SetReference(f"CDEC{len(list(board.GetFootprints())) + 1}")
            cap.SetValue(f"{value}µF")
            cap.SetPosition(position)
            
            # Set footprint type (0603 or 0805 for decoupling)
            cap.SetFootprintName("Capacitor_SMD:C_0603_1608Metric")
            
            # Add to board
            board.Add(cap)
            
            return cap
            
        except Exception as e:
            print(f"Error creating capacitor at position: {e}")
            return None

    def _find_power_tracks(self, board: pcbnew.BOARD) -> List[pcbnew.TRACK]:
        """Find power supply tracks on the board."""
        power_tracks = []
        
        try:
            for track in board.GetTracks():
                net_name = track.GetNet().GetNetname().upper()
                if any(keyword in net_name for keyword in ["VCC", "VDD", "V+", "V-", "POWER"]):
                    power_tracks.append(track)
            
            return power_tracks
            
        except Exception as e:
            print(f"Error finding power tracks: {e}")
            return []

    def _estimate_track_current(self, track: pcbnew.TRACK) -> float:
        """Estimate current flowing through a track."""
        try:
            # Simple heuristic based on track width
            track_width_mm = track.GetWidth() / 1e6
            # Assume 1A per mm of track width (conservative estimate)
            return track_width_mm
            
        except Exception as e:
            print(f"Error estimating track current: {e}")
            return 0.1  # Default 100mA

    def _calculate_required_width(self, current: float) -> float:
        """Calculate required track width for a given current."""
        try:
            # Simple calculation: 1mm width per 1A current
            # In practice, this would use more sophisticated thermal calculations
            return max(self.min_track_width, current)
            
        except Exception as e:
            print(f"Error calculating required width: {e}")
            return self.min_track_width

    def _estimate_component_current(self, component: pcbnew.FOOTPRINT) -> float:
        """Estimate current draw of a component."""
        try:
            ref = component.GetReference().upper()
            value = component.GetValue().upper()
            
            # Op-amps typically draw 1-10mA
            if ref.startswith("U") and "OPA" in value:
                return 0.005  # 5mA
            
            # Power components draw more
            elif any(keyword in ref for keyword in ["POWER", "REG", "PSU"]):
                return 0.1  # 100mA
            
            # Passive components draw minimal current
            elif ref.startswith(("R", "C", "L")):
                return 0.001  # 1mA
            
            # Default
            return 0.01  # 10mA
            
        except Exception as e:
            print(f"Error estimating component current: {e}")
            return 0.01

    def _calculate_track_resistance(self, tracks: List[pcbnew.TRACK]) -> float:
        """Calculate total resistance of tracks."""
        try:
            total_resistance = 0.0
            for track in tracks:
                length_mm = track.GetLength() / 1e6
                width_mm = track.GetWidth() / 1e6
                # Approximate resistance: 0.5mΩ per mm per mm width
                resistance = 0.0005 * length_mm / width_mm
                total_resistance += resistance
            
            return total_resistance
            
        except Exception as e:
            print(f"Error calculating track resistance: {e}")
            return 0.01  # Default 10mΩ

    def _calculate_psrr(self, opamp: pcbnew.FOOTPRINT, board: pcbnew.BOARD) -> float:
        """Calculate power supply rejection ratio for an op-amp."""
        try:
            # Find decoupling capacitors near op-amp
            opamp_pos = opamp.GetPosition()
            decoupling_caps = 0
            
            for footprint in board.GetFootprints():
                if footprint.GetReference().startswith("C"):
                    cap_pos = footprint.GetPosition()
                    distance = math.sqrt((opamp_pos.x - cap_pos.x)**2 + (opamp_pos.y - cap_pos.y)**2) / 1e6
                    if distance < self.max_decoupling_distance:
                        decoupling_caps += 1
            
            # PSRR calculation (simplified)
            # Base PSRR for typical op-amp: 80dB
            # Each decoupling cap improves PSRR by ~10dB
            base_psrr = 80.0
            improvement = decoupling_caps * 10.0
            
            return min(120.0, base_psrr + improvement)  # Cap at 120dB
            
        except Exception as e:
            print(f"Error calculating PSRR: {e}")
            return 80.0  # Default PSRR 