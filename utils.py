"""
Utility module for data management operations.
Provides convenient functions for adding and updating todos, goals, and events.
"""

from datetime import datetime
from typing import Optional, List
from db import db

def add_todo(title: str, description: str = "", priority: int = 3, 
             due_date: Optional[str] = None, start_date: Optional[str] = None,
             tags: Optional[List[str]] = None):
    """
    Add a new todo item.
    
    Args:
        title: Todo title
        description: Detailed description
        priority: 1-5 (1=low, 5=high)
        due_date: ISO format datetime string (e.g., "2026-02-10T17:00:00")
        start_date: ISO format datetime string
        tags: List of tags
    """
    due = datetime.fromisoformat(due_date) if due_date else None
    start = datetime.fromisoformat(start_date) if start_date else None
    
    todo = db.add_todo(
        title=title,
        description=description,
        priority=priority,
        due_date=due,
        start_date=start,
        tags=tags
    )
    print(f"✓ Added todo: {title} (ID: {todo.id})")
    return todo

def add_goal(title: str, description: str = "", priority: int = 3,
             due_date: Optional[str] = None, tags: Optional[List[str]] = None):
    """
    Add a new goal.
    
    Args:
        title: Goal title
        description: Detailed description
        priority: 1-5 (1=low, 5=high)
        due_date: ISO format datetime string
        tags: List of tags
    """
    due = datetime.fromisoformat(due_date) if due_date else None
    
    goal = db.add_goal(
        title=title,
        description=description,
        priority=priority,
        due_date=due,
        tags=tags
    )
    print(f"✓ Added goal: {title} (ID: {goal.id})")
    return goal

def add_event(title: str, date: str,
              description: str = "", tags: Optional[List[str]] = None):
    """
    Add a new event.
    
    Args:
        title: Event title
        date: ISO format datetime string
        description: Event description
        tags: List of tags
    """
    event_date = datetime.fromisoformat(date)
    
    event = db.add_event(
        title=title,
        date=event_date,
        description=description,
        tags=tags
    )
    print(f"✓ Added event: {title} (ID: {event.id})")
    return event

def attach_todo_to_goal(todo_id: int, goal_id: int):
    """Attach a todo to a goal using the Link system."""
    todo = next((t for t in db.todos if t.id == todo_id), None)
    goal = next((g for g in db.goals if g.id == goal_id), None)
    
    if todo and goal:
        db.create_link('goal', goal_id, 'todo', todo_id)
        print(f"✓ Attached {todo.title} to goal {goal.title}")
    else:
        print(f"✗ Todo or goal not found")

def attach_todo_to_todo(parent_todo_id: int, subtask_id: int):
    """Attach a todo to another todo as a subtask using the Link system."""
    parent = next((t for t in db.todos if t.id == parent_todo_id), None)
    subtask = next((t for t in db.todos if t.id == subtask_id), None)
    
    if parent and subtask:
        db.create_link('todo', parent_todo_id, 'todo', subtask_id)
        print(f"✓ Attached {subtask.title} as subtask of {parent.title}")
    else:
        print(f"✗ Todo not found")

def attach_event_to_goal(event_id: int, goal_id: int):
    """Attach an event to a goal using the Link system."""
    event = next((e for e in db.events if e.id == event_id), None)
    goal = next((g for g in db.goals if g.id == goal_id), None)
    
    if event and goal:
        db.create_link('goal', goal_id, 'event', event_id)
        print(f"✓ Attached {event.title} to goal {goal.title}")
    else:
        print(f"✗ Event or goal not found")

def complete_todo(todo_id: int):
    """Mark a todo as completed."""
    todo = next((t for t in db.todos if t.id == todo_id), None)
    if todo:
        todo.completed = True
        db.save()
        print(f"✓ Completed: {todo.title}")
    else:
        print(f"✗ Todo {todo_id} not found")

def complete_goal(goal_id: int):
    """Mark a goal as completed."""
    goal = next((g for g in db.goals if g.id == goal_id), None)
    if goal:
        goal.completed = True
        db.save()
        print(f"✓ Completed: {goal.title}")
    else:
        print(f"✗ Goal {goal_id} not found")

def list_todos(show_completed: bool = False):
    """List all todos."""
    todos = [t for t in db.todos if t.completed == show_completed]
    if not todos:
        print("No todos found.")
        return
    
    for todo in sorted(todos, key=lambda t: t.priority, reverse=True):
        due_str = f" - Due: {todo.due_date.strftime('%Y-%m-%d')}" if todo.due_date else ""
        priority_symbol = "🔴" * todo.priority if todo.priority >= 4 else "🟡" * todo.priority
        print(f"[{todo.id}] {priority_symbol} {todo.title}{due_str}")
        if todo.description:
            print(f"     {todo.description}")

def list_goals(show_completed: bool = False):
    """List all goals."""
    goals = [g for g in db.goals if g.completed == show_completed]
    if not goals:
        print("No goals found.")
        return
    
    for goal in sorted(goals, key=lambda g: g.priority, reverse=True):
        due_str = f" - Due: {goal.due_date.strftime('%Y-%m-%d')}" if goal.due_date else ""
        priority_symbol = "🔴" * goal.priority if goal.priority >= 4 else "🟡" * goal.priority
        print(f"[{goal.id}] {priority_symbol} {goal.title}{due_str}")

def add_dependent_note(title: str, content: str, parent_type: str, parent_id: int):
    """
    Add a dependent note attached to a parent entity.
    
    Args:
        title: Note title
        content: Note content
        parent_type: 'event', 'todo', 'goal', or 'note'
        parent_id: ID of the parent entity
    """
    try:
        note = db.add_dependent_note(title, content, parent_type, parent_id)
        print(f"✓ Added note: {title} (ID: {note.id}) to {parent_type} {parent_id}")
        return note
    except ValueError as e:
        print(f"✗ Error: {e}")
        return None

def get_dependent_notes(parent_type: str, parent_id: int):
    """Get all dependent notes for a parent entity."""
    notes = db.dependent_notes
    filtered = [n for n in notes if n.parent_type == parent_type and n.parent_id == parent_id]
    
    if not filtered:
        print(f"No notes found for {parent_type} {parent_id}")
        return
    
    print(f"Notes for {parent_type} {parent_id}:")
    for note in filtered:
        print(f"  [{note.id}] {note.title}")
        print(f"      {note.content}")

def delete_dependent_note(note_id: int):
    """Delete a dependent note."""
    success = db.delete_dependent_note(note_id)
    if success:
        print(f"✓ Deleted note {note_id}")
    else:
        print(f"✗ Note {note_id} not found")

if __name__ == "__main__":
    # Example usage
    print("Utility module loaded. Use these functions to manage your data:")
    print("- add_todo, add_goal, add_event")
    print("- complete_todo, complete_goal")
    print("- attach_todo_to_goal, attach_todo_to_todo, attach_event_to_goal")
    print("- list_todos, list_goals")
    print("- add_dependent_note, get_dependent_notes, delete_dependent_note")
