"""
Simple SQLite database for storing memories and tasks.
THIS IS REAL - IT ACTUALLY WORKS.
"""

import sqlite3
import os
from typing import List, Dict, Optional

# Ensure the SQLite database is created next to this file so all components
# (CLI assistant and Flask dashboard) share the same data regardless of the
# current working directory.
DB_PATH = os.path.join(os.path.dirname(__file__), "voice_assistant.db")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        """Initialize the database connection."""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create memories table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create tasks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def save_memory(self, key: str, value: str) -> bool:
        """Save a memory to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO memories (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def get_memory(self, key: str) -> Optional[str]:
        """Get a memory by key."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memories WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            print(f"Database error: {e}")
            return None

    def list_memories(self) -> List[Dict]:
        """List all memories."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, value, created_at FROM memories ORDER BY created_at DESC"
            )
            memories = []
            for row in cursor.fetchall():
                memories.append(
                    {"key": row[0], "value": row[1], "created_at": row[2]}
                )
            conn.close()
            return memories
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def create_task(self, title: str, description: str = "") -> int:
        """Create a new task."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title, description) VALUES (?, ?)",
                (title, description),
            )
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return task_id
        except Exception as e:
            print(f"Database error: {e}")
            return -1

    def list_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """List tasks, optionally filtered by status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if status:
                cursor.execute(
                    "SELECT id, title, description, status, created_at FROM tasks WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                )
            else:
                cursor.execute(
                    "SELECT id, title, description, status, created_at FROM tasks ORDER BY created_at DESC"
                )

            tasks = []
            for row in cursor.fetchall():
                tasks.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "description": row[2],
                        "status": row[3],
                        "created_at": row[4],
                    }
                )
            conn.close()
            return tasks
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def update_task_status(self, task_id: int, status: str) -> bool:
        """Update task status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if status == "completed":
                cursor.execute(
                    "UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, task_id),
                )
            else:
                cursor.execute(
                    "UPDATE tasks SET status = ? WHERE id = ?",
                    (status, task_id),
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False


# Global database instance
db = Database()
