"""Template version control system for KiCad PCB designs."""

import os
import json
import shutil
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import pcbnew
from kicad_pcb_generator.utils.semantic_version import SemanticVersion

logger = logging.getLogger(__name__)

@dataclass
class VersionMetadata:
    """Metadata for a template version."""
    version: str
    author: str
    date: str
    description: str
    changes: List[str]
    validation_status: Dict[str, bool]
    dependencies: Dict[str, str]
    tags: List[str]

class TemplateVersionControl:
    """Manages template versions and version history."""
    
    def __init__(self, template_dir: str):
        """Initialize version control for a template.
        
        Args:
            template_dir: Path to template directory
        """
        self.template_dir = Path(template_dir)
        self.history_file = self.template_dir / "version_history.json"
        self.versions_dir = self.template_dir / "versions"
        self._ensure_directories()
        self._load_history()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self):
        """Load version history from JSON file."""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = {}
    
    def _save_history(self):
        """Save version history to JSON file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def create_version(self, board: pcbnew.BOARD, metadata: VersionMetadata) -> bool:
        """Create a new version of the template.
        
        Args:
            board: KiCad board object
            metadata: Version metadata
            
        Returns:
            bool: True if version was created successfully
        """
        try:
            # Validate version number
            version = SemanticVersion(metadata.version)
            if metadata.version in self.history:
                logger.error(f"Version {metadata.version} already exists")
                return False
            
            # Create version directory
            version_dir = self.versions_dir / metadata.version
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Save board files
            board_path = version_dir / "board.kicad_pcb"
            pcbnew.SaveBoard(str(board_path), board)
            
            # Save metadata
            metadata_path = version_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            # Update history
            self.history[metadata.version] = {
                'date': metadata.date,
                'author': metadata.author,
                'description': metadata.description,
                'validation_status': metadata.validation_status
            }
            self._save_history()
            
            logger.info(f"Created version {metadata.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create version: {str(e)}")
            return False
    
    def get_version(self, version: str) -> Optional[Tuple[pcbnew.BOARD, VersionMetadata]]:
        """Get a specific version of the template.
        
        Args:
            version: Version string
            
        Returns:
            Tuple of (board, metadata) if version exists, None otherwise
        """
        try:
            version_dir = self.versions_dir / version
            if not version_dir.exists():
                return None
            
            # Load board
            board_path = version_dir / "board.kicad_pcb"
            board = pcbnew.LoadBoard(str(board_path))
            
            # Load metadata
            metadata_path = version_dir / "metadata.json"
            with open(metadata_path, 'r') as f:
                metadata_dict = json.load(f)
                metadata = VersionMetadata(**metadata_dict)
            
            return board, metadata
            
        except Exception as e:
            logger.error(f"Failed to get version {version}: {str(e)}")
            return None
    
    def get_version_history(self) -> List[Dict]:
        """Get version history.
        
        Returns:
            List of version metadata dictionaries
        """
        return [
            {'version': v, **data}
            for v, data in sorted(
                self.history.items(),
                key=lambda x: SemanticVersion(x[0])
            )
        ]
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """Compare two versions of the template.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Dictionary of differences
        """
        try:
            v1_data = self.get_version(version1)
            v2_data = self.get_version(version2)
            
            if not v1_data or not v2_data:
                return {'error': 'One or both versions not found'}
            
            board1, meta1 = v1_data
            board2, meta2 = v2_data
            
            # Compare board properties
            board_diff = {
                'layers': board1.GetCopperLayerCount() != board2.GetCopperLayerCount(),
                'components': len(board1.GetFootprints()) != len(board2.GetFootprints()),
                'nets': len(board1.GetNetsByName()) != len(board2.GetNetsByName())
            }
            
            # Compare metadata
            meta_diff = {
                'author': meta1.author != meta2.author,
                'description': meta1.description != meta2.description,
                'validation_status': meta1.validation_status != meta2.validation_status,
                'dependencies': meta1.dependencies != meta2.dependencies
            }
            
            return {
                'board_differences': board_diff,
                'metadata_differences': meta_diff
            }
            
        except Exception as e:
            logger.error(f"Failed to compare versions: {str(e)}")
            return {'error': str(e)}
    
    def rollback_version(self, version: str) -> bool:
        """Rollback to a previous version.
        
        Args:
            version: Version to rollback to
            
        Returns:
            bool: True if rollback was successful
        """
        try:
            version_data = self.get_version(version)
            if not version_data:
                return False
            
            board, _ = version_data
            
            # Save current board
            current_path = self.template_dir / "board.kicad_pcb"
            pcbnew.SaveBoard(str(current_path), board)
            
            logger.info(f"Rolled back to version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback version: {str(e)}")
            return False
    
    def validate_version(self, version: str) -> Dict:
        """Validate a specific version.
        
        Args:
            version: Version to validate
            
        Returns:
            Dictionary of validation results
        """
        try:
            version_data = self.get_version(version)
            if not version_data:
                return {'error': 'Version not found'}
            
            board, _ = version_data
            
            # Run DRC
            drc_results = self._run_drc(board)
            
            # Run ERC
            erc_results = self._run_erc(board)
            
            # Update validation status in history
            self.history[version]['validation_status'] = {
                'drc': not bool(drc_results.get('errors')),
                'erc': not bool(erc_results.get('errors'))
            }
            self._save_history()
            
            return {
                'drc': drc_results,
                'erc': erc_results
            }
            
        except Exception as e:
            logger.error(f"Failed to validate version: {str(e)}")
            return {'error': str(e)}
    
    def _run_drc(self, board: pcbnew.BOARD) -> Dict:
        """Run Design Rule Check on board.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of DRC results
        """
        try:
            # Get DRC errors
            drc_errors = []
            for item in board.GetDRCErrors():
                drc_errors.append({
                    'type': item.GetErrorCode(),
                    'message': item.GetErrorMessage(),
                    'position': (item.GetPosition().x, item.GetPosition().y)
                })
            
            return {
                'errors': drc_errors,
                'passed': len(drc_errors) == 0
            }
            
        except Exception as e:
            logger.error(f"DRC check failed: {str(e)}")
            return {'error': str(e)}
    
    def _run_erc(self, board: pcbnew.BOARD) -> Dict:
        """Run Electrical Rule Check on board.
        
        Args:
            board: KiCad board object
            
        Returns:
            Dictionary of ERC results
        """
        try:
            # Get ERC errors
            erc_errors = []
            for item in board.GetERCErrors():
                erc_errors.append({
                    'type': item.GetErrorCode(),
                    'message': item.GetErrorMessage(),
                    'position': (item.GetPosition().x, item.GetPosition().y)
                })
            
            return {
                'errors': erc_errors,
                'passed': len(erc_errors) == 0
            }
            
        except Exception as e:
            logger.error(f"ERC check failed: {str(e)}")
            return {'error': str(e)} 
