import json
import os
from datetime import datetime
from typing import Optional, List
from data import Note, ToDo, Goal, Event

DB_FILE = "db.json"

class Database:
    def __init__(self):
        self.notes: List[Note] = []
        self.todos: List[ToDo] = []
        self.goals: List[Goal] = []
        self.events: List[Event] = []
        self.load()
    
    def load(self):
        """Load data from JSON file."""
        if not os.path.exists(DB_FILE):
            return
        
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
            
            # Load notes
            for note_data in data.get('notes', []):
                note_data['created_at'] = datetime.fromisoformat(note_data['created_at'])
                self.notes.append(Note(**note_data))
            
            # Load todos
            for todo_data in data.get('todos', []):
                todo_data['due_date'] = datetime.fromisoformat(todo_data['due_date']) if todo_data.get('due_date') else None
                todo_data['start_date'] = datetime.fromisoformat(todo_data['start_date']) if todo_data.get('start_date') else None
                todo_data['created_at'] = datetime.fromisoformat(todo_data['created_at'])
                self.todos.append(ToDo(**todo_data))
            
            # Load goals
            for goal_data in data.get('goals', []):
                goal_data['due_date'] = datetime.fromisoformat(goal_data['due_date']) if goal_data.get('due_date') else None
                goal_data['created_at'] = datetime.fromisoformat(goal_data['created_at'])
                self.goals.append(Goal(**goal_data))
            
            # Load events
            for event_data in data.get('events', []):
                event_data['start'] = datetime.fromisoformat(event_data['start'])
                event_data['end'] = datetime.fromisoformat(event_data['end'])
                self.events.append(Event(**event_data))
        
        except Exception as e:
            print(f"Error loading database: {e}")
    
    def save(self):
        """Save data to JSON file."""
        data = {
            'notes': [self._serialize_note(n) for n in self.notes],
            'todos': [self._serialize_todo(t) for t in self.todos],
            'goals': [self._serialize_goal(g) for g in self.goals],
            'events': [self._serialize_event(e) for e in self.events],
        }
        
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def _serialize_note(note: Note) -> dict:
        return {
            'id': note.id,
            'title': note.title,
            'type': note.type,
            'created_at': note.created_at.isoformat(),
            'content': note.content,
        }
    
    @staticmethod
    def _serialize_todo(todo: ToDo) -> dict:
        return {
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'priority': todo.priority,
            'due_date': todo.due_date.isoformat() if todo.due_date else None,
            'completed': todo.completed,
            'start_date': todo.start_date.isoformat() if todo.start_date else None,
            'attached_to_todo_id': todo.attached_to_todo_id,
            'attached_to_goal_id': todo.attached_to_goal_id,
            'tags': todo.tags,
            'created_at': todo.created_at.isoformat(),
        }
    
    @staticmethod
    def _serialize_goal(goal: Goal) -> dict:
        return {
            'id': goal.id,
            'title': goal.title,
            'description': goal.description,
            'priority': goal.priority,
            'due_date': goal.due_date.isoformat() if goal.due_date else None,
            'completed': goal.completed,
            'attached_todo_ids': goal.attached_todo_ids,
            'attached_goal_ids': goal.attached_goal_ids,
            'attached_event_ids': goal.attached_event_ids,
            'tags': goal.tags,
            'created_at': goal.created_at.isoformat(),
        }
    
    @staticmethod
    def _serialize_event(event: Event) -> dict:
        return {
            'id': event.id,
            'title': event.title,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
            'description': event.description,
            'attached_to_goal_id': event.attached_to_goal_id,
            'tags': event.tags,
        }
    
    # Query functions for AI to use
    
    def get_events_this_week(self) -> List[dict]:
        """Get events scheduled for this week."""
        from datetime import timedelta
        today = datetime.today()
        week_end = today + timedelta(days=7)
        upcoming = [e for e in self.events if today <= e.start <= week_end]
        return [self._serialize_event(e) for e in upcoming]
    
    def get_all_events(self) -> List[dict]:
        """Get all events."""
        return [self._serialize_event(e) for e in self.events]
    
    def get_todos_by_priority(self, priority: Optional[int] = None, completed: bool = False) -> List[dict]:
        """Get todos, optionally filtered by priority and completion status."""
        filtered = [t for t in self.todos if not t.completed == completed]
        if priority is not None:
            filtered = [t for t in filtered if t.priority == priority]
        return [self._serialize_todo(t) for t in filtered]
    
    def get_overdue_todos(self) -> List[dict]:
        """Get todos that are overdue."""
        now = datetime.now()
        overdue = [t for t in self.todos if t.due_date and t.due_date < now and not t.completed]
        return [self._serialize_todo(t) for t in overdue]
    
    def get_goals(self, completed: bool = False) -> List[dict]:
        """Get goals, optionally filtered by completion status."""
        filtered = [g for g in self.goals if g.completed == completed]
        return [self._serialize_goal(g) for g in filtered]
    
    def get_goal_details(self, goal_id: int) -> Optional[dict]:
        """Get detailed information about a specific goal including attached todos and events."""
        goal = next((g for g in self.goals if g.id == goal_id), None)
        if not goal:
            return None
        
        goal_dict = self._serialize_goal(goal)
        goal_dict['todos'] = [self._serialize_todo(t) for t in self.todos if t.attached_to_goal_id == goal_id]
        goal_dict['events'] = [self._serialize_event(e) for e in self.events if e.attached_to_goal_id == goal_id]
        goal_dict['sub_goals'] = [self._serialize_goal(g) for g in self.goals if g.id in goal.attached_goal_ids]
        
        return goal_dict
    
    def get_notes(self) -> List[dict]:
        """Get all notes."""
        return [self._serialize_note(n) for n in self.notes]
    
    def get_upcoming_todos(self, days: int = 7) -> List[dict]:
        """Get todos due within specified number of days."""
        from datetime import timedelta
        today = datetime.today()
        end_date = today + timedelta(days=days)
        upcoming = [t for t in self.todos if t.due_date and today <= t.due_date <= end_date and not t.completed]
        return [self._serialize_todo(t) for t in upcoming]
    
    def add_note(self, title: str, type: str, content: str) -> Note:
        """Add a new note."""
        note_id = max([n.id for n in self.notes], default=0) + 1
        note = Note(id=note_id, title=title, type=type, created_at=datetime.now(), content=content)
        self.notes.append(note)
        self.save()
        return note
    
    def add_todo(self, title: str, description: str, priority: int, due_date: Optional[datetime] = None,
                 start_date: Optional[datetime] = None, attached_to_goal_id: Optional[int] = None,
                 attached_to_todo_id: Optional[int] = None, tags: Optional[List[str]] = None) -> ToDo:
        """Add a new todo."""
        todo_id = max([t.id for t in self.todos], default=0) + 1
        todo = ToDo(
            id=todo_id, title=title, description=description, priority=priority,
            due_date=due_date, start_date=start_date, attached_to_goal_id=attached_to_goal_id,
            attached_to_todo_id=attached_to_todo_id, tags=tags or [], created_at=datetime.now()
        )
        self.todos.append(todo)
        self.save()
        return todo
    
    def add_goal(self, title: str, description: str, priority: int, due_date: Optional[datetime] = None,
                 tags: Optional[List[str]] = None) -> Goal:
        """Add a new goal."""
        goal_id = max([g.id for g in self.goals], default=0) + 1
        goal = Goal(
            id=goal_id, title=title, description=description, priority=priority,
            due_date=due_date, tags=tags or [], created_at=datetime.now()
        )
        self.goals.append(goal)
        self.save()
        return goal
    
    def add_event(self, title: str, start: datetime, end: datetime, description: str = "",
                  attached_to_goal_id: Optional[int] = None, tags: Optional[List[str]] = None) -> Event:
        """Add a new event."""
        event_id = max([e.id for e in self.events], default=0) + 1
        event = Event(
            id=event_id, title=title, start=start, end=end, description=description,
            attached_to_goal_id=attached_to_goal_id, tags=tags or []
        )
        self.events.append(event)
        self.save()
        return event


# Global database instance
db = Database()
