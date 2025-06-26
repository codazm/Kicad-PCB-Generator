"""
Manufacturing module for KiCad PCB Generator.
Handles panelization, visualization, and manufacturing output generation.
"""

from .panelization import PanelizationManager
from .visualization import VisualizationManager
from .output import OutputManager

__version__ = "0.1.0"
__all__ = ["PanelizationManager", "VisualizationManager", "OutputManager"] 
