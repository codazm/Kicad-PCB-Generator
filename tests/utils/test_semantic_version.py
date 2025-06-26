"""Tests for semantic version utility."""

import unittest
from kicad_pcb_generator.utils.semantic_version import SemanticVersion

class TestSemanticVersion(unittest.TestCase):
    """Test cases for semantic version utility."""
    
    def test_valid_versions(self):
        """Test valid version strings."""
        valid_versions = [
            "1.0.0",
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-rc.1",
            "1.0.0+20130313144700",
            "1.0.0-alpha+20130313144700",
            "1.0.0-beta+exp.sha.5114f85",
            "1.0.0-rc.1+exp.sha.5114f85"
        ]
        
        for version in valid_versions:
            with self.subTest(version=version):
                semver = SemanticVersion(version)
                self.assertEqual(str(semver), version)
    
    def test_invalid_versions(self):
        """Test invalid version strings."""
        invalid_versions = [
            "1",
            "1.0",
            "1.0.0.0",
            "1.0.0-alpha.",
            "1.0.0-alpha..1",
            "1.0.0-alpha.1.",
            "1.0.0+",
            "1.0.0+.",
            "1.0.0+.1",
            "1.0.0-alpha+",
            "1.0.0-alpha+."
        ]
        
        for version in invalid_versions:
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    SemanticVersion(version)
    
    def test_version_comparison(self):
        """Test version comparison."""
        versions = [
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.beta",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0",
            "1.0.1",
            "1.1.0",
            "2.0.0"
        ]
        
        # Convert to SemanticVersion objects
        semvers = [SemanticVersion(v) for v in versions]
        
        # Test each pair of versions
        for i, v1 in enumerate(semvers):
            for j, v2 in enumerate(semvers):
                with self.subTest(v1=str(v1), v2=str(v2)):
                    if i < j:
                        self.assertLess(v1, v2)
                        self.assertLessEqual(v1, v2)
                        self.assertGreater(v2, v1)
                        self.assertGreaterEqual(v2, v1)
                    elif i > j:
                        self.assertGreater(v1, v2)
                        self.assertGreaterEqual(v1, v2)
                        self.assertLess(v2, v1)
                        self.assertLessEqual(v2, v1)
                    else:
                        self.assertEqual(v1, v2)
                        self.assertLessEqual(v1, v2)
                        self.assertGreaterEqual(v1, v2)
    
    def test_version_increment(self):
        """Test version increment methods."""
        v = SemanticVersion("1.2.3")
        
        # Test major increment
        self.assertEqual(str(v.increment_major()), "2.0.0")
        
        # Test minor increment
        self.assertEqual(str(v.increment_minor()), "1.3.0")
        
        # Test patch increment
        self.assertEqual(str(v.increment_patch()), "1.2.4")
    
    def test_prerelease(self):
        """Test prerelease functionality."""
        v = SemanticVersion("1.0.0")
        
        # Test adding prerelease
        alpha = v.with_prerelease("alpha.1")
        self.assertEqual(str(alpha), "1.0.0-alpha.1")
        
        # Test adding build metadata
        build = alpha.with_build("20130313144700")
        self.assertEqual(str(build), "1.0.0-alpha.1+20130313144700")
        
        # Test prerelease type
        self.assertEqual(alpha.get_prerelease_type(), "alpha")
        self.assertEqual(alpha.get_prerelease_number(), 1)
    
    def test_stable_version(self):
        """Test stable version checks."""
        stable = SemanticVersion("1.0.0")
        prerelease = SemanticVersion("1.0.0-alpha")
        
        self.assertTrue(stable.is_stable())
        self.assertFalse(stable.is_prerelease())
        self.assertFalse(prerelease.is_stable())
        self.assertTrue(prerelease.is_prerelease())
    
    def test_next_version(self):
        """Test getting next version."""
        v = SemanticVersion("1.2.3")
        
        # Test major bump
        self.assertEqual(str(v.get_next_version("major")), "2.0.0")
        
        # Test minor bump
        self.assertEqual(str(v.get_next_version("minor")), "1.3.0")
        
        # Test patch bump
        self.assertEqual(str(v.get_next_version("patch")), "1.2.4")
        
        # Test invalid bump type
        with self.assertRaises(ValueError):
            v.get_next_version("invalid")
    
    def test_hash(self):
        """Test version hashing."""
        v1 = SemanticVersion("1.0.0")
        v2 = SemanticVersion("1.0.0")
        v3 = SemanticVersion("1.0.1")
        
        self.assertEqual(hash(v1), hash(v2))
        self.assertNotEqual(hash(v1), hash(v3))

if __name__ == "__main__":
    unittest.main() 