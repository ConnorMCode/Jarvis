import json
import os
from datetime import datetime
from typing import Optional, List
from data import Note, DependentNote, ToDo, Goal, Event, Link

DB_FILE = "db.json"

class Database:
    def __init__(self):
        self.notes: List[Note] = []
        self.dependent_notes: List[DependentNote] = []  # Notes with required parents
        self.todos: List[ToDo] = []
        self.goals: List[Goal] = []
        self.events: List[Event] = []
        self.links: List[Link] = []  # Relationship management
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
            
            # Load dependent notes
            for note_data in data.get('dependent_notes', []):
                note_data['created_at'] = datetime.fromisoformat(note_data['created_at'])
                self.dependent_notes.append(DependentNote(**note_data))
            
            # Load todos
            for todo_data in data.get('todos', []):
                todo_data['due_date'] = datetime.fromisoformat(todo_data['due_date']) if todo_data.get('due_date') else None
                todo_data['start_date'] = datetime.fromisoformat(todo_data['start_date']) if todo_data.get('start_date') else None
                todo_data['created_at'] = datetime.fromisoformat(todo_data['created_at'])
                # Remove old attachment fields if they exist (migration)
                todo_data.pop('attached_to_todo_id', None)
                todo_data.pop('attached_to_goal_id', None)
                self.todos.append(ToDo(**todo_data))
                # Normalize tags loaded from file
                self.todos[-1].tags = self._normalize_tags(getattr(self.todos[-1], 'tags', []))
            
            # Load goals
            for goal_data in data.get('goals', []):
                goal_data['due_date'] = datetime.fromisoformat(goal_data['due_date']) if goal_data.get('due_date') else None
                goal_data['created_at'] = datetime.fromisoformat(goal_data['created_at'])
                # Remove old attachment fields if they exist (migration)
                goal_data.pop('attached_todo_ids', None)
                goal_data.pop('attached_goal_ids', None)
                goal_data.pop('attached_event_ids', None)
                self.goals.append(Goal(**goal_data))
                # Normalize tags loaded from file
                self.goals[-1].tags = self._normalize_tags(getattr(self.goals[-1], 'tags', []))
            
            # Load events
            for event_data in data.get('events', []):
                event_data['date'] = datetime.fromisoformat(event_data['date'])
                # Remove old attachment field if it exists (migration)
                event_data.pop('attached_to_goal_id', None)
                self.events.append(Event(**event_data))
                # Normalize tags loaded from file
                self.events[-1].tags = self._normalize_tags(getattr(self.events[-1], 'tags', []))
            
            # Load links (relationships)
            for link_data in data.get('links', []):
                link_data['created_at'] = datetime.fromisoformat(link_data['created_at'])
                self.links.append(Link(**link_data))
        
        except Exception as e:
            print(f"Error loading database: {e}")
    
    def save(self):
        """Save data to JSON file."""
        data = {
            'notes': [self._serialize_note(n) for n in self.notes],
            'dependent_notes': [self._serialize_dependent_note(n) for n in self.dependent_notes],
            'todos': [self._serialize_todo(t) for t in self.todos],
            'goals': [self._serialize_goal(g) for g in self.goals],
            'events': [self._serialize_event(e) for e in self.events],
            'links': [self._serialize_link(l) for l in self.links],
        }
        
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _normalize_tags(self, tags: Optional[List[str]]) -> List[str]:
        """Normalize tag list to lowercase, trimmed, and deduplicated while preserving order."""
        if not tags:
            return []
        seen = set()
        normalized = []
        for t in tags:
            if not isinstance(t, str):
                continue
            s = t.strip().lower()
            if s and s not in seen:
                seen.add(s)
                normalized.append(s)
        return normalized
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
    def _serialize_dependent_note(note: DependentNote) -> dict:
        return {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'parent_type': note.parent_type,
            'parent_id': note.parent_id,
            'created_at': note.created_at.isoformat(),
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
            'tags': todo.tags,
            'created_at': todo.created_at.isoformat(),
        }
    
    def _serialize_todo_with_notes(self, todo: ToDo) -> dict:
        """Serialize todo including dependent notes."""
        todo_dict = self._serialize_todo(todo)
        dependent_notes = [n for n in self.dependent_notes if n.parent_type == 'todo' and n.parent_id == todo.id]
        if dependent_notes:
            todo_dict['notes'] = [{
                'id': n.id,
                'title': n.title,
                'content': n.content
            } for n in dependent_notes]
        return todo_dict
    
    @staticmethod
    def _serialize_goal(goal: Goal) -> dict:
        return {
            'id': goal.id,
            'title': goal.title,
            'description': goal.description,
            'priority': goal.priority,
            'due_date': goal.due_date.isoformat() if goal.due_date else None,
            'completed': goal.completed,
            'tags': goal.tags,
            'created_at': goal.created_at.isoformat(),
        }
    
    def _serialize_goal_with_notes(self, goal: Goal) -> dict:
        """Serialize goal including dependent notes."""
        goal_dict = self._serialize_goal(goal)
        dependent_notes = [n for n in self.dependent_notes if n.parent_type == 'goal' and n.parent_id == goal.id]
        if dependent_notes:
            goal_dict['notes'] = [{
                'id': n.id,
                'title': n.title,
                'content': n.content
            } for n in dependent_notes]
        return goal_dict
    
    @staticmethod
    def _serialize_event(event: Event) -> dict:
        return {
            'id': event.id,
            'title': event.title,
            'date': event.date.isoformat(),
            'description': event.description,
            'tags': event.tags,
        }
    
    def _serialize_event_with_notes(self, event: Event) -> dict:
        """Serialize event including dependent notes."""
        event_dict = self._serialize_event(event)
        dependent_notes = [n for n in self.dependent_notes if n.parent_type == 'event' and n.parent_id == event.id]
        if dependent_notes:
            event_dict['notes'] = [{
                'id': n.id,
                'title': n.title,
                'content': n.content
            } for n in dependent_notes]
        return event_dict
    
    @staticmethod
    def _serialize_link(link: Link) -> dict:
        return {
            'id': link.id,
            'from_type': link.from_type,
            'from_id': link.from_id,
            'to_type': link.to_type,
            'to_id': link.to_id,
            'created_at': link.created_at.isoformat(),
        }
    
    # Link management methods
    
    def create_link(self, from_type: str, from_id: int, to_type: str, to_id: int) -> Link:
        """Create a link between two entities."""
        link_id = max([l.id for l in self.links], default=0) + 1
        link = Link(
            id=link_id,
            from_type=from_type,
            from_id=from_id,
            to_type=to_type,
            to_id=to_id
        )
        self.links.append(link)
        self.save()
        return link
    
    def delete_link(self, link_id: int) -> bool:
        """Delete a link by ID."""
        link = next((l for l in self.links if l.id == link_id), None)
        if link:
            self.links.remove(link)
            self.save()
            return True
        return False
    
    def get_links_from(self, from_type: str, from_id: int) -> List[Link]:
        """Get all links originating from a specific entity."""
        return [l for l in self.links if l.from_type == from_type and l.from_id == from_id]
    
    def get_links_to(self, to_type: str, to_id: int) -> List[Link]:
        """Get all links pointing to a specific entity."""
        return [l for l in self.links if l.to_type == to_type and l.to_id == to_id]
    
    def get_related_todos(self, entity_type: str, entity_id: int) -> List[ToDo]:
        """Get all todos related to an entity (used for goals, other todos, etc)."""
        links = self.get_links_from(entity_type, entity_id)
        todo_ids = [l.to_id for l in links if l.to_type == 'todo']
        return [t for t in self.todos if t.id in todo_ids]
    
    def get_related_goals(self, entity_type: str, entity_id: int) -> List[Goal]:
        """Get all goals related to an entity."""
        links = self.get_links_from(entity_type, entity_id)
        goal_ids = [l.to_id for l in links if l.to_type == 'goal']
        return [g for g in self.goals if g.id in goal_ids]
    
    def get_related_events(self, entity_type: str, entity_id: int) -> List[Event]:
        """Get all events related to an entity."""
        links = self.get_links_from(entity_type, entity_id)
        event_ids = [l.to_id for l in links if l.to_type == 'event']
        return [e for e in self.events if e.id in event_ids]
    
    def get_parent_goal(self, todo_id: int) -> Optional[Goal]:
        """Get the parent goal of a todo (if linked)."""
        links = self.get_links_to('goal', next((l for l in self.links if l.from_type == 'todo' and l.from_id == todo_id and l.to_type == 'goal'), None))
        if not links:
            links = [l for l in self.links if l.from_type == 'todo' and l.from_id == todo_id and l.to_type == 'goal']
        if links:
            goal_id = links[0].to_id
            return next((g for g in self.goals if g.id == goal_id), None)
        return None
    
    # Query functions for AI to use
    
    def get_events_this_week(self) -> List[dict]:
        """Get events scheduled for this week with attached notes."""
        from datetime import timedelta
        today = datetime.today()
        week_end = today + timedelta(days=7)
        upcoming = [e for e in self.events if today <= e.start <= week_end]
        return [self._serialize_event_with_notes(e) for e in upcoming]
    
    def get_all_events(self) -> List[dict]:
        """Get all events with attached notes."""
        return [self._serialize_event_with_notes(e) for e in self.events]
    
    def get_todos_by_priority(self, priority: Optional[int] = None, completed: bool = False) -> List[dict]:
        """Get todos, optionally filtered by priority and completion status, with attached notes."""
        filtered = [t for t in self.todos if t.completed == completed]
        if priority is not None:
            filtered = [t for t in filtered if t.priority == priority]
        return [self._serialize_todo_with_notes(t) for t in filtered]
    
    def get_overdue_todos(self) -> List[dict]:
        """Get todos that are overdue with attached notes."""
        now = datetime.now()
        overdue = [t for t in self.todos if t.due_date and t.due_date < now and not t.completed]
        return [self._serialize_todo_with_notes(t) for t in overdue]
    
    def get_all_todos(self) -> List[dict]:
        """Get all incomplete todos with attached notes, regardless of due date."""
        incomplete = [t for t in self.todos if not t.completed]
        return [self._serialize_todo_with_notes(t) for t in incomplete]
    
    def get_goals(self, completed: bool = False) -> List[dict]:
        """Get goals, optionally filtered by completion status, with attached notes."""
        filtered = [g for g in self.goals if g.completed == completed]
        return [self._serialize_goal_with_notes(g) for g in filtered]
    
    def get_goal_details(self, goal_id: int) -> Optional[dict]:
        """Get detailed information about a specific goal including attached todos and events."""
        goal = next((g for g in self.goals if g.id == goal_id), None)
        if not goal:
            return None
        
        goal_dict = self._serialize_goal(goal)
        # Use Link system to find related entities
        goal_dict['todos'] = [self._serialize_todo(t) for t in self.get_related_todos('goal', goal_id)]
        goal_dict['events'] = [self._serialize_event(e) for e in self.get_related_events('goal', goal_id)]
        goal_dict['sub_goals'] = [self._serialize_goal(g) for g in self.get_related_goals('goal', goal_id)]
        
        return goal_dict
    
    def get_notes(self) -> List[dict]:
        """Get all notes."""
        return [self._serialize_note(n) for n in self.notes]
    
    def get_upcoming_todos(self, days: int = 7) -> List[dict]:
        """Get todos due within specified number of days, with attached notes."""
        from datetime import timedelta
        today = datetime.today()
        end_date = today + timedelta(days=days)
        upcoming = [t for t in self.todos if t.due_date and today <= t.due_date <= end_date and not t.completed]
        return [self._serialize_todo_with_notes(t) for t in upcoming]
    
    def add_note(self, title: str, type: str, content: str) -> Note:
        """Add a new note."""
        note_id = max([n.id for n in self.notes], default=0) + 1
        note = Note(id=note_id, title=title, type=type, created_at=datetime.now(), content=content)
        self.notes.append(note)
        self.save()
        return note
    
    def add_todo(self, title: str, description: str, priority: int, due_date: Optional[datetime] = None,
                 start_date: Optional[datetime] = None, tags: Optional[List[str]] = None) -> ToDo:
        """Add a new todo."""
        todo_id = max([t.id for t in self.todos], default=0) + 1
        todo = ToDo(
            id=todo_id, title=title, description=description, priority=priority,
            due_date=due_date, start_date=start_date, tags=self._normalize_tags(tags or []), created_at=datetime.now()
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
            due_date=due_date, tags=self._normalize_tags(tags or []), created_at=datetime.now()
        )
        self.goals.append(goal)
        self.save()
        return goal
    
    def add_event(self, title: str, date: datetime, description: str = "",
                  tags: Optional[List[str]] = None) -> Event:
        """Add a new event."""
        event_id = max([e.id for e in self.events], default=0) + 1
        event = Event(
            id=event_id, title=title, date=date, description=description,
            tags=self._normalize_tags(tags or [])
        )
        self.events.append(event)
        self.save()
        return event
    
    def add_dependent_note(self, title: str, content: str, parent_type: str, parent_id: int) -> DependentNote:
        """Add a dependent note (must have a parent)."""
        # Verify parent exists
        parent = self._get_entity(parent_type, parent_id)
        if not parent:
            raise ValueError(f"{parent_type} with id {parent_id} not found")
        
        note_id = max([n.id for n in self.dependent_notes], default=0) + 1
        note = DependentNote(
            id=note_id,
            title=title,
            content=content,
            parent_type=parent_type,
            parent_id=parent_id,
            created_at=datetime.now()
        )
        self.dependent_notes.append(note)
        self.save()
        return note
    
    def _get_entity(self, entity_type: str, entity_id: int):
        """Helper to get any entity by type and id."""
        if entity_type == 'todo':
            return next((t for t in self.todos if t.id == entity_id), None)
        elif entity_type == 'goal':
            return next((g for g in self.goals if g.id == entity_id), None)
        elif entity_type == 'event':
            return next((e for e in self.events if e.id == entity_id), None)
        elif entity_type == 'note':
            return next((n for n in self.dependent_notes if n.id == entity_id), None)
        return None
    
    # Delete functions
    
    def delete_event(self, event_id: int) -> bool:
        """Delete an event by ID and all associated links and dependent notes."""
        event = next((e for e in self.events if e.id == event_id), None)
        if event:
            self.events.remove(event)
            # Clean up associated links
            self.links = [l for l in self.links if not (
                (l.from_type == 'event' and l.from_id == event_id) or
                (l.to_type == 'event' and l.to_id == event_id)
            )]
            # Clean up dependent notes
            self.dependent_notes = [n for n in self.dependent_notes if not (
                n.parent_type == 'event' and n.parent_id == event_id
            )]
            self.save()
            return True
        return False
    
    def delete_events_this_week(self) -> int:
        """Delete all events scheduled for this week. Returns count deleted."""
        from datetime import timedelta
        today = datetime.today()
        week_end = today + timedelta(days=7)
        events_to_delete = [e for e in self.events if today <= e.start <= week_end]
        for event in events_to_delete:
            self.events.remove(event)
            # Clean up associated links
            self.links = [l for l in self.links if not (
                (l.from_type == 'event' and l.from_id == event.id) or
                (l.to_type == 'event' and l.to_id == event.id)
            )]
            # Clean up dependent notes
            self.dependent_notes = [n for n in self.dependent_notes if not (
                n.parent_type == 'event' and n.parent_id == event.id
            )]
        if events_to_delete:
            self.save()
        return len(events_to_delete)
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo by ID and all associated links and dependent notes."""
        todo = next((t for t in self.todos if t.id == todo_id), None)
        if todo:
            self.todos.remove(todo)
            # Clean up associated links
            self.links = [l for l in self.links if not (
                (l.from_type == 'todo' and l.from_id == todo_id) or
                (l.to_type == 'todo' and l.to_id == todo_id)
            )]
            # Clean up dependent notes
            self.dependent_notes = [n for n in self.dependent_notes if not (
                n.parent_type == 'todo' and n.parent_id == todo_id
            )]
            self.save()
            return True
        return False
    
    def delete_goal(self, goal_id: int) -> bool:
        """Delete a goal by ID and all associated links and dependent notes."""
        goal = next((g for g in self.goals if g.id == goal_id), None)
        if goal:
            self.goals.remove(goal)
            # Clean up associated links
            self.links = [l for l in self.links if not (
                (l.from_type == 'goal' and l.from_id == goal_id) or
                (l.to_type == 'goal' and l.to_id == goal_id)
            )]
            # Clean up dependent notes
            self.dependent_notes = [n for n in self.dependent_notes if not (
                n.parent_type == 'goal' and n.parent_id == goal_id
            )]
            self.save()
            return True
        return False
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID and all associated links."""
        note = next((n for n in self.notes if n.id == note_id), None)
        if note:
            self.notes.remove(note)
            # Clean up associated links
            self.links = [l for l in self.links if not (
                (l.from_type == 'note' and l.from_id == note_id) or
                (l.to_type == 'note' and l.to_id == note_id)
            )]
            self.save()
            return True
        return False
    
    def delete_dependent_note(self, note_id: int) -> bool:
        """Delete a dependent note by ID."""
        note = next((n for n in self.dependent_notes if n.id == note_id), None)
        if note:
            self.dependent_notes.remove(note)
            self.save()
            return True
        return False
    
    def get_dependent_notes(self, parent_type: str = None, parent_id: int = None) -> List[dict]:
        """Get dependent notes, optionally filtered by parent."""
        if parent_type and parent_id:
            notes = [n for n in self.dependent_notes if n.parent_type == parent_type and n.parent_id == parent_id]
        else:
            notes = self.dependent_notes
        
        return [{
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'parent_type': n.parent_type,
            'parent_id': n.parent_id,
            'created_at': n.created_at.isoformat(),
        } for n in notes]
    
    # Update functions (preserve links and notes while updating fields)
    
    def update_todo(self, todo_id: int, title: Optional[str] = None, description: Optional[str] = None,
                    priority: Optional[int] = None, due_date: Optional[datetime] = None,
                    start_date: Optional[datetime] = None, tags: Optional[List[str]] = None,
                    completed: Optional[bool] = None) -> Optional[dict]:
        """Update a todo's fields while preserving all links and dependent notes."""
        todo = next((t for t in self.todos if t.id == todo_id), None)
        if not todo:
            return None
        
        # Only update fields that were provided
        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if priority is not None:
            todo.priority = priority
        if due_date is not None:
            todo.due_date = due_date
        if start_date is not None:
            todo.start_date = start_date
        if tags is not None:
            todo.tags = self._normalize_tags(tags)
        if completed is not None:
            todo.completed = completed
        
        self.save()
        return self._serialize_todo_with_notes(todo)
    
    def update_goal(self, goal_id: int, title: Optional[str] = None, description: Optional[str] = None,
                    priority: Optional[int] = None, due_date: Optional[datetime] = None,
                    tags: Optional[List[str]] = None, completed: Optional[bool] = None) -> Optional[dict]:
        """Update a goal's fields while preserving all links and dependent notes."""
        goal = next((g for g in self.goals if g.id == goal_id), None)
        if not goal:
            return None
        
        # Only update fields that were provided
        if title is not None:
            goal.title = title
        if description is not None:
            goal.description = description
        if priority is not None:
            goal.priority = priority
        if due_date is not None:
            goal.due_date = due_date
        if tags is not None:
            goal.tags = self._normalize_tags(tags)
        if completed is not None:
            goal.completed = completed
        
        self.save()
        return self._serialize_goal_with_notes(goal)
    
    def update_event(self, event_id: int, title: Optional[str] = None, description: Optional[str] = None,
                     start: Optional[datetime] = None, end: Optional[datetime] = None,
                     tags: Optional[List[str]] = None) -> Optional[dict]:
        """Update an event's fields while preserving all links and dependent notes."""
        event = next((e for e in self.events if e.id == event_id), None)
        if not event:
            return None
        
        # Only update fields that were provided
        if title is not None:
            event.title = title
        if description is not None:
            event.description = description
        if start is not None:
            event.start = start
        if end is not None:
            event.end = end
        if tags is not None:
            event.tags = self._normalize_tags(tags)
        
        self.save()
        return self._serialize_event_with_notes(event)
    
    def update_note(self, note_id: int, title: Optional[str] = None, content: Optional[str] = None,
                    note_type: Optional[str] = None) -> Optional[dict]:
        """Update a standalone note's fields."""
        note = next((n for n in self.notes if n.id == note_id), None)
        if not note:
            return None
        
        # Only update fields that were provided
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if note_type is not None:
            note.type = note_type
        
        self.save()
        return self._serialize_note(note)
    
    def update_dependent_note(self, note_id: int, title: Optional[str] = None,
                              content: Optional[str] = None) -> Optional[dict]:
        """Update a dependent note's title or content."""
        note = next((n for n in self.dependent_notes if n.id == note_id), None)
        if not note:
            return None
        
        # Only update fields that were provided
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        
        self.save()
        return {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'parent_type': note.parent_type,
            'parent_id': note.parent_id,
            'created_at': note.created_at.isoformat(),
        }
    
    # Search functions
    
    def search_todos_by_title(self, title: str) -> List[dict]:
        """Search todos by title (case-insensitive partial match)."""
        search = title.lower()
        matching = [t for t in self.todos if search in t.title.lower()]
        return [self._serialize_todo_with_notes(t) for t in matching]

    def search_goals_by_title(self, title: str) -> List[dict]:
        """Search goals by title (case-insensitive partial match)."""
        search = title.lower()
        matching = [g for g in self.goals if search in g.title.lower()]
        return [self._serialize_goal_with_notes(g) for g in matching]

    def search_events_by_title(self, title: str) -> List[dict]:
        """Search events by title (case-insensitive partial match)."""
        search = title.lower()
        matching = [e for e in self.events if search in e.title.lower()]
        return [self._serialize_event_with_notes(e) for e in matching]

    # Tag-based search functions (primary search method)
    
    def search_todos_by_tag(self, tag: str) -> List[dict]:
        """Search todos by tag (case-insensitive match)."""
        tag_lower = tag.lower()
        matching = [t for t in self.todos if any(tag_lower == t_tag.lower() for t_tag in t.tags)]
        return [self._serialize_todo_with_notes(t) for t in matching]

    def search_goals_by_tag(self, tag: str) -> List[dict]:
        """Search goals by tag (case-insensitive match)."""
        tag_lower = tag.lower()
        matching = [g for g in self.goals if any(tag_lower == g_tag.lower() for g_tag in g.tags)]
        return [self._serialize_goal_with_notes(g) for g in matching]

    def search_events_by_tag(self, tag: str) -> List[dict]:
        """Search events by tag (case-insensitive match)."""
        tag_lower = tag.lower()
        matching = [e for e in self.events if any(tag_lower == e_tag.lower() for e_tag in e.tags)]
        return [self._serialize_event_with_notes(e) for e in matching]

    def search_all_by_tag(self, tag: str) -> dict:
        """Search todos, goals, and events by tag and return all results."""
        return {
            "todos": self.search_todos_by_tag(tag),
            "goals": self.search_goals_by_tag(tag),
            "events": self.search_events_by_tag(tag)
        }


# Global database instance
db = Database()
