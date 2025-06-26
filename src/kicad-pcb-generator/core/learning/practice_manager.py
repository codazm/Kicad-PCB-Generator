"""Practice system for the KiCad PCB Generator."""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
import json
import os
import logging
from pathlib import Path

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from ..validation.validation_manager import ValidationManager
from ..validation.base_validator import ValidationResult, ValidationSeverity
from .learning_data import PracticeExercise, UserProgress

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

@dataclass
class PracticeFeedback:
    """Feedback for a practice exercise."""
    exercise_id: str
    user_id: str
    timestamp: datetime
    score: float
    feedback: str
    suggestions: List[str]
    validation_results: List[ValidationResult]

@dataclass
class PracticeItem:
    """Data structure for practice items."""
    exercise_id: str
    user_id: str
    exercise: PracticeExercise
    progress: UserProgress
    feedback: Optional[PracticeFeedback] = None
    status: str = "pending"
    score: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        """Validate required fields and set defaults."""
        if not self.exercise_id:
            raise ValueError("exercise_id is required")
        if not self.user_id:
            raise ValueError("user_id is required")
        if not isinstance(self.exercise, PracticeExercise):
            raise ValueError("exercise must be a PracticeExercise instance")
        if not isinstance(self.progress, UserProgress):
            raise ValueError("progress must be a UserProgress instance")
        if self.last_updated is None:
            self.last_updated = datetime.now()

