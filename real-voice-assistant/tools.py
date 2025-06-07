"""
Real tool functions that the OpenAI API can call.
These are ACTUAL WORKING functions, not simulations.
"""

from database import db
from datetime import datetime
import json


def save_memory(key: str, value: str) -> dict:
    """Save information to memory."""
    success = db.save_memory(key, value)
    return {
        "success": success,
        "message": (
            f"Memory '{key}' saved successfully"
            if success
            else "Failed to save memory"
        ),
    }


def get_memory(key: str) -> dict:
    """Retrieve information from memory."""
    value = db.get_memory(key)
    if value:
        return {"success": True, "key": key, "value": value}
    return {"success": False, "message": f"No memory found for key '{key}'"}


def list_memories() -> dict:
    """List all stored memories."""
    memories = db.list_memories()
    return {"success": True, "count": len(memories), "memories": memories}


def create_task(title: str, description: str = "") -> dict:
    """Create a new task."""
    task_id = db.create_task(title, description)
    if task_id > 0:
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task created with ID {task_id}",
        }
    return {"success": False, "message": "Failed to create task"}


def list_tasks(status: str = None) -> dict:
    """List all tasks or filter by status."""
    tasks = db.list_tasks(status)
    return {"success": True, "count": len(tasks), "tasks": tasks}


def complete_task(task_id: int) -> dict:
    """Mark a task as completed."""
    success = db.update_task_status(task_id, "completed")
    return {
        "success": success,
        "message": (
            f"Task {task_id} marked as completed"
            if success
            else "Failed to update task"
        ),
    }


def get_current_time() -> dict:
    """Get the current date and time."""
    now = datetime.now()
    return {
        "success": True,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A"),
    }


# Tool definitions for OpenAI function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save information to memory for later retrieval",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The key to store the memory under",
                    },
                    "value": {
                        "type": "string",
                        "description": "The information to remember",
                    },
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory",
            "description": "Retrieve information from memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The key to retrieve",
                    }
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_memories",
            "description": "List all stored memories",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The task title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional task description",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all tasks or filter by status",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending, completed",
                        "enum": ["pending", "completed"],
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "The ID of the task to complete",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# Function map for execution
FUNCTION_MAP = {
    "save_memory": save_memory,
    "get_memory": get_memory,
    "list_memories": list_memories,
    "create_task": create_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "get_current_time": get_current_time,
}


def execute_function(function_name: str, arguments: dict) -> dict:
    """Execute a function by name with arguments."""
    if function_name in FUNCTION_MAP:
        try:
            return FUNCTION_MAP[function_name](**arguments)
        except Exception as e:
            return {
                "success": False,
                "error": f"Function execution failed: {str(e)}",
            }
    return {"success": False, "error": f"Unknown function: {function_name}"}
