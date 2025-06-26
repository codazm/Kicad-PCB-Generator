"""
Circuit simulator for audio circuits.
"""
import numpy as np
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import logging
import pcbnew
import math

from ...core.validation.base_validator import BaseValidator

logger = logging.getLogger(__name__)

class SimulationType(Enum):
    """Types of circuit simulation."""
    DC = "dc"
    AC = "ac"
    TRANSIENT = "transient"
    NOISE = "noise"
    FOURIER = "fourier"

@dataclass
class SimulationResult:
    """Result of a circuit simulation.

    Historical code paths set ``simulation_type``; recent unit-tests check the
    attribute ``type``.  We store the canonical value in ``simulation_type`` and
    expose ``type`` as a read/write property that aliases it, keeping both
    call-sites happy.
    """

    simulation_type: SimulationType
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

    # Alias expected by tests -------------------------------------------------
    @property
    def type(self) -> SimulationType:  # noqa: D401
        return self.simulation_type

    @type.setter
    def type(self, value: SimulationType) -> None:  # pragma: no cover
        self.simulation_type = value

class CircuitSimulator(BaseValidator):
    """Circuit simulator for audio circuits."""
    
    def __init__(self, board: Optional[pcbnew.BOARD] = None):
        """Initialize the circuit simulator.

        Args:
            board: Optional KiCad BOARD object (mocked in unit-tests).  When
                   *None*, the simulator falls back to ``pcbnew.GetBoard()`` at
                   runtime.
        """
        super().__init__()
        self.board: Optional[pcbnew.BOARD] = board
        self.callbacks: List[Callable] = []
        self.results_cache: Dict[str, SimulationResult] = {}
        
    def add_simulation_callback(self, callback: Callable) -> None:
        """Add a callback to be called after simulation.
        
        Args:
            callback: Function to call after simulation
        """
        self.callbacks.append(callback)
        
    def run_simulation(self, simulation_type: SimulationType, **kwargs) -> SimulationResult:
        """Run a circuit simulation.
        
        Args:
            simulation_type: Type of simulation to run
            **kwargs: Additional simulation parameters
            
        Returns:
            Simulation result
        """
        # Create cache key
        cache_key = f"{simulation_type.value}_{hash(str(kwargs))}"
        
        # Check cache first
        if cache_key in self.results_cache:
            logger.debug(f"Using cached result for {cache_key}")
            return self.results_cache[cache_key]
        
        # Create circuit
        circuit = self._create_circuit()
        
        # Run simulation based on type
        if simulation_type == SimulationType.DC:
            result = self._run_dc_simulation(circuit, **kwargs)
        elif simulation_type == SimulationType.AC:
            result = self._run_ac_simulation(circuit, **kwargs)
        elif simulation_type == SimulationType.TRANSIENT:
            result = self._run_transient_simulation(circuit, **kwargs)
        elif simulation_type == SimulationType.NOISE:
            result = self._run_noise_simulation(circuit, **kwargs)
        elif simulation_type == SimulationType.FOURIER:
            result = self._run_fourier_simulation(circuit, **kwargs)
        else:
            result = SimulationResult(
                simulation_type=simulation_type,
                data={},
                metadata={},
                success=False,
                error_message=f"Unknown simulation type: {simulation_type}"
            )
        
        # Cache result
        self.results_cache[cache_key] = result
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Error in simulation callback: {e}")
        
        return result
    
    def _create_circuit(self) -> Dict[str, Any]:
        """Create a circuit for simulation.
        
        Returns:
            Circuit data
        """
        try:
            # Prefer instance board if provided (e.g. unit-tests); otherwise ask pcbnew
            board = self.board or pcbnew.GetBoard()
            if not board:
                logger.error("No board available for circuit creation")
                return {}
            
            # Extract circuit components and connections
            circuit_data = {
                "components": {},
                "nets": {},
                "connections": [],
                "board_info": {
                    "layers": [],
                    "dimensions": {},
                    "properties": {}
                }
            }
            
            # Extract components
            for footprint in board.GetFootprints():
                component_data = {
                    "reference": footprint.GetReference(),
                    "value": footprint.GetValue(),
                    "position": (footprint.GetPosition().x, footprint.GetPosition().y),
                    "orientation": footprint.GetOrientationDegrees(),
                    "layer": footprint.GetLayerName(),
                    "pads": []
                }
                
                # Extract pad information
                for pad in footprint.Pads():
                    pad_data = {
                        "number": pad.GetNumber(),
                        "position": (pad.GetPosition().x, pad.GetPosition().y),
                        "net": pad.GetNetname() if pad.GetNet() else "",
                        "shape": str(pad.GetShape()),
                        "size": (pad.GetSize().x, pad.GetSize().y)
                    }
                    component_data["pads"].append(pad_data)
                
                circuit_data["components"][footprint.GetReference()] = component_data
            
            # Extract nets and connections
            for net in board.GetNetsByNetcode().values():
                net_data = {
                    "name": net.GetNetname(),
                    "code": net.GetNetCode(),
                    "tracks": [],
                    "vias": []
                }
                
                # Extract tracks
                for track in net.GetTracks():
                    track_data = {
                        "start": (track.GetStart().x, track.GetStart().y),
                        "end": (track.GetEnd().x, track.GetEnd().y),
                        "width": track.GetWidth(),
                        "layer": track.GetLayerName()
                    }
                    net_data["tracks"].append(track_data)
                
                # Extract vias
                for via in net.GetVias():
                    via_data = {
                        "position": (via.GetPosition().x, via.GetPosition().y),
                        "diameter": via.GetDrill(),
                        "layers": [via.GetLayerName()]
                    }
                    net_data["vias"].append(via_data)
                
                circuit_data["nets"][net.GetNetname()] = net_data
            
            # Extract board information
            board_box = board.GetBoardBoundingBox()
            circuit_data["board_info"]["dimensions"] = {
                "width": board_box.GetWidth() / 1e6,  # Convert to mm
                "height": board_box.GetHeight() / 1e6,
                "area": (board_box.GetWidth() * board_box.GetHeight()) / 1e12  # Convert to mm²
            }
            
            # Extract layer information
            for layer_id in range(board.GetCopperLayerCount()):
                layer_name = board.GetLayerName(layer_id)
                if layer_name:
                    circuit_data["board_info"]["layers"].append({
                        "id": layer_id,
                        "name": layer_name,
                        "type": "copper" if layer_id < board.GetCopperLayerCount() else "other"
                    })
            
            logger.info(f"Created circuit with {len(circuit_data['components'])} components and {len(circuit_data['nets'])} nets")
            return circuit_data
            
        except Exception as e:
            logger.error(f"Error creating circuit: {str(e)}")
            return {}
    
    def _run_dc_simulation(self, circuit: Dict[str, Any], **kwargs) -> SimulationResult:
        """Run DC simulation.
        
        Args:
            circuit: Circuit data
            **kwargs: Simulation parameters
            
        Returns:
            DC simulation result
        """
        try:
            if not circuit or not circuit.get("components"):
                return SimulationResult(
                    simulation_type=SimulationType.DC,
                    data={},
                    metadata={},
                    success=False,
                    error_message="No circuit data available for DC simulation"
                )
            
            # Extract simulation parameters
            voltage_sources = kwargs.get("voltage_sources", {})
            current_sources = kwargs.get("current_sources", {})
            tolerance = kwargs.get("tolerance", 1e-6)
            max_iterations = kwargs.get("max_iterations", 1000)
            
            # Perform DC analysis
            dc_results = {
                "node_voltages": {},
                "branch_currents": {},
                "power_dissipation": {},
                "convergence": True,
                "iterations": 0
            }
            
            # Calculate node voltages (simplified DC analysis)
            for net_name, net_data in circuit.get("nets", {}).items():
                if net_name in voltage_sources:
                    # Voltage source node
                    dc_results["node_voltages"][net_name] = voltage_sources[net_name]
                elif net_name.startswith(("VCC", "VDD", "+")):
                    # Power supply node
                    dc_results["node_voltages"][net_name] = 5.0  # Default 5V
                elif net_name.startswith(("GND", "VSS", "-")):
                    # Ground node
                    dc_results["node_voltages"][net_name] = 0.0
                else:
                    # Signal node - calculate based on connected components
                    dc_results["node_voltages"][net_name] = self._calculate_node_voltage(net_name, net_data, voltage_sources)
            
            # Calculate branch currents
            for net_name, net_data in circuit.get("nets", {}).items():
                if net_name in current_sources:
                    dc_results["branch_currents"][net_name] = current_sources[net_name]
                else:
                    # Calculate current based on connected components
                    dc_results["branch_currents"][net_name] = self._calculate_branch_current(net_name, net_data)
            
            # Calculate power dissipation
            for component_ref, component_data in circuit.get("components", {}).items():
                power = self._calculate_component_power(component_ref, component_data, dc_results)
                dc_results["power_dissipation"][component_ref] = power
            
            # Add metadata
            metadata = {
                "simulation_type": "DC",
                "parameters": {
                    "voltage_sources": voltage_sources,
                    "current_sources": current_sources,
                    "tolerance": tolerance,
                    "max_iterations": max_iterations
                },
                "circuit_stats": {
                    "components": len(circuit.get("components", {})),
                    "nets": len(circuit.get("nets", {})),
                    "nodes": len(dc_results["node_voltages"])
                }
            }
            
            logger.info(f"DC simulation completed for {len(dc_results['node_voltages'])} nodes")
            return SimulationResult(
                simulation_type=SimulationType.DC,
                data=dc_results,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in DC simulation: {str(e)}")
            return SimulationResult(
                simulation_type=SimulationType.DC,
                data={},
                metadata={},
                success=False,
                error_message=f"DC simulation failed: {str(e)}"
            )
    
    def _run_ac_simulation(self, circuit: Dict[str, Any], **kwargs) -> SimulationResult:
        """Run AC simulation with high-precision support for extended audio bandwidth.
        
        Args:
            circuit: Circuit data
            **kwargs: Simulation parameters
            
        Returns:
            AC simulation result
        """
        try:
            if not circuit or not circuit.get("components"):
                return SimulationResult(
                    simulation_type=SimulationType.AC,
                    data={},
                    metadata={},
                    success=False,
                    error_message="No circuit data available for AC simulation"
                )
            
            # Extract simulation parameters with high-precision defaults
            start_freq = kwargs.get("start_frequency", 20.0)  # Hz - audio minimum
            stop_freq = kwargs.get("stop_frequency", 80000.0)  # Hz - extended audio bandwidth
            num_points = kwargs.get("num_points", 200)  # Increased for better precision
            ac_source = kwargs.get("ac_source", "V1")
            ac_amplitude = kwargs.get("ac_amplitude", 1.0)   # V
            high_precision = kwargs.get("high_precision", True)  # Enable high-precision mode
            
            # Generate frequency points with optimized distribution for audio
            frequencies = self._generate_audio_frequency_points(start_freq, stop_freq, num_points, high_precision)
            
            # Perform AC analysis
            ac_results = {
                "frequencies": frequencies,
                "magnitude_response": {},
                "phase_response": {},
                "impedance": {},
                "transfer_functions": {},
                "bandwidth_analysis": {},
                "precision_metrics": {}
            }
            
            # Calculate frequency response for each net
            for net_name, net_data in circuit.get("nets", {}).items():
                if net_name.startswith(("GND", "VSS", "-")):
                    continue  # Skip ground nets
                
                magnitude = []
                phase = []
                impedance = []
                
                for freq in frequencies:
                    # Calculate magnitude response with enhanced precision
                    mag = self._calculate_magnitude_response_high_precision(net_name, net_data, freq, ac_amplitude)
                    magnitude.append(mag)
                    
                    # Calculate phase response with enhanced precision
                    ph = self._calculate_phase_response_high_precision(net_name, net_data, freq)
                    phase.append(ph)
                    
                    # Calculate impedance with enhanced precision
                    imp = self._calculate_impedance_high_precision(net_name, net_data, freq)
                    impedance.append(imp)
                
                ac_results["magnitude_response"][net_name] = magnitude
                ac_results["phase_response"][net_name] = phase
                ac_results["impedance"][net_name] = impedance
                
                # Calculate bandwidth analysis for this net
                ac_results["bandwidth_analysis"][net_name] = self._analyze_bandwidth_characteristics(
                    frequencies, magnitude, phase, high_precision
                )
            
            # Calculate transfer functions with enhanced precision
            for net_name in ac_results["magnitude_response"]:
                if net_name != ac_source:
                    transfer_mag = []
                    transfer_phase = []
                    
                    for i, freq in enumerate(frequencies):
                        # Calculate transfer function magnitude with high precision
                        input_mag = ac_results["magnitude_response"].get(ac_source, [1.0])[i] if ac_source in ac_results["magnitude_response"] else 1.0
                        output_mag = ac_results["magnitude_response"][net_name][i]
                        transfer_mag.append(output_mag / input_mag if input_mag > 0 else 0.0)
                        
                        # Calculate transfer function phase with high precision
                        input_phase = ac_results["phase_response"].get(ac_source, [0.0])[i] if ac_source in ac_results["phase_response"] else 0.0
                        output_phase = ac_results["phase_response"][net_name][i]
                        transfer_phase.append(output_phase - input_phase)
                    
                    ac_results["transfer_functions"][f"{ac_source}_to_{net_name}"] = {
                        "magnitude": transfer_mag,
                        "phase": transfer_phase
                    }
            
            # Calculate precision metrics
            ac_results["precision_metrics"] = self._calculate_precision_metrics(
                frequencies, ac_results, high_precision
            )
            
            # Add metadata
            metadata = {
                "simulation_type": "AC",
                "parameters": {
                    "start_frequency": start_freq,
                    "stop_frequency": stop_freq,
                    "num_points": num_points,
                    "ac_source": ac_source,
                    "ac_amplitude": ac_amplitude,
                    "high_precision": high_precision,
                    "extended_bandwidth": stop_freq > 20000.0
                },
                "circuit_stats": {
                    "components": len(circuit.get("components", {})),
                    "nets": len(circuit.get("nets", {})),
                    "frequencies": len(frequencies)
                },
                "precision_info": {
                    "frequency_resolution": (stop_freq - start_freq) / num_points,
                    "max_frequency": max(frequencies),
                    "min_frequency": min(frequencies),
                    "logarithmic_distribution": True
                }
            }
            
            logger.info(f"High-precision AC simulation completed for {len(frequencies)} frequency points up to {stop_freq}Hz")
            return SimulationResult(
                simulation_type=SimulationType.AC,
                data=ac_results,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in AC simulation: {str(e)}")
            return SimulationResult(
                simulation_type=SimulationType.AC,
                data={},
                metadata={},
                success=False,
                error_message=f"AC simulation failed: {str(e)}"
            )
    
    def _run_transient_simulation(self, circuit: Dict[str, Any], **kwargs) -> SimulationResult:
        """Run transient simulation.
        
        Args:
            circuit: Circuit data
            **kwargs: Simulation parameters
            
        Returns:
            Transient simulation result
        """
        try:
            if not circuit or not circuit.get("components"):
                return SimulationResult(
                    simulation_type=SimulationType.TRANSIENT,
                    data={},
                    metadata={},
                    success=False,
                    error_message="No circuit data available for transient simulation"
                )
            
            # Extract simulation parameters
            start_time = kwargs.get("start_time", 0.0)      # s
            stop_time = kwargs.get("stop_time", 1e-3)       # s
            time_step = kwargs.get("time_step", 1e-6)       # s
            input_signal = kwargs.get("input_signal", "step")
            input_amplitude = kwargs.get("input_amplitude", 1.0)  # V
            
            # Generate time points
            time_points = []
            current_time = start_time
            while current_time <= stop_time:
                time_points.append(current_time)
                current_time += time_step
            
            # Perform transient analysis
            transient_results = {
                "time": time_points,
                "voltages": {},
                "currents": {},
                "power": {},
                "signals": {}
            }
            
            # Generate input signal
            input_signal_data = self._generate_input_signal(time_points, input_signal, input_amplitude)
            transient_results["signals"]["input"] = input_signal_data
            
            # Calculate transient response for each net
            for net_name, net_data in circuit.get("nets", {}).items():
                if net_name.startswith(("GND", "VSS", "-")):
                    continue  # Skip ground nets
                
                voltages = []
                currents = []
                power = []
                
                for t in time_points:
                    # Calculate voltage response (simplified)
                    voltage = self._calculate_transient_voltage(net_name, net_data, t, input_signal_data)
                    voltages.append(voltage)
                    
                    # Calculate current response (simplified)
                    current = self._calculate_transient_current(net_name, net_data, t, voltage)
                    currents.append(current)
                    
                    # Calculate power (simplified)
                    power_val = voltage * current
                    power.append(power_val)
                
                transient_results["voltages"][net_name] = voltages
                transient_results["currents"][net_name] = currents
                transient_results["power"][net_name] = power
            
            # Add metadata
            metadata = {
                "simulation_type": "Transient",
                "parameters": {
                    "start_time": start_time,
                    "stop_time": stop_time,
                    "time_step": time_step,
                    "input_signal": input_signal,
                    "input_amplitude": input_amplitude
                },
                "circuit_stats": {
                    "components": len(circuit.get("components", {})),
                    "nets": len(circuit.get("nets", {})),
                    "time_points": len(time_points)
                }
            }
            
            logger.info(f"Transient simulation completed for {len(time_points)} time points")
            return SimulationResult(
                simulation_type=SimulationType.TRANSIENT,
                data=transient_results,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in transient simulation: {str(e)}")
            return SimulationResult(
                simulation_type=SimulationType.TRANSIENT,
                data={},
                metadata={},
                success=False,
                error_message=f"Transient simulation failed: {str(e)}"
            )
    
    def _run_noise_simulation(self, circuit: Dict[str, Any], **kwargs) -> SimulationResult:
        """Run noise simulation with high-precision support for extended audio bandwidth.
        
        Args:
            circuit: Circuit data
            **kwargs: Simulation parameters
            
        Returns:
            Noise simulation result
        """
        try:
            if not circuit or not circuit.get("components"):
                return SimulationResult(
                    simulation_type=SimulationType.NOISE,
                    data={},
                    metadata={},
                    success=False,
                    error_message="No circuit data available for noise simulation"
                )
            
            # Extract simulation parameters with high-precision defaults
            start_freq = kwargs.get("start_frequency", 20.0)    # Hz - audio minimum
            stop_freq = kwargs.get("stop_frequency", 80000.0)   # Hz - extended audio bandwidth
            num_points = kwargs.get("num_points", 200)          # Increased for better precision
            temperature = kwargs.get("temperature", 300.0)      # K
            reference_impedance = kwargs.get("reference_impedance", 50.0)  # Ω
            high_precision = kwargs.get("high_precision", True) # Enable high-precision mode
            
            # Generate frequency points optimized for audio
            frequencies = self._generate_audio_frequency_points(start_freq, stop_freq, num_points, high_precision)
            
            # Perform noise analysis
            noise_results = {
                "frequencies": frequencies,
                "thermal_noise": {},
                "shot_noise": {},
                "flicker_noise": {},
                "total_noise": {},
                "noise_figure": {},
                "snr": {},
                "high_frequency_noise": {},
                "noise_spectrum_analysis": {}
            }
            
            # Calculate noise for each net
            for net_name, net_data in circuit.get("nets", {}).items():
                if net_name.startswith(("GND", "VSS", "-")):
                    continue  # Skip ground nets
                
                thermal = []
                shot = []
                flicker = []
                total = []
                nf = []
                snr = []
                hf_noise = []
                
                for freq in frequencies:
                    # Calculate thermal noise with high precision
                    thermal_noise = self._calculate_thermal_noise_high_precision(net_name, net_data, freq, temperature)
                    thermal.append(thermal_noise)
                    
                    # Calculate shot noise with high precision
                    shot_noise = self._calculate_shot_noise_high_precision(net_name, net_data, freq)
                    shot.append(shot_noise)
                    
                    # Calculate flicker noise with high precision
                    flicker_noise = self._calculate_flicker_noise_high_precision(net_name, net_data, freq)
                    flicker.append(flicker_noise)
                    
                    # Calculate high-frequency noise components
                    if freq > 20000.0:
                        hf_component = self._calculate_high_frequency_noise(net_name, net_data, freq, temperature)
                        hf_noise.append(hf_component)
                    else:
                        hf_noise.append(0.0)
                    
                    # Calculate total noise with enhanced precision
                    total_noise = (thermal_noise**2 + shot_noise**2 + flicker_noise**2 + hf_noise[-1]**2)**0.5
                    total.append(total_noise)
                    
                    # Calculate noise figure with high precision
                    noise_figure = self._calculate_noise_figure_high_precision(net_name, net_data, freq, total_noise, reference_impedance)
                    nf.append(noise_figure)
                    
                    # Calculate signal-to-noise ratio with high precision
                    signal_level = self._estimate_signal_level_high_precision(net_name, net_data, freq)
                    snr_val = 20 * math.log10(signal_level / total_noise) if total_noise > 0 else 100
                    snr.append(snr_val)
                
                noise_results["thermal_noise"][net_name] = thermal
                noise_results["shot_noise"][net_name] = shot
                noise_results["flicker_noise"][net_name] = flicker
                noise_results["total_noise"][net_name] = total
                noise_results["noise_figure"][net_name] = nf
                noise_results["snr"][net_name] = snr
                noise_results["high_frequency_noise"][net_name] = hf_noise
                
                # Calculate noise spectrum analysis for this net
                noise_results["noise_spectrum_analysis"][net_name] = self._analyze_noise_spectrum(
                    frequencies, thermal, shot, flicker, hf_noise, high_precision
                )
            
            # Add metadata
            metadata = {
                "simulation_type": "Noise",
                "parameters": {
                    "start_frequency": start_freq,
                    "stop_frequency": stop_freq,
                    "num_points": num_points,
                    "temperature": temperature,
                    "reference_impedance": reference_impedance,
                    "high_precision": high_precision,
                    "extended_bandwidth": stop_freq > 20000.0
                },
                "circuit_stats": {
                    "components": len(circuit.get("components", {})),
                    "nets": len(circuit.get("nets", {})),
                    "frequencies": len(frequencies)
                },
                "noise_analysis_info": {
                    "frequency_resolution": (stop_freq - start_freq) / num_points,
                    "max_frequency": max(frequencies),
                    "high_frequency_analysis": max(frequencies) > 20000.0,
                    "noise_components": ["thermal", "shot", "flicker", "high_frequency"]
                }
            }
            
            logger.info(f"High-precision noise simulation completed for {len(frequencies)} frequency points up to {stop_freq}Hz")
            return SimulationResult(
                simulation_type=SimulationType.NOISE,
                data=noise_results,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in noise simulation: {str(e)}")
            return SimulationResult(
                simulation_type=SimulationType.NOISE,
                data={},
                metadata={},
                success=False,
                error_message=f"Noise simulation failed: {str(e)}"
            )
    
    def _run_fourier_simulation(self, circuit: Dict[str, Any], **kwargs) -> SimulationResult:
        """Run Fourier analysis.
        
        Args:
            circuit: Circuit data
            **kwargs: Simulation parameters
            
        Returns:
            Fourier analysis result
        """
        try:
            if not circuit or not circuit.get("components"):
                return SimulationResult(
                    simulation_type=SimulationType.FOURIER,
                    data={},
                    metadata={},
                    success=False,
                    error_message="No circuit data available for Fourier analysis"
                )
            
            # Extract simulation parameters
            fundamental_freq = kwargs.get("fundamental_frequency", 1e3)  # Hz
            num_harmonics = kwargs.get("num_harmonics", 10)
            window_type = kwargs.get("window_type", "hanning")
            
            # Perform Fourier analysis
            fourier_results = {
                "frequencies": [],
                "magnitude_spectrum": {},
                "phase_spectrum": {},
                "harmonic_content": {},
                "thd": {},  # Total Harmonic Distortion
                "power_spectrum": {}
            }
            
            # Generate harmonic frequencies
            frequencies = [fundamental_freq * (i + 1) for i in range(num_harmonics)]
            fourier_results["frequencies"] = frequencies
            
            # Calculate Fourier analysis for each net
            for net_name, net_data in circuit.get("nets", {}).items():
                if net_name.startswith(("GND", "VSS", "-")):
                    continue  # Skip ground nets
                
                magnitude = []
                phase = []
                harmonics = []
                power = []
                
                for i, freq in enumerate(frequencies):
                    # Calculate magnitude spectrum
                    mag = self._calculate_fourier_magnitude(net_name, net_data, freq, fundamental_freq)
                    magnitude.append(mag)
                    
                    # Calculate phase spectrum
                    ph = self._calculate_fourier_phase(net_name, net_data, freq, fundamental_freq)
                    phase.append(ph)
                    
                    # Calculate harmonic content
                    harmonic = mag / magnitude[0] if magnitude[0] > 0 else 0.0
                    harmonics.append(harmonic)
                    
                    # Calculate power spectrum
                    power_val = mag**2 / 2  # RMS power
                    power.append(power_val)
                
                fourier_results["magnitude_spectrum"][net_name] = magnitude
                fourier_results["phase_spectrum"][net_name] = phase
                fourier_results["harmonic_content"][net_name] = harmonics
                fourier_results["power_spectrum"][net_name] = power
                
                # Calculate Total Harmonic Distortion
                if len(harmonics) > 1:
                    thd = math.sqrt(sum(h**2 for h in harmonics[1:])) / harmonics[0] if harmonics[0] > 0 else 0.0
                    fourier_results["thd"][net_name] = thd
                else:
                    fourier_results["thd"][net_name] = 0.0
            
            # Add metadata
            metadata = {
                "simulation_type": "Fourier",
                "parameters": {
                    "fundamental_frequency": fundamental_freq,
                    "num_harmonics": num_harmonics,
                    "window_type": window_type
                },
                "circuit_stats": {
                    "components": len(circuit.get("components", {})),
                    "nets": len(circuit.get("nets", {})),
                    "harmonics": num_harmonics
                }
            }
            
            logger.info(f"Fourier analysis completed for {num_harmonics} harmonics")
            return SimulationResult(
                simulation_type=SimulationType.FOURIER,
                data=fourier_results,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in Fourier analysis: {str(e)}")
            return SimulationResult(
                simulation_type=SimulationType.FOURIER,
                data={},
                metadata={},
                success=False,
                error_message=f"Fourier analysis failed: {str(e)}"
            )
    
    def clear_cache(self) -> None:
        """Clear the results cache."""
        self.results_cache.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get simulation metrics.
        
        Returns:
            Dictionary of metrics
        """
        try:
            metrics = {
                "cache_size": len(self.results_cache),
                "total_simulations": len(self.results_cache),
                "successful_simulations": 0,
                "failed_simulations": 0,
                "simulation_types": {},
                "average_execution_time": 0.0,
                "memory_usage": 0.0
            }
            
            # Calculate metrics from cached results
            total_time = 0.0
            for cache_key, result in self.results_cache.items():
                if result.success:
                    metrics["successful_simulations"] += 1
                else:
                    metrics["failed_simulations"] += 1
                
                # Count simulation types
                sim_type = result.simulation_type.value
                metrics["simulation_types"][sim_type] = metrics["simulation_types"].get(sim_type, 0) + 1
                
                # Extract execution time from metadata
                if result.metadata and "execution_time" in result.metadata:
                    total_time += result.metadata["execution_time"]
            
            # Calculate average execution time
            if metrics["total_simulations"] > 0:
                metrics["average_execution_time"] = total_time / metrics["total_simulations"]
            
            # Estimate memory usage (rough calculation)
            metrics["memory_usage"] = len(self.results_cache) * 1024  # 1KB per result estimate
            
            logger.info(f"Retrieved simulation metrics: {metrics['successful_simulations']} successful, {metrics['failed_simulations']} failed")
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting simulation metrics: {str(e)}")
            return {}
    
    def plot_results(self, result: SimulationResult) -> None:
        """Plot simulation results.
        
        Args:
            result: Simulation result to plot
        """
        try:
            if not result.success or not result.data:
                logger.warning("Cannot plot unsuccessful or empty simulation result")
                return
            
            # Import plotting libraries (optional dependencies)
            try:
                import matplotlib.pyplot as plt
                import numpy as np
            except ImportError:
                logger.warning("Matplotlib not available for plotting. Install with: pip install matplotlib numpy")
                return
            
            # Create figure based on simulation type
            if result.simulation_type == SimulationType.AC:
                self._plot_ac_results(result, plt, np)
            elif result.simulation_type == SimulationType.TRANSIENT:
                self._plot_transient_results(result, plt, np)
            elif result.simulation_type == SimulationType.NOISE:
                self._plot_noise_results(result, plt, np)
            elif result.simulation_type == SimulationType.FOURIER:
                self._plot_fourier_results(result, plt, np)
            elif result.simulation_type == SimulationType.DC:
                self._plot_dc_results(result, plt, np)
            else:
                logger.warning(f"Plotting not implemented for simulation type: {result.simulation_type}")
            
        except Exception as e:
            logger.error(f"Error plotting simulation results: {str(e)}")
    
    # Helper methods for simulation calculations
    
    def _calculate_node_voltage(self, net_name: str, net_data: Dict[str, Any], voltage_sources: Dict[str, float]) -> float:
        """Calculate node voltage for a net.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            voltage_sources: Dictionary of voltage sources
            
        Returns:
            Calculated voltage
        """
        # Simplified voltage calculation based on connected components
        if net_name in voltage_sources:
            return voltage_sources[net_name]
        
        # Calculate based on connected components
        total_voltage = 0.0
        total_weight = 0.0
        
        for track in net_data.get("tracks", []):
            # Simple voltage drop calculation
            length = math.sqrt((track["end"][0] - track["start"][0])**2 + (track["end"][1] - track["start"][1])**2)
            resistance = length * 0.1  # 0.1 ohm per unit length (simplified)
            voltage_drop = 0.1  # Simplified voltage drop
            total_voltage += voltage_drop
            total_weight += 1.0
        
        return total_voltage / total_weight if total_weight > 0 else 0.0
    
    def _calculate_branch_current(self, net_name: str, net_data: Dict[str, Any]) -> float:
        """Calculate branch current for a net.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            
        Returns:
            Calculated current
        """
        # Simplified current calculation
        if net_name.startswith(("VCC", "VDD", "+")):
            return 0.1  # 100mA typical for power nets
        elif net_name.startswith(("GND", "VSS", "-")):
            return 0.0  # Ground nets have no current
        else:
            return 0.01  # 10mA typical for signal nets
    
    def _calculate_component_power(self, component_ref: str, component_data: Dict[str, Any], dc_results: Dict[str, Any]) -> float:
        """Calculate power dissipation for a component.
        
        Args:
            component_ref: Component reference
            component_data: Component data
            dc_results: DC simulation results
            
        Returns:
            Calculated power dissipation
        """
        # Simplified power calculation
        component_type = component_data.get("value", "").upper()
        
        if "OP" in component_type or "AMP" in component_type:
            return 0.1  # 100mW typical for op-amps
        elif "REG" in component_type:
            return 0.5  # 500mW typical for regulators
        elif "C" in component_ref:
            return 0.001  # 1mW typical for capacitors
        elif "R" in component_ref:
            return 0.01  # 10mW typical for resistors
        else:
            return 0.05  # 50mW default
    
    def _calculate_magnitude_response_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float, amplitude: float) -> float:
        """Calculate magnitude response for a net with high-precision support.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            frequency: Frequency in Hz
            amplitude: Input amplitude
            
        Returns:
            Magnitude response
        """
        # Simplified frequency response calculation
        # This would normally involve complex impedance calculations
        
        # Simple low-pass filter response
        cutoff_freq = 1e6  # 1MHz cutoff
        if frequency < cutoff_freq:
            return amplitude
        else:
            return amplitude / (1 + (frequency / cutoff_freq)**2)**0.5
    
    def _calculate_phase_response_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float) -> float:
        """Calculate phase response for a net with high-precision support.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            frequency: Frequency in Hz
            
        Returns:
            Phase response in degrees
        """
        # Simplified phase response calculation
        cutoff_freq = 1e6  # 1MHz cutoff
        if frequency < cutoff_freq:
            return 0.0
        else:
            return -45.0 * math.log10(frequency / cutoff_freq)
    
    def _calculate_impedance_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float) -> float:
        """Calculate impedance for a net with high-precision support.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            frequency: Frequency in Hz
            
        Returns:
            Impedance in ohms
        """
        # Simplified impedance calculation
        if net_name.startswith(("VCC", "VDD", "+")):
            return 0.1  # Low impedance for power nets
        elif net_name.startswith(("GND", "VSS", "-")):
            return 0.01  # Very low impedance for ground nets
        else:
            return 50.0  # 50 ohm typical for signal nets
    
    def _generate_input_signal(self, time_points: List[float], signal_type: str, amplitude: float) -> List[float]:
        """Generate input signal for transient simulation.
        
        Args:
            time_points: List of time points
            signal_type: Type of signal (step, sine, square, etc.)
            amplitude: Signal amplitude
            
        Returns:
            List of signal values
        """
        signal_values = []
        
        for t in time_points:
            if signal_type == "step":
                signal_values.append(amplitude if t > 0 else 0.0)
            elif signal_type == "sine":
                freq = 1e3  # 1kHz
                signal_values.append(amplitude * math.sin(2 * math.pi * freq * t))
            elif signal_type == "square":
                freq = 1e3  # 1kHz
                signal_values.append(amplitude if math.sin(2 * math.pi * freq * t) > 0 else -amplitude)
            else:
                signal_values.append(0.0)
        
        return signal_values
    
    def _calculate_transient_voltage(self, net_name: str, net_data: Dict[str, Any], time: float, input_signal: List[float]) -> float:
        """Calculate transient voltage for a net.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            time: Time point
            input_signal: Input signal values
            
        Returns:
            Calculated voltage
        """
        # Simplified transient response calculation
        # This would normally involve solving differential equations
        
        # Simple RC response
        tau = 1e-6  # 1μs time constant
        input_index = min(int(time * 1e6), len(input_signal) - 1)  # Convert to microseconds
        input_val = input_signal[input_index] if input_index < len(input_signal) else 0.0
        
        return input_val * (1 - math.exp(-time / tau))
    
    def _calculate_transient_current(self, net_name: str, net_data: Dict[str, Any], time: float, voltage: float) -> float:
        """Calculate transient current for a net.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            time: Time point
            voltage: Voltage at this time
            
        Returns:
            Calculated current
        """
        # Simplified current calculation
        impedance = self._calculate_impedance_high_precision(net_name, net_data, 1e3)  # Use 1kHz for transient
        return voltage / impedance if impedance > 0 else 0.0
    
    def _calculate_thermal_noise_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float, temperature: float) -> float:
        """Calculate thermal noise with high precision for extended audio bandwidth.
        
        Args:
            net_name: Net name
            net_data: Net data
            frequency: Frequency in Hz
            temperature: Temperature in K
            
        Returns:
            Thermal noise voltage in V/√Hz
        """
        try:
            k = 1.38e-23  # Boltzmann constant
            resistance = self._calculate_impedance_high_precision(net_name, net_data, frequency)
            
            # Enhanced bandwidth calculation for extended audio range
            if frequency > 20000.0:
                # Higher bandwidth for extended frequencies
                bandwidth = 2e6  # 2MHz for extended analysis
            else:
                bandwidth = 1e6  # 1MHz for standard audio
            
            # Calculate thermal noise with frequency-dependent resistance
            thermal_noise = math.sqrt(4 * k * temperature * resistance * bandwidth)
            
            # Add frequency-dependent effects for high frequencies
            if frequency > 20000.0:
                # Skin effect and dielectric losses at high frequencies
                skin_effect_factor = math.sqrt(frequency / 20000.0)
                thermal_noise *= skin_effect_factor
            
            return thermal_noise
            
        except Exception as e:
            logger.error(f"Error calculating high-precision thermal noise: {e}")
            return 1e-9  # 1nV/√Hz default
    
    def _calculate_shot_noise_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float) -> float:
        """Calculate shot noise with high precision for extended audio bandwidth.
        
        Args:
            net_name: Net name
            net_data: Net data
            frequency: Frequency in Hz
            
        Returns:
            Shot noise voltage in V/√Hz
        """
        try:
            q = 1.602e-19  # Elementary charge
            current = self._estimate_current_level(net_name, net_data, frequency)
            
            # Enhanced bandwidth calculation
            if frequency > 20000.0:
                bandwidth = 2e6  # 2MHz for extended analysis
            else:
                bandwidth = 1e6  # 1MHz for standard audio
            
            shot_current = math.sqrt(2 * q * current * bandwidth)
            impedance = self._calculate_impedance_high_precision(net_name, net_data, frequency)
            
            # Add frequency-dependent effects
            if frequency > 20000.0:
                # High-frequency effects on shot noise
                hf_factor = 1.0 + 0.1 * math.log10(frequency / 20000.0)
                shot_current *= hf_factor
            
            return shot_current * impedance
            
        except Exception as e:
            logger.error(f"Error calculating high-precision shot noise: {e}")
            return 1e-9  # 1nV/√Hz default
    
    def _calculate_flicker_noise_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float) -> float:
        """Calculate flicker noise with high precision for extended audio bandwidth.
        
        Args:
            net_name: Net name
            net_data: Net data
            frequency: Frequency in Hz
            
        Returns:
            Flicker noise voltage in V/√Hz
        """
        try:
            # Base flicker noise (1/f noise)
            base_noise = 1e-9 / math.sqrt(frequency)  # 1nV/√Hz at 1Hz
            
            # Enhanced flicker noise model for extended bandwidth
            if frequency > 20000.0:
                # Flicker noise typically decreases at high frequencies
                # but some components may show different behavior
                flicker_corner = 1000.0  # 1kHz corner frequency
                if frequency > flicker_corner:
                    # Above corner frequency, flicker noise decreases
                    flicker_factor = math.sqrt(flicker_corner / frequency)
                else:
                    flicker_factor = 1.0
                
                # Add high-frequency flicker noise components
                hf_flicker = base_noise * 0.1 * math.exp(-frequency / 50000.0)  # Exponential decay
                base_noise = base_noise * flicker_factor + hf_flicker
            
            return base_noise
            
        except Exception as e:
            logger.error(f"Error calculating high-precision flicker noise: {e}")
            return 1e-9  # 1nV/√Hz default
    
    def _calculate_high_frequency_noise(self, net_name: str, net_data: Dict[str, Any], frequency: float, temperature: float) -> float:
        """Calculate high-frequency noise components for frequencies above 20kHz.
        
        Args:
            net_name: Net name
            net_data: Net data
            frequency: Frequency in Hz (should be > 20kHz)
            temperature: Temperature in K
            
        Returns:
            High-frequency noise voltage in V/√Hz
        """
        try:
            if frequency <= 20000.0:
                return 0.0
            
            # High-frequency noise sources
            hf_noise = 0.0
            
            # 1. Dielectric losses in PCB substrate
            dielectric_loss = 1e-10 * math.sqrt(frequency / 20000.0)  # Frequency-dependent dielectric loss
            
            # 2. Skin effect in conductors
            skin_effect_noise = 5e-11 * math.sqrt(frequency / 20000.0)  # Skin effect contribution
            
            # 3. Radiation losses at high frequencies
            radiation_loss = 1e-11 * (frequency / 20000.0)  # Radiation loss increases with frequency
            
            # 4. Component parasitics (capacitance, inductance)
            parasitic_noise = 2e-11 * math.sqrt(frequency / 20000.0)  # Parasitic effects
            
            # Combine high-frequency noise components
            hf_noise = math.sqrt(dielectric_loss**2 + skin_effect_noise**2 + 
                               radiation_loss**2 + parasitic_noise**2)
            
            # Temperature dependence
            hf_noise *= math.sqrt(temperature / 300.0)
            
            return hf_noise
            
        except Exception as e:
            logger.error(f"Error calculating high-frequency noise: {e}")
            return 0.0
    
    def _calculate_noise_figure_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float, total_noise: float, reference_impedance: float) -> float:
        """Calculate noise figure with high precision for extended audio bandwidth.
        
        Args:
            net_name: Net name
            net_data: Net data
            frequency: Frequency in Hz
            total_noise: Total noise voltage
            reference_impedance: Reference impedance in Ω
            
        Returns:
            Noise figure in dB
        """
        try:
            # Calculate available noise power
            available_noise_power = total_noise**2 / (4 * reference_impedance)
            
            # Calculate thermal noise power at reference temperature
            k = 1.38e-23  # Boltzmann constant
            T0 = 290.0  # Reference temperature (K)
            
            if frequency > 20000.0:
                bandwidth = 2e6  # 2MHz for extended analysis
            else:
                bandwidth = 1e6  # 1MHz for standard audio
            
            thermal_noise_power = k * T0 * bandwidth
            
            # Calculate noise figure
            if thermal_noise_power > 0:
                noise_figure = 10 * math.log10(available_noise_power / thermal_noise_power)
            else:
                noise_figure = 0.0
            
            # Add frequency-dependent corrections for high frequencies
            if frequency > 20000.0:
                # High-frequency noise figure corrections
                hf_correction = 0.5 * math.log10(frequency / 20000.0)
                noise_figure += hf_correction
            
            return noise_figure
            
        except Exception as e:
            logger.error(f"Error calculating high-precision noise figure: {e}")
            return 0.0
    
    def _estimate_signal_level_high_precision(self, net_name: str, net_data: Dict[str, Any], frequency: float) -> float:
        """Estimate signal level with high precision for extended audio bandwidth.
        
        Args:
            net_name: Net name
            net_data: Net data
            frequency: Frequency in Hz
            
        Returns:
            Estimated signal level in V
        """
        try:
            # Base signal level estimation
            base_level = self._estimate_signal_level(net_name, net_data, frequency)
            
            # Enhanced estimation for high frequencies
            if frequency > 20000.0:
                # High-frequency signal level adjustments
                # Signals may have different characteristics at high frequencies
                hf_factor = 1.0 - 0.1 * math.log10(frequency / 20000.0)  # Slight rolloff
                base_level *= max(0.1, hf_factor)  # Minimum 10% of base level
            
            return base_level
            
        except Exception as e:
            logger.error(f"Error estimating high-precision signal level: {e}")
            return 1.0  # 1V default
    
    def _estimate_current_level(self, net_name: str, net_data: Dict[str, Any], frequency: float) -> float:
        """Estimate current level for noise calculations.
        
        Args:
            net_name: Net name
            net_data: Net data
            frequency: Frequency in Hz
            
        Returns:
            Estimated current level in A
        """
        try:
            # Estimate current based on net characteristics
            signal_level = self._estimate_signal_level_high_precision(net_name, net_data, frequency)
            impedance = self._calculate_impedance_high_precision(net_name, net_data, frequency)
            
            if impedance > 0:
                return signal_level / impedance
            else:
                return 1e-3  # 1mA default
                
        except Exception as e:
            logger.error(f"Error estimating current level: {e}")
            return 1e-3  # 1mA default
    
    def _analyze_noise_spectrum(self, frequencies: List[float], thermal: List[float], shot: List[float], 
                               flicker: List[float], hf_noise: List[float], high_precision: bool) -> Dict[str, Any]:
        """Analyze noise spectrum characteristics for high-precision audio analysis.
        
        Args:
            frequencies: List of frequency points
            thermal: Thermal noise values
            shot: Shot noise values
            flicker: Flicker noise values
            hf_noise: High-frequency noise values
            high_precision: High-precision mode flag
            
        Returns:
            Dictionary containing noise spectrum analysis
        """
        try:
            if not frequencies or len(frequencies) != len(thermal):
                return {}
            
            # Calculate total noise spectrum
            total_noise = [(t**2 + s**2 + f**2 + h**2)**0.5 
                          for t, s, f, h in zip(thermal, shot, flicker, hf_noise)]
            
            # Find dominant noise source at different frequency ranges
            low_freq_range = [i for i, f in enumerate(frequencies) if f <= 1000.0]
            mid_freq_range = [i for i, f in enumerate(frequencies) if 1000.0 < f <= 20000.0]
            high_freq_range = [i for i, f in enumerate(frequencies) if f > 20000.0]
            
            # Analyze dominant noise sources
            dominant_sources = {}
            if low_freq_range:
                low_freq_thermal = sum(thermal[i] for i in low_freq_range) / len(low_freq_range)
                low_freq_flicker = sum(flicker[i] for i in low_freq_range) / len(low_freq_range)
                dominant_sources["low_frequency"] = "flicker" if low_freq_flicker > low_freq_thermal else "thermal"
            
            if mid_freq_range:
                mid_freq_thermal = sum(thermal[i] for i in mid_freq_range) / len(mid_freq_range)
                mid_freq_shot = sum(shot[i] for i in mid_freq_range) / len(mid_freq_range)
                dominant_sources["mid_frequency"] = "shot" if mid_freq_shot > mid_freq_thermal else "thermal"
            
            if high_freq_range:
                high_freq_thermal = sum(thermal[i] for i in high_freq_range) / len(high_freq_range)
                high_freq_hf = sum(hf_noise[i] for i in high_freq_range) / len(high_freq_range)
                dominant_sources["high_frequency"] = "high_frequency" if high_freq_hf > high_freq_thermal else "thermal"
            
            # Calculate noise metrics
            noise_metrics = {
                "total_noise_rms": math.sqrt(sum(n**2 for n in total_noise) / len(total_noise)),
                "peak_noise": max(total_noise),
                "noise_floor": min(total_noise),
                "noise_dynamic_range": max(total_noise) / min(total_noise) if min(total_noise) > 0 else float('inf'),
                "average_noise": sum(total_noise) / len(total_noise)
            }
            
            # High-precision analysis
            precision_analysis = {}
            if high_precision:
                # Calculate noise slope analysis
                noise_slopes = []
                for i in range(1, len(frequencies)):
                    if frequencies[i] > frequencies[i-1]:
                        slope = (total_noise[i] - total_noise[i-1]) / (frequencies[i] - frequencies[i-1])
                        noise_slopes.append(slope)
                
                if noise_slopes:
                    precision_analysis["average_noise_slope"] = sum(noise_slopes) / len(noise_slopes)
                    precision_analysis["noise_slope_variation"] = max(noise_slopes) - min(noise_slopes)
                
                # Calculate frequency-dependent noise characteristics
                precision_analysis["frequency_dependent_analysis"] = {
                    "low_freq_noise": sum(total_noise[i] for i in low_freq_range) / len(low_freq_range) if low_freq_range else 0,
                    "mid_freq_noise": sum(total_noise[i] for i in mid_freq_range) / len(mid_freq_range) if mid_freq_range else 0,
                    "high_freq_noise": sum(total_noise[i] for i in high_freq_range) / len(high_freq_range) if high_freq_range else 0
                }
            
            return {
                "dominant_noise_sources": dominant_sources,
                "noise_metrics": noise_metrics,
                "precision_analysis": precision_analysis,
                "frequency_ranges": {
                    "low_frequency": len(low_freq_range),
                    "mid_frequency": len(mid_freq_range),
                    "high_frequency": len(high_freq_range)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing noise spectrum: {e}")
            return {}
    
    def _calculate_fourier_magnitude(self, net_name: str, net_data: Dict[str, Any], frequency: float, fundamental_freq: float) -> float:
        """Calculate Fourier magnitude spectrum.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            frequency: Frequency in Hz
            fundamental_freq: Fundamental frequency
            
        Returns:
            Magnitude at this frequency
        """
        # Simplified Fourier magnitude calculation
        # This would normally involve FFT of time-domain signal
        
        harmonic_number = frequency / fundamental_freq
        if harmonic_number < 1:
            return 0.0
        
        # Simple harmonic decay
        return 1.0 / harmonic_number
    
    def _calculate_fourier_phase(self, net_name: str, net_data: Dict[str, Any], frequency: float, fundamental_freq: float) -> float:
        """Calculate Fourier phase spectrum.
        
        Args:
            net_name: Name of the net
            net_data: Net data
            frequency: Frequency in Hz
            fundamental_freq: Fundamental frequency
            
        Returns:
            Phase at this frequency in degrees
        """
        # Simplified Fourier phase calculation
        harmonic_number = frequency / fundamental_freq
        if harmonic_number < 1:
            return 0.0
        
        # Simple phase progression
        return 45.0 * harmonic_number
    
    def _generate_audio_frequency_points(self, start_freq: float, stop_freq: float, num_points: int, high_precision: bool = True) -> List[float]:
        """Generate frequency points optimized for audio analysis with high precision.
        
        Args:
            start_freq: Start frequency in Hz
            stop_freq: Stop frequency in Hz
            num_points: Number of frequency points
            high_precision: Enable high-precision mode
            
        Returns:
            List of frequency points optimized for audio analysis
        """
        frequencies = []
        
        if high_precision:
            # Use logarithmic distribution with higher density in critical audio ranges
            # More points in 20Hz-1kHz (low frequency detail)
            # More points in 1kHz-20kHz (mid frequency detail)
            # More points in 20kHz-80kHz (high frequency detail)
            
            # Calculate distribution weights
            low_freq_weight = 0.3   # 30% of points for 20Hz-1kHz
            mid_freq_weight = 0.4   # 40% of points for 1kHz-20kHz
            high_freq_weight = 0.3  # 30% of points for 20kHz-80kHz
            
            # Generate low frequency points (20Hz - 1kHz)
            low_freq_points = int(num_points * low_freq_weight)
            for i in range(low_freq_points):
                freq = start_freq * (1000.0 / start_freq) ** (i / (low_freq_points - 1))
                frequencies.append(freq)
            
            # Generate mid frequency points (1kHz - 20kHz)
            mid_freq_points = int(num_points * mid_freq_weight)
            for i in range(mid_freq_points):
                freq = 1000.0 * (20000.0 / 1000.0) ** (i / (mid_freq_points - 1))
                frequencies.append(freq)
            
            # Generate high frequency points (20kHz - 80kHz)
            high_freq_points = num_points - len(frequencies)
            for i in range(high_freq_points):
                freq = 20000.0 * (stop_freq / 20000.0) ** (i / (high_freq_points - 1))
                frequencies.append(freq)
            
            # Sort and remove duplicates
            frequencies = sorted(list(set(frequencies)))
            
        else:
            # Standard logarithmic distribution
            for i in range(num_points):
                if num_points == 1:
                    freq = start_freq
                else:
                    freq = start_freq * (stop_freq / start_freq) ** (i / (num_points - 1))
                frequencies.append(freq)
        
        return frequencies
    
    def _analyze_bandwidth_characteristics(self, frequencies: List[float], magnitude: List[float], phase: List[float], high_precision: bool) -> Dict[str, Any]:
        """Analyze bandwidth characteristics for high-precision audio analysis.
        
        Args:
            frequencies: List of frequency points
            magnitude: Magnitude response
            phase: Phase response
            high_precision: High-precision mode flag
            
        Returns:
            Dictionary containing bandwidth analysis results
        """
        try:
            if not frequencies or not magnitude or len(frequencies) != len(magnitude):
                return {}
            
            # Find -3dB bandwidth
            max_magnitude = max(magnitude)
            threshold = max_magnitude / math.sqrt(2)  # -3dB point
            
            # Find low frequency -3dB point
            low_freq_3db = frequencies[0]
            for i, mag in enumerate(magnitude):
                if mag >= threshold:
                    low_freq_3db = frequencies[i]
                    break
            
            # Find high frequency -3dB point
            high_freq_3db = frequencies[-1]
            for i in range(len(magnitude) - 1, -1, -1):
                if magnitude[i] >= threshold:
                    high_freq_3db = frequencies[i]
                    break
            
            # Calculate bandwidth
            bandwidth = high_freq_3db - low_freq_3db
            
            # Calculate flatness (variation in passband)
            passband_magnitudes = [mag for freq, mag in zip(frequencies, magnitude) 
                                 if low_freq_3db <= freq <= high_freq_3db]
            if passband_magnitudes:
                flatness = min(passband_magnitudes) / max(passband_magnitudes)
            else:
                flatness = 1.0
            
            # Calculate phase variation
            passband_phases = [ph for freq, ph in zip(frequencies, phase) 
                             if low_freq_3db <= freq <= high_freq_3db]
            if passband_phases:
                phase_variation = max(passband_phases) - min(passband_phases)
            else:
                phase_variation = 0.0
            
            # High-precision metrics
            precision_metrics = {}
            if high_precision:
                # Calculate group delay
                group_delay = self._calculate_group_delay(frequencies, phase)
                precision_metrics["group_delay"] = group_delay
                
                # Calculate phase linearity
                phase_linearity = self._calculate_phase_linearity(frequencies, phase)
                precision_metrics["phase_linearity"] = phase_linearity
                
                # Calculate frequency resolution
                freq_resolution = (frequencies[-1] - frequencies[0]) / len(frequencies)
                precision_metrics["frequency_resolution"] = freq_resolution
            
            return {
                "low_freq_3db": low_freq_3db,
                "high_freq_3db": high_freq_3db,
                "bandwidth": bandwidth,
                "flatness": flatness,
                "phase_variation": phase_variation,
                "max_frequency": max(frequencies),
                "extended_bandwidth": max(frequencies) > 20000.0,
                "precision_metrics": precision_metrics
            }
            
        except Exception as e:
            logger.error(f"Error analyzing bandwidth characteristics: {e}")
            return {}
    
    def _calculate_precision_metrics(self, frequencies: List[float], ac_results: Dict[str, Any], high_precision: bool) -> Dict[str, Any]:
        """Calculate precision metrics for high-precision audio analysis.
        
        Args:
            frequencies: List of frequency points
            ac_results: AC simulation results
            high_precision: High-precision mode flag
            
        Returns:
            Dictionary containing precision metrics
        """
        try:
            metrics = {
                "frequency_range": {
                    "min": min(frequencies),
                    "max": max(frequencies),
                    "span": max(frequencies) - min(frequencies)
                },
                "resolution": {
                    "points": len(frequencies),
                    "average_step": (max(frequencies) - min(frequencies)) / len(frequencies),
                    "logarithmic": True
                },
                "bandwidth_coverage": {
                    "audio_bandwidth": max(frequencies) >= 20000.0,
                    "extended_bandwidth": max(frequencies) >= 80000.0,
                    "ultra_high_frequency": max(frequencies) > 100000.0
                }
            }
            
            if high_precision:
                # Calculate additional precision metrics
                metrics["precision_enhancements"] = {
                    "high_precision_mode": True,
                    "extended_analysis": True,
                    "enhanced_resolution": len(frequencies) >= 200,
                    "frequency_distribution": "optimized_audio"
                }
                
                # Calculate signal quality metrics
                if "magnitude_response" in ac_results:
                    all_magnitudes = []
                    for net_magnitudes in ac_results["magnitude_response"].values():
                        all_magnitudes.extend(net_magnitudes)
                    
                    if all_magnitudes:
                        metrics["signal_quality"] = {
                            "dynamic_range": max(all_magnitudes) / min(all_magnitudes) if min(all_magnitudes) > 0 else float('inf'),
                            "average_magnitude": sum(all_magnitudes) / len(all_magnitudes),
                            "magnitude_variation": max(all_magnitudes) - min(all_magnitudes)
                        }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating precision metrics: {e}")
            return {}
    
    def _calculate_group_delay(self, frequencies: List[float], phase: List[float]) -> List[float]:
        """Calculate group delay from phase response.
        
        Args:
            frequencies: List of frequency points
            phase: Phase response in degrees
            
        Returns:
            List of group delay values in seconds
        """
        try:
            if len(frequencies) < 2 or len(phase) < 2:
                return []
            
            group_delay = []
            for i in range(1, len(frequencies)):
                # Calculate group delay as negative derivative of phase
                phase_diff = (phase[i] - phase[i-1]) * math.pi / 180.0  # Convert to radians
                freq_diff = frequencies[i] - frequencies[i-1]
                
                if freq_diff > 0:
                    delay = -phase_diff / (2 * math.pi * freq_diff)
                    group_delay.append(delay)
                else:
                    group_delay.append(0.0)
            
            # Add first point (extrapolate)
            if group_delay:
                group_delay.insert(0, group_delay[0])
            
            return group_delay
            
        except Exception as e:
            logger.error(f"Error calculating group delay: {e}")
            return []
    
    def _calculate_phase_linearity(self, frequencies: List[float], phase: List[float]) -> float:
        """Calculate phase linearity as a measure of phase distortion.
        
        Args:
            frequencies: List of frequency points
            phase: Phase response in degrees
            
        Returns:
            Phase linearity score (0-1, higher is better)
        """
        try:
            if len(frequencies) < 3 or len(phase) < 3:
                return 1.0
            
            # Fit linear trend to phase vs frequency
            # Calculate deviation from linearity
            phase_normalized = [p - phase[0] for p in phase]
            freq_normalized = [f - frequencies[0] for f in frequencies]
            
            # Simple linear fit
            if max(freq_normalized) > 0:
                slope = max(phase_normalized) / max(freq_normalized)
                linear_phase = [slope * f for f in freq_normalized]
                
                # Calculate RMS deviation
                deviations = [abs(p - lp) for p, lp in zip(phase_normalized, linear_phase)]
                rms_deviation = math.sqrt(sum(d*d for d in deviations) / len(deviations))
                
                # Convert to linearity score (0-1)
                max_phase_range = max(phase_normalized) - min(phase_normalized)
                if max_phase_range > 0:
                    linearity = max(0, 1 - rms_deviation / max_phase_range)
                else:
                    linearity = 1.0
                
                return linearity
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating phase linearity: {e}")
            return 1.0
    
    # Plotting helper methods
    
    def _plot_ac_results(self, result: SimulationResult, plt, np) -> None:
        """Plot AC simulation results.
        
        Args:
            result: AC simulation result
            plt: Matplotlib pyplot
            np: NumPy
        """
        data = result.data
        frequencies = data.get("frequencies", [])
        
        if not frequencies:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("AC Simulation Results")
        
        # Magnitude response
        for net_name, magnitude in data.get("magnitude_response", {}).items():
            ax1.semilogx(frequencies, [20 * math.log10(m) if m > 0 else -100 for m in magnitude], label=net_name)
        ax1.set_xlabel("Frequency (Hz)")
        ax1.set_ylabel("Magnitude (dB)")
        ax1.set_title("Magnitude Response")
        ax1.grid(True)
        ax1.legend()
        
        # Phase response
        for net_name, phase in data.get("phase_response", {}).items():
            ax2.semilogx(frequencies, phase, label=net_name)
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Phase (degrees)")
        ax2.set_title("Phase Response")
        ax2.grid(True)
        ax2.legend()
        
        # Impedance
        for net_name, impedance in data.get("impedance", {}).items():
            ax3.semilogx(frequencies, impedance, label=net_name)
        ax3.set_xlabel("Frequency (Hz)")
        ax3.set_ylabel("Impedance (Ω)")
        ax3.set_title("Impedance")
        ax3.grid(True)
        ax3.legend()
        
        # Transfer functions
        for tf_name, tf_data in data.get("transfer_functions", {}).items():
            ax4.semilogx(frequencies, [20 * math.log10(m) if m > 0 else -100 for m in tf_data["magnitude"]], label=tf_name)
        ax4.set_xlabel("Frequency (Hz)")
        ax4.set_ylabel("Transfer Function (dB)")
        ax4.set_title("Transfer Functions")
        ax4.grid(True)
        ax4.legend()
        
        plt.tight_layout()
        plt.show()
    
    def _plot_transient_results(self, result: SimulationResult, plt, np) -> None:
        """Plot transient simulation results.
        
        Args:
            result: Transient simulation result
            plt: Matplotlib pyplot
            np: NumPy
        """
        data = result.data
        time_points = data.get("time", [])
        
        if not time_points:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("Transient Simulation Results")
        
        # Voltages
        for net_name, voltages in data.get("voltages", {}).items():
            ax1.plot(time_points, voltages, label=net_name)
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Voltage (V)")
        ax1.set_title("Voltage Response")
        ax1.grid(True)
        ax1.legend()
        
        # Currents
        for net_name, currents in data.get("currents", {}).items():
            ax2.plot(time_points, currents, label=net_name)
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Current (A)")
        ax2.set_title("Current Response")
        ax2.grid(True)
        ax2.legend()
        
        # Power
        for net_name, power in data.get("power", {}).items():
            ax3.plot(time_points, power, label=net_name)
        ax3.set_xlabel("Time (s)")
        ax3.set_ylabel("Power (W)")
        ax3.set_title("Power Dissipation")
        ax3.grid(True)
        ax3.legend()
        
        # Input signal
        if "input" in data.get("signals", {}):
            ax4.plot(time_points, data["signals"]["input"], label="Input", linewidth=2)
        ax4.set_xlabel("Time (s)")
        ax4.set_ylabel("Amplitude")
        ax4.set_title("Input Signal")
        ax4.grid(True)
        ax4.legend()
        
        plt.tight_layout()
        plt.show()
    
    def _plot_noise_results(self, result: SimulationResult, plt, np) -> None:
        """Plot noise simulation results.
        
        Args:
            result: Noise simulation result
            plt: Matplotlib pyplot
            np: NumPy
        """
        data = result.data
        frequencies = data.get("frequencies", [])
        
        if not frequencies:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("Noise Analysis Results")
        
        # Total noise
        for net_name, total_noise in data.get("total_noise", {}).items():
            ax1.semilogx(frequencies, [20 * math.log10(n) if n > 0 else -100 for n in total_noise], label=net_name)
        ax1.set_xlabel("Frequency (Hz)")
        ax1.set_ylabel("Noise (dBV)")
        ax1.set_title("Total Noise")
        ax1.grid(True)
        ax1.legend()
        
        # Noise figure
        for net_name, nf in data.get("noise_figure", {}).items():
            ax2.semilogx(frequencies, nf, label=net_name)
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Noise Figure (dB)")
        ax2.set_title("Noise Figure")
        ax2.grid(True)
        ax2.legend()
        
        # SNR
        for net_name, snr in data.get("snr", {}).items():
            ax3.semilogx(frequencies, snr, label=net_name)
        ax3.set_xlabel("Frequency (Hz)")
        ax3.set_ylabel("SNR (dB)")
        ax3.set_title("Signal-to-Noise Ratio")
        ax3.grid(True)
        ax3.legend()
        
        # Noise components
        for net_name in data.get("thermal_noise", {}):
            thermal = data["thermal_noise"][net_name]
            shot = data["shot_noise"][net_name]
            flicker = data["flicker_noise"][net_name]
            
            ax4.semilogx(frequencies, [20 * math.log10(n) if n > 0 else -100 for n in thermal], label=f"{net_name} (Thermal)")
            ax4.semilogx(frequencies, [20 * math.log10(n) if n > 0 else -100 for n in shot], label=f"{net_name} (Shot)")
            ax4.semilogx(frequencies, [20 * math.log10(n) if n > 0 else -100 for n in flicker], label=f"{net_name} (Flicker)")
        ax4.set_xlabel("Frequency (Hz)")
        ax4.set_ylabel("Noise (dBV)")
        ax4.set_title("Noise Components")
        ax4.grid(True)
        ax4.legend()
        
        plt.tight_layout()
        plt.show()
    
    def _plot_fourier_results(self, result: SimulationResult, plt, np) -> None:
        """Plot Fourier analysis results.
        
        Args:
            result: Fourier analysis result
            plt: Matplotlib pyplot
            np: NumPy
        """
        data = result.data
        frequencies = data.get("frequencies", [])
        
        if not frequencies:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("Fourier Analysis Results")
        
        # Magnitude spectrum
        for net_name, magnitude in data.get("magnitude_spectrum", {}).items():
            ax1.semilogy(frequencies, magnitude, label=net_name)
        ax1.set_xlabel("Frequency (Hz)")
        ax1.set_ylabel("Magnitude")
        ax1.set_title("Magnitude Spectrum")
        ax1.grid(True)
        ax1.legend()
        
        # Phase spectrum
        for net_name, phase in data.get("phase_spectrum", {}).items():
            ax2.plot(frequencies, phase, label=net_name)
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Phase (degrees)")
        ax2.set_title("Phase Spectrum")
        ax2.grid(True)
        ax2.legend()
        
        # Harmonic content
        for net_name, harmonics in data.get("harmonic_content", {}).items():
            ax3.semilogy(frequencies, harmonics, label=net_name)
        ax3.set_xlabel("Frequency (Hz)")
        ax3.set_ylabel("Harmonic Content")
        ax3.set_title("Harmonic Content")
        ax3.grid(True)
        ax3.legend()
        
        # THD
        thd_values = list(data.get("thd", {}).values())
        thd_names = list(data.get("thd", {}).keys())
        if thd_values:
            ax4.bar(range(len(thd_values)), thd_values)
            ax4.set_xlabel("Net")
            ax4.set_ylabel("THD")
            ax4.set_title("Total Harmonic Distortion")
            ax4.set_xticks(range(len(thd_names)))
            ax4.set_xticklabels(thd_names, rotation=45)
            ax4.grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def _plot_dc_results(self, result: SimulationResult, plt, np) -> None:
        """Plot DC simulation results.
        
        Args:
            result: DC simulation result
            plt: Matplotlib pyplot
            np: NumPy
        """
        data = result.data
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("DC Simulation Results")
        
        # Node voltages
        node_names = list(data.get("node_voltages", {}).keys())
        node_voltages = list(data.get("node_voltages", {}).values())
        if node_voltages:
            ax1.bar(range(len(node_voltages)), node_voltages)
            ax1.set_xlabel("Node")
            ax1.set_ylabel("Voltage (V)")
            ax1.set_title("Node Voltages")
            ax1.set_xticks(range(len(node_names)))
            ax1.set_xticklabels(node_names, rotation=45)
            ax1.grid(True)
        
        # Branch currents
        branch_names = list(data.get("branch_currents", {}).keys())
        branch_currents = list(data.get("branch_currents", {}).values())
        if branch_currents:
            ax2.bar(range(len(branch_currents)), branch_currents)
            ax2.set_xlabel("Branch")
            ax2.set_ylabel("Current (A)")
            ax2.set_title("Branch Currents")
            ax2.set_xticks(range(len(branch_names)))
            ax2.set_xticklabels(branch_names, rotation=45)
            ax2.grid(True)
        
        # Power dissipation
        component_names = list(data.get("power_dissipation", {}).keys())
        power_values = list(data.get("power_dissipation", {}).values())
        if power_values:
            ax3.bar(range(len(power_values)), power_values)
            ax3.set_xlabel("Component")
            ax3.set_ylabel("Power (W)")
            ax3.set_title("Power Dissipation")
            ax3.set_xticks(range(len(component_names)))
            ax3.set_xticklabels(component_names, rotation=45)
            ax3.grid(True)
        
        # Summary statistics
        if node_voltages:
            ax4.text(0.1, 0.8, f"Total Nodes: {len(node_voltages)}", transform=ax4.transAxes, fontsize=12)
            ax4.text(0.1, 0.6, f"Max Voltage: {max(node_voltages):.3f}V", transform=ax4.transAxes, fontsize=12)
            ax4.text(0.1, 0.4, f"Min Voltage: {min(node_voltages):.3f}V", transform=ax4.transAxes, fontsize=12)
            ax4.text(0.1, 0.2, f"Total Power: {sum(power_values):.3f}W", transform=ax4.transAxes, fontsize=12)
            ax4.set_title("Summary")
            ax4.axis('off')
        
        plt.tight_layout()
        plt.show() 
