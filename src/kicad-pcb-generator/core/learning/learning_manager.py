"""Learning system manager for handling tutorials, learning paths, and progress tracking."""

from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from pathlib import Path
import json
import logging
from datetime import datetime
from dataclasses import dataclass

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus

if TYPE_CHECKING:
    from ..base.results.analysis_result import AnalysisResult

@dataclass
class LearningItem:
    """Represents a learning item (tutorial, learning path, or progress)."""
    id: str
    type: str  # "tutorial", "learning_path", "progress"
    title: str
    description: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class LearningManager(BaseManager[LearningItem]):
    """Manages the learning system including tutorials, learning paths, and progress tracking."""
    
    def __init__(self, storage_path: Union[str, Path], logger: Optional[logging.Logger] = None):
        """Initialize the learning manager.
        
        Args:
            storage_path: Path to store learning data
            logger: Optional logger instance
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.storage_path = Path(storage_path)
        
        # Create storage directories
        self.tutorials_path = self.storage_path / "tutorials"
        self.learning_paths_path = self.storage_path / "learning_paths"
        self.progress_path = self.storage_path / "progress"
        
        for path in [self.tutorials_path, self.learning_paths_path, self.progress_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Load learning data
        self._load_learning_data()
    
    def _load_learning_data(self) -> None:
        """Load all learning data into the manager."""
        # Load tutorials
        tutorials = self._load_tutorials()
        for tutorial_id, tutorial_data in tutorials.items():
            learning_item = LearningItem(
                id=tutorial_id,
                type="tutorial",
                title=tutorial_data.get('title', ''),
                description=tutorial_data.get('description', ''),
                data=tutorial_data,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.create(tutorial_id, learning_item)
        
        # Load learning paths
        learning_paths = self._load_learning_paths()
        for path_id, path_data in learning_paths.items():
            learning_item = LearningItem(
                id=path_id,
                type="learning_path",
                title=path_data.get('title', ''),
                description=path_data.get('description', ''),
                data=path_data,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.create(path_id, learning_item)
        
        # Load user progress
        user_progress = self._load_user_progress()
        for user_id, progress_data in user_progress.items():
            learning_item = LearningItem(
                id=user_id,
                type="progress",
                title=f"Progress for {user_id}",
                description="User learning progress",
                data=progress_data,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.create(user_id, learning_item)
    
    def _load_tutorials(self) -> Dict[str, Any]:
        """Load tutorial data from storage."""
        tutorials_file = self.tutorials_path / "tutorials.json"
        if tutorials_file.exists():
            with open(tutorials_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_learning_paths(self) -> Dict[str, Any]:
        """Load learning paths from storage."""
        paths_file = self.learning_paths_path / "learning_paths.json"
        if paths_file.exists():
            with open(paths_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_user_progress(self) -> Dict[str, Any]:
        """Load user progress from storage."""
        progress_file = self.progress_path / "user_progress.json"
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_user_progress(self) -> None:
        """Save user progress to storage."""
        progress_file = self.progress_path / "user_progress.json"
        progress_data = {}
        
        # Get all progress items
        result = self.list_all()
        if result.success and result.data:
            for item in result.data.values():
                if item.type == "progress":
                    progress_data[item.id] = item.data
        
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def get_tutorial(self, tutorial_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tutorial by ID."""
        result = self.read(tutorial_id)
        if result.success and result.data and result.data.type == "tutorial":
            return result.data.data
        return None
    
    def get_learning_path(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific learning path by ID."""
        result = self.read(path_id)
        if result.success and result.data and result.data.type == "learning_path":
            return result.data.data
        return None
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get progress for a specific user."""
        result = self.read(user_id)
        if result.success and result.data and result.data.type == "progress":
            return result.data.data
        
        # Return default progress structure
        return {
            'tutorials': {},
            'learning_paths': {},
            'practice_exercises': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def update_tutorial_progress(self, user_id: str, tutorial_id: str, step: int) -> None:
        """Update tutorial progress for a user."""
        user_progress = self.get_user_progress(user_id)
        
        if user_id not in user_progress:
            user_progress = {
                'tutorials': {},
                'learning_paths': {},
                'practice_exercises': {},
                'last_updated': datetime.now().isoformat()
            }
        
        tutorial = self.get_tutorial(tutorial_id)
        if tutorial:
            user_progress['tutorials'][tutorial_id] = {
                'current_step': step,
                'completed': step >= len(tutorial['steps']),
                'last_updated': datetime.now().isoformat()
            }
        
        # Update the progress item
        learning_item = LearningItem(
            id=user_id,
            type="progress",
            title=f"Progress for {user_id}",
            description="User learning progress",
            data=user_progress,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.update(user_id, learning_item)
        self.save_user_progress()
    
    def update_learning_path_progress(self, user_id: str, path_id: str, module: str) -> None:
        """Update learning path progress for a user."""
        user_progress = self.get_user_progress(user_id)
        
        if user_id not in user_progress:
            user_progress = {
                'tutorials': {},
                'learning_paths': {},
                'practice_exercises': {},
                'last_updated': datetime.now().isoformat()
            }
        
        if path_id not in user_progress['learning_paths']:
            user_progress['learning_paths'][path_id] = {
                'completed_modules': [],
                'current_module': module,
                'last_updated': datetime.now().isoformat()
            }
        
        user_progress['learning_paths'][path_id]['current_module'] = module
        if module not in user_progress['learning_paths'][path_id]['completed_modules']:
            user_progress['learning_paths'][path_id]['completed_modules'].append(module)
        
        # Update the progress item
        learning_item = LearningItem(
            id=user_id,
            type="progress",
            title=f"Progress for {user_id}",
            description="User learning progress",
            data=user_progress,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.update(user_id, learning_item)
        self.save_user_progress()
    
    def get_recommended_tutorials(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recommended tutorials based on user progress."""
        user_progress = self.get_user_progress(user_id)
        completed_tutorials = set(user_progress['tutorials'].keys())
        
        recommendations = []
        result = self.list_all()
        if result.success and result.data:
            for item in result.data.values():
                if item.type == "tutorial":
                    tutorial_id = item.id
                    if tutorial_id not in completed_tutorials:
                        # Check prerequisites
                        prerequisites = item.data.get('prerequisites', [])
                        if all(prereq in completed_tutorials for prereq in prerequisites):
                            recommendations.append({
                                'id': tutorial_id,
                                'title': item.title,
                                'description': item.description,
                                'difficulty': item.data.get('difficulty', 'intermediate')
                            })
        
        return sorted(recommendations, key=lambda x: x['difficulty'])
    
    def get_recommended_learning_paths(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recommended learning paths based on user progress."""
        user_progress = self.get_user_progress(user_id)
        completed_paths = set(user_progress['learning_paths'].keys())
        
        recommendations = []
        result = self.list_all()
        if result.success and result.data:
            for item in result.data.values():
                if item.type == "learning_path":
                    path_id = item.id
                    if path_id not in completed_paths:
                        # Check prerequisites
                        prerequisites = item.data.get('prerequisites', [])
                        if all(prereq in completed_paths for prereq in prerequisites):
                            recommendations.append({
                                'id': path_id,
                                'title': item.title,
                                'description': item.description,
                                'modules': len(item.data['modules']),
                                'estimated_time': item.data.get('estimated_time', '2 hours')
                            })
        
        return sorted(recommendations, key=lambda x: len(x['modules']))
    
    def get_learning_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get learning metrics for a user."""
        user_progress = self.get_user_progress(user_id)
        
        # Count tutorials
        tutorials_result = self.list_all()
        total_tutorials = 0
        if tutorials_result.success and tutorials_result.data:
            total_tutorials = len([item for item in tutorials_result.data.values() if item.type == "tutorial"])
        
        # Count learning paths
        total_paths = 0
        if tutorials_result.success and tutorials_result.data:
            total_paths = len([item for item in tutorials_result.data.values() if item.type == "learning_path"])
        
        metrics = {
            'tutorials': {
                'total': total_tutorials,
                'completed': len([t for t in user_progress['tutorials'].values() if t['completed']]),
                'in_progress': len([t for t in user_progress['tutorials'].values() if not t['completed']])
            },
            'learning_paths': {
                'total': total_paths,
                'completed': len([p for p in user_progress['learning_paths'].values() 
                                if len(p['completed_modules']) == len(self.get_learning_path(p['current_module'])['modules'])]),
                'in_progress': len([p for p in user_progress['learning_paths'].values() 
                                  if len(p['completed_modules']) < len(self.get_learning_path(p['current_module'])['modules'])])
            },
            'practice_exercises': {
                'total': len(user_progress['practice_exercises']),
                'completed': len([e for e in user_progress['practice_exercises'].values() if e['completed']])
            },
            'last_updated': user_progress['last_updated']
        }
        
        return metrics
    
    def _validate_data(self, data: LearningItem) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.id:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Learning item ID is required",
                    errors=["Learning item ID cannot be empty"]
                )
            
            if not data.type:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Learning item type is required",
                    errors=["Learning item type cannot be empty"]
                )
            
            if data.type not in ["tutorial", "learning_path", "progress"]:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid learning item type",
                    errors=["Type must be 'tutorial', 'learning_path', or 'progress'"]
                )
            
            if not data.title:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Learning item title is required",
                    errors=["Learning item title cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Learning item validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Learning item validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a learning item.
        
        Args:
            key: Learning item ID to clean up
        """
        # No specific cleanup needed for learning items; reserved for future use.
        self.logger.debug("LearningManager cleanup hook called for item '%s'", key)
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache - no additional operations needed
        super()._clear_cache() 