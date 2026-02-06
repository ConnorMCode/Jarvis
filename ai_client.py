import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from db import db

load_dotenv()

client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

# Define tools that the AI can use
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_events_this_week",
            "description": "Get all events scheduled for this week",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_events",
            "description": "Get all events in the calendar",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_todos_by_priority",
            "description": "Get todos filtered by priority level (1=low to 5=high) and completion status",
            "parameters": {
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "integer",
                        "description": "Filter by priority level (1-5), omit for all priorities"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Filter by completion status (default: false for incomplete todos)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_todos",
            "description": "Get all todos that are overdue and not yet completed",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_todos",
            "description": "Get todos due within a specified number of days",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look ahead (default: 7)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_todos",
            "description": "Get all incomplete todos, regardless of due date",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals",
            "description": "Get all goals, optionally filtered by completion status",
            "parameters": {
                "type": "object",
                "properties": {
                    "completed": {
                        "type": "boolean",
                        "description": "Filter by completion status (default: false for incomplete goals)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_goal_details",
            "description": "Get detailed information about a specific goal including attached todos and events",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "The ID of the goal to retrieve"
                    }
                },
                "required": ["goal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_notes",
            "description": "Get all notes",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_event",
            "description": "Add a new event to the calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Event title"
                    },
                    "start": {
                        "type": "string",
                        "description": "Event start time in ISO format (e.g., 2026-02-08T14:00:00)"
                    },
                    "end": {
                        "type": "string",
                        "description": "Event end time in ISO format (e.g., 2026-02-08T15:00:00)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the event (optional)"
                    }
                },
                "required": ["title", "start", "end"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "Add a new todo item",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Todo title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Todo description (optional)"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority level 1-5 (1=low, 5=high). Default is 3."
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in ISO format (e.g., 2026-02-15T17:00:00) (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the todo (optional)"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_goal",
            "description": "Add a new goal",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Goal title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Goal description (optional)"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority level 1-5 (1=low, 5=high). Default is 3."
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in ISO format (e.g., 2026-02-28T23:59:59) (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the goal (optional)"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_note",
            "description": "Add a new note",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Note title"
                    },
                    "type": {
                        "type": "string",
                        "description": "Note type (e.g., 'general', 'idea', 'research', 'reminder')"
                    },
                    "content": {
                        "type": "string",
                        "description": "Note content"
                    }
                },
                "required": ["title", "type", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": "Delete a specific event by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "The ID of the event to delete"
                    }
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_events_this_week",
            "description": "Delete all events scheduled for this week",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_todo",
            "description": "Delete a specific todo by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "The ID of the todo to delete"
                    }
                },
                "required": ["todo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_goal",
            "description": "Delete a specific goal by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "The ID of the goal to delete"
                    }
                },
                "required": ["goal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_note",
            "description": "Delete a specific note by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "integer",
                        "description": "The ID of the note to delete"
                    }
                },
                "required": ["note_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_todo",
            "description": "Update a todo's fields (title, description, priority, due date, tags, etc). Preserves all links and notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "The ID of the todo to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "New priority 1-5 (optional)"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "New due date in ISO format (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags (optional)"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Mark as completed/incomplete (optional)"
                    }
                },
                "required": ["todo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_goal",
            "description": "Update a goal's fields (title, description, priority, due date, tags, etc). Preserves all links and notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "The ID of the goal to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "New priority 1-5 (optional)"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "New due date in ISO format (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags (optional)"
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Mark as completed/incomplete (optional)"
                    }
                },
                "required": ["goal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_event",
            "description": "Update an event's fields (title, description, start/end times, tags, etc). Preserves all links and notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "The ID of the event to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)"
                    },
                    "start": {
                        "type": "string",
                        "description": "New start time in ISO format (optional)"
                    },
                    "end": {
                        "type": "string",
                        "description": "New end time in ISO format (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags (optional)"
                    }
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_todo_to_goal",
            "description": "Link a todo to a goal, indicating the todo contributes to the goal",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "The ID of the todo to link"
                    },
                    "goal_id": {
                        "type": "integer",
                        "description": "The ID of the goal"
                    }
                },
                "required": ["todo_id", "goal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_todo_to_todo",
            "description": "Link a todo to another todo as a subtask or related task",
            "parameters": {
                "type": "object",
                "properties": {
                    "parent_todo_id": {
                        "type": "integer",
                        "description": "The ID of the parent todo"
                    },
                    "subtask_id": {
                        "type": "integer",
                        "description": "The ID of the subtask"
                    }
                },
                "required": ["parent_todo_id", "subtask_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_event_to_goal",
            "description": "Link an event to a goal, indicating the event contributes to the goal",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "The ID of the event to link"
                    },
                    "goal_id": {
                        "type": "integer",
                        "description": "The ID of the goal"
                    }
                },
                "required": ["event_id", "goal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_todo_to_event",
            "description": "Link a todo to an event, indicating they are related",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "The ID of the todo"
                    },
                    "event_id": {
                        "type": "integer",
                        "description": "The ID of the event"
                    }
                },
                "required": ["todo_id", "event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_goal_to_goal",
            "description": "Link a goal to another goal as a sub-goal",
            "parameters": {
                "type": "object",
                "properties": {
                    "parent_goal_id": {
                        "type": "integer",
                        "description": "The ID of the parent goal"
                    },
                    "subgoal_id": {
                        "type": "integer",
                        "description": "The ID of the sub-goal"
                    }
                },
                "required": ["parent_goal_id", "subgoal_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_todo_to_note",
            "description": "Link a todo to a note for reference or documentation",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "The ID of the todo"
                    },
                    "note_id": {
                        "type": "integer",
                        "description": "The ID of the note"
                    }
                },
                "required": ["todo_id", "note_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unlink_items",
            "description": "Remove a link between two items",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_type": {
                        "type": "string",
                        "description": "Type of the source item (todo, goal, event, note)"
                    },
                    "from_id": {
                        "type": "integer",
                        "description": "ID of the source item"
                    },
                    "to_type": {
                        "type": "string",
                        "description": "Type of the target item (todo, goal, event, note)"
                    },
                    "to_id": {
                        "type": "integer",
                        "description": "ID of the target item"
                    }
                },
                "required": ["from_type", "from_id", "to_type", "to_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_linked_items",
            "description": "Get all items linked to a specific item",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_type": {
                        "type": "string",
                        "description": "Type of the item (todo, goal, event, note)"
                    },
                    "item_id": {
                        "type": "integer",
                        "description": "ID of the item"
                    }
                },
                "required": ["item_type", "item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_dependent_note",
            "description": "Add a note attached to an event, todo, goal, or another note. The note will be deleted if the parent is deleted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Note title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Note content"
                    },
                    "parent_type": {
                        "type": "string",
                        "description": "Type of parent item (event, todo, goal, or note)"
                    },
                    "parent_id": {
                        "type": "integer",
                        "description": "ID of the parent item"
                    }
                },
                "required": ["title", "content", "parent_type", "parent_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dependent_notes",
            "description": "Get dependent notes for a specific item",
            "parameters": {
                "type": "object",
                "properties": {
                    "parent_type": {
                        "type": "string",
                        "description": "Type of parent item (event, todo, goal, note)"
                    },
                    "parent_id": {
                        "type": "integer",
                        "description": "ID of the parent item"
                    }
                },
                "required": ["parent_type", "parent_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_dependent_note",
            "description": "Delete a dependent note by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "integer",
                        "description": "The ID of the dependent note to delete"
                    }
                },
                "required": ["note_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_todos_by_title",
            "description": "Search for todos by title (partial match, case-insensitive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title or part of title to search for"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_goals_by_title",
            "description": "Search for goals by title (partial match, case-insensitive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title or part of title to search for"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_events_by_title",
            "description": "Search for events by title (partial match, case-insensitive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title or part of title to search for"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_todos_by_tag",
            "description": "Search todos by tag (PRIMARY search method). Returns all todos with the specified tag.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag to search for (case-insensitive, e.g., 'apartment', 'rent', 'urgent')"
                    }
                },
                "required": ["tag"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_goals_by_tag",
            "description": "Search goals by tag (PRIMARY search method). Returns all goals with the specified tag.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag to search for (case-insensitive, e.g., 'apartment', 'rent', 'urgent')"
                    }
                },
                "required": ["tag"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_events_by_tag",
            "description": "Search events by tag (PRIMARY search method). Returns all events with the specified tag.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag to search for (case-insensitive, e.g., 'apartment', 'rent', 'urgent')"
                    }
                },
                "required": ["tag"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_all_by_tag",
            "description": "Search todos, goals, and events by tag simultaneously (PRIMARY search method). Most efficient way to find all items related to a topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag to search for across all item types (case-insensitive, e.g., 'apartment', 'rent', 'urgent')"
                    }
                },
                "required": ["tag"]
            }
        }
    }
]

