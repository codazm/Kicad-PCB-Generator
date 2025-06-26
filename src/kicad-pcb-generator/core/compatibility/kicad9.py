"""KiCad 9 compatibility layer."""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pcbnew

class KiCad9Compatibility:
    """KiCad 9 compatibility layer.
    
    This class provides a compatibility layer for KiCad 9, handling version
    checking, board operations, and component management.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize compatibility layer.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.board = None
        self._check_version()
    
    def _check_version(self) -> None:
        """Check KiCad version.
        
        Raises:
            RuntimeError: If KiCad version is not 9.x
        """
        version = pcbnew.GetBuildVersion()
        match = re.match(r"(\d+)\.(\d+)", version)
        if not match:
            raise RuntimeError(f"Invalid KiCad version format: {version}")
        
        major, minor = map(int, match.groups())
        if major != 9:
            raise RuntimeError(f"KiCad version {major}.{minor} is not supported. Only version 9.x is supported.")
        
        self.logger.info(f"Using KiCad version {major}.{minor}")
    
    def get_board(self) -> Optional[pcbnew.BOARD]:
        """Get current board.
        
        Returns:
            Board if available
        """
        try:
            self.board = pcbnew.GetBoard()
            return self.board
        except Exception as e:
            self.logger.error(f"Failed to get board: {e}")
            return None
    
    def get_footprints(self) -> List[pcbnew.FOOTPRINT]:
        """Get all footprints.
        
        Returns:
            List of footprints
        """
        try:
            if not self.board:
                self.get_board()
            if not self.board:
                return []
            
            return list(self.board.GetFootprints())
        except Exception as e:
            self.logger.error(f"Failed to get footprints: {e}")
            return []
    
    def get_footprint(self, footprint_id: str) -> Optional[pcbnew.FOOTPRINT]:
        """Get footprint by ID.
        
        Args:
            footprint_id: Footprint ID
            
        Returns:
            Footprint if found
        """
        try:
            footprints = self.get_footprints()
            for footprint in footprints:
                if footprint.GetReference() == footprint_id:
                    return footprint
            return None
        except Exception as e:
            self.logger.error(f"Failed to get footprint: {e}")
            return None
    
    def update_footprint(
        self,
        footprint_id: str,
        position: Tuple[float, float],
        orientation: float
    ) -> bool:
        """Update footprint position and orientation.
        
        Args:
            footprint_id: Footprint ID
            position: (x, y) position in millimeters
            orientation: Orientation in degrees
            
        Returns:
            True if successful
        """
        try:
            footprint = self.get_footprint(footprint_id)
            if not footprint:
                return False
            
            # Convert position to internal units (nanometers)
            x, y = position
            x_nm = int(x * 1e6)
            y_nm = int(y * 1e6)
            
            # Set position
            footprint.SetPosition(pcbnew.VECTOR2I(x_nm, y_nm))
            
            # Set orientation
            footprint.SetOrientationDegrees(orientation)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update footprint: {e}")
            return False
    
    def get_nets(self) -> Dict[str, List[str]]:
        """Get all nets.
        
        Returns:
            Dictionary of nets and their connections
        """
        try:
            if not self.board:
                self.get_board()
            if not self.board:
                return {}
            
            nets = {}
            for net in self.board.GetNetsByName().values():
                net_name = net.GetNetname()
                connections = []
                
                # Get pads connected to this net
                for pad in net.GetPads():
                    footprint = pad.GetParent()
                    if footprint:
                        pad_name = pad.GetName()
                        connections.append(f"{footprint.GetReference()}-{pad_name}")
                
                nets[net_name] = connections
            
            return nets
            
        except Exception as e:
            self.logger.error(f"Failed to get nets: {e}")
            return {}
    
    def get_tracks(self) -> List[pcbnew.TRACK]:
        """Get all tracks.
        
        Returns:
            List of tracks
        """
        try:
            if not self.board:
                self.get_board()
            if not self.board:
                return []
            
            return list(self.board.GetTracks())
        except Exception as e:
            self.logger.error(f"Failed to get tracks: {e}")
            return []
    
    def get_zones(self) -> List[pcbnew.ZONE]:
        """Get all zones.
        
        Returns:
            List of zones
        """
        try:
            if not self.board:
                self.get_board()
            if not self.board:
                return []
            
            return list(self.board.Zones())
        except Exception as e:
            self.logger.error(f"Failed to get zones: {e}")
            return []
    
    def get_layers(self) -> List[str]:
        """Get all layers.
        
        Returns:
            List of layer names
        """
        try:
            if not self.board:
                self.get_board()
            if not self.board:
                return []
            
            return [self.board.GetLayerName(i) for i in range(self.board.GetCopperLayerCount())]
        except Exception as e:
            self.logger.error(f"Failed to get layers: {e}")
            return []
    
    def get_design_rules(self) -> Dict[str, Any]:
        """Get design rules.
        
        Returns:
            Dictionary of design rules
        """
        try:
            if not self.board:
                self.get_board()
            if not self.board:
                return {}
            
            rules = {}
            
            # Get clearance rules
            rules["clearance"] = self.board.GetDesignSettings().GetMinClearance()
            
            # Get track width rules
            rules["track_width"] = self.board.GetDesignSettings().GetTrackWidth()
            
            # Get via rules
            rules["via_diameter"] = self.board.GetDesignSettings().GetViasDimensions()
            rules["via_drill"] = self.board.GetDesignSettings().GetViasDrill()
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Failed to get design rules: {e}")
            return {}
    
    def save_board(self, file_path: str) -> bool:
        """Save board to file.
        
        Args:
            file_path: Path to save board
            
        Returns:
            True if successful
        """
        try:
            if not self.board:
                self.get_board()
            if not self.board:
                return False
            
            self.board.Save(file_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save board: {e}")
            return False
    
    def load_board(self, file_path: str) -> bool:
        """Load board from file.
        
        Args:
            file_path: Path to load board
            
        Returns:
            True if successful
        """
        try:
            self.board = pcbnew.LoadBoard(file_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load board: {e}")
            return False 