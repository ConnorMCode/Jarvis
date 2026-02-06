from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Note:
    id: int
    title: str
    type: str
    created_at: datetime
    content: str

@dataclass
class DependentNote:
    """A note that must have a parent entity. Deleted when parent is deleted."""
    id: int
    title: str
    content: str
    parent_type: str  # 'event', 'todo', 'goal', or 'note'
    parent_id: int    # ID of the parent entity
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ToDo:
    id: int
    title: str
    description: str
    priority: int  # 1 (low) to 5 (high)
    due_date: Optional[datetime] = None
    completed: bool = False
    start_date: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Goal:
    id: int
    title: str
    description: str
    priority: int  # 1 (low) to 5 (high)
    due_date: Optional[datetime] = None
    completed: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Event:
    id: int
    title: str
    start: datetime
    end: datetime
    description: str = ""
    tags: list[str] = field(default_factory=list)

@dataclass
class Link:
    """Represents a relationship between any two entities (flexible, single-source-of-truth).
    
    Example relationships:
    - Link(from_type='goal', from_id=1, to_type='todo', to_id=5)
    - Link(from_type='todo', from_id=5, to_type='todo', to_id=3)  # subtask
    - Link(from_type='event', from_id=2, to_type='goal', to_id=1)
    - Link(from_type='todo', from_id=5, to_type='note', to_id=7)
    """
    id: int
    from_type: str  # 'goal', 'todo', 'event', 'note'
    from_id: int
    to_type: str    # 'goal', 'todo', 'event', 'note'
    to_id: int
    created_at: datetime = field(default_factory=datetime.now)