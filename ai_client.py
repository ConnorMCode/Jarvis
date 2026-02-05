import os
import json
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
    elif function_name == "get_goals":
        completed = function_args.get("completed", False)
        result = db.get_goals(completed)
    elif function_name == "get_goal_details":
        goal_id = function_args.get("goal_id")
        result = db.get_goal_details(goal_id)
    elif function_name == "get_notes":
        result = db.get_notes()
    else:
        result = {"error": f"Unknown function: {function_name}"}
    
    if debug:
        result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
        print(f"  [DEBUG] Result: {result_preview}")
    
    return json.dumps(result, default=str)

def ask_ai(user_input: str, debug: bool = False) -> tuple[str, dict]:
    """
    Sends a user message to GPT with function calling capabilities.
    The AI can call functions to access specific data as needed.
    Returns AI message and usage info.
    """
    if debug:
        print(f"\n[DEBUG] User query: {user_input}")
        print("[DEBUG] Sending to AI with available tools...")
    
    messages = [
        {"role": "user", "content": user_input}
    ]
    
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
