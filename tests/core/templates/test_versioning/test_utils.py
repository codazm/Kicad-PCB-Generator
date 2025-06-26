"""Test utilities for versioning tests."""

import os
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from unittest.mock import Mock, patch, MagicMock
import wx
import threading
import queue
import time

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)

class VersionTestUtils:
    """Utilities for versioning tests."""
    
    @staticmethod
    def setup_test_environment(test_dir: str) -> None:
        """Set up test environment.
        
        Args:
            test_dir: Directory for test data
        """
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        os.makedirs(test_dir)
    
    @staticmethod
    def cleanup_test_environment(test_dir: str) -> None:
        """Clean up test environment.
        
        Args:
            test_dir: Directory for test data
        """
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
    
    @staticmethod
    def create_mock_template(**kwargs) -> Mock:
        """Create a mock template with specified attributes.
        
        Args:
            **kwargs: Template attributes
            
        Returns:
            Mock template object
        """
        template = Mock()
        for key, value in kwargs.items():
            setattr(template, key, value)
        return template
    
    @staticmethod
    def create_mock_change(**kwargs) -> TemplateChange:
        """Create a mock change with specified attributes.
        
        Args:
            **kwargs: Change attributes
            
        Returns:
            TemplateChange object
        """
        return TemplateChange(
            timestamp=kwargs.get('timestamp', datetime.now()),
            change_type=kwargs.get('change_type', ChangeType.CREATED),
            user=kwargs.get('user', 'test_user'),
            description=kwargs.get('description', 'Test change')
        )
    
    @staticmethod
    def mock_version_manager(methods: Dict[str, Callable]) -> Mock:
        """Create a mock version manager with specified methods.
        
        Args:
            methods: Dictionary of method names and their implementations
            
        Returns:
            Mock version manager
        """
        manager = Mock(spec=TemplateVersionManager)
        for method_name, implementation in methods.items():
            setattr(manager, method_name, implementation)
        return manager
    
    @staticmethod
    def create_test_file(path: str, content: Dict[str, Any]) -> None:
        """Create a test file with specified content.
        
        Args:
            path: File path
            content: File content
        """
        with open(path, 'w') as f:
            json.dump(content, f, indent=2)
    
    @staticmethod
    def read_test_file(path: str) -> Dict[str, Any]:
        """Read a test file.
        
        Args:
            path: File path
            
        Returns:
            File content
        """
        with open(path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def assert_version_equal(version1: TemplateVersion, version2: TemplateVersion) -> None:
        """Assert that two versions are equal.
        
        Args:
            version1: First version
            version2: Second version
        """
        assert version1.version_id == version2.version_id
        assert version1.metadata == version2.metadata
        assert version1.change.timestamp == version2.change.timestamp
        assert version1.change.change_type == version2.change.change_type
        assert version1.change.user == version2.change.user
        assert version1.change.description == version2.change.description
    
    @staticmethod
    def assert_validation_results_equal(results1: List[Dict[str, Any]], results2: List[Dict[str, Any]]) -> None:
        """Assert that two validation result lists are equal.
        
        Args:
            results1: First validation results
            results2: Second validation results
        """
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1['severity'] == r2['severity']
            assert r1['message'] == r2['message']
            assert r1['details'] == r2['details']
    
    @staticmethod
    def create_test_scenario(scenario_type: str, **kwargs) -> Any:
        """Create a test scenario.
        
        Args:
            scenario_type: Type of scenario to create
            **kwargs: Scenario parameters
            
        Returns:
            Created scenario
        """
        if scenario_type == 'conflict':
            return VersionTestUtils._create_conflict_scenario(**kwargs)
        elif scenario_type == 'migration':
            return VersionTestUtils._create_migration_scenario(**kwargs)
        elif scenario_type == 'rollback':
            return VersionTestUtils._create_rollback_scenario(**kwargs)
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
    
    @staticmethod
    def _create_conflict_scenario(**kwargs) -> Dict[str, Any]:
        """Create a conflict scenario.
        
        Args:
            **kwargs: Scenario parameters
            
        Returns:
            Conflict scenario
        """
        return {
            'base_version': kwargs.get('base_version', '1.0.0'),
            'conflicting_changes': [
                {
                    'user': 'user1',
                    'data': {'key': 'value1'}
                },
                {
                    'user': 'user2',
                    'data': {'key': 'value2'}
                }
            ]
        }
    
    @staticmethod
    def _create_migration_scenario(**kwargs) -> Dict[str, Any]:
        """Create a migration scenario.
        
        Args:
            **kwargs: Scenario parameters
            
        Returns:
            Migration scenario
        """
        return {
            'start_format': kwargs.get('start_format', '0.9'),
            'target_format': kwargs.get('target_format', '1.0'),
            'migration_steps': [
                {
                    'version': '1.0.0',
                    'changes': ['format_update', 'schema_update']
                }
            ]
        }
    
    @staticmethod
    def _create_rollback_scenario(**kwargs) -> Dict[str, Any]:
        """Create a rollback scenario.
        
        Args:
            **kwargs: Scenario parameters
            
        Returns:
            Rollback scenario
        """
        return {
            'versions': [
                {
                    'version': '1.0.0',
                    'data': {'key': 'value1'}
                },
                {
                    'version': '1.0.1',
                    'data': {'key': 'value2'}
                },
                {
                    'version': '1.0.2',
                    'data': {'key': 'value3'}
                }
            ],
            'rollback_target': kwargs.get('rollback_target', '1.0.0')
        }
    
    @staticmethod
    def mock_file_operations() -> None:
        """Mock file operations for testing."""
        def mock_open(*args, **kwargs):
            return Mock()
        
        def mock_makedirs(*args, **kwargs):
            pass
        
        def mock_rmtree(*args, **kwargs):
            pass
        
        patch('builtins.open', mock_open).start()
        patch('os.makedirs', mock_makedirs).start()
        patch('shutil.rmtree', mock_rmtree).start()
    
    @staticmethod
    def create_test_data_generator() -> Callable[[str], Dict[str, Any]]:
        """Create a test data generator.
        
        Returns:
            Function that generates test data
        """
        def generate_data(data_type: str) -> Dict[str, Any]:
            """Generate test data of specified type.
            
            Args:
                data_type: Type of data to generate
                
            Returns:
                Generated test data
            """
            if data_type == 'template':
                return {
                    'name': 'Test Template',
                    'version': '1.0.0',
                    'data': {'key': 'value'}
                }
            elif data_type == 'validation':
                return {
                    'is_valid': True,
                    'results': [
                        {
                            'severity': 'info',
                            'message': 'Test validation',
                            'details': 'Test details'
                        }
                    ]
                }
            else:
                raise ValueError(f"Unknown data type: {data_type}")
        
        return generate_data
    
    @staticmethod
    def create_mock_wx_app() -> wx.App:
        """Create a mock wx application.
        
        Returns:
            Mock wx application
        """
        app = wx.App()
        return app
    
    @staticmethod
    def create_mock_wx_dialog(parent: Optional[wx.Window] = None) -> wx.Dialog:
        """Create a mock wx dialog.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx dialog
        """
        dialog = wx.Dialog(parent or wx.Frame(None))
        return dialog
    
    @staticmethod
    def create_mock_wx_panel(parent: Optional[wx.Window] = None) -> wx.Panel:
        """Create a mock wx panel.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx panel
        """
        panel = wx.Panel(parent or wx.Frame(None))
        return panel
    
    @staticmethod
    def create_mock_wx_list_ctrl(parent: Optional[wx.Window] = None) -> wx.ListCtrl:
        """Create a mock wx list control.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx list control
        """
        list_ctrl = wx.ListCtrl(
            parent or wx.Frame(None),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        return list_ctrl
    
    @staticmethod
    def create_mock_wx_button(parent: Optional[wx.Window] = None) -> wx.Button:
        """Create a mock wx button.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx button
        """
        button = wx.Button(parent or wx.Frame(None), label="Test Button")
        return button
    
    @staticmethod
    def create_mock_wx_text_ctrl(parent: Optional[wx.Window] = None) -> wx.TextCtrl:
        """Create a mock wx text control.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx text control
        """
        text_ctrl = wx.TextCtrl(parent or wx.Frame(None))
        return text_ctrl
    
    @staticmethod
    def create_mock_wx_choice(parent: Optional[wx.Window] = None) -> wx.Choice:
        """Create a mock wx choice control.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx choice control
        """
        choice = wx.Choice(parent or wx.Frame(None), choices=["Option 1", "Option 2"])
        return choice
    
    @staticmethod
    def create_mock_wx_checkbox(parent: Optional[wx.Window] = None) -> wx.CheckBox:
        """Create a mock wx checkbox.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx checkbox
        """
        checkbox = wx.CheckBox(parent or wx.Frame(None), label="Test Checkbox")
        return checkbox
    
    @staticmethod
    def create_mock_wx_radio_button(parent: Optional[wx.Window] = None) -> wx.RadioButton:
        """Create a mock wx radio button.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx radio button
        """
        radio = wx.RadioButton(parent or wx.Frame(None), label="Test Radio")
        return radio
    
    @staticmethod
    def create_mock_wx_static_text(parent: Optional[wx.Window] = None) -> wx.StaticText:
        """Create a mock wx static text.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx static text
        """
        static_text = wx.StaticText(parent or wx.Frame(None), label="Test Text")
        return static_text
    
    @staticmethod
    def create_mock_wx_menu() -> wx.Menu:
        """Create a mock wx menu.
        
        Returns:
            Mock wx menu
        """
        menu = wx.Menu()
        return menu
    
    @staticmethod
    def create_mock_wx_menu_bar() -> wx.MenuBar:
        """Create a mock wx menu bar.
        
        Returns:
            Mock wx menu bar
        """
        menu_bar = wx.MenuBar()
        return menu_bar
    
    @staticmethod
    def create_mock_wx_status_bar(parent: Optional[wx.Window] = None) -> wx.StatusBar:
        """Create a mock wx status bar.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx status bar
        """
        status_bar = wx.StatusBar(parent or wx.Frame(None))
        return status_bar
    
    @staticmethod
    def create_mock_wx_tool_bar(parent: Optional[wx.Window] = None) -> wx.ToolBar:
        """Create a mock wx tool bar.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx tool bar
        """
        tool_bar = wx.ToolBar(parent or wx.Frame(None))
        return tool_bar
    
    @staticmethod
    def create_mock_wx_notebook(parent: Optional[wx.Window] = None) -> wx.Notebook:
        """Create a mock wx notebook.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx notebook
        """
        notebook = wx.Notebook(parent or wx.Frame(None))
        return notebook
    
    @staticmethod
    def create_mock_wx_splitter_window(parent: Optional[wx.Window] = None) -> wx.SplitterWindow:
        """Create a mock wx splitter window.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx splitter window
        """
        splitter = wx.SplitterWindow(parent or wx.Frame(None))
        return splitter
    
    @staticmethod
    def create_mock_wx_grid(parent: Optional[wx.Window] = None) -> wx.grid.Grid:
        """Create a mock wx grid.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx grid
        """
        grid = wx.grid.Grid(parent or wx.Frame(None))
        return grid
    
    @staticmethod
    def create_mock_wx_tree_ctrl(parent: Optional[wx.Window] = None) -> wx.TreeCtrl:
        """Create a mock wx tree control.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx tree control
        """
        tree = wx.TreeCtrl(parent or wx.Frame(None))
        return tree
    
    @staticmethod
    def create_mock_wx_html_window(parent: Optional[wx.Window] = None) -> wx.html.HtmlWindow:
        """Create a mock wx HTML window.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx HTML window
        """
        html = wx.html.HtmlWindow(parent or wx.Frame(None))
        return html
    
    @staticmethod
    def create_mock_wx_aui_manager(parent: Optional[wx.Window] = None) -> wx.aui.AuiManager:
        """Create a mock wx AUI manager.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx AUI manager
        """
        manager = wx.aui.AuiManager(parent or wx.Frame(None))
        return manager
    
    @staticmethod
    def create_mock_wx_aui_notebook(parent: Optional[wx.Window] = None) -> wx.aui.AuiNotebook:
        """Create a mock wx AUI notebook.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx AUI notebook
        """
        notebook = wx.aui.AuiNotebook(parent or wx.Frame(None))
        return notebook
    
    @staticmethod
    def create_mock_wx_aui_tool_bar(parent: Optional[wx.Window] = None) -> wx.aui.AuiToolBar:
        """Create a mock wx AUI tool bar.
        
        Args:
            parent: Parent window
            
        Returns:
            Mock wx AUI tool bar
        """
        tool_bar = wx.aui.AuiToolBar(parent or wx.Frame(None))
        return tool_bar
    
    @staticmethod
    def create_mock_wx_aui_pane_info() -> wx.aui.AuiPaneInfo:
        """Create a mock wx AUI pane info.
        
        Returns:
            Mock wx AUI pane info
        """
        pane_info = wx.aui.AuiPaneInfo()
        return pane_info
    
    @staticmethod
    def create_mock_wx_aui_dock_art() -> wx.aui.AuiDockArt:
        """Create a mock wx AUI dock art.
        
        Returns:
            Mock wx AUI dock art
        """
        dock_art = wx.aui.AuiDockArt()
        return dock_art
    
    @staticmethod
    def create_mock_wx_aui_manager_event(event_type: int) -> wx.aui.AuiManagerEvent:
        """Create a mock wx AUI manager event.
        
        Args:
            event_type: Event type
            
        Returns:
            Mock wx AUI manager event
        """
        event = wx.aui.AuiManagerEvent(event_type)
        return event
    
    @staticmethod
    def create_mock_wx_aui_notebook_event(event_type: int) -> wx.aui.AuiNotebookEvent:
        """Create a mock wx AUI notebook event.
        
        Args:
            event_type: Event type
            
        Returns:
            Mock wx AUI notebook event
        """
        event = wx.aui.AuiNotebookEvent(event_type)
        return event
    
    @staticmethod
    def create_mock_wx_aui_tool_bar_event(event_type: int) -> wx.aui.AuiToolBarEvent:
        """Create a mock wx AUI tool bar event.
        
        Args:
            event_type: Event type
            
        Returns:
            Mock wx AUI tool bar event
        """
        event = wx.aui.AuiToolBarEvent(event_type)
        return event
    
    @staticmethod
    def create_mock_wx_aui_pane_info_event(event_type: int) -> wx.aui.AuiPaneInfoEvent:
        """Create a mock wx AUI pane info event.
        
        Args:
            event_type: Event type
            
        Returns:
            Mock wx AUI pane info event
        """
        event = wx.aui.AuiPaneInfoEvent(event_type)
        return event
    
    @staticmethod
    def create_mock_wx_aui_dock_art_event(event_type: int) -> wx.aui.AuiDockArtEvent:
        """Create a mock wx AUI dock art event.
        
        Args:
            event_type: Event type
            
        Returns:
            Mock wx AUI dock art event
        """
        event = wx.aui.AuiDockArtEvent(event_type)
        return event
    
    @staticmethod
    def create_mock_wx_aui_manager_event_handler() -> Callable[[wx.aui.AuiManagerEvent], None]:
        """Create a mock wx AUI manager event handler.
        
        Returns:
            Mock wx AUI manager event handler
        """
        def handler(event: wx.aui.AuiManagerEvent) -> None:
            pass
        return handler
    
    @staticmethod
    def create_mock_wx_aui_notebook_event_handler() -> Callable[[wx.aui.AuiNotebookEvent], None]:
        """Create a mock wx AUI notebook event handler.
        
        Returns:
            Mock wx AUI notebook event handler
        """
        def handler(event: wx.aui.AuiNotebookEvent) -> None:
            pass
        return handler
    
    @staticmethod
    def create_mock_wx_aui_tool_bar_event_handler() -> Callable[[wx.aui.AuiToolBarEvent], None]:
        """Create a mock wx AUI tool bar event handler.
        
        Returns:
            Mock wx AUI tool bar event handler
        """
        def handler(event: wx.aui.AuiToolBarEvent) -> None:
            pass
        return handler
    
    @staticmethod
    def create_mock_wx_aui_pane_info_event_handler() -> Callable[[wx.aui.AuiPaneInfoEvent], None]:
        """Create a mock wx AUI pane info event handler.
        
        Returns:
            Mock wx AUI pane info event handler
        """
        def handler(event: wx.aui.AuiPaneInfoEvent) -> None:
            pass
        return handler
    
    @staticmethod
    def create_mock_wx_aui_dock_art_event_handler() -> Callable[[wx.aui.AuiDockArtEvent], None]:
        """Create a mock wx AUI dock art event handler.
        
        Returns:
            Mock wx AUI dock art event handler
        """
        def handler(event: wx.aui.AuiDockArtEvent) -> None:
            pass
        return handler 