import sqlite3
from typing import List, Dict, Any
from backend.config import DB_PATH
from utils.helpers import setup_logger

logger = setup_logger("DBManager")

class DBManager:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS command_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        user_command TEXT NOT NULL,
                        ai_response TEXT,
                        execution_steps TEXT,
                        status TEXT
                    )
                ''')
                conn.commit()
                logger.info("SQLite database initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def save_task(self, command: str, ai_response: str, steps: str, status: str) -> int:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO command_history (user_command, ai_response, execution_steps, status)
                    VALUES (?, ?, ?, ?)
                ''', (command, ai_response, steps, status))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
            return -1

    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, timestamp, user_command, status
                    FROM command_history
                    ORDER BY id DESC LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                return [{"id": r[0], "timestamp": r[1], "command": r[2], "status": r[3]} for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            return []