def execute_function(function_name: str, function_args: dict, debug: bool = False) -> str:
    """Execute a function and return the result as a string."""
    if debug:
        print(f"\n  [DEBUG] Executing function: {function_name}")
        print(f"  [DEBUG] Arguments: {json.dumps(function_args, indent=2)}")
    
    if function_name == "get_events_this_week":
        result = db.get_events_this_week()
    elif function_name == "get_all_events":
        result = db.get_all_events()
    elif function_name == "get_todos_by_priority":
        priority = function_args.get("priority")
        completed = function_args.get("completed", False)
        result = db.get_todos_by_priority(priority, completed)
    elif function_name == "get_overdue_todos":
        result = db.get_overdue_todos()
    elif function_name == "get_upcoming_todos":
        days = function_args.get("days", 7)
        result = db.get_upcoming_todos(days)
    elif function_name == "get_all_todos":
        result = db.get_all_todos()
    elif function_name == "get_goals":
        completed = function_args.get("completed", False)
        result = db.get_goals(completed)
    elif function_name == "get_goal_details":
        goal_id = function_args.get("goal_id")
        result = db.get_goal_details(goal_id)
    elif function_name == "get_notes":
        result = db.get_notes()
    elif function_name == "add_event":
        try:
            start = function_args.get("start")
            end = function_args.get("end")
            start_dt = datetime.fromisoformat(start) if start else None
            end_dt = datetime.fromisoformat(end) if end else None
            result = db.add_event(
                title=function_args.get("title"),
                start=start_dt,
                end=end_dt,
                description=function_args.get("description", ""),
                tags=function_args.get("tags", [])
            )
            result = {"success": True, "event": db._serialize_event(result), "message": f"Event '{function_args.get('title')}' added successfully"}
        except ValueError as e:
            result = {"success": False, "message": f"Invalid date format: {str(e)}. Please use ISO format (e.g., 2026-02-10T14:00:00)"}
    elif function_name == "add_todo":
        try:
            due_date = function_args.get("due_date")
            due_dt = datetime.fromisoformat(due_date) if due_date else None
            result = db.add_todo(
                title=function_args.get("title"),
                description=function_args.get("description", ""),
                priority=function_args.get("priority", 3),
                due_date=due_dt,
                tags=function_args.get("tags", [])
            )
            result = {"success": True, "todo": db._serialize_todo(result), "message": f"Todo '{function_args.get('title')}' added successfully"}
        except ValueError as e:
            result = {"success": False, "message": f"Invalid date format: {str(e)}. Please use ISO format (e.g., 2026-02-15T17:00:00)"}
    elif function_name == "add_goal":
        try:
            due_date = function_args.get("due_date")
            due_dt = datetime.fromisoformat(due_date) if due_date else None
            result = db.add_goal(
                title=function_args.get("title"),
                description=function_args.get("description", ""),
                priority=function_args.get("priority", 3),
                due_date=due_dt,
                tags=function_args.get("tags", [])
            )
            result = {"success": True, "goal": db._serialize_goal(result), "message": f"Goal '{function_args.get('title')}' added successfully"}
        except ValueError as e:
            result = {"success": False, "message": f"Invalid date format: {str(e)}. Please use ISO format (e.g., 2026-02-28T23:59:59)"}
    elif function_name == "add_note":
        result = db.add_note(
            title=function_args.get("title"),
            type=function_args.get("type"),
            content=function_args.get("content")
        )
        result = {"success": True, "note": db._serialize_note(result), "message": f"Note '{function_args.get('title')}' added successfully"}
    elif function_name == "delete_event":
        event_id = function_args.get("event_id")
        success = db.delete_event(event_id)
        if success:
            result = {"success": True, "message": f"Event {event_id} deleted successfully"}
        else:
            result = {"success": False, "message": f"Event {event_id} not found"}
    elif function_name == "delete_events_this_week":
        count = db.delete_events_this_week()
        result = {"success": True, "message": f"Deleted {count} event(s) from this week's schedule"}
    elif function_name == "delete_todo":
        todo_id = function_args.get("todo_id")
        success = db.delete_todo(todo_id)
        if success:
            result = {"success": True, "message": f"Todo {todo_id} deleted successfully"}
        else:
            result = {"success": False, "message": f"Todo {todo_id} not found"}
    elif function_name == "delete_goal":
        goal_id = function_args.get("goal_id")
        success = db.delete_goal(goal_id)
        if success:
            result = {"success": True, "message": f"Goal {goal_id} deleted successfully"}
        else:
            result = {"success": False, "message": f"Goal {goal_id} not found"}
    elif function_name == "delete_note":
        note_id = function_args.get("note_id")
        success = db.delete_note(note_id)
        if success:
            result = {"success": True, "message": f"Note {note_id} deleted successfully"}
        else:
            result = {"success": False, "message": f"Note {note_id} not found"}
    elif function_name == "update_todo":
        try:
            todo_id = function_args.get("todo_id")
            due_date = function_args.get("due_date")
            due_dt = datetime.fromisoformat(due_date) if due_date else None
            updated_todo = db.update_todo(
                todo_id=todo_id,
                title=function_args.get("title"),
                description=function_args.get("description"),
                priority=function_args.get("priority"),
                due_date=due_dt,
                tags=function_args.get("tags"),
                completed=function_args.get("completed")
            )
            if updated_todo:
                result = {"success": True, "todo": updated_todo, "message": f"Todo {todo_id} updated successfully"}
            else:
                result = {"success": False, "message": f"Todo {todo_id} not found"}
        except ValueError as e:
            result = {"success": False, "message": f"Invalid date format: {str(e)}. Please use ISO format (e.g., 2026-02-15T17:00:00)"}
    elif function_name == "update_goal":
        try:
            goal_id = function_args.get("goal_id")
            due_date = function_args.get("due_date")
            due_dt = datetime.fromisoformat(due_date) if due_date else None
            updated_goal = db.update_goal(
                goal_id=goal_id,
                title=function_args.get("title"),
                description=function_args.get("description"),
                priority=function_args.get("priority"),
                due_date=due_dt,
                tags=function_args.get("tags"),
                completed=function_args.get("completed")
            )
            if updated_goal:
                result = {"success": True, "goal": updated_goal, "message": f"Goal {goal_id} updated successfully"}
            else:
                result = {"success": False, "message": f"Goal {goal_id} not found"}
        except ValueError as e:
            result = {"success": False, "message": f"Invalid date format: {str(e)}. Please use ISO format (e.g., 2026-02-28T23:59:59)"}
    elif function_name == "update_event":
        try:
            event_id = function_args.get("event_id")
            start = function_args.get("start")
            end = function_args.get("end")
            start_dt = datetime.fromisoformat(start) if start else None
            end_dt = datetime.fromisoformat(end) if end else None
            updated_event = db.update_event(
                event_id=event_id,
                title=function_args.get("title"),
                description=function_args.get("description"),
                start=start_dt,
                end=end_dt,
                tags=function_args.get("tags")
            )
            if updated_event:
                result = {"success": True, "event": updated_event, "message": f"Event {event_id} updated successfully"}
            else:
                result = {"success": False, "message": f"Event {event_id} not found"}
        except ValueError as e:
            result = {"success": False, "message": f"Invalid date format: {str(e)}. Please use ISO format (e.g., 2026-02-10T14:00:00)"}
    elif function_name == "link_todo_to_goal":
        todo_id = function_args.get("todo_id")
        goal_id = function_args.get("goal_id")
        todo = next((t for t in db.todos if t.id == todo_id), None)
        goal = next((g for g in db.goals if g.id == goal_id), None)
        if todo and goal:
            db.create_link('goal', goal_id, 'todo', todo_id)
            result = {"success": True, "message": f"Linked todo '{todo.title}' to goal '{goal.title}'"}
        else:
            result = {"success": False, "message": f"Todo {todo_id} or Goal {goal_id} not found"}
    elif function_name == "link_todo_to_todo":
        parent_todo_id = function_args.get("parent_todo_id")
        subtask_id = function_args.get("subtask_id")
        parent = next((t for t in db.todos if t.id == parent_todo_id), None)
        subtask = next((t for t in db.todos if t.id == subtask_id), None)
        if parent and subtask:
            db.create_link('todo', parent_todo_id, 'todo', subtask_id)
            result = {"success": True, "message": f"Linked '{subtask.title}' as subtask of '{parent.title}'"}
        else:
            result = {"success": False, "message": f"Todo {parent_todo_id} or Todo {subtask_id} not found"}
    elif function_name == "link_event_to_goal":
        event_id = function_args.get("event_id")
        goal_id = function_args.get("goal_id")
        event = next((e for e in db.events if e.id == event_id), None)
        goal = next((g for g in db.goals if g.id == goal_id), None)
        if event and goal:
            db.create_link('goal', goal_id, 'event', event_id)
            result = {"success": True, "message": f"Linked event '{event.title}' to goal '{goal.title}'"}
        else:
            result = {"success": False, "message": f"Event {event_id} or Goal {goal_id} not found"}
    elif function_name == "link_todo_to_event":
        todo_id = function_args.get("todo_id")
        event_id = function_args.get("event_id")
        todo = next((t for t in db.todos if t.id == todo_id), None)
        event = next((e for e in db.events if e.id == event_id), None)
        if todo and event:
            db.create_link('todo', todo_id, 'event', event_id)
            result = {"success": True, "message": f"Linked todo '{todo.title}' to event '{event.title}'"}
        else:
            result = {"success": False, "message": f"Todo {todo_id} or Event {event_id} not found"}
    elif function_name == "link_goal_to_goal":
        parent_goal_id = function_args.get("parent_goal_id")
        subgoal_id = function_args.get("subgoal_id")
        parent_goal = next((g for g in db.goals if g.id == parent_goal_id), None)
        subgoal = next((g for g in db.goals if g.id == subgoal_id), None)
        if parent_goal and subgoal:
            db.create_link('goal', parent_goal_id, 'goal', subgoal_id)
            result = {"success": True, "message": f"Linked '{subgoal.title}' as sub-goal of '{parent_goal.title}'"}
        else:
            result = {"success": False, "message": f"Goal {parent_goal_id} or Goal {subgoal_id} not found"}
    elif function_name == "link_todo_to_note":
        todo_id = function_args.get("todo_id")
        note_id = function_args.get("note_id")
        todo = next((t for t in db.todos if t.id == todo_id), None)
        note = next((n for n in db.notes if n.id == note_id), None)
        if todo and note:
            db.create_link('todo', todo_id, 'note', note_id)
            result = {"success": True, "message": f"Linked todo '{todo.title}' to note '{note.title}'"}
        else:
            result = {"success": False, "message": f"Todo {todo_id} or Note {note_id} not found"}
    elif function_name == "unlink_items":
        from_type = function_args.get("from_type")
        from_id = function_args.get("from_id")
        to_type = function_args.get("to_type")
        to_id = function_args.get("to_id")
        # Find the link
        link = next((l for l in db.links if l.from_type == from_type and l.from_id == from_id 
                     and l.to_type == to_type and l.to_id == to_id), None)
        if link:
            success = db.delete_link(link.id)
            if success:
                result = {"success": True, "message": f"Unlinked {from_type} {from_id} from {to_type} {to_id}"}
            else:
                result = {"success": False, "message": "Error removing link"}
        else:
            result = {"success": False, "message": f"No link found between {from_type} {from_id} and {to_type} {to_id}"}
    elif function_name == "get_linked_items":
        item_type = function_args.get("item_type")
        item_id = function_args.get("item_id")
        
        # Create lookup dictionaries for O(1) access instead of O(n)
        todo_map = {t.id: t for t in db.todos}
        goal_map = {g.id: g for g in db.goals}
        event_map = {e.id: e for e in db.events}
        note_map = {n.id: n for n in db.notes}
        
        # Get all outgoing links from this item
        outgoing = db.get_links_from(item_type, item_id)
        
        # Get all incoming links to this item
        incoming = db.get_links_to(item_type, item_id)
        
        # Serialize the results
        result_outgoing = []
        for link in outgoing:
            item = None
            if link.to_type == 'todo':
                item = todo_map.get(link.to_id)
            elif link.to_type == 'goal':
                item = goal_map.get(link.to_id)
            elif link.to_type == 'event':
                item = event_map.get(link.to_id)
            elif link.to_type == 'note':
                item = note_map.get(link.to_id)
            
            if item:
                result_outgoing.append({
                    "relationship": f"{item_type} -> {link.to_type}",
                    "type": link.to_type,
                    "id": link.to_id,
                    "title": getattr(item, 'title', 'N/A')
                })
        
        result_incoming = []
        for link in incoming:
            item = None
            if link.from_type == 'todo':
                item = todo_map.get(link.from_id)
            elif link.from_type == 'goal':
                item = goal_map.get(link.from_id)
            elif link.from_type == 'event':
                item = event_map.get(link.from_id)
            elif link.from_type == 'note':
                item = note_map.get(link.from_id)
            
            if item:
                result_incoming.append({
                    "relationship": f"{link.from_type} -> {item_type}",
                    "type": link.from_type,
                    "id": link.from_id,
                    "title": getattr(item, 'title', 'N/A')
                })
        
        result = {
            "item": {
                "type": item_type,
                "id": item_id
            },
            "links_from": result_outgoing,
            "links_to": result_incoming
        }
    elif function_name == "add_dependent_note":
        title = function_args.get("title")
        content = function_args.get("content")
        parent_type = function_args.get("parent_type")
        parent_id = function_args.get("parent_id")
        # Try to attach the dependent note. If the parent id is invalid, return candidate matches
        # so the caller (AI) can confirm the correct id before retrying.
        try:
            note = db.add_dependent_note(title, content, parent_type, parent_id)
            result = {"success": True, "note": {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "parent_type": note.parent_type,
                "parent_id": note.parent_id
            }, "message": f"Note '{title}' attached to {parent_type} {parent_id}"}
        except ValueError as e:
            # Parent not found — gather candidate matches by tag first (preferred),
            # then fall back to title-based matches. Return candidates so the caller
            # (AI) can confirm the correct id before retrying.
            candidates = {}

            # Build simple token candidates from title/content to use as tag searches.
            tag_tokens = []
            def extract_tokens(text: str):
                tokens = []
                for part in text.replace('/', ' ').replace('-', ' ').split():
                    t = ''.join(ch for ch in part if ch.isalnum()).lower()
                    if len(t) >= 3 and not t.isnumeric():
                        tokens.append(t)
                return tokens

            if title:
                tag_tokens.extend(extract_tokens(title))
            if content:
                tag_tokens.extend(extract_tokens(content))

            # Deduplicate while preserving order, limit to first 6 tokens
            seen_tokens = []
            for tk in tag_tokens:
                if tk not in seen_tokens:
                    seen_tokens.append(tk)
            tag_tokens = seen_tokens[:6]

            # Try tag-based searches across all types (preferred)
            tag_matches = {}
            try:
                for tk in tag_tokens:
                    res = db.search_all_by_tag(tk)
                    # Only include tokens that returned something
                    if any(res.values()):
                        tag_matches[tk] = res
            except Exception:
                tag_matches = {}

            # If no tag matches found, fall back to title-based searches using short phrases
            title_matches = {}
            if not tag_matches:
                # Build short title phrases (title and first sentence fragment)
                search_terms = []
                if title:
                    search_terms.append(title)
                if content:
                    first_sentence = content.split('.', 1)[0]
                    if first_sentence and first_sentence not in search_terms:
                        search_terms.append(first_sentence[:40])

                try:
                    if parent_type == 'todo':
                        matches = []
                        for t in search_terms:
                            matches.extend(db.search_todos_by_title(t))
                        title_matches['todos_by_title'] = matches
                    elif parent_type == 'goal':
                        matches = []
                        for t in search_terms:
                            matches.extend(db.search_goals_by_title(t))
                        title_matches['goals_by_title'] = matches
                    elif parent_type == 'event':
                        matches = []
                        for t in search_terms:
                            matches.extend(db.search_events_by_title(t))
                        title_matches['events_by_title'] = matches
                    else:
                        matches_t = []
                        matches_g = []
                        matches_e = []
                        for t in search_terms:
                            matches_t.extend(db.search_todos_by_title(t))
                            matches_g.extend(db.search_goals_by_title(t))
                            matches_e.extend(db.search_events_by_title(t))
                        title_matches = {
                            'todos_by_title': matches_t,
                            'goals_by_title': matches_g,
                            'events_by_title': matches_e
                        }
                except Exception:
                    title_matches = {}

            # Combine candidates preferring tag matches
            if tag_matches:
                candidates['by_tag'] = tag_matches
            if title_matches:
                candidates['by_title'] = title_matches

            result = {
                "success": False,
                "message": str(e),
                "hint": "Parent id not found. Confirm the correct parent id before retrying, or pick from candidates.",
                "candidates": candidates
            }
    elif function_name == "get_dependent_notes":
        parent_type = function_args.get("parent_type")
        parent_id = function_args.get("parent_id")
        notes = db.get_dependent_notes(parent_type, parent_id)
        result = {"notes": notes}
    elif function_name == "delete_dependent_note":
        note_id = function_args.get("note_id")
        success = db.delete_dependent_note(note_id)
        if success:
            result = {"success": True, "message": f"Dependent note {note_id} deleted successfully"}
        else:
            result = {"success": False, "message": f"Dependent note {note_id} not found"}
    elif function_name == "search_todos_by_title":
        title = function_args.get("title")
        result = db.search_todos_by_title(title)
    elif function_name == "search_goals_by_title":
        title = function_args.get("title")
        result = db.search_goals_by_title(title)
    elif function_name == "search_events_by_title":
        title = function_args.get("title")
        result = db.search_events_by_title(title)
    elif function_name == "search_todos_by_tag":
        tag = function_args.get("tag")
        result = db.search_todos_by_tag(tag)
    elif function_name == "search_goals_by_tag":
        tag = function_args.get("tag")
        result = db.search_goals_by_tag(tag)
    elif function_name == "search_events_by_tag":
        tag = function_args.get("tag")
        result = db.search_events_by_tag(tag)
    elif function_name == "search_all_by_tag":
        tag = function_args.get("tag")
        result = db.search_all_by_tag(tag)
    else:
        result = {"error": f"Unknown function: {function_name}"}
    
    if debug:
        result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
        print(f"  [DEBUG] Result: {result_preview}")
    
    return json.dumps(result, default=str)

def ask_ai(user_input: str, debug: bool = False, messages_history: list = None) -> tuple[str, dict]:
    """
    Sends a user message to GPT with function calling capabilities.
    The AI can call functions to access specific data as needed.
    Supports multi-turn conversations for clarifying questions.
    
    Args:
        user_input: The user's message
        debug: Whether to print debug information
        messages_history: Optional list of previous conversation messages to provide context
    
    Returns:
        Tuple of (AI response, usage info)
    """
    if debug:
        print(f"\n[DEBUG] User query: {user_input}")
        print("[DEBUG] Sending to AI with available tools...")
    
    # Get current date for context
    today = datetime.now().strftime("%A, %B %d, %Y")
    
    # Comprehensive system prompt - sent with every request to maintain consistency
    system_prompt = f"""You are Jarvis, an intelligent personal assistant specializing in task management, goal tracking, and calendar organization.

Your role is to help users manage their:
- Events and calendar
- To-do items and tasks
- Goals and objectives
- Notes and information

Guidelines:
1. Today's date is {today}. Use this to interpret relative dates like 'tomorrow', 'next week', 'this weekend', etc.
2. When users provide incomplete information that is ambiguous or unclear, ask clarifying questions instead of making assumptions. Otherwise, attempt to fulfill the request without asking unnecessary questions.
3. Be concise and friendly in your responses.
4. When creating items (events, todos, goals, notes), confirm what you've created with a brief summary.
5. Use the available tools to query, add, or delete items as requested.
6. Maintain context from the entire conversation to make informed decisions.
7. If a user asks about their schedule, goals, or tasks, query the database first to provide accurate information.
8. IMPORTANT: Use tag-based search as your PRIMARY search method. When looking for items related to a topic (e.g., 'apartment', 'rent', 'work'), use search_all_by_tag, search_todos_by_tag, search_goals_by_tag, or search_events_by_tag. This is more reliable than searching by title. Example: User says "find my apartment tasks" → Use search_all_by_tag("apartment") instead of searching by title.
9. IMPORTANT: Dependent notes are automatically included in all query results for events, todos, and goals (they appear in a 'notes' field). When presenting these items to the user, actively look for and mention any attached notes if they provide relevant context or important information. Integrate note information naturally into your response.
10. CRITICAL: When a user asks to modify an item (e.g., "change the due date", "add a tag", "update priority"), ALWAYS use the update_todo, update_goal, or update_event functions. NEVER delete and recreate items, as this breaks all links and relationships. The update functions preserve all connections while changing only the specified fields.
11. WHEN REFERENCING ITEMS: If the user refers to an item by name, description, or natural language (not by explicit ID), DO NOT call `add_dependent_note` or `update_*` directly. First call the appropriate search tool(s) (`search_all_by_tag`, `search_todos_by_tag`, `search_goals_by_tag`, `search_events_by_tag`, or title-based searches) to find candidate items, confirm the correct `id` with the user if ambiguous, then call the add/update tool with the confirmed numeric `id`.

Ethos:
- Your goal is to assist users in staying organized, productive, and on top of their commitments.
- In this spirit, feel free to make suggestions to improve their schedule, prioritize tasks, or remind them of important deadlines."""
    
    # Initialize messages with system context
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add previous conversation history if provided
    if messages_history:
        messages.extend(messages_history)
    
    # Add the current user message
    messages.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    
    if debug:
        print(f"[DEBUG] Initial response finish_reason: {response.choices[0].finish_reason}")
    
    # Process tool calls in a loop until the AI finishes
    while response.choices[0].finish_reason == "tool_calls":
        assistant_message = response.choices[0].message
        
        if debug:
            print(f"[DEBUG] AI decided to call {len(assistant_message.tool_calls)} function(s):")
            for tool_call in assistant_message.tool_calls:
                print(f"  - {tool_call.function.name}")
        
        # Append the assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })
        
        # Process each tool call and add results
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            function_result = execute_function(function_name, function_args, debug=debug)
            
            # Add tool result as a separate message
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_result
            })
        
        if debug:
            print("[DEBUG] Requesting AI response with tool results...")
        
        # Get next response from AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        if debug:
            print(f"[DEBUG] Response finish_reason: {response.choices[0].finish_reason}")
    
    final_response = response.choices[0].message.content
    
    if debug:
        print(f"\n[DEBUG] AI finished. Final response length: {len(final_response)} characters")
        print(f"[DEBUG] Tokens used - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}")
    
    return final_response, response.usage
