"""Advanced template versioning system for KiCad 9.

This module provides functionality for tracking template versions, managing version history,
and integrating with KiCad 9's native versioning capabilities.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import json
import hashlib
import logging
import shutil
import pcbnew

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from .base import TemplateBase
from ..compatibility.kicad9 import KiCad9Compatibility
from ..board.layer_manager import LayerManager, LayerProperties

class ChangeType(Enum):
    """Types of changes that can be made to a template."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    RULE_CHANGED = "rule_changed"
    COMPONENT_CHANGED = "component_changed"
    LAYER_CHANGED = "layer_changed"
    ZONE_CHANGED = "zone_changed"
    VARIANT_CHANGED = "variant_changed"
    BOARD_CHANGED = "board_changed"  # New type for KiCad board changes

@dataclass
class TemplateChange:
    """Represents a change made to a template."""
    timestamp: datetime
    change_type: ChangeType
    user: str
    description: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    kicad_changes: Optional[Dict[str, Any]] = None  # Track KiCad-specific changes

@dataclass
class TemplateVersion:
    """Represents a version of a template."""
    version: str
    timestamp: datetime
    changes: List[TemplateChange]
    hash: str
    metadata: Dict[str, Any]
    kicad_version: Optional[str] = None
    kicad_board_hash: Optional[str] = None  # Hash of KiCad board state
    deprecated: bool = False
    deprecated_at: Optional[datetime] = None
    deprecated_by: Optional[str] = None

class TemplateVersionManager(BaseManager[TemplateVersion]):
    """Manages template versions and history.
    
    This class provides functionality for tracking template versions, managing version history,
    and integrating with KiCad 9's native versioning capabilities.
    Now inherits from BaseManager for standardized CRUD operations.
    """
    
    def __init__(self, storage_path: str, logger: Optional[logging.Logger] = None):
        """Initialize version manager.
        
        Args:
            storage_path: Path to store version history
            logger: Optional logger instance
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.storage_path = Path(storage_path)
        self.kicad = KiCad9Compatibility()
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing versions
        self._load_versions()
    
    def _load_versions(self) -> None:
        """Load version history from storage."""
        try:
            version_file = self.storage_path / "versions.json"
            if version_file.exists():
                with open(version_file, 'r') as f:
                    data = json.load(f)
                    for template_id, versions in data.items():
                        for v in versions:
                            template_version = TemplateVersion(
                                version=v['version'],
                                timestamp=datetime.fromisoformat(v['timestamp']),
                                changes=[
                                    TemplateChange(
                                        timestamp=datetime.fromisoformat(c['timestamp']),
                                        change_type=ChangeType(c['change_type']),
                                        user=c['user'],
                                        description=c['description'],
                                        old_value=c.get('old_value'),
                                        new_value=c.get('new_value'),
                                        metadata=c.get('metadata'),
                                        kicad_changes=c.get('kicad_changes')
                                    )
                                    for c in v['changes']
                                ],
                                hash=v['hash'],
                                metadata=v['metadata'],
                                kicad_version=v.get('kicad_version'),
                                kicad_board_hash=v.get('kicad_board_hash'),
                                deprecated=v.get('deprecated', False),
                                deprecated_at=datetime.fromisoformat(v['deprecated_at']) if v.get('deprecated_at') else None,
                                deprecated_by=v.get('deprecated_by')
                            )
                            # Use BaseManager's create method with composite key
                            key = f"{template_id}:{v['version']}"
                            self.create(key, template_version)
        except Exception as e:
            self.logger.error(f"Failed to load versions: {e}")
    
    def _save_versions(self) -> None:
        """Save version history to storage."""
        try:
            # Group versions by template_id
            data = {}
            for key, version in self._items.items():
                template_id, version_str = key.split(':', 1)
                if template_id not in data:
                    data[template_id] = []
                
                data[template_id].append({
                    'version': version.version,
                    'timestamp': version.timestamp.isoformat(),
                    'changes': [
                        {
                            'timestamp': c.timestamp.isoformat(),
                            'change_type': c.change_type.value,
                            'user': c.user,
                            'description': c.description,
                            'old_value': c.old_value,
                            'new_value': c.new_value,
                            'metadata': c.metadata,
                            'kicad_changes': c.kicad_changes
                        }
                        for c in version.changes
                    ],
                    'hash': version.hash,
                    'metadata': version.metadata,
                    'kicad_version': version.kicad_version,
                    'kicad_board_hash': version.kicad_board_hash,
                    'deprecated': version.deprecated,
                    'deprecated_at': version.deprecated_at.isoformat() if version.deprecated_at else None,
                    'deprecated_by': version.deprecated_by
                })
            
            version_file = self.storage_path / "versions.json"
            with open(version_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save versions: {e}")
    
    def _calculate_hash(self, template: TemplateBase) -> str:
        """Calculate hash for template data.
        
        Args:
            template: Template to hash
            
        Returns:
            Hash string
        """
        data = {
            'name': template.name,
            'description': template.description,
            'version': template.version,
            'layer_stack': template.layer_stack.__dict__ if template.layer_stack else None,
            'zones': {name: zone.__dict__ for name, zone in template.zones.items()},
            'variants': {name: variant.__dict__ for name, variant in template.variants.items()},
            'rules': template.rules
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _calculate_board_hash(self, board: pcbnew.BOARD) -> str:
        """Calculate hash for KiCad board state.
        
        Args:
            board: KiCad board object
            
        Returns:
            Hash string
        """
        try:
            # Get board data
            board_data = {
                'layers': [board.GetLayerName(i) for i in range(board.GetCopperLayerCount())],
                'nets': {net.GetNetname(): [pad.GetName() for pad in net.GetPads()] 
                        for net in board.GetNetsByName().values()},
                'footprints': [fp.GetReference() for fp in board.GetFootprints()],
                'tracks': [track.GetNetname() for track in board.GetTracks()],
                'zones': [zone.GetNetname() for zone in board.Zones()],
                'rules': {
                    'clearance': board.GetDesignSettings().GetMinClearance(),
                    'track_width': board.GetDesignSettings().GetTrackWidth(),
                    'via_diameter': board.GetDesignSettings().GetViasDimensions(),
                    'via_drill': board.GetDesignSettings().GetViasDrill()
                }
            }
            
            # Calculate hash
            data_str = json.dumps(board_data, sort_keys=True)
            return hashlib.sha256(data_str.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Failed to calculate board hash: {e}")
            return ""
    
    def _get_kicad_changes(self, old_board: Optional[pcbnew.BOARD], new_board: pcbnew.BOARD) -> Dict[str, Any]:
        """Get changes between two KiCad board states.
        
        Args:
            old_board: Previous board state
            new_board: New board state
            
        Returns:
            Dictionary of changes
        """
        changes = {}
        
        try:
            # Compare layers
            if old_board:
                old_layers = set(old_board.GetLayerName(i) for i in range(old_board.GetCopperLayerCount()))
                new_layers = set(new_board.GetLayerName(i) for i in range(new_board.GetCopperLayerCount()))
                if old_layers != new_layers:
                    changes['layers'] = {
                        'added': list(new_layers - old_layers),
                        'removed': list(old_layers - new_layers)
                    }
            
            # Compare nets
            if old_board:
                old_nets = {net.GetNetname(): set(pad.GetName() for pad in net.GetPads())
                           for net in old_board.GetNetsByName().values()}
                new_nets = {net.GetNetname(): set(pad.GetName() for pad in net.GetPads())
                           for net in new_board.GetNetsByName().values()}
                
                net_changes = {}
                for net_name in set(old_nets.keys()) | set(new_nets.keys()):
                    if net_name not in old_nets:
                        net_changes[net_name] = {'added': list(new_nets[net_name])}
                    elif net_name not in new_nets:
                        net_changes[net_name] = {'removed': list(old_nets[net_name])}
                    else:
                        added = new_nets[net_name] - old_nets[net_name]
                        removed = old_nets[net_name] - new_nets[net_name]
                        if added or removed:
                            net_changes[net_name] = {
                                'added': list(added),
                                'removed': list(removed)
                            }
                
                if net_changes:
                    changes['nets'] = net_changes
            
            # Compare footprints
            if old_board:
                old_footprints = {fp.GetReference() for fp in old_board.GetFootprints()}
                new_footprints = {fp.GetReference() for fp in new_board.GetFootprints()}
                if old_footprints != new_footprints:
                    changes['footprints'] = {
                        'added': list(new_footprints - old_footprints),
                        'removed': list(old_footprints - new_footprints)
                    }
            
            # Compare tracks
            if old_board:
                old_tracks = {track.GetNetname() for track in old_board.GetTracks()}
                new_tracks = {track.GetNetname() for track in new_board.GetTracks()}
                if old_tracks != new_tracks:
                    changes['tracks'] = {
                        'added': list(new_tracks - old_tracks),
                        'removed': list(old_tracks - new_tracks)
                    }
            
            # Compare zones
            if old_board:
                old_zones = {zone.GetNetname() for zone in old_board.Zones()}
                new_zones = {zone.GetNetname() for zone in new_board.Zones()}
                if old_zones != new_zones:
                    changes['zones'] = {
                        'added': list(new_zones - old_zones),
                        'removed': list(old_zones - new_zones)
                    }
            
            # Compare design rules
            if old_board:
                old_rules = {
                    'clearance': old_board.GetDesignSettings().GetMinClearance(),
                    'track_width': old_board.GetDesignSettings().GetTrackWidth(),
                    'via_diameter': old_board.GetDesignSettings().GetViasDimensions(),
                    'via_drill': old_board.GetDesignSettings().GetViasDrill()
                }
                new_rules = {
                    'clearance': new_board.GetDesignSettings().GetMinClearance(),
                    'track_width': new_board.GetDesignSettings().GetTrackWidth(),
                    'via_diameter': new_board.GetDesignSettings().GetViasDimensions(),
                    'via_drill': new_board.GetDesignSettings().GetViasDrill()
                }
                
                rule_changes = {}
                for rule_name in set(old_rules.keys()) | set(new_rules.keys()):
                    if rule_name not in old_rules:
                        rule_changes[rule_name] = {'added': new_rules[rule_name]}
                    elif rule_name not in new_rules:
                        rule_changes[rule_name] = {'removed': old_rules[rule_name]}
                    elif old_rules[rule_name] != new_rules[rule_name]:
                        rule_changes[rule_name] = {
                            'old': old_rules[rule_name],
                            'new': new_rules[rule_name]
                        }
                
                if rule_changes:
                    changes['rules'] = rule_changes
            
        except Exception as e:
            self.logger.error(f"Failed to get KiCad changes: {e}")
        
        return changes
    
    def add_version(self,
                   template_id: str,
                   template: TemplateBase,
                   change: TemplateChange,
                   board: Optional[pcbnew.BOARD] = None) -> None:
        """Add a new version of a template.
        
        Args:
            template_id: Template ID
            template: Template object
            change: Change that created this version
            board: Optional KiCad board object
        """
        try:
            # Calculate template hash
            template_hash = self._calculate_hash(template)
            
            # Calculate board hash if provided
            board_hash = None
            kicad_version = None
            if board:
                board_hash = self._calculate_board_hash(board)
                kicad_version = self.kicad.get_version()
            
            # Create version object
            version = TemplateVersion(
                version=template.version,
                timestamp=datetime.now(),
                changes=[change],
                hash=template_hash,
                metadata=template.metadata if hasattr(template, 'metadata') else {},
                kicad_version=kicad_version,
                kicad_board_hash=board_hash
            )
            
            # Use BaseManager's create method with composite key
            key = f"{template_id}:{template.version}"
            result = self.create(key, version)
            
            if result.success:
                self._save_versions()
                self.logger.info(f"Added version {template.version} for template {template_id}")
            else:
                self.logger.error(f"Failed to add version: {result.message}")
                
        except Exception as e:
            self.logger.error(f"Error adding version: {e}")
    
    def get_version(self, template_id: str, version: str) -> Optional[TemplateVersion]:
        """Get a specific version of a template.
        
        Args:
            template_id: Template ID
            version: Version to get
            
        Returns:
            TemplateVersion if found, None otherwise
        """
        key = f"{template_id}:{version}"
        result = self.read(key)
        return result.data if result.success else None
    
    def get_latest_version(self, template_id: str) -> Optional[TemplateVersion]:
        """Get the latest version of a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            Latest TemplateVersion if found, None otherwise
        """
        # Get all versions for this template
        versions = []
        for key, version_obj in self._items.items():
            if key.startswith(f"{template_id}:"):
                versions.append(version_obj)
        
        if not versions:
            return None
        
        # Return the latest version (highest timestamp)
        return max(versions, key=lambda v: v.timestamp)
    
    def get_version_history(self, template_id: str) -> List[TemplateVersion]:
        """Get version history for a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            List of TemplateVersion objects
        """
        versions = []
        for key, version_obj in self._items.items():
            if key.startswith(f"{template_id}:"):
                versions.append(version_obj)
        
        # Sort by timestamp
        return sorted(versions, key=lambda v: v.timestamp)
    
    def compare_versions(self,
                        template_id: str,
                        version1: str,
                        version2: str) -> List[TemplateChange]:
        """Compare two versions of a template.
        
        Args:
            template_id: Template ID
            version1: First version
            version2: Second version
            
        Returns:
            List of changes between versions
        """
        v1 = self.get_version(template_id, version1)
        v2 = self.get_version(template_id, version2)
        
        if not v1 or not v2:
            return []
        
        # Get all changes from both versions
        changes = []
        changes.extend(v1.changes)
        changes.extend(v2.changes)
        
        # Remove duplicates and sort by timestamp
        unique_changes = {}
        for change in changes:
            change_key = f"{change.timestamp}:{change.change_type}:{change.description}"
            if change_key not in unique_changes:
                unique_changes[change_key] = change
        
        return sorted(unique_changes.values(), key=lambda c: c.timestamp)
    
    def rollback_to_version(self,
                          template_id: str,
                          version: str,
                          user: str) -> Optional[TemplateBase]:
        """Rollback to a specific version.
        
        Args:
            template_id: Template ID
            version: Version to rollback to
            user: User performing the rollback
            
        Returns:
            TemplateBase if successful, None otherwise
        """
        try:
            target_version = self.get_version(template_id, version)
            if not target_version:
                return None
            
            # Create rollback change
            rollback_change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user=user,
                description=f"Rollback to version {version}",
                old_value=None,
                new_value=target_version.hash,
                metadata={'rollback': True, 'target_version': version}
            )
            
            # Add rollback as new version
            # Note: This would require the actual template object to recreate
            # For now, we'll just log the rollback
            self.logger.info(f"Rollback to version {version} requested by {user}")
            
            return None  # Would need template recreation logic
            
        except Exception as e:
            self.logger.error(f"Error rolling back to version: {e}")
            return None
    
    def deprecate_version(self,
                         template_id: str,
                         version: str,
                         user: str,
                         reason: str) -> bool:
        """Deprecate a version.
        
        Args:
            template_id: Template ID
            version: Version to deprecate
            user: User deprecating the version
            reason: Reason for deprecation
            
        Returns:
            True if successful
        """
        try:
            key = f"{template_id}:{version}"
            result = self.read(key)
            if not result.success:
                return False
            
            version_obj = result.data
            version_obj.deprecated = True
            version_obj.deprecated_at = datetime.now()
            version_obj.deprecated_by = user
            
            # Add deprecation change
            deprecation_change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user=user,
                description=f"Version deprecated: {reason}",
                old_value=False,
                new_value=True,
                metadata={'deprecated': True, 'reason': reason}
            )
            version_obj.changes.append(deprecation_change)
            
            # Update using BaseManager
            update_result = self.update(key, version_obj)
            if update_result.success:
                self._save_versions()
                self.logger.info(f"Deprecated version {version} for template {template_id}")
                return True
            else:
                self.logger.error(f"Failed to deprecate version: {update_result.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deprecating version: {e}")
            return False
    
    def get_deprecated_versions(self, template_id: str) -> List[TemplateVersion]:
        """Get deprecated versions of a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            List of deprecated TemplateVersion objects
        """
        deprecated = []
        for key, version_obj in self._items.items():
            if key.startswith(f"{template_id}:") and version_obj.deprecated:
                deprecated.append(version_obj)
        
        return sorted(deprecated, key=lambda v: v.timestamp)
    
    def get_compatible_versions(self,
                              template_id: str,
                              kicad_version: Optional[str] = None) -> List[TemplateVersion]:
        """Get versions compatible with a specific KiCad version.
        
        Args:
            template_id: Template ID
            kicad_version: KiCad version to check compatibility with
            
        Returns:
            List of compatible TemplateVersion objects
        """
        compatible = []
        for key, version_obj in self._items.items():
            if key.startswith(f"{template_id}:"):
                if kicad_version is None or version_obj.kicad_version == kicad_version:
                    compatible.append(version_obj)
        
        return sorted(compatible, key=lambda v: v.timestamp)
    
    def _validate_data(self, data: TemplateVersion) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.version:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Template version is required",
                    errors=["Template version cannot be empty"]
                )
            
            if not data.timestamp:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Template version timestamp is required",
                    errors=["Template version timestamp cannot be empty"]
                )
            
            if not data.changes:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Template version must have at least one change",
                    errors=["Template version changes cannot be empty"]
                )
            
            if not data.hash:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Template version hash is required",
                    errors=["Template version hash cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Template version validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Template version validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a template version.
        
        Args:
            key: Template version key to clean up
        """
        # Placeholder for future cleanup (e.g., temp files). Currently a no-op.
        self.logger.debug("TemplateVersionManager cleanup hook for key '%s'", key)
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache and save to disk
        super()._clear_cache()
        self._save_versions() 