"""
Tool definitions and implementations for the Realtime Voice Assistant.
Production-ready tool system with comprehensive functionality.
"""

import asyncio
import logging
import json
import subprocess
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import uuid

from database import memory_repo, task_repo, session_repo
from config import settings


logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing and executing tools."""
    
    def __init__(self):
        self.tools = {}
        self.tool_definitions = {}
        
    def register_tool(self, name: str, function, definition: Dict[str, Any]):
        """Register a tool with its function and OpenAI definition."""
        self.tools[name] = function
        self.tool_definitions[name] = definition
        logger.info(f"Registered tool: {name}")
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for OpenAI API."""
        return list(self.tool_definitions.values())
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool_function = self.tools[name]
        
        try:
            if asyncio.iscoroutinefunction(tool_function):
                return await tool_function(**kwargs)
            else:
                return tool_function(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise


# Global tool registry
tool_registry = ToolRegistry()


# Memory Management Tools
async def create_memory(user_id: str, key: str, content: Any, memory_type: str = "short_term", 
                       category: Optional[str] = None, importance: float = 0.5) -> Dict[str, Any]:
    """Create a new memory entry."""
    try:
        if isinstance(content, str):
            content_dict = {"text": content}
        elif isinstance(content, dict):
            content_dict = content
        else:
            content_dict = {"data": str(content)}
        
        memory = await memory_repo.create_memory(
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            content=content_dict,
            category=category,
            importance_score=importance
        )
        
        return {
            "success": True,
            "memory_id": str(memory.id),
            "message": f"Memory '{key}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        return {"success": False, "error": str(e)}


async def get_memory(user_id: str, key: str) -> Dict[str, Any]:
    """Retrieve a memory entry."""
    try:
        memory = await memory_repo.get_memory(user_id, key)
        
        if not memory:
            return {"success": False, "error": "Memory not found"}
        
        return {
            "success": True,
            "memory": memory.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving memory: {e}")
        return {"success": False, "error": str(e)}


async def create_task(user_id: str, title: str, description: Optional[str] = None,
                     category: Optional[str] = None, priority: str = "medium",
                     due_date: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a new task."""
    try:
        task_data = {
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "tags": tags or []
        }
        
        if due_date:
            try:
                task_data["due_date"] = datetime.fromisoformat(due_date)
            except ValueError:
                return {"success": False, "error": "Invalid due_date format. Use ISO format: YYYY-MM-DDTHH:MM:SS"}
        
        task = await task_repo.create_task(user_id=user_id, **task_data)
        
        return {
            "success": True,
            "task_id": str(task.id),
            "task": task.to_dict(),
            "message": f"Task '{title}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return {"success": False, "error": str(e)}


async def list_tasks(user_id: str, status: Optional[str] = None, 
                    category: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """List user tasks with filters."""
    try:
        tasks = await task_repo.get_user_tasks(
            user_id=user_id,
            status=status,
            limit=limit
        )
        
        # Filter by category if specified
        if category:
            tasks = [task for task in tasks if task.category == category]
        
        return {
            "success": True,
            "tasks": [task.to_dict() for task in tasks],
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return {"success": False, "error": str(e)}


async def get_current_time() -> Dict[str, Any]:
    """Get current time and date information."""
    try:
        now = datetime.now()
        
        return {
            "success": True,
            "current_time": {
                "iso": now.isoformat(),
                "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "weekday": now.strftime("%A"),
                "timestamp": int(now.timestamp())
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        return {"success": False, "error": str(e)}


# Register all tools
def register_all_tools():
    """Register all available tools with their definitions."""
    
    # Memory tools
    tool_registry.register_tool("create_memory", create_memory, {
        "type": "function",
        "function": {
            "name": "create_memory",
            "description": "Create a new memory entry for storing information",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "key": {"type": "string", "description": "Unique key for the memory"},
                    "content": {"type": "string", "description": "Content to store"},
                    "memory_type": {"type": "string", "enum": ["short_term", "long_term", "episodic", "semantic"], "default": "short_term"},
                    "category": {"type": "string", "description": "Memory category"},
                    "importance": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5}
                },
                "required": ["user_id", "key", "content"]
            }
        }
    })
    
    tool_registry.register_tool("get_memory", get_memory, {
        "type": "function",
        "function": {
            "name": "get_memory",
            "description": "Retrieve a memory entry by key",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "key": {"type": "string", "description": "Memory key to retrieve"}
                },
                "required": ["user_id", "key"]
            }
        }
    })
    
    # Task tools
    tool_registry.register_tool("create_task", create_task, {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "category": {"type": "string", "description": "Task category"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "default": "medium"},
                    "due_date": {"type": "string", "description": "Due date in ISO format"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["user_id", "title"]
            }
        }
    })
    
    tool_registry.register_tool("list_tasks", list_tasks, {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List user tasks with optional filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled", "on_hold"]},
                    "category": {"type": "string", "description": "Task category"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}
                },
                "required": ["user_id"]
            }
        }
    })
    
    tool_registry.register_tool("get_current_time", get_current_time, {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get current time and date information",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })
    
    logger.info(f"Registered {len(tool_registry.tools)} tools")


# Initialize tools on module import
register_all_tools()