class PracticeManager(BaseManager[PracticeItem]):
    """Manages practice exercises and feedback."""
    
    def __init__(self, storage_path: str, logger: Optional[logging.Logger] = None):
        """Initialize practice manager.
        
        Args:
            storage_path: Path to store practice data
            logger: Optional logger
        """
        super().__init__()
        self.storage_path = Path(storage_path)
        self.logger = logger or logging.getLogger(__name__)
        
        # Create storage directories
        self.exercises_path = self.storage_path / "exercises"
        self.progress_path = self.storage_path / "progress"
        self.feedback_path = self.storage_path / "feedback"
        
        for path in [self.exercises_path, self.progress_path, self.feedback_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize validation manager
        self.validation_manager = ValidationManager()
        
        # Load exercises
        self.exercises: Dict[str, PracticeExercise] = {}
        self._load_exercises()
    
    def _validate_data(self, data: PracticeItem) -> ManagerResult:
        """Validate practice item data.
        
        Args:
            data: Practice item to validate
            
        Returns:
            Manager result
        """
        try:
            # Basic validation
            if not isinstance(data, PracticeItem):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Data must be a PracticeItem instance",
                    errors=["Invalid data type"]
                )
            
            # Validate exercise ID
            if not data.exercise_id or not isinstance(data.exercise_id, str):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid exercise ID",
                    errors=["exercise_id must be a non-empty string"]
                )
            
            # Validate user ID
            if not data.user_id or not isinstance(data.user_id, str):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid user ID",
                    errors=["user_id must be a non-empty string"]
                )
            
            # Validate exercise
            if not isinstance(data.exercise, PracticeExercise):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid exercise",
                    errors=["exercise must be a PracticeExercise instance"]
                )
            
            # Validate progress
            if not isinstance(data.progress, UserProgress):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid progress",
                    errors=["progress must be a UserProgress instance"]
                )
            
            # Validate score
            if not isinstance(data.score, (int, float)) or data.score < 0 or data.score > 1:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid score",
                    errors=["score must be a number between 0 and 1"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Practice item validation successful"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating practice item: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Validation error: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a practice item.
        
        Args:
            key: Key of the item to clean up
        """
        try:
            # Remove from exercises if present
            if key in self.exercises:
                del self.exercises[key]
            
            # Clean up related files
            exercise_file = self.exercises_path / f"{key}.json"
            if exercise_file.exists():
                exercise_file.unlink()
            
            self.logger.debug(f"Cleaned up practice item: {key}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up practice item {key}: {e}")
    
    def add_practice_exercise(self, exercise: PracticeExercise) -> ManagerResult:
        """Add a practice exercise to the manager.
        
        Args:
            exercise: Practice exercise to add
            
        Returns:
            Manager result
        """
        try:
            # Create practice item
            item = PracticeItem(
                exercise_id=exercise.id,
                user_id="system",  # System exercise
                exercise=exercise,
                progress=UserProgress(
                    user_id="system",
                    completed_exercises=[],
                    in_progress_exercises=[],
                    scores={}
                ),
                status="available"
            )
            
            # Add to manager
            result = self.create(exercise.id, item)
            
            if result.success:
                # Add to exercises dictionary
                self.exercises[exercise.id] = exercise
                
                # Save to file
                self._save_exercise(exercise)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding practice exercise {exercise.id}: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.CREATE,
                status=ManagerStatus.FAILED,
                message=f"Error adding practice exercise: {e}",
                errors=[str(e)]
            )
    
    def _save_exercise(self, exercise: PracticeExercise) -> None:
        """Save exercise to file.
        
        Args:
            exercise: Exercise to save
        """
        try:
            exercise_file = self.exercises_path / f"{exercise.id}.json"
            with open(exercise_file, "w") as f:
                json.dump(exercise.__dict__, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving exercise: {str(e)}")
            raise
    
    def _load_exercises(self) -> None:
        """Load practice exercises from storage."""
        try:
            for exercise_file in self.exercises_path.glob("*.json"):
                with open(exercise_file, "r") as f:
                    data = json.load(f)
                    exercise = PracticeExercise(**data)
                    self.exercises[exercise.id] = exercise
        except Exception as e:
            self.logger.error(f"Error loading exercises: {str(e)}")
            raise
    
    def get_exercise(self, exercise_id: str) -> Optional[PracticeExercise]:
        """Get a practice exercise by ID.
        
        Args:
            exercise_id: Exercise ID
            
        Returns:
            Practice exercise if found
        """
        return self.exercises.get(exercise_id)
    
    def get_exercises_by_category(self, category: str) -> List[PracticeExercise]:
        """Get practice exercises by category.
        
        Args:
            category: Exercise category
            
        Returns:
            List of practice exercises
        """
        return [
            exercise for exercise in self.exercises.values()
            if exercise.category == category
        ]
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get user's practice progress.
        
        Args:
            user_id: User ID
            
        Returns:
            User progress
        """
        progress_file = self.progress_path / f"{user_id}.json"
        if not progress_file.exists():
            return UserProgress(
                user_id=user_id,
                completed_exercises=[],
                in_progress_exercises=[],
                scores={}
            )
        
        try:
            with open(progress_file, "r") as f:
                data = json.load(f)
                return UserProgress(**data)
        except Exception as e:
            self.logger.error(f"Error loading user progress: {str(e)}")
            return UserProgress(
                user_id=user_id,
                completed_exercises=[],
                in_progress_exercises=[],
                scores={}
            )
    
    def save_user_progress(self, progress: UserProgress) -> None:
        """Save user's practice progress.
        
        Args:
            progress: User progress
        """
        try:
            progress_file = self.progress_path / f"{progress.user_id}.json"
            with open(progress_file, "w") as f:
                json.dump(progress.__dict__, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving user progress: {str(e)}")
            raise
    
    def validate_solution(
        self,
        exercise_id: str,
        user_id: str,
        solution: Dict[str, Any]
    ) -> PracticeFeedback:
        """Validate a practice exercise solution.
        
        Args:
            exercise_id: Exercise ID
            user_id: User ID
            solution: User's solution
            
        Returns:
            Practice feedback
        """
        exercise = self.get_exercise(exercise_id)
        if not exercise:
            raise ValueError(f"Exercise not found: {exercise_id}")
        
        # Validate solution
        validation_results = self.validation_manager.validate(
            solution,
            categories=exercise.validation_categories
        )
        
        # Calculate score
        score = self._calculate_score(validation_results)
        
        # Generate feedback
        feedback = self._generate_feedback(validation_results)
        suggestions = self._generate_suggestions(validation_results)
        
        # Create feedback
        practice_feedback = PracticeFeedback(
            exercise_id=exercise_id,
            user_id=user_id,
            timestamp=datetime.now(),
            score=score,
            feedback=feedback,
            suggestions=suggestions,
            validation_results=validation_results
        )
        
        # Save feedback
        self._save_feedback(practice_feedback)
        
        # Update progress
        progress = self.get_user_progress(user_id)
        if score >= 0.8:  # 80% threshold for completion
            if exercise_id not in progress.completed_exercises:
                progress.completed_exercises.append(exercise_id)
            if exercise_id in progress.in_progress_exercises:
                progress.in_progress_exercises.remove(exercise_id)
        else:
            if exercise_id not in progress.in_progress_exercises:
                progress.in_progress_exercises.append(exercise_id)
        
        progress.scores[exercise_id] = score
        self.save_user_progress(progress)
        
        return practice_feedback
    
    def _calculate_score(self, validation_results: List[ValidationResult]) -> float:
        """Calculate score from validation results.
        
        Args:
            validation_results: Validation results
            
        Returns:
            Score between 0 and 1
        """
        if not validation_results:
            return 1.0
        
        # Weight results by severity
        weights = {
            ValidationSeverity.ERROR: 1.0,
            ValidationSeverity.WARNING: 0.5,
            ValidationSeverity.INFO: 0.1
        }
        
        total_weight = sum(weights[r.severity] for r in validation_results)
        max_weight = len(validation_results) * max(weights.values())
        
        return max(0.0, 1.0 - (total_weight / max_weight))
    
    def _generate_feedback(self, validation_results: List[ValidationResult]) -> str:
        """Generate feedback from validation results.
        
        Args:
            validation_results: Validation results
            
        Returns:
            Feedback message
        """
        if not validation_results:
            return "Great job! Your solution passed all validations."
        
        # Group results by severity
        by_severity = {
            ValidationSeverity.ERROR: [],
            ValidationSeverity.WARNING: [],
            ValidationSeverity.INFO: []
        }
        
        for result in validation_results:
            by_severity[result.severity].append(result)
        
        # Build feedback message
        feedback = []
        
        if by_severity[ValidationSeverity.ERROR]:
            feedback.append("Your solution has some issues that need to be fixed:")
            for result in by_severity[ValidationSeverity.ERROR]:
                feedback.append(f"- {result.message}")
        
        if by_severity[ValidationSeverity.WARNING]:
            feedback.append("\nThere are some potential improvements:")
            for result in by_severity[ValidationSeverity.WARNING]:
                feedback.append(f"- {result.message}")
        
        if by_severity[ValidationSeverity.INFO]:
            feedback.append("\nSome suggestions for optimization:")
            for result in by_severity[ValidationSeverity.INFO]:
                feedback.append(f"- {result.message}")
        
        return "\n".join(feedback)
    
    def _generate_suggestions(self, validation_results: List[ValidationResult]) -> List[str]:
        """Generate suggestions from validation results.
        
        Args:
            validation_results: Validation results
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        for result in validation_results:
            if hasattr(result, "suggestion") and result.suggestion:
                suggestions.append(result.suggestion)
        
        return suggestions
    
    def _save_feedback(self, feedback: PracticeFeedback) -> None:
        """Save practice feedback.
        
        Args:
            feedback: Practice feedback
        """
        try:
            feedback_file = self.feedback_path / f"{feedback.user_id}_{feedback.exercise_id}.json"
            with open(feedback_file, "w") as f:
                json.dump({
                    "exercise_id": feedback.exercise_id,
                    "user_id": feedback.user_id,
                    "timestamp": feedback.timestamp.isoformat(),
                    "score": feedback.score,
                    "feedback": feedback.feedback,
                    "suggestions": feedback.suggestions,
                    "validation_results": [
                        {
                            "category": r.category.value,
                            "message": r.message,
                            "severity": r.severity.value
                        }
                        for r in feedback.validation_results
                    ]
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving feedback: {str(e)}")
            raise 