"""Data structures for the learning system."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class TutorialStep:
    """Represents a step in a tutorial."""
    id: str
    title: str
    content: str
    interactive_elements: List[Dict[str, Any]] = field(default_factory=list)
    required_completion: bool = True
    estimated_time: str = "5 minutes"

@dataclass
class Tutorial:
    """Represents a tutorial."""
    id: str
    title: str
    description: str
    steps: List[TutorialStep]
    prerequisites: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class LearningModule:
    """Represents a module in a learning path."""
    id: str
    title: str
    description: str
    tutorials: List[str]  # List of tutorial IDs
    practice_exercises: List[str]  # List of exercise IDs
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: str = "1 hour"
    difficulty: str = "intermediate"

@dataclass
class LearningPath:
    """Represents a learning path."""
    id: str
    title: str
    description: str
    modules: List[LearningModule]
    prerequisites: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class PracticeExercise:
    """Represents a practice exercise."""
    id: str
    title: str
    description: str
    instructions: str
    solution: str
    difficulty: str = "intermediate"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class UserProgress:
    """Represents a user's learning progress."""
    user_id: str
    tutorials: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    learning_paths: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    practice_exercises: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class LearningMetrics:
    """Represents learning metrics for a user."""
    user_id: str
    tutorials_completed: int = 0
    tutorials_in_progress: int = 0
    learning_paths_completed: int = 0
    learning_paths_in_progress: int = 0
    practice_exercises_completed: int = 0
    total_learning_time: str = "0 hours"
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class LearningRecommendation:
    """Represents a learning recommendation for a user."""
    user_id: str
    recommended_tutorials: List[Dict[str, Any]] = field(default_factory=list)
    recommended_learning_paths: List[Dict[str, Any]] = field(default_factory=list)
    recommended_practice_exercises: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now) 