"""Schematic topology analysis for audio circuits."""
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import networkx as nx
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ComponentNode:
    """Represents a component in the schematic topology."""
    reference: str
    value: str
    component_type: str
    position: Tuple[float, float]
    pins: List[str]
    nets: List[str]
    power_pins: List[str]
    signal_pins: List[str]

@dataclass
class SignalPath:
    """Represents a signal path in the schematic."""
    start_component: str
    end_component: str
    path_components: List[str]
    path_nets: List[str]
    length: float
    impedance: float
    signal_type: str  # "audio", "power", "control", "digital"

@dataclass
class CriticalPath:
    """Represents a critical signal path that requires special attention."""
    path: SignalPath
    criticality_score: float
    issues: List[str]
    recommendations: List[str]

@dataclass
class NoiseSource:
    """Represents a potential noise source in the circuit."""
    component: str
    noise_type: str  # "switching", "thermal", "shot", "flicker"
    frequency_range: Tuple[float, float]
    amplitude: float
    affected_components: List[str]

@dataclass
class TopologyAnalysis:
    """Results of schematic topology analysis."""
    components: Dict[str, ComponentNode]
    signal_paths: List[SignalPath]
    critical_paths: List[CriticalPath]
    noise_sources: List[NoiseSource]
    component_dependencies: Dict[str, List[str]]
    ground_references: Dict[str, str]
    power_distribution: Dict[str, List[str]]
    analysis_score: float

class SignalType(Enum):
    """Types of signals in audio circuits."""
    AUDIO = "audio"
    POWER = "power"
    CONTROL = "control"
    DIGITAL = "digital"
    GROUND = "ground"

class ComponentType(Enum):
    """Types of components in audio circuits."""
    OPAMP = "opamp"
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    TRANSISTOR = "transistor"
    DIODE = "diode"
    CONNECTOR = "connector"
    REGULATOR = "regulator"
    OSCILLATOR = "oscillator"
    MICROCONTROLLER = "microcontroller"

