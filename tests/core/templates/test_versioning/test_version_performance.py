"""Tests for version performance scenarios."""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import time
import cProfile
import pstats
import io

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)

class TestVersionPerformance(unittest.TestCase):
    """Test version performance scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = "test_templates"
        self.manager = TemplateVersionManager(self.test_dir)
        
        # Create test template
        self.template = Mock()
        self.template.name = "Test Template"
        self.template.description = "Test template description"
        self.template.metadata = {
            "name": "Test Template",
            "description": "Test template description",
            "version": "1.0.0"
        }
    
    def test_large_version_history_performance(self):
        """Test performance with large version history."""
        # Create many versions
        start_time = time.time()
        
        for i in range(1000):  # Create 1000 versions
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0"
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            self.manager.add_version("test_template", template, change)
        
        creation_time = time.time() - start_time
        self.assertLess(creation_time, 10.0)  # Should complete within 10 seconds
        
        # Test history retrieval performance
        start_time = time.time()
        history = self.manager.get_version_history("test_template")
        retrieval_time = time.time() - start_time
        self.assertLess(retrieval_time, 1.0)  # Should complete within 1 second
        
        self.assertEqual(len(history), 1000)
    
    def test_version_search_performance(self):
        """Test performance of version search operations."""
        # Create versions with searchable content
        for i in range(100):
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0",
                "tags": [f"tag{j}" for j in range(5)],
                "description": f"Description for version {i+1}"
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            self.manager.add_version("test_template", template, change)
        
        # Test search performance
        start_time = time.time()
        results = self.manager.search_versions(
            "test_template",
            query="Description",
            tags=["tag1", "tag2"]
        )
        search_time = time.time() - start_time
        self.assertLess(search_time, 0.5)  # Should complete within 0.5 seconds
        
        self.assertGreater(len(results), 0)
    
    def test_version_compression_performance(self):
        """Test performance of version compression."""
        # Create versions to compress
        for i in range(500):
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0",
                "data": {"key": "value" * 100}  # Large data
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            self.manager.add_version("test_template", template, change)
        
        # Test compression performance
        start_time = time.time()
        compressed = self.manager.compress_version_history("test_template", max_versions=100)
        compression_time = time.time() - start_time
        self.assertLess(compression_time, 5.0)  # Should complete within 5 seconds
        
        self.assertEqual(len(compressed), 100)
    
    def test_version_validation_performance(self):
        """Test performance of version validation."""
        # Create versions to validate
        for i in range(200):
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0",
                "validation_rules": [f"rule{j}" for j in range(10)]
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            self.manager.add_version("test_template", template, change)
        
        # Test validation performance
        start_time = time.time()
        results = self.manager.validate_versions("test_template", [f"v{i+1}" for i in range(200)])
        validation_time = time.time() - start_time
        self.assertLess(validation_time, 5.0)  # Should complete within 5 seconds
        
        self.assertEqual(len(results), 200)
    
    def test_memory_usage(self):
        """Test memory usage with large version sets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large version set
        for i in range(1000):
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0",
                "data": {"key": "value" * 1000}  # Large data
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            self.manager.add_version("test_template", template, change)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 1GB)
        self.assertLess(memory_increase, 1024 * 1024 * 1024)
    
    def test_concurrent_operations_performance(self):
        """Test performance of concurrent operations."""
        import threading
        
        def create_versions(start, count):
            for i in range(start, start + count):
                template = Mock()
                template.metadata = {
                    "name": f"Test Template v{i+1}",
                    "version": f"{i+1}.0.0"
                }
                
                change = TemplateChange(
                    timestamp=datetime.now(),
                    change_type=ChangeType.MODIFIED,
                    user=f"user{i%5}",
                    description=f"Version {i+1}"
                )
                
                self.manager.add_version("test_template", template, change)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=create_versions,
                args=(i * 100, 100)
            )
            threads.append(thread)
        
        # Start timing
        start_time = time.time()
        
        # Start threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check performance
        total_time = time.time() - start_time
        self.assertLess(total_time, 15.0)  # Should complete within 15 seconds
        
        # Verify results
        history = self.manager.get_version_history("test_template")
        self.assertEqual(len(history), 500)

if __name__ == "__main__":
    unittest.main() 