"""Schematic to PCB layout converter for audio circuits."""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pcbnew
from ..rules.design import AudioDesignRules, SignalType
from ..validation.audio_validator import AudioPCBValidator
from ..validation.schematic.validator import AudioSchematicValidator
from ..components.stability import StabilityManager, FilterType, FilterSpec
from .modular_synth_layout_rules import ModularSynthLayoutRules
import logging
import math

logger = logging.getLogger(__name__)

@dataclass
class LayoutResult:
    """Result of a layout conversion."""
    success: bool
    board: Optional[pcbnew.BOARD] = None
    errors: List[str] = None
    warnings: List[str] = None

@dataclass
class StarGroundResult:
    """Result of star grounding implementation."""
    success: bool
    star_point: Optional[pcbnew.VECTOR2I] = None
    ground_connections: List[pcbnew.VECTOR2I] = None
    errors: List[str] = None

@dataclass
class GroundSeparationResult:
    """Result of analog/digital ground separation."""
    success: bool
    analog_ground_zone: Optional[pcbnew.ZONE] = None
    digital_ground_zone: Optional[pcbnew.ZONE] = None
    connection_point: Optional[pcbnew.VECTOR2I] = None
    errors: List[str] = None

class AudioLayoutConverter:
    """Converts schematics to PCB layouts following audio design principles."""
    
    def __init__(self, modular_mode: bool = False):
        """Initialize the layout converter."""
        self.design_rules = AudioDesignRules()
        self.pcb_validator = AudioPCBValidator()
        self.schematic_validator = AudioSchematicValidator()
        self.stability_manager = StabilityManager()
        self.modular_mode = modular_mode
        self.modular_rules = ModularSynthLayoutRules() if modular_mode else None
        
        # Audio-specific layout parameters
        self.star_ground_distance_threshold = 50.0  # mm - max distance to star point
        self.analog_digital_separation_distance = 10.0  # mm - min separation
        self.audio_component_spacing = 5.0  # mm - min spacing between audio components
        self.power_decoupling_distance = 3.0  # mm - max distance for decoupling caps
    
    def convert_schematic(self, schematic: Any) -> LayoutResult:
        """Convert a schematic to a PCB layout.
        
        Args:
            schematic: KiCad schematic object
            
        Returns:
            Layout result containing the converted board and any errors/warnings
        """
        # Validate schematic
        validation_results = self.schematic_validator.validate_schematic(schematic)
        errors = [r.message for r in validation_results if r.severity == "error"]
        warnings = [r.message for r in validation_results if r.severity == "warning"]
        
        if errors:
            return LayoutResult(success=False, board=None, errors=errors, warnings=warnings)
        
        # Create board
        board = pcbnew.BOARD()
        
        # Setup board
        self._setup_board(board)
        
        # Add components
        self._add_components(board, schematic)
        
        # Add stability components
        self._add_stability_components(board)
        
        # Add nets
        self._add_nets(board, schematic)
        
        # Apply advanced audio layout features
        self._apply_advanced_audio_layout(board)
        
        # Add power planes
        self._add_power_planes(board)
        
        # Add ground planes
        self._add_ground_planes(board)
        
        # Route signals
        self._route_signals(board)
        
        # Validate layout
        layout_results = self.pcb_validator.validate_board(board)
        errors.extend([r.message for r in layout_results if r.severity == "error"])
        warnings.extend([r.message for r in layout_results if r.severity == "warning"])
        
        # Modular synth-specific validation
        if self.modular_mode and self.modular_rules:
            modular_errors = self.modular_rules.validate(board)
            errors.extend(modular_errors)
        
        return LayoutResult(
            success=len(errors) == 0,
            board=board,
            errors=errors,
            warnings=warnings
        )
    
    def _setup_board(self, board: pcbnew.BOARD):
        """Setup board parameters."""
        # Set board thickness
        board.SetBoardThickness(1.6)  # 1.6mm
        
        # Set copper weight
        board.SetCopperWeight(1)  # 1oz
        
        # Enable layers
        board.SetEnabledLayers(
            pcbnew.F_Cu |  # Front copper
            pcbnew.B_Cu |  # Back copper
            pcbnew.In1_Cu |  # Inner layer 1
            pcbnew.In2_Cu |  # Inner layer 2
            pcbnew.F_SilkS |  # Front silkscreen
            pcbnew.B_SilkS |  # Back silkscreen
            pcbnew.Edge_Cuts  # Board outline
        )
        
        # Set design rules
        rules = board.GetDesignSettings()
        rules.SetTrackWidth(self.design_rules.signal_path_width)
        rules.SetViasMinSize(self.design_rules.via_diameter)
        rules.SetMinClearance(self.design_rules.signal_path_clearance)
    
    def _add_components(self, board: pcbnew.BOARD, schematic: Any):
        """Add components to the board with audio-specific placement."""
        # Get board dimensions
        bbox = board.GetBoardEdgesBoundingBox()
        width = bbox.GetWidth()
        height = bbox.GetHeight()
        
        # Define placement zones with margin
        margin = int(width * 0.1)  # 10% margin
        center_x = width // 2
        center_y = height // 2
        
        # Group components by type
        components = schematic.GetComponents()
        opamps = [c for c in components if c.GetValue().startswith("OPA")]
        connectors = [c for c in components if c.GetValue().startswith(("AUDIO", "POWER"))]
        passives = [c for c in components if c.GetValue().startswith(("R", "C", "L"))]
        power = [c for c in components if c.GetValue().startswith("POWER")]
        
        # Place opamps in center
        for i, opamp in enumerate(opamps):
            row = i // 2
            col = i % 2
            x = center_x + (col - 0.5) * int(width * 0.2)  # 20% spacing
            y = center_y + (row - 0.5) * int(height * 0.2)
            
            footprint = pcbnew.FOOTPRINT(board)
            footprint.SetReference(opamp.GetReference())
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))
            board.Add(footprint)
            
            # Add decoupling capacitors
            self._place_decoupling_capacitors(opamp, passives, board, schematic)
        
        # Place connectors on edges
        for i, conn in enumerate(connectors):
            if "IN" in conn.GetValue():
                # Input connectors on left
                x = margin
                y = margin + i * int(height * 0.2)
            elif "OUT" in conn.GetValue():
                # Output connectors on right
                x = width - margin
                y = margin + i * int(height * 0.2)
            else:
                # Power connectors on top
                x = margin + i * int(width * 0.2)
                y = margin
            
            footprint = pcbnew.FOOTPRINT(board)
            footprint.SetReference(conn.GetReference())
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))
            board.Add(footprint)
        
        # Place passives near associated opamps
        for passive in passives:
            # Find connected opamp
            connected_opamp = None
            for opamp in opamps:
                if self._are_components_connected(passive, opamp, schematic):
                    connected_opamp = opamp
                    break
            
            if connected_opamp:
                opamp_pos = self._get_component_position(connected_opamp, board)
                x = opamp_pos.x + int(width * 0.02)  # 2% offset
                y = opamp_pos.y + int(height * 0.02)
            else:
                # Place unconnected passives in a grid
                x = margin + len(passives) * int(width * 0.02)
                y = margin + len(passives) * int(height * 0.02)
            
            footprint = pcbnew.FOOTPRINT(board)
            footprint.SetReference(passive.GetReference())
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))
            board.Add(footprint)
        
        # Place power components at top
        for i, power_comp in enumerate(power):
            x = margin + i * int(width * 0.2)
            y = margin * 2  # Double margin from top
            
            footprint = pcbnew.FOOTPRINT(board)
            footprint.SetReference(power_comp.GetReference())
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))
            board.Add(footprint)
    
    def _add_stability_components(self, board: pcbnew.BOARD):
        """Add stability and filtering components."""
        # Add ferrite beads for power supply filtering
        self.stability_manager.add_ferrite_bead("FB1", 100, 1.0)  # Main power
        self.stability_manager.add_ferrite_bead("FB2", 100, 0.5)  # Analog power
        
        # Add EMC filters for input/output
        emc_filter_spec = FilterSpec(
            type=FilterType.EMI,
            cutoff_freq=1e6,  # 1MHz
            order=2,
            attenuation=-40
        )
        self.stability_manager.add_emc_filter("EMC1", emc_filter_spec)  # Input
        self.stability_manager.add_emc_filter("EMC2", emc_filter_spec)  # Output
        
        # Add power supply filters
        self.stability_manager.add_power_filter("C1", 10.0, 16.0)  # Main power
        self.stability_manager.add_power_filter("C2", 1.0, 16.0)   # Analog power
        
        # Add audio filters
        audio_filter_spec = FilterSpec(
            type=FilterType.LOW_PASS,
            cutoff_freq=20e3,  # 20kHz
            order=2,
            ripple=0.1
        )
        self.stability_manager.add_audio_filter("AF1", audio_filter_spec)  # Input
        self.stability_manager.add_audio_filter("AF2", audio_filter_spec)  # Output
        
        # Place stability components
        for component in self.stability_manager.get_components():
            footprint = pcbnew.FOOTPRINT(board)
            footprint.SetReference(component.reference)
            
            # Place based on component type
            if component.type == "ferrite":
                # Place ferrite beads near power components
                x = int(board.GetBoardEdgesBoundingBox().GetWidth() * 0.1)  # 10% margin
                y = int(board.GetBoardEdgesBoundingBox().GetHeight() * 0.1)
            elif component.type == "emc_filter":
                # Place EMC filters near connectors
                x = int(board.GetBoardEdgesBoundingBox().GetWidth() * 0.9)  # 90% width
                y = int(board.GetBoardEdgesBoundingBox().GetHeight() * 0.1)
            elif component.type == "capacitor":
                # Place power filter capacitors near power components
                x = int(board.GetBoardEdgesBoundingBox().GetWidth() * 0.2)  # 20% width
                y = int(board.GetBoardEdgesBoundingBox().GetHeight() * 0.1)
            else:  # audio_filter
                # Place audio filters near opamps
                x = int(board.GetBoardEdgesBoundingBox().GetWidth() * 0.5)  # Center
                y = int(board.GetBoardEdgesBoundingBox().GetHeight() * 0.5)
            
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))
            board.Add(footprint)
    
    def _place_decoupling_capacitors(self, opamp: Any, passives: List[Any], board: pcbnew.BOARD, schematic: Any):
        """Place decoupling capacitors next to opamps."""
        # Find decoupling capacitors
        decoupling = []
        for passive in passives:
            if (passive.GetValue().startswith("C") and 
                self._are_components_connected(passive, opamp, schematic)):
                decoupling.append(passive)
        
        # Place capacitors
        opamp_pos = self._get_component_position(opamp, board)
        for i, cap in enumerate(decoupling):
            x = opamp_pos.x + int(board.GetBoardEdgesBoundingBox().GetWidth() * 0.02)  # 2% offset
            y = opamp_pos.y + (i * int(board.GetBoardEdgesBoundingBox().GetWidth() * 0.02))
            
            footprint = pcbnew.FOOTPRINT(board)
            footprint.SetReference(cap.GetReference())
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))
            board.Add(footprint)
    
    def _are_components_connected(self, comp1: Any, comp2: Any, schematic: Any) -> bool:
        """Check if two components are connected."""
        comp1_pins = comp1.GetPins()
        comp2_pins = comp2.GetPins()
        
        for pin1 in comp1_pins:
            for pin2 in comp2_pins:
                if pin1.GetNetname() == pin2.GetNetname():
                    return True
        return False
    
    def _get_component_position(self, component: Any, board: pcbnew.BOARD) -> pcbnew.VECTOR2I:
        """Get the position of a component on the board."""
        for footprint in board.GetFootprints():
            if footprint.GetReference() == component.GetReference():
                return footprint.GetPosition()
        return pcbnew.VECTOR2I(0, 0)
    
    def _get_connected_components(self, net: Any, board: pcbnew.BOARD) -> List[Any]:
        """Get components connected to a net."""
        connected = []
        for footprint in board.GetFootprints():
            for pad in footprint.GetPads():
                if pad.GetNetname() == net.GetNetname():
                    connected.append(footprint)
                    break
        return connected
    
    def _calculate_audio_path(self, start: Any, end: Any, board: pcbnew.BOARD) -> List[pcbnew.VECTOR2I]:
        """Calculate a curved path for audio signals."""
        start_pos = start.GetPosition()
        end_pos = end.GetPosition()
        
        # Calculate midpoint
        mid_x = (start_pos.x + end_pos.x) // 2
        mid_y = (start_pos.y + end_pos.y) // 2
        
        # Add curve offset
        curve_offset = int(board.GetBoardEdgesBoundingBox().GetWidth() * 0.02)  # 2% of board width
        mid_y += curve_offset
        
        return [
            start_pos,
            pcbnew.VECTOR2I(mid_x, mid_y),
            end_pos
        ]
    
    def _calculate_digital_path(self, start: Any, end: Any, board: pcbnew.BOARD) -> List[pcbnew.VECTOR2I]:
        """Calculate a path for digital signals, routing around the center."""
        start_pos = start.GetPosition()
        end_pos = end.GetPosition()
        
        # Calculate intermediate points to route around center
        mid_x = (start_pos.x + end_pos.x) // 2
        mid_y = (start_pos.y + end_pos.y) // 2
        
        return [
            start_pos,
            pcbnew.VECTOR2I(mid_x, start_pos.y),  # First horizontal
            pcbnew.VECTOR2I(mid_x, end_pos.y),    # Then vertical
            end_pos
        ]
    
    def _add_nets(self, board: pcbnew.BOARD, schematic: Any):
        """Add nets to the board."""
        for net in schematic.GetNets():
            board_net = pcbnew.NETINFO_ITEM(board, net.GetNetname())
            board.Add(board_net)
            
            # Set net class based on name
            if "AUDIO" in net.GetNetname():
                board_net.SetNetClass("Audio")
            elif "POWER" in net.GetNetname():
                board_net.SetNetClass("Power")
            elif "GND" in net.GetNetname():
                board_net.SetNetClass("Ground")
            else:
                board_net.SetNetClass("Signal")
    
    def _add_power_planes(self, board: pcbnew.BOARD):
        """Add power planes."""
        for net in board.GetNets():
            if "POWER" in net.GetNetname():
                zone = pcbnew.ZONE(board)
                zone.SetNet(net)
                zone.SetLayer(pcbnew.In1_Cu)
                zone.SetLocalClearance(self.design_rules.power_plane_clearance)
                zone.SetMinThickness(self.design_rules.power_plane_width)
                board.Add(zone)
    
    def _add_ground_planes(self, board: pcbnew.BOARD):
        """Add ground planes."""
        for net in board.GetNets():
            if "GND" in net.GetNetname():
                zone = pcbnew.ZONE(board)
                zone.SetNet(net)
                zone.SetLayer(pcbnew.In2_Cu)
                zone.SetLocalClearance(self.design_rules.ground_plane_clearance)
                zone.SetMinThickness(self.design_rules.ground_plane_width)
                board.Add(zone)
    
    def _route_signals(self, board: pcbnew.BOARD):
        """Route signals with audio-specific considerations."""
        for net in board.GetNets():
            components = self._get_connected_components(net, board)
            if len(components) < 2:
                continue
            
            # Route between each pair of components
            for i in range(len(components) - 1):
                start = components[i]
                end = components[i + 1]
                
                # Calculate path based on net type
                if "AUDIO" in net.GetNetname():
                    path = self._calculate_audio_path(start, end, board)
                else:
                    path = self._calculate_digital_path(start, end, board)
                
                # Create track
                track = pcbnew.TRACK(board)
                track.SetNet(net)
                
                # Set track properties based on net type
                if "AUDIO" in net.GetNetname():
                    track.SetWidth(self.design_rules.audio_signal_width)
                    track.SetClearance(self.design_rules.audio_signal_clearance)
                    track.SetLayer(pcbnew.F_Cu)
                elif "POWER" in net.GetNetname():
                    track.SetWidth(self.design_rules.power_signal_width)
                    track.SetClearance(self.design_rules.power_signal_clearance)
                    track.SetLayer(pcbnew.In1_Cu)
                elif "GND" in net.GetNetname():
                    track.SetWidth(self.design_rules.ground_signal_width)
                    track.SetClearance(self.design_rules.ground_signal_clearance)
                    track.SetLayer(pcbnew.In2_Cu)
                else:
                    track.SetWidth(self.design_rules.signal_path_width)
                    track.SetClearance(self.design_rules.signal_path_clearance)
                    track.SetLayer(pcbnew.F_Cu)
                
                # Set track points
                track.SetStart(path[0])
                track.SetEnd(path[-1])
                
                # Add intermediate points for curved paths
                for point in path[1:-1]:
                    track.AddPoint(point)
                
                board.Add(track)

    def _apply_advanced_audio_layout(self, board: pcbnew.BOARD) -> None:
        """Apply advanced audio layout features including star grounding and ground separation."""
        try:
            # Import power decoupling optimizer
            from .power_decoupling import PowerDecouplingOptimizer
            
            # Initialize optimizers
            decoupling_optimizer = PowerDecouplingOptimizer()
            
            # Place audio components optimally
            self.place_audio_components(board)
            
            # Implement star grounding
            star_ground_result = self.implement_star_grounding(board)
            if not star_ground_result.success:
                print(f"Warning: Star grounding failed: {star_ground_result.errors}")
            
            # Separate analog and digital grounds
            ground_separation_result = self.separate_analog_digital_grounds(board)
            if not ground_separation_result.success:
                print(f"Warning: Ground separation failed: {ground_separation_result.errors}")
            
            # Optimize power decoupling
            opamps = [f for f in board.GetFootprints() if f.GetReference().startswith("U")]
            decoupling_result = decoupling_optimizer.optimize_decoupling(board)
            if decoupling_result.success:
                print(f"Placed {len(decoupling_result.placed_capacitors)} decoupling capacitors")
                print(f"Power rail optimizations: {len(decoupling_result.power_rail_optimizations)}")
            else:
                print(f"Warning: Power decoupling optimization failed: {decoupling_result.errors}")
            
            # Analyze power supply rejection
            psrr_analysis = decoupling_optimizer.analyze_power_supply_rejection(board)
            for opamp, psrr in psrr_analysis.items():
                logger.info(f"PSRR for {opamp}: {psrr:.1f} dB")
            
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Input error applying advanced audio layout: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error applying advanced audio layout: {str(e)}")

    def implement_star_grounding(self, board: pcbnew.BOARD) -> StarGroundResult:
        """Implement star grounding for audio circuits.
        
        Args:
            board: KiCad board object
            
        Returns:
            StarGroundResult with star point and ground connections
        """
        try:
            # Find optimal star ground point
            star_point = self._find_optimal_star_ground_point(board)
            if not star_point:
                return StarGroundResult(
                    success=False,
                    errors=["Could not determine optimal star ground point"]
                )
            
            # Find all ground connections
            ground_connections = self._find_ground_connections(board)
            
            # Route all grounds to star point
            routed_connections = []
            for connection in ground_connections:
                if self._route_ground_to_star_point(board, connection, star_point):
                    routed_connections.append(connection)
            
            # Create star ground zone
            self._create_star_ground_zone(board, star_point)
            
            return StarGroundResult(
                success=True,
                star_point=star_point,
                ground_connections=routed_connections,
                errors=[]
            )
        except (ValueError, KeyError, TypeError) as e:
            error_msg = f"Input error implementing star grounding: {str(e)}"
            logger.error(error_msg)
            return StarGroundResult(
                success=False,
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Unexpected error implementing star grounding: {str(e)}"
            logger.error(error_msg)
            return StarGroundResult(
                success=False,
                errors=[error_msg]
            )

    def separate_analog_digital_grounds(self, board: pcbnew.BOARD) -> GroundSeparationResult:
        """Separate and properly connect analog and digital grounds.
        
        Args:
            board: KiCad board object
            
        Returns:
            GroundSeparationResult with separated ground zones
        """
        try:
            # Identify analog and digital components
            analog_components = self._identify_analog_components(board)
            digital_components = self._identify_digital_components(board)
            
            # Create separate ground zones
            analog_ground_zone = self._create_analog_ground_zone(board, analog_components)
            digital_ground_zone = self._create_digital_ground_zone(board, digital_components)
            
            # Find optimal connection point
            connection_point = self._find_ground_connection_point(board, analog_ground_zone, digital_ground_zone)
            
            # Connect grounds at single point
            if connection_point:
                self._connect_grounds_at_point(board, analog_ground_zone, digital_ground_zone, connection_point)
            
            return GroundSeparationResult(
                success=True,
                analog_ground_zone=analog_ground_zone,
                digital_ground_zone=digital_ground_zone,
                connection_point=connection_point,
                errors=[]
            )
        except (ValueError, KeyError, TypeError) as e:
            error_msg = f"Input error separating analog/digital grounds: {str(e)}"
            logger.error(error_msg)
            return GroundSeparationResult(
                success=False,
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Unexpected error separating analog/digital grounds: {str(e)}"
            logger.error(error_msg)
            return GroundSeparationResult(
                success=False,
                errors=[error_msg]
            )

    def place_audio_components(self, board: pcbnew.BOARD) -> bool:
        """Place components according to audio-specific rules.
        
        Args:
            board: KiCad board object
            
        Returns:
            True if placement was successful
        """
        try:
            # Get all components
            footprints = list(board.GetFootprints())
            
            # Group components by type
            opamps = [f for f in footprints if f.GetReference().startswith("U")]
            connectors = [f for f in footprints if f.GetReference().startswith(("J", "CONN"))]
            passives = [f for f in footprints if f.GetReference().startswith(("R", "C", "L"))]
            power_components = [f for f in footprints if f.GetReference().startswith(("POWER", "REG"))]
            
            # Get board dimensions
            bbox = board.ComputeBoundingBox()
            board_width = bbox.GetWidth() / 1e6  # Convert to mm
            board_height = bbox.GetHeight() / 1e6
            
            # Place op-amps in center for short signal paths
            self._place_opamps_center(board, opamps, board_width, board_height)
            
            # Place input connectors on left edge
            input_connectors = [c for c in connectors if "IN" in c.GetReference().upper()]
            self._place_connectors_edge(board, input_connectors, "left", board_width, board_height)
            
            # Place output connectors on right edge
            output_connectors = [c for c in connectors if "OUT" in c.GetReference().upper()]
            self._place_connectors_edge(board, output_connectors, "right", board_width, board_height)
            
            # Place power components at top
            self._place_power_components_top(board, power_components, board_width, board_height)
            
            # Place passive components near associated op-amps
            self._place_passives_near_opamps(board, passives, opamps)
            
            # Place decoupling capacitors close to power pins
            self._place_decoupling_capacitors_optimized(board, passives, opamps)
            
            return True
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Input error placing audio components: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error placing audio components: {str(e)}")
            return False

    # --- Helper methods for star grounding ---
    def _find_optimal_star_ground_point(self, board: pcbnew.BOARD) -> Optional[pcbnew.VECTOR2I]:
        """Find the optimal star ground point on the board."""
        try:
            # Get board center
            bbox = board.ComputeBoundingBox()
            center_x = bbox.GetCenter().x
            center_y = bbox.GetCenter().y
            
            # Find power supply components (likely to be near star ground)
            power_components = []
            for footprint in board.GetFootprints():
                ref = footprint.GetReference().upper()
                if any(keyword in ref for keyword in ["POWER", "REG", "PSU", "VCC", "VDD"]):
                    power_components.append(footprint)
            
            if power_components:
                # Use center of power components
                total_x = sum(f.GetPosition().x for f in power_components)
                total_y = sum(f.GetPosition().y for f in power_components)
                star_x = total_x // len(power_components)
                star_y = total_y // len(power_components)
            else:
                # Use board center
                star_x = center_x
                star_y = center_y
            
            return pcbnew.VECTOR2I(star_x, star_y)
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error finding star ground point: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error finding star ground point: {str(e)}")
            return None

    def _find_ground_connections(self, board: pcbnew.BOARD) -> List[pcbnew.VECTOR2I]:
        """Find all ground connection points on the board."""
        ground_connections = []
        
        try:
            for footprint in board.GetFootprints():
                for pad in footprint.GetPads():
                    net_name = pad.GetNetname().upper()
                    if net_name in ("GND", "GROUND", "AGND", "DGND"):
                        ground_connections.append(pad.GetPosition())
            
            return ground_connections
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error finding ground connections: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error finding ground connections: {str(e)}")
            return []

    def _route_ground_to_star_point(self, board: pcbnew.BOARD, connection: pcbnew.VECTOR2I, star_point: pcbnew.VECTOR2I) -> bool:
        """Route a ground connection to the star point."""
        try:
            # Create ground track
            track = pcbnew.TRACK(board)
            track.SetStart(connection)
            track.SetEnd(star_point)
            track.SetWidth(int(self.design_rules.ground_signal_width * 1e6))  # Convert to nanometers
            track.SetLayer(pcbnew.F_Cu)
            
            # Set net to ground
            ground_net = board.GetNetcodeFromNetname("GND")
            if ground_net >= 0:
                track.SetNetCode(ground_net)
            
            # Add track to board
            board.Add(track)
            return True
        except (AttributeError, ValueError) as e:
            logger.error(f"Board data error routing ground to star point: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error routing ground to star point: {str(e)}")
            return False

    def _create_star_ground_zone(self, board: pcbnew.BOARD, star_point: pcbnew.VECTOR2I) -> None:
        """Create a ground zone around the star point."""
        try:
            # Create ground zone
            zone = pcbnew.ZONE(board)
            zone.SetLayer(pcbnew.F_Cu)
            zone.SetLocalClearance(int(self.design_rules.ground_plane_clearance * 1e6))
            zone.SetMinThickness(int(self.design_rules.ground_plane_width * 1e6))
            
            # Set zone outline around star point
            zone_size = int(5 * 1e6)  # 5mm zone around star point
            zone_outline = [
                pcbnew.VECTOR2I(star_point.x - zone_size, star_point.y - zone_size),
                pcbnew.VECTOR2I(star_point.x + zone_size, star_point.y - zone_size),
                pcbnew.VECTOR2I(star_point.x + zone_size, star_point.y + zone_size),
                pcbnew.VECTOR2I(star_point.x - zone_size, star_point.y + zone_size)
            ]
            
            zone.SetOutline(zone_outline)
            
            # Find ground net
            for net in board.GetNets():
                if "GND" in net.GetNetname().upper():
                    zone.SetNet(net)
                    break
            
            board.Add(zone)
            
        except Exception as e:
            print(f"Error creating star ground zone: {e}")

    # --- Helper methods for ground separation ---
    def _identify_analog_components(self, board: pcbnew.BOARD) -> List[pcbnew.FOOTPRINT]:
        """Identify analog components on the board."""
        analog_components = []
        
        try:
            for footprint in board.GetFootprints():
                ref = footprint.GetReference().upper()
                value = footprint.GetValue().upper()
                
                # Audio-specific components
                if (ref.startswith("U") and "OPA" in value) or \
                   ref.startswith(("AUDIO", "IN", "OUT")) or \
                   value.startswith(("OPA", "TL", "NE", "LM")):
                    analog_components.append(footprint)
            
            return analog_components
            
        except Exception as e:
            print(f"Error identifying analog components: {e}")
            return []

    def _identify_digital_components(self, board: pcbnew.BOARD) -> List[pcbnew.FOOTPRINT]:
        """Identify digital components on the board."""
        digital_components = []
        
        try:
            for footprint in board.GetFootprints():
                ref = footprint.GetReference().upper()
                value = footprint.GetValue().upper()
                
                # Digital components
                if (ref.startswith("U") and any(keyword in value for keyword in ["MCU", "CPU", "DSP", "FPGA", "CLK", "OSC"])) or \
                   ref.startswith(("DIGITAL", "CLK", "OSC")):
                    digital_components.append(footprint)
            
            return digital_components
            
        except Exception as e:
            print(f"Error identifying digital components: {e}")
            return []

    def _create_analog_ground_zone(self, board: pcbnew.BOARD, analog_components: List[pcbnew.FOOTPRINT]) -> Optional[pcbnew.ZONE]:
        """Create analog ground zone."""
        try:
            if not analog_components:
                return None
            
            # Calculate analog zone bounds
            min_x = min(f.GetPosition().x for f in analog_components)
            max_x = max(f.GetPosition().x for f in analog_components)
            min_y = min(f.GetPosition().y for f in analog_components)
            max_y = max(f.GetPosition().y for f in analog_components)
            
            # Add margin
            margin = int(10 * 1e6)  # 10mm margin
            zone_outline = [
                pcbnew.VECTOR2I(min_x - margin, min_y - margin),
                pcbnew.VECTOR2I(max_x + margin, min_y - margin),
                pcbnew.VECTOR2I(max_x + margin, max_y + margin),
                pcbnew.VECTOR2I(min_x - margin, max_y + margin)
            ]
            
            zone = pcbnew.ZONE(board)
            zone.SetLayer(pcbnew.In2_Cu)  # Inner layer 2
            zone.SetLocalClearance(int(self.design_rules.ground_plane_clearance * 1e6))
            zone.SetMinThickness(int(self.design_rules.ground_plane_width * 1e6))
            zone.SetOutline(zone_outline)
            
            # Set to analog ground net
            for net in board.GetNets():
                if "AGND" in net.GetNetname().upper():
                    zone.SetNet(net)
                    break
            
            board.Add(zone)
            return zone
            
        except Exception as e:
            print(f"Error creating analog ground zone: {e}")
            return None

    def _create_digital_ground_zone(self, board: pcbnew.BOARD, digital_components: List[pcbnew.FOOTPRINT]) -> Optional[pcbnew.ZONE]:
        """Create digital ground zone."""
        try:
            if not digital_components:
                return None
            
            # Calculate digital zone bounds
            min_x = min(f.GetPosition().x for f in digital_components)
            max_x = max(f.GetPosition().x for f in digital_components)
            min_y = min(f.GetPosition().y for f in digital_components)
            max_y = max(f.GetPosition().y for f in digital_components)
            
            # Add margin
            margin = int(10 * 1e6)  # 10mm margin
            zone_outline = [
                pcbnew.VECTOR2I(min_x - margin, min_y - margin),
                pcbnew.VECTOR2I(max_x + margin, min_y - margin),
                pcbnew.VECTOR2I(max_x + margin, max_y + margin),
                pcbnew.VECTOR2I(min_x - margin, max_y + margin)
            ]
            
            zone = pcbnew.ZONE(board)
            zone.SetLayer(pcbnew.In2_Cu)  # Inner layer 2
            zone.SetLocalClearance(int(self.design_rules.ground_plane_clearance * 1e6))
            zone.SetMinThickness(int(self.design_rules.ground_plane_width * 1e6))
            zone.SetOutline(zone_outline)
            
            # Set to digital ground net
            for net in board.GetNets():
                if "DGND" in net.GetNetname().upper():
                    zone.SetNet(net)
                    break
            
            board.Add(zone)
            return zone
            
        except Exception as e:
            print(f"Error creating digital ground zone: {e}")
            return None

    def _find_ground_connection_point(self, board: pcbnew.BOARD, analog_zone: pcbnew.ZONE, digital_zone: pcbnew.ZONE) -> Optional[pcbnew.VECTOR2I]:
        """Find optimal point to connect analog and digital grounds."""
        try:
            # Use board center as connection point
            bbox = board.ComputeBoundingBox()
            center_x = bbox.GetCenter().x
            center_y = bbox.GetCenter().y
            
            return pcbnew.VECTOR2I(center_x, center_y)
            
        except Exception as e:
            print(f"Error finding ground connection point: {e}")
            return None

    def _connect_grounds_at_point(self, board: pcbnew.BOARD, analog_zone: pcbnew.ZONE, digital_zone: pcbnew.ZONE, connection_point: pcbnew.VECTOR2I) -> None:
        """Connect analog and digital grounds at a single point."""
        try:
            # Create connection track
            track = pcbnew.TRACK(board)
            track.SetStart(connection_point)
            track.SetEnd(connection_point)  # Same point for now
            track.SetWidth(int(self.design_rules.ground_signal_width * 1e6))
            track.SetLayer(pcbnew.In2_Cu)
            
            # Find main ground net
            for net in board.GetNets():
                if "GND" in net.GetNetname().upper():
                    track.SetNet(net)
                    break
            
            board.Add(track)
            
        except Exception as e:
            print(f"Error connecting grounds: {e}")

    # --- Helper methods for audio component placement ---
    def _place_opamps_center(self, board: pcbnew.BOARD, opamps: List[pcbnew.FOOTPRINT], board_width: float, board_height: float) -> None:
        """Place op-amps in the center of the board."""
        try:
            center_x = int(board_width * 1e6 / 2)
            center_y = int(board_height * 1e6 / 2)
            
            for i, opamp in enumerate(opamps):
                # Arrange in a grid pattern
                row = i // 2
                col = i % 2
                spacing = int(20 * 1e6)  # 20mm spacing
                
                x = center_x + (col - 0.5) * spacing
                y = center_y + (row - 0.5) * spacing
                
                opamp.SetPosition(pcbnew.VECTOR2I(x, y))
                
        except Exception as e:
            print(f"Error placing op-amps: {e}")

    def _place_connectors_edge(self, board: pcbnew.BOARD, connectors: List[pcbnew.FOOTPRINT], edge: str, board_width: float, board_height: float) -> None:
        """Place connectors on specified edge."""
        try:
            margin = int(10 * 1e6)  # 10mm margin
            spacing = int(20 * 1e6)  # 20mm spacing
            
            for i, connector in enumerate(connectors):
                if edge == "left":
                    x = margin
                    y = margin + i * spacing
                elif edge == "right":
                    x = int(board_width * 1e6) - margin
                    y = margin + i * spacing
                else:
                    continue
                
                connector.SetPosition(pcbnew.VECTOR2I(x, y))
                
        except Exception as e:
            print(f"Error placing connectors: {e}")

    def _place_power_components_top(self, board: pcbnew.BOARD, power_components: List[pcbnew.FOOTPRINT], board_width: float, board_height: float) -> None:
        """Place power components at the top of the board."""
        try:
            margin = int(10 * 1e6)  # 10mm margin
            spacing = int(30 * 1e6)  # 30mm spacing
            
            for i, component in enumerate(power_components):
                x = margin + i * spacing
                y = margin
                
                component.SetPosition(pcbnew.VECTOR2I(x, y))
                
        except Exception as e:
            print(f"Error placing power components: {e}")

    def _place_passives_near_opamps(self, board: pcbnew.BOARD, passives: List[pcbnew.FOOTPRINT], opamps: List[pcbnew.FOOTPRINT]) -> None:
        """Place passive components near associated op-amps."""
        try:
            for passive in passives:
                # Find closest op-amp
                closest_opamp = None
                min_distance = float('inf')
                
                for opamp in opamps:
                    distance = self._calculate_distance(passive.GetPosition(), opamp.GetPosition())
                    if distance < min_distance:
                        min_distance = distance
                        closest_opamp = opamp
                
                if closest_opamp:
                    # Place near op-amp
                    opamp_pos = closest_opamp.GetPosition()
                    offset = int(5 * 1e6)  # 5mm offset
                    
                    passive.SetPosition(pcbnew.VECTOR2I(
                        opamp_pos.x + offset,
                        opamp_pos.y + offset
                    ))
                
        except Exception as e:
            print(f"Error placing passives: {e}")

    def _place_decoupling_capacitors_optimized(self, board: pcbnew.BOARD, passives: List[pcbnew.FOOTPRINT], opamps: List[pcbnew.FOOTPRINT]) -> None:
        """Place decoupling capacitors optimally close to power pins."""
        try:
            decoupling_caps = [p for p in passives if p.GetReference().startswith("C") and "DEC" in p.GetReference().upper()]
            
            for cap in decoupling_caps:
                # Find associated op-amp
                closest_opamp = None
                min_distance = float('inf')
                
                for opamp in opamps:
                    distance = self._calculate_distance(cap.GetPosition(), opamp.GetPosition())
                    if distance < min_distance:
                        min_distance = distance
                        closest_opamp = opamp
                
                if closest_opamp:
                    # Place very close to op-amp power pins
                    opamp_pos = closest_opamp.GetPosition()
                    offset = int(2 * 1e6)  # 2mm offset for decoupling
                    
                    cap.SetPosition(pcbnew.VECTOR2I(
                        opamp_pos.x + offset,
                        opamp_pos.y + offset
                    ))
                
        except Exception as e:
            print(f"Error placing decoupling capacitors: {e}")

    def _calculate_distance(self, pos1: pcbnew.VECTOR2I, pos2: pcbnew.VECTOR2I) -> float:
        """Calculate distance between two positions."""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        return (dx * dx + dy * dy) ** 0.5 