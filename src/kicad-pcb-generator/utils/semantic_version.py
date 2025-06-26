"""Semantic version utility for version management."""

import re
from typing import List, Optional, Tuple

class SemanticVersion:
    """Semantic version implementation following semver.org specification."""
    
    def __init__(self, version: str):
        """Initialize semantic version.
        
        Args:
            version: Version string in format 'major.minor.patch[-prerelease][+build]'
            
        Raises:
            ValueError: If version string is invalid
        """
        self.version = version
        self.major, self.minor, self.patch, self.prerelease, self.build = self._parse_version(version)
    
    def _parse_version(self, version: str) -> Tuple[int, int, int, Optional[str], Optional[str]]:
        """Parse version string into components.
        
        Args:
            version: Version string to parse
            
        Returns:
            Tuple containing (major, minor, patch, prerelease, build)
            
        Raises:
            ValueError: If version string is invalid
        """
        # Basic version pattern
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        match = re.match(pattern, version)
        
        if not match:
            raise ValueError(f"Invalid version string: {version}")
        
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease = match.group(4)
        build = match.group(5)
        
        return major, minor, patch, prerelease, build
    
    def __str__(self) -> str:
        """Get string representation of version."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __eq__(self, other: object) -> bool:
        """Check if versions are equal."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )
    
    def __lt__(self, other: object) -> bool:
        """Check if this version is less than other version."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        
        # Compare major, minor, patch
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        
        # Compare prerelease
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is None:
            return False
        if other.prerelease is None:
            return True
        
        # Compare prerelease identifiers
        self_ids = self.prerelease.split('.')
        other_ids = other.prerelease.split('.')
        
        for i in range(max(len(self_ids), len(other_ids))):
            if i >= len(self_ids):
                return True
            if i >= len(other_ids):
                return False
            
            self_id = self_ids[i]
            other_id = other_ids[i]
            
            # Try to compare as numbers
            try:
                self_num = int(self_id)
                other_num = int(other_id)
                if self_num != other_num:
                    return self_num < other_num
            except ValueError:
                # Compare as strings
                if self_id != other_id:
                    return self_id < other_id
        
        return False
    
    def __le__(self, other: object) -> bool:
        """Check if this version is less than or equal to other version."""
        return self < other or self == other
    
    def __gt__(self, other: object) -> bool:
        """Check if this version is greater than other version."""
        return not (self <= other)
    
    def __ge__(self, other: object) -> bool:
        """Check if this version is greater than or equal to other version."""
        return not (self < other)
    
    def __hash__(self) -> int:
        """Get hash of version."""
        return hash(str(self))
    
    def increment_major(self) -> 'SemanticVersion':
        """Increment major version."""
        return SemanticVersion(f"{self.major + 1}.0.0")
    
    def increment_minor(self) -> 'SemanticVersion':
        """Increment minor version."""
        return SemanticVersion(f"{self.major}.{self.minor + 1}.0")
    
    def increment_patch(self) -> 'SemanticVersion':
        """Increment patch version."""
        return SemanticVersion(f"{self.major}.{self.minor}.{self.patch + 1}")
    
    def with_prerelease(self, prerelease: str) -> 'SemanticVersion':
        """Create new version with prerelease."""
        version = f"{self.major}.{self.minor}.{self.patch}-{prerelease}"
        if self.build:
            version += f"+{self.build}"
        return SemanticVersion(version)
    
    def with_build(self, build: str) -> 'SemanticVersion':
        """Create new version with build metadata."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        version += f"+{build}"
        return SemanticVersion(version)
    
    def is_stable(self) -> bool:
        """Check if version is stable (no prerelease)."""
        return self.prerelease is None
    
    def is_prerelease(self) -> bool:
        """Check if version is prerelease."""
        return self.prerelease is not None
    
    def get_next_version(self, bump_type: str = 'patch') -> 'SemanticVersion':
        """Get next version based on bump type.
        
        Args:
            bump_type: Type of version bump ('major', 'minor', or 'patch')
            
        Returns:
            Next version
            
        Raises:
            ValueError: If bump_type is invalid
        """
        if bump_type == 'major':
            return self.increment_major()
        elif bump_type == 'minor':
            return self.increment_minor()
        elif bump_type == 'patch':
            return self.increment_patch()
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")
    
    def get_prerelease_type(self) -> Optional[str]:
        """Get prerelease type if version is prerelease.
        
        Returns:
            Prerelease type (e.g., 'alpha', 'beta', 'rc') or None
        """
        if not self.prerelease:
            return None
        
        prerelease_types = ['alpha', 'beta', 'rc']
        for type_ in prerelease_types:
            if self.prerelease.startswith(type_):
                return type_
        return None
    
    def get_prerelease_number(self) -> Optional[int]:
        """Get prerelease number if version is prerelease.
        
        Returns:
            Prerelease number or None
        """
        if not self.prerelease:
            return None
        
        match = re.search(r'\d+$', self.prerelease)
        if match:
            return int(match.group())
        return None 
