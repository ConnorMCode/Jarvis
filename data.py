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
class ToDo:
    id: int
    title: str
    description: str
    priority: int  # 1 (low) to 5 (high)
    due_date: Optional[datetime] = None
    completed: bool = False
    start_date: Optional[datetime] = None
    attached_to_todo_id: Optional[int] = None  # Parent todo if this is a sub-task
    attached_to_goal_id: Optional[int] = None  # Associated goal
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
    attached_todo_ids: list[int] = field(default_factory=list)  # Direct todos
    attached_goal_ids: list[int] = field(default_factory=list)  # Sub-goals
    attached_event_ids: list[int] = field(default_factory=list)  # Associated events
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Event:
    id: int
    title: str
    start: datetime
    end: datetime
    description: str = ""
    attached_to_goal_id: Optional[int] = None
    tags: list[str] = field(default_factory=list)