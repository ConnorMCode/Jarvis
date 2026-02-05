# Jarvis - AI-Powered Notes, Tasks & Calendar Assistant

A sophisticated personal assistant that combines notes, to-do lists, goals, and calendar events with an AI interface. Uses OpenAI's function calling to intelligently fetch only the data needed for each query.

## Features

### Data Types
- **Notes**: Simple text notes with title and content
- **To-Do Items**: Task items with priorities (1-5), due dates, time frames, and tags. Can be attached to goals or other to-do items as sub-tasks
- **Goals**: High-level objectives with attached to-do items and events. Can have sub-goals
- **Events**: Calendar events that can be attached to specific goals
- **Relationships**: Complex attachment system connecting todos to goals, events to goals, and todos as hierarchical sub-tasks

### AI Integration
The AI assistant uses **OpenAI function calling** to:
- Query your calendar for events this week or all events
- Check to-do items filtered by priority or completion status
- Find overdue tasks
- View upcoming deadlines
- Explore goals and their attached tasks/events
- Access your notes
- Only fetch the data relevant to your query

### Data Storage
- Local JSON file (`db.json`) for current storage
- Database layer (`db.py`) designed for future migration to SQL or other systems
- Automatic serialization/deserialization of datetime objects

## Project Structure

```
├── run.py               # GUI launcher (default)
├── main.py              # CLI entry point
├── gui.py               # GUI interface (Tkinter)
├── ai_client.py         # OpenAI integration with function calling
├── db.py                # Database layer with JSON storage & query functions
├── data.py              # Data model definitions (Note, ToDo, Goal, Event)
├── utils.py             # Utility functions for data management
├── db.json              # Local data storage (JSON)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Copy `.env.example` to `.env` and add your OpenAI API key:
```bash
cp .env.example .env
```

Then edit `.env` and add your API key:
```
OPEN_API_KEY=your_openai_api_key_here
```

Get your key from: https://platform.openai.com/account/api-keys

### 3. Run the Application

**GUI Mode (Default):**
```bash
python run.py
```

**CLI Mode with Debug:**
```bash
python main.py --debug
# or
python main.py -d
```

**CLI Mode Normal:**
```bash
python main.py
```

### 4. Using the Application

#### GUI Mode
- Launch with `python run.py`
- Type your message in the text entry field at the bottom
- Press Enter or click "Send" to submit
- Click the "Debug: OFF/ON" button to toggle debug mode
- View all responses in the chat area above

#### CLI Mode
- Type your natural language queries at the `>` prompt
- Type `debug` to toggle debug mode (shows AI reasoning)
- Type `quit` or `exit` to exit

### 5. Chat with the AI
```
> What do I have on my calendar this week?
> Show me my high-priority to-dos
> What are my goals and their progress?
> Tell me about the "Launch v2.0 release" goal
```

## Data Management

### Using the Interactive Chat
Simply ask the AI naturally:
- "What events do I have coming up?"
- "Show me overdue tasks"
- "Tell me about my fitness goal"

### Using Utilities (Python)
You can also manage data programmatically using `utils.py`:

```python
from utils import add_todo, add_goal, complete_todo, attach_todo_to_goal

# Add a new to-do
add_todo(
    title="Implement API endpoint",
    description="Create /api/v2/users endpoint",
    priority=5,
    due_date="2026-02-10T17:00:00",
    attached_to_goal_id=1,
    tags=["work", "api"]
)

# Add a goal
goal = add_goal(
    title="Complete redesign",
    priority=4,
    due_date="2026-03-31T23:59:59",
    tags=["design"]
)

# Complete a task
complete_todo(todo_id=1)

# Attach a todo to a goal
attach_todo_to_goal(todo_id=1, goal_id=1)

# List items
list_todos()
list_goals()
```

## API Functions (Available to AI)

The AI can call these functions automatically:

- **`get_events_this_week()`** - Get all events for the current week
- **`get_all_events()`** - Get all events
- **`get_todos_by_priority(priority, completed)`** - Filter todos by priority and status
- **`get_overdue_todos()`** - Get incomplete todos past their due date
- **`get_upcoming_todos(days)`** - Get todos due within N days
- **`get_goals(completed)`** - Get goals by completion status
- **`get_goal_details(goal_id)`** - Get detailed goal info with attached todos and events
- **`get_notes()`** - Get all notes

## Data Model Examples

### To-Do Item
```python
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive README and API docs",
  "priority": 4,  # 1-5 scale
  "due_date": "2026-02-10T17:00:00",
  "start_date": "2026-02-05T09:00:00",
  "completed": false,
  "attached_to_goal_id": 1,  # Parent goal
  "attached_to_todo_id": null,  # Parent todo (for sub-tasks)
  "tags": ["work", "documentation"]
}
```

### Goal
```python
{
  "id": 1,
  "title": "Launch v2.0 release",
  "description": "Complete all features and documentation",
  "priority": 5,
  "due_date": "2026-02-28T17:00:00",
  "completed": false,
  "attached_todo_ids": [1, 2, 3],  # Direct todos
  "attached_goal_ids": [],  # Sub-goals
  "attached_event_ids": [1, 2],  # Events tied to this goal
  "tags": ["work", "milestone"]
}
```

## Future Enhancements

- [ ] Migrate from JSON to SQL database (PostgreSQL/SQLite)
- [ ] Web interface / dashboard
- [ ] Additional AI functions (create/edit items via AI conversation)
- [ ] Recurring todos and events
- [ ] Time tracking for todos
- [ ] Analytics and insights about productivity
- [ ] Mobile app synchronization
- [ ] Collaboration features for shared goals
- [ ] Export/import functionality

## Technical Notes

### Function Calling Implementation
The AI uses OpenAI's tool calling feature to request data on-demand. This architecture has several advantages:

1. **Efficiency**: Only relevant data is fetched for each query
2. **Scalability**: As data grows, the AI doesn't get slower
3. **Flexibility**: Easy to add new query functions without changing core AI logic
4. **Context-aware**: The AI decides what data it needs based on the question

### Data Serialization
The database layer handles serialization of Python objects to JSON:
- DateTime objects are converted to ISO format strings
- Relationships are preserved via IDs
- Future database migration only requires changing the Database class

## License

[Your License Here]
