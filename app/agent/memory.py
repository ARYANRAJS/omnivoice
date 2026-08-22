import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.DATA_DIR / "memory.db"

def init_db():
    """Initialize SQLite database tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact_key TEXT UNIQUE NOT NULL,
            fact_value TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Run init_db on module import
init_db()

def save_message(role: str, content: str):
    """Store conversation turn into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversation_history (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_recent_history(limit: int = 10) -> List[Dict[str, str]]:
    """Retrieve recent conversation history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM conversation_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    # Reverse to chronological order
    history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
    return history

def remember_fact(fact_key: str, fact_value: str) -> str:
    """Store explicit fact/preference into SQLite memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    key_clean = fact_key.strip().lower()
    cursor.execute("""
        INSERT INTO user_memory (fact_key, fact_value, timestamp)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(fact_key) DO UPDATE SET fact_value=excluded.fact_value, timestamp=CURRENT_TIMESTAMP
    """, (key_clean, fact_value.strip()))
    conn.commit()
    conn.close()
    return f"Remembered: '{fact_key}' = '{fact_value}'."

def recall_facts() -> List[Tuple[str, str]]:
    """Get all stored facts from user_memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT fact_key, fact_value FROM user_memory ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def forget_fact(fact_key: str = None) -> str:
    """Forget specific fact or latest stored fact."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if fact_key:
        cursor.execute("DELETE FROM user_memory WHERE fact_key = ?", (fact_key.strip().lower(),))
    else:
        cursor.execute("DELETE FROM user_memory WHERE id = (SELECT MAX(id) FROM user_memory)")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    if count > 0:
        return "Forgot memory item successfully."
    return "No matching memory item to forget."

def clear_all_memory() -> str:
    """Clear all memory and history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_memory")
    cursor.execute("DELETE FROM conversation_history")
    conn.commit()
    conn.close()
    return "Memory and conversation history cleared."

def get_memory_summary() -> str:
    """Format memory items for display or LLM context insertion."""
    facts = recall_facts()
    if not facts:
        return "No explicit user memory stored yet."
    items = [f"- {k}: {v}" for k, v in facts]
    return "Stored Memory Items:\n" + "\n".join(items)