class SchematicTopologyAnalyzer:
    """Analyzes schematic topology for audio circuits."""
    
    def __init__(self):
        """Initialize the schematic topology analyzer."""
        # Audio-specific analysis parameters with extended bandwidth support
        self.audio_frequency_range = (20, 80000)  # Hz - extended to 80kHz
        self.critical_path_threshold = 0.7  # Score threshold for critical paths
        self.max_signal_path_length = 100.0  # mm
        self.min_impedance_matching = 0.9  # 90% impedance matching required
        self.noise_threshold = -60.0  # dB - noise level threshold
        self.high_precision_mode = True  # Enable high-precision analysis
        self.extended_bandwidth_analysis = True  # Enable extended bandwidth analysis
        
        # Component type mappings
        self.component_type_mapping = {
            "OPA": ComponentType.OPAMP,
            "TL": ComponentType.OPAMP,
            "NE": ComponentType.OPAMP,
            "LM": ComponentType.OPAMP,
            "R": ComponentType.RESISTOR,
            "C": ComponentType.CAPACITOR,
            "L": ComponentType.INDUCTOR,
            "Q": ComponentType.TRANSISTOR,
            "D": ComponentType.DIODE,
            "J": ComponentType.CONNECTOR,
            "REG": ComponentType.REGULATOR,
            "OSC": ComponentType.OSCILLATOR,
            "MCU": ComponentType.MICROCONTROLLER,
        }
    
    def analyze_schematic(self, schematic_data: Dict[str, Any]) -> TopologyAnalysis:
        """Analyze schematic topology for audio circuits.
        
        Args:
            schematic_data: Dictionary containing schematic information
            
        Returns:
            TopologyAnalysis object with analysis results
        """
        try:
            # Parse components
            components = self._parse_components(schematic_data)
            
            # Build signal flow graph
            signal_graph = self._build_signal_flow_graph(components)
            
            # Analyze signal paths
            signal_paths = self._analyze_signal_paths(signal_graph, components)
            
            # Identify critical paths
            critical_paths = self._identify_critical_paths(signal_paths, components)
            
            # Analyze noise sources
            noise_sources = self._analyze_noise_sources(components)
            
            # Analyze component dependencies
            component_dependencies = self._analyze_component_dependencies(signal_graph)
            
            # Analyze ground references
            ground_references = self._analyze_ground_references(components)
            
            # Analyze power distribution
            power_distribution = self._analyze_power_distribution(components)
            
            # Calculate overall analysis score
            analysis_score = self._calculate_analysis_score(
                signal_paths, critical_paths, noise_sources
            )
            
            return TopologyAnalysis(
                components=components,
                signal_paths=signal_paths,
                critical_paths=critical_paths,
                noise_sources=noise_sources,
                component_dependencies=component_dependencies,
                ground_references=ground_references,
                power_distribution=power_distribution,
                analysis_score=analysis_score
            )
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error analyzing schematic topology: %s", e)
            raise
    
    def optimize_signal_flow(self, topology: TopologyAnalysis) -> List[Dict[str, Any]]:
        """Optimize signal flow based on topology analysis.
        
        Args:
            topology: TopologyAnalysis object
            
        Returns:
            List of optimization recommendations
        """
        optimizations = []
        
        try:
            # Optimize critical paths
            for critical_path in topology.critical_paths:
                if critical_path.criticality_score > 0.8:
                    optimizations.append({
                        "type": "critical_path_optimization",
                        "path": critical_path.path,
                        "recommendations": critical_path.recommendations,
                        "priority": "high"
                    })
            
            # Optimize noise sources
            for noise_source in topology.noise_sources:
                if noise_source.amplitude > self.noise_threshold:
                    optimizations.append({
                        "type": "noise_reduction",
                        "source": noise_source.component,
                        "recommendations": [
                            "Add shielding",
                            "Increase distance from sensitive components",
                            "Add filtering capacitors"
                        ],
                        "priority": "medium"
                    })
            
            # Optimize component placement
            placement_optimizations = self._optimize_component_placement(topology)
            optimizations.extend(placement_optimizations)
            
            return optimizations
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error optimizing signal flow: %s", e)
            return []

    def analyze_frequency_response(self, topology: TopologyAnalysis) -> Dict[str, Any]:
        """Analyze frequency response characteristics of the circuit.
        
        Args:
            topology: TopologyAnalysis object
            
        Returns:
            Dictionary with frequency response analysis
        """
        frequency_analysis = {}
        
        try:
            # Analyze audio signal paths
            audio_paths = [p for p in topology.signal_paths if p.signal_type == "audio"]
            
            for path in audio_paths:
                # Calculate frequency response based on components
                response = self._calculate_path_frequency_response(path, topology.components)
                frequency_analysis[path.start_component + "_to_" + path.end_component] = response
            
            # Analyze overall frequency response
            overall_response = self._calculate_overall_frequency_response(topology)
            frequency_analysis["overall"] = overall_response
            
            return frequency_analysis
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error analyzing frequency response: %s", e)
            return {}

    def identify_ground_loops(self, topology: TopologyAnalysis) -> List[Dict[str, Any]]:
        """Identify potential ground loops in the circuit.
        
        Args:
            topology: TopologyAnalysis object
            
        Returns:
            List of potential ground loops
        """
        ground_loops = []
        
        try:
            # Build ground connection graph
            ground_graph = nx.Graph()
            
            for component_ref, ground_ref in topology.ground_references.items():
                ground_graph.add_edge(component_ref, ground_ref)
            
            # Find cycles in ground connections
            cycles = list(nx.simple_cycles(ground_graph.to_directed()))
            
            for cycle in cycles:
                if len(cycle) > 2:  # Only consider loops with more than 2 components
                    ground_loops.append({
                        "components": cycle,
                        "severity": "high" if len(cycle) > 3 else "medium",
                        "recommendation": "Implement star grounding or ground isolation"
                    })
            
            return ground_loops
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error identifying ground loops: %s", e)
            return []

    # --- Helper methods ---
    def _parse_components(self, schematic_data: Dict[str, Any]) -> Dict[str, ComponentNode]:
        """Parse components from schematic data."""
        components = {}
        
        try:
            for comp_data in schematic_data.get("components", []):
                ref = comp_data.get("reference", "")
                value = comp_data.get("value", "")
                position = comp_data.get("position", (0, 0))
                pins = comp_data.get("pins", [])
                nets = comp_data.get("nets", [])
                
                # Determine component type
                component_type = self._determine_component_type(ref, value)
                
                # Separate power and signal pins
                power_pins = [pin for pin in pins if any(net in pin for net in ["VCC", "VDD", "V+", "V-", "GND"])]
                signal_pins = [pin for pin in pins if pin not in power_pins]
                
                components[ref] = ComponentNode(
                    reference=ref,
                    value=value,
                    component_type=component_type.value,
                    position=position,
                    pins=pins,
                    nets=nets,
                    power_pins=power_pins,
                    signal_pins=signal_pins
                )
            
            return components
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error parsing components: %s", e)
            return {}

    def _determine_component_type(self, ref: str, value: str) -> ComponentType:
        """Determine component type from reference and value."""
        ref_upper = ref.upper()
        value_upper = value.upper()
        
        for prefix, comp_type in self.component_type_mapping.items():
            if ref_upper.startswith(prefix) or value_upper.startswith(prefix):
                return comp_type
        
        # Default based on reference
        if ref_upper.startswith("R"):
            return ComponentType.RESISTOR
        elif ref_upper.startswith("C"):
            return ComponentType.CAPACITOR
        elif ref_upper.startswith("L"):
            return ComponentType.INDUCTOR
        elif ref_upper.startswith("Q"):
            return ComponentType.TRANSISTOR
        elif ref_upper.startswith("D"):
            return ComponentType.DIODE
        elif ref_upper.startswith("J"):
            return ComponentType.CONNECTOR
        else:
            return ComponentType.OPAMP  # Default for unknown components

    def _build_signal_flow_graph(self, components: Dict[str, ComponentNode]) -> nx.DiGraph:
        """Build signal flow graph from components."""
        graph = nx.DiGraph()
        
        try:
            # Add nodes
            for ref, component in components.items():
                graph.add_node(ref, component=component)
            
            # Add edges based on net connections
            net_connections = {}
            
            for ref, component in components.items():
                for net in component.nets:
                    if net not in net_connections:
                        net_connections[net] = []
                    net_connections[net].append(ref)
            
            # Create edges for components sharing nets
            for net, connected_components in net_connections.items():
                if len(connected_components) > 1:
                    # Create edges between all components sharing this net
                    for i, comp1 in enumerate(connected_components):
                        for comp2 in connected_components[i+1:]:
                            graph.add_edge(comp1, comp2, net=net)
                            graph.add_edge(comp2, comp1, net=net)
            
            return graph
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error building signal flow graph: %s", e)
            return nx.DiGraph()

    def _analyze_signal_paths(self, graph: nx.DiGraph, components: Dict[str, ComponentNode]) -> List[SignalPath]:
        """Analyze signal paths in the circuit."""
        signal_paths = []
        
        try:
            # Find all pairs of components
            component_refs = list(components.keys())
            
            for i, start_comp in enumerate(component_refs):
                for end_comp in component_refs[i+1:]:
                    # Find shortest path between components
                    try:
                        path = nx.shortest_path(graph, start_comp, end_comp)
                        if len(path) > 1:  # Only consider actual paths
                            # Calculate path properties
                            path_length = self._calculate_path_length(path, components)
                            path_impedance = self._calculate_path_impedance(path, components)
                            signal_type = self._determine_signal_type(path, components)
                            
                            # Get nets involved in this path
                            path_nets = []
                            for j in range(len(path) - 1):
                                edge_data = graph.get_edge_data(path[j], path[j+1])
                                if edge_data and 'net' in edge_data:
                                    path_nets.append(edge_data['net'])
                            
                            signal_path = SignalPath(
                                start_component=start_comp,
                                end_component=end_comp,
                                path_components=path,
                                path_nets=path_nets,
                                length=path_length,
                                impedance=path_impedance,
                                signal_type=signal_type
                            )
                            signal_paths.append(signal_path)
                    except nx.NetworkXNoPath:
                        # No path exists between these components
                        continue
            
            return signal_paths
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error analyzing signal paths: %s", e)
            return []

    def _identify_critical_paths(self, signal_paths: List[SignalPath], components: Dict[str, ComponentNode]) -> List[CriticalPath]:
        """Identify critical signal paths that require special attention."""
        critical_paths = []
        
        try:
            for path in signal_paths:
                issues = []
                recommendations = []
                criticality_score = 0.0
                
                # Check path length
                if path.length > self.max_signal_path_length:
                    issues.append(f"Path length ({path.length:.1f}mm) exceeds maximum ({self.max_signal_path_length}mm)")
                    recommendations.append("Reduce path length by repositioning components")
                    criticality_score += 0.3
                
                # Check impedance matching for audio signals
                if path.signal_type == "audio" and path.impedance < self.min_impedance_matching:
                    issues.append(f"Poor impedance matching ({path.impedance:.2f}) for audio signal")
                    recommendations.append("Improve impedance matching with proper termination")
                    criticality_score += 0.4
                
                # Check for high-frequency signals
                if path.signal_type == "digital" and path.length > 50.0:
                    issues.append("Long digital signal path may cause timing issues")
                    recommendations.append("Consider signal integrity analysis")
                    criticality_score += 0.2
                
                # Check for power supply paths
                if path.signal_type == "power" and path.length > 20.0:
                    issues.append("Long power supply path may cause voltage drop")
                    recommendations.append("Add power supply decoupling capacitors")
                    criticality_score += 0.3
                
                if criticality_score > self.critical_path_threshold:
                    critical_path = CriticalPath(
                        path=path,
                        criticality_score=criticality_score,
                        issues=issues,
                        recommendations=recommendations
                    )
                    critical_paths.append(critical_path)
            
            return critical_paths
            
        except Exception as e:
            logger.error("Error identifying critical paths: %s", e)
            return []

    def _analyze_noise_sources(self, components: Dict[str, ComponentNode]) -> List[NoiseSource]:
        """Analyze potential noise sources in the circuit."""
        noise_sources = []
        
        try:
            for ref, component in components.items():
                # Identify switching components
                if component.component_type in ["transistor", "microcontroller", "oscillator"]:
                    noise_sources.append(NoiseSource(
                        component=ref,
                        noise_type="switching",
                        frequency_range=(1e6, 100e6),  # 1MHz to 100MHz
                        amplitude=-40.0,  # -40 dB
                        affected_components=self._find_affected_components(ref, components)
                    ))
                
                # Identify thermal noise sources
                if component.component_type == "resistor":
                    # High-value resistors generate more thermal noise
                    try:
                        value = float(component.value.replace("R", "").replace("k", "000").replace("M", "000000"))
                        if value > 10000:  # 10k ohm
                            noise_sources.append(NoiseSource(
                                component=ref,
                                noise_type="thermal",
                                frequency_range=(1, 1e6),  # 1Hz to 1MHz
                                amplitude=-60.0 + 10 * np.log10(value/10000),  # -60 dB + 10*log(R/10k)
                                affected_components=self._find_affected_components(ref, components)
                            ))
                    except (ValueError, AttributeError):
                        pass
            
            return noise_sources
            
        except Exception as e:
            logger.error("Error analyzing noise sources: %s", e)
            return []

    def _analyze_component_dependencies(self, graph: nx.DiGraph) -> Dict[str, List[str]]:
        """Analyze component dependencies based on signal flow."""
        dependencies = {}
        
        try:
            for node in graph.nodes():
                # Find components that depend on this one (incoming edges)
                dependencies[node] = list(graph.predecessors(node))
            
            return dependencies
            
        except Exception as e:
            logger.error("Error analyzing component dependencies: %s", e)
            return {}

    def _analyze_ground_references(self, components: Dict[str, ComponentNode]) -> Dict[str, str]:
        """Analyze ground references for each component."""
        ground_references = {}
        
        try:
            for ref, component in components.items():
                # Find ground connections
                ground_nets = [net for net in component.nets if "GND" in net.upper()]
                if ground_nets:
                    ground_references[ref] = ground_nets[0]
                else:
                    ground_references[ref] = "GND"  # Default ground reference
            
            return ground_references
            
        except Exception as e:
            logger.error("Error analyzing ground references: %s", e)
            return {}

    def _analyze_power_distribution(self, components: Dict[str, ComponentNode]) -> Dict[str, List[str]]:
        """Analyze power distribution network."""
        power_distribution = {}
        
        try:
            for ref, component in components.items():
                # Find power connections
                power_nets = [net for net in component.nets if any(power in net.upper() for power in ["VCC", "VDD", "V+", "V-"])]
                power_distribution[ref] = power_nets
            
            return power_distribution
            
        except Exception as e:
            logger.error("Error analyzing power distribution: %s", e)
            return {}

    def _calculate_analysis_score(self, signal_paths: List[SignalPath], critical_paths: List[CriticalPath], noise_sources: List[NoiseSource]) -> float:
        """Calculate overall analysis score."""
        try:
            score = 100.0  # Start with perfect score
            
            # Deduct points for critical paths
            for critical_path in critical_paths:
                score -= critical_path.criticality_score * 10
            
            # Deduct points for noise sources
            for noise_source in noise_sources:
                if noise_source.noise_type == "switching":
                    score -= 5
                elif noise_source.noise_type == "thermal":
                    score -= 2
            
            # Deduct points for long signal paths
            for path in signal_paths:
                if path.length > self.max_signal_path_length:
                    score -= 3
            
            return max(0.0, score)  # Ensure score doesn't go below 0
            
        except Exception as e:
            logger.error("Error calculating analysis score: %s", e)
            return 0.0

    def _calculate_path_length(self, path: List[str], components: Dict[str, ComponentNode]) -> float:
        """Calculate the physical length of a signal path."""
        try:
            total_length = 0.0
            
            for i in range(len(path) - 1):
                comp1 = components[path[i]]
                comp2 = components[path[i+1]]
                
                # Calculate Euclidean distance between components
                dx = comp1.position[0] - comp2.position[0]
                dy = comp1.position[1] - comp2.position[1]
                distance = (dx**2 + dy**2)**0.5
                
                total_length += distance
            
            return total_length
            
        except Exception as e:
            logger.error("Error calculating path length: %s", e)
            return 0.0

    def _calculate_path_impedance(self, path: List[str], components: Dict[str, ComponentNode]) -> float:
        """Calculate the impedance of a signal path."""
        try:
            # Simplified impedance calculation
            # In a real implementation, this would consider trace width, thickness, etc.
            total_impedance = 50.0  # Default 50 ohm impedance
            
            for comp_ref in path:
                component = components[comp_ref]
                
                # Adjust impedance based on component type
                if component.component_type == "resistor":
                    try:
                        value = float(component.value.replace("R", "").replace("k", "000").replace("M", "000000"))
                        total_impedance += value
                    except (ValueError, AttributeError):
                        pass
                elif component.component_type == "capacitor":
                    total_impedance *= 0.9  # Capacitors reduce impedance
                elif component.component_type == "inductor":
                    total_impedance *= 1.1  # Inductors increase impedance
            
            return total_impedance
            
        except Exception as e:
            logger.error("Error calculating path impedance: %s", e)
            return 50.0

    def _determine_signal_type(self, path: List[str], components: Dict[str, ComponentNode]) -> str:
        """Determine the type of signal flowing through a path."""
        try:
            # Check for power supply components
            for comp_ref in path:
                component = components[comp_ref]
                if component.component_type in ["regulator", "connector"]:
                    return "power"
            
            # Check for digital components
            for comp_ref in path:
                component = components[comp_ref]
                if component.component_type in ["microcontroller", "oscillator"]:
                    return "digital"
            
            # Check for audio components
            for comp_ref in path:
                component = components[comp_ref]
                if component.component_type in ["opamp", "transistor"]:
                    return "audio"
            
            # Default to control signal
            return "control"
            
        except Exception as e:
            logger.error("Error determining signal type: %s", e)
            return "control"

    def _find_affected_components(self, noise_source: str, components: Dict[str, ComponentNode]) -> List[str]:
        """Find components that might be affected by a noise source."""
        try:
            affected = []
            source_pos = components[noise_source].position
            
            for ref, component in components.items():
                if ref != noise_source:
                    # Calculate distance to noise source
                    dx = source_pos[0] - component.position[0]
                    dy = source_pos[1] - component.position[1]
                    distance = (dx**2 + dy**2)**0.5
                    
                    # Components within 20mm are potentially affected
                    if distance < 20.0:
                        affected.append(ref)
            
            return affected
            
        except Exception as e:
            logger.error("Error finding affected components: %s", e)
            return []

    def _optimize_component_placement(self, topology: TopologyAnalysis) -> List[Dict[str, Any]]:
        """Optimize component placement based on topology analysis."""
        optimizations = []
        
        try:
            # Group components by signal type
            audio_components = []
            power_components = []
            digital_components = []
            
            for ref, component in topology.components.items():
                if component.component_type in ["opamp", "transistor"]:
                    audio_components.append(ref)
                elif component.component_type in ["regulator", "connector"]:
                    power_components.append(ref)
                elif component.component_type in ["microcontroller", "oscillator"]:
                    digital_components.append(ref)
            
            # Suggest placement optimizations
            if len(audio_components) > 1:
                optimizations.append({
                    "type": "component_grouping",
                    "components": audio_components,
                    "recommendation": "Group audio components together for shorter signal paths",
                    "priority": "medium"
                })
            
            if len(power_components) > 0:
                optimizations.append({
                    "type": "power_placement",
                    "components": power_components,
                    "recommendation": "Place power components near board edges for better heat dissipation",
                    "priority": "low"
                })
            
            if len(digital_components) > 0:
                optimizations.append({
                    "type": "digital_isolation",
                    "components": digital_components,
                    "recommendation": "Isolate digital components from analog sections",
                    "priority": "high"
                })
            
            return optimizations
            
        except Exception as e:
            logger.error("Error optimizing component placement: %s", e)
            return []

    def _calculate_path_frequency_response(self, path: SignalPath, components: Dict[str, ComponentNode]) -> Dict[str, Any]:
        """Calculate frequency response for a specific signal path with high-precision support for extended bandwidth."""
        try:
            # Enhanced frequency response calculation for extended audio bandwidth
            # Use optimized frequency distribution for audio analysis
            
            if self.high_precision_mode:
                # High-precision frequency distribution optimized for audio
                # More points in critical frequency ranges
                low_freq_points = np.logspace(1, 3, 30)  # 10Hz to 1kHz (30 points)
                mid_freq_points = np.logspace(3, 4.3, 40)  # 1kHz to 20kHz (40 points)
                high_freq_points = np.logspace(4.3, 4.9, 30)  # 20kHz to 80kHz (30 points)
                frequencies = np.concatenate([low_freq_points, mid_freq_points, high_freq_points])
            else:
                # Standard frequency distribution
                frequencies = np.logspace(1, 5, 100)  # 10Hz to 100kHz
            
            # Calculate magnitude response with enhanced precision
            magnitude = np.ones_like(frequencies)
            for comp_ref in path.path_components:
                component = components[comp_ref]
                
                if component.component_type == "capacitor":
                    # Enhanced high-pass filter effect with frequency-dependent behavior
                    if self.extended_bandwidth_analysis:
                        # Extended bandwidth capacitor model
                        corner_freq = 1000.0  # 1kHz corner frequency
                        magnitude *= frequencies / (frequencies + corner_freq)
                        
                        # Add high-frequency effects for extended bandwidth
                        hf_effects = np.ones_like(frequencies)
                        hf_mask = frequencies > 20000.0
                        if np.any(hf_mask):
                            hf_effects[hf_mask] = 1.0 - 0.1 * np.log10(frequencies[hf_mask] / 20000.0)
                            hf_effects[hf_mask] = np.maximum(hf_effects[hf_mask], 0.1)  # Minimum 10%
                        magnitude *= hf_effects
                    else:
                        # Standard high-pass filter effect
                        magnitude *= frequencies / (frequencies + 1000)
                        
                elif component.component_type == "inductor":
                    # Enhanced low-pass filter effect
                    if self.extended_bandwidth_analysis:
                        # Extended bandwidth inductor model
                        corner_freq = 1000.0  # 1kHz corner frequency
                        magnitude *= corner_freq / (frequencies + corner_freq)
                        
                        # Add high-frequency parasitic effects
                        hf_parasitics = np.ones_like(frequencies)
                        hf_mask = frequencies > 20000.0
                        if np.any(hf_mask):
                            hf_parasitics[hf_mask] = 1.0 + 0.05 * np.log10(frequencies[hf_mask] / 20000.0)
                        magnitude *= hf_parasitics
                    else:
                        # Standard low-pass filter effect
                        magnitude *= 1000 / (frequencies + 1000)
                
                elif component.component_type == "opamp":
                    # Op-amp frequency response model
                    if self.extended_bandwidth_analysis:
                        # Extended bandwidth op-amp model
                        unity_gain_freq = 1e6  # 1MHz unity gain frequency
                        magnitude *= unity_gain_freq / (frequencies + unity_gain_freq)
                        
                        # Add high-frequency rolloff for extended bandwidth
                        hf_rolloff = np.ones_like(frequencies)
                        hf_mask = frequencies > 20000.0
                        if np.any(hf_mask):
                            hf_rolloff[hf_mask] = 1.0 - 0.2 * np.log10(frequencies[hf_mask] / 20000.0)
                            hf_rolloff[hf_mask] = np.maximum(hf_rolloff[hf_mask], 0.05)  # Minimum 5%
                        magnitude *= hf_rolloff
            
            # Calculate phase response with enhanced precision
            if self.high_precision_mode:
                # Enhanced phase calculation for extended bandwidth
                phase = np.zeros_like(frequencies)
                
                for comp_ref in path.path_components:
                    component = components[comp_ref]
                    
                    if component.component_type == "capacitor":
                        # High-pass filter phase response
                        corner_freq = 1000.0
                        phase += -np.arctan2(corner_freq, frequencies) * 180 / np.pi
                        
                        # Add high-frequency phase effects
                        hf_phase = np.zeros_like(frequencies)
                        hf_mask = frequencies > 20000.0
                        if np.any(hf_mask):
                            hf_phase[hf_mask] = -5.0 * np.log10(frequencies[hf_mask] / 20000.0)
                        phase += hf_phase
                        
                    elif component.component_type == "inductor":
                        # Low-pass filter phase response
                        corner_freq = 1000.0
                        phase += -np.arctan2(frequencies, corner_freq) * 180 / np.pi
                        
                        # Add high-frequency parasitic phase effects
                        hf_phase = np.zeros_like(frequencies)
                        hf_mask = frequencies > 20000.0
                        if np.any(hf_mask):
                            hf_phase[hf_mask] = 3.0 * np.log10(frequencies[hf_mask] / 20000.0)
                        phase += hf_phase
            else:
                # Standard phase calculation
                phase = -np.arctan2(frequencies, 1000) * 180 / np.pi
            
            # Calculate additional metrics for extended bandwidth
            extended_metrics = {}
            if self.extended_bandwidth_analysis:
                # Calculate bandwidth metrics
                max_magnitude = np.max(magnitude)
                threshold = max_magnitude / np.sqrt(2)  # -3dB point
                
                # Find -3dB bandwidth
                above_threshold = magnitude >= threshold
                if np.any(above_threshold):
                    low_freq_3db = frequencies[above_threshold][0]
                    high_freq_3db = frequencies[above_threshold][-1]
                    bandwidth = high_freq_3db - low_freq_3db
                else:
                    bandwidth = 0.0
                
                # Calculate flatness in passband
                passband_mask = (frequencies >= low_freq_3db) & (frequencies <= high_freq_3db)
                if np.any(passband_mask):
                    passband_magnitudes = magnitude[passband_mask]
                    flatness = np.min(passband_magnitudes) / np.max(passband_magnitudes)
                else:
                    flatness = 1.0
                
                # Calculate phase variation
                if np.any(passband_mask):
                    passband_phases = phase[passband_mask]
                    phase_variation = np.max(passband_phases) - np.min(passband_phases)
                else:
                    phase_variation = 0.0
                
                extended_metrics = {
                    "bandwidth": bandwidth,
                    "flatness": flatness,
                    "phase_variation": phase_variation,
                    "low_freq_3db": low_freq_3db if 'low_freq_3db' in locals() else 0.0,
                    "high_freq_3db": high_freq_3db if 'high_freq_3db' in locals() else 0.0,
                    "extended_bandwidth_support": True,
                    "max_frequency": np.max(frequencies)
                }
            
            return {
                "frequencies": frequencies.tolist(),
                "magnitude": magnitude.tolist(),
                "phase": phase.tolist(),
                "extended_metrics": extended_metrics,
                "high_precision_mode": self.high_precision_mode,
                "extended_bandwidth_analysis": self.extended_bandwidth_analysis
            }
            
        except Exception as e:
            logger.error("Error calculating path frequency response: %s", e)
            return {
                "frequencies": [],
                "magnitude": [],
                "phase": [],
                "extended_metrics": {},
                "high_precision_mode": self.high_precision_mode,
                "extended_bandwidth_analysis": self.extended_bandwidth_analysis
            }

    def _calculate_overall_frequency_response(self, topology: TopologyAnalysis) -> Dict[str, Any]:
        """Calculate overall frequency response of the circuit."""
        try:
            # Combine frequency responses from all audio paths
            all_frequencies = []
            all_magnitudes = []
            all_phases = []
            
            for path in topology.signal_paths:
                if path.signal_type == "audio":
                    response = self._calculate_path_frequency_response(path, topology.components)
                    all_frequencies.extend(response["frequencies"])
                    all_magnitudes.extend(response["magnitude"])
                    all_phases.extend(response["phase"])
            
            if all_frequencies:
                # Calculate average response
                return {
                    "frequencies": all_frequencies,
                    "magnitude": all_magnitudes,
                    "phase": all_phases
                }
            else:
                return {
                    "frequencies": [],
                    "magnitude": [],
                    "phase": []
                }
            
        except Exception as e:
            logger.error("Error calculating overall frequency response: %s", e)
            return {
                "frequencies": [],
                "magnitude": [],
                "phase": []
            } 