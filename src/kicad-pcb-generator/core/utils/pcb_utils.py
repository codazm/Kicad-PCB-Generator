"""Utility functions for PCB calculations."""
import math
from typing import Tuple, Optional
import pcbnew

class PCBUtils:
    """Utility functions for PCB calculations."""
    
    @staticmethod
    def calculate_track_distance(start1: Tuple[float, float], end1: Tuple[float, float],
                               start2: Tuple[float, float], end2: Tuple[float, float]) -> float:
        """Calculate minimum distance between two track segments.
        
        Args:
            start1: Start point of first track (x, y)
            end1: End point of first track (x, y)
            start2: Start point of second track (x, y)
            end2: End point of second track (x, y)
            
        Returns:
            Minimum distance between tracks in mm
        """
        # Check for intersection
        def ccw(A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float]) -> bool:
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        def intersect(A: Tuple[float, float], B: Tuple[float, float],
                     C: Tuple[float, float], D: Tuple[float, float]) -> bool:
            return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
        
        if intersect(start1, end1, start2, end2):
            return 0.0
        
        # Calculate minimum distance between segments
        def point_to_segment_distance(p: Tuple[float, float], v: Tuple[float, float],
                                    w: Tuple[float, float]) -> float:
            l2 = (w[0] - v[0])**2 + (w[1] - v[1])**2
            if l2 == 0:
                return math.sqrt((p[0] - v[0])**2 + (p[1] - v[1])**2)
            
            t = max(0, min(1, ((p[0] - v[0]) * (w[0] - v[0]) +
                              (p[1] - v[1]) * (w[1] - v[1])) / l2))
            
            px = v[0] + t * (w[0] - v[0])
            py = v[1] + t * (w[1] - v[1])
            
            return math.sqrt((p[0] - px)**2 + (p[1] - py)**2)
        
        distances = [
            point_to_segment_distance(start1, start2, end2),
            point_to_segment_distance(end1, start2, end2),
            point_to_segment_distance(start2, start1, end1),
            point_to_segment_distance(end2, start1, end1)
        ]
        
        return min(distances)
    
    @staticmethod
    def calculate_trace_impedance(width: float, layer: int) -> float:
        """Calculate trace impedance based on width and layer.
        
        Args:
            width: Trace width in mm
            layer: PCB layer number
            
        Returns:
            Estimated impedance in ohms
        """
        # Simplified microstrip impedance calculation
        h = 0.1  # Substrate height in mm
        t = 0.035  # Trace thickness in mm
        er = 4.5  # Substrate relative permittivity
        
        # Calculate effective width
        weff = width + 0.8 * t
        
        # Calculate impedance
        z0 = 87 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * weff + t))
        return z0
    
    @staticmethod
    def calculate_crosstalk_risk(distance: float, width1: float, width2: float) -> float:
        """Calculate crosstalk risk between two traces.
        
        Args:
            distance: Distance between traces in mm
            width1: Width of first trace in mm
            width2: Width of second trace in mm
            
        Returns:
            Crosstalk risk factor (0-1)
        """
        # Simplified crosstalk calculation
        h = 0.1  # Substrate height in mm
        k = 0.5  # Coupling coefficient
        
        # Calculate mutual capacitance
        cm = k * math.sqrt(width1 * width2) / (distance + h)
        
        # Normalize to 0-1 range
        return min(1.0, cm / 0.1)
    
    @staticmethod
    def estimate_track_current(width: float) -> float:
        """Estimate maximum current for a trace width.
        
        Args:
            width: Trace width in mm
            
        Returns:
            Estimated maximum current in amperes
        """
        # IPC-2221 current capacity estimation
        # External layer, 10°C temperature rise
        return width * 24.0  # 24A per mm width
    
    @staticmethod
    def calculate_voltage_drop(length: float, width: float, current: float) -> float:
        """Calculate voltage drop along a trace.
        
        Args:
            length: Trace length in mm
            width: Trace width in mm
            current: Current in amperes
            
        Returns:
            Voltage drop in volts
        """
        # Copper resistivity at 20°C (Ω·m)
        rho = 1.68e-8
        
        # Convert to meters
        length_m = length / 1000
        width_m = width / 1000
        thickness_m = 0.035 / 1000  # 35μm
        
        # Calculate resistance
        resistance = rho * length_m / (width_m * thickness_m)
        
        # Calculate voltage drop
        return resistance * current
    
    @staticmethod
    def calculate_ground_loop_area(net: str) -> float:
        """Calculate ground loop area for a net.
        
        Args:
            net: Net name
            
        Returns:
            Ground loop area in mm²
        """
        # This is a simplified calculation
        # In a real implementation, this would:
        # 1. Find all tracks in the net
        # 2. Calculate the area enclosed by the tracks
        # 3. Consider the return path through the ground plane
        return 50.0  # Placeholder value 
