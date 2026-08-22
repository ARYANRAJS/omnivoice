import sqlite3
import logging
from typing import List, Dict, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.DATA_DIR / "memory.db"

def init_graph_db():
    """Initialize enhanced memory & behavior profile database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User behaviors & habits profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            behavior_pattern TEXT NOT NULL,
            frequency_score INTEGER DEFAULT 1,
            last_observed DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Knowledge graph nodes and relations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_entity TEXT NOT NULL,
            relation TEXT NOT NULL,
            target_entity TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_entity, relation, target_entity)
        )
    """)

    conn.commit()
    conn.close()

init_graph_db()

def log_user_behavior(category: str, pattern: str) -> str:
    """Log or update user habit/behavior pattern."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, frequency_score FROM user_behaviors
        WHERE category = ? AND behavior_pattern = ?
    """, (category.lower(), pattern.strip()))
    row = cursor.fetchone()

    if row:
        bid, score = row
        cursor.execute("""
            UPDATE user_behaviors
            SET frequency_score = ?, last_observed = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (score + 1, bid))
    else:
        cursor.execute("""
            INSERT INTO user_behaviors (category, behavior_pattern)
            VALUES (?, ?)
        """, (category.lower(), pattern.strip()))
    
    conn.commit()
    conn.close()
    return f"Behavior logged under category '{category}': {pattern}"

def add_graph_relation(source: str, relation: str, target: str) -> str:
    """Add a relation edge to the knowledge graph."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO knowledge_graph (source_entity, relation, target_entity)
        VALUES (?, ?, ?)
        ON CONFLICT(source_entity, relation, target_entity)
        DO UPDATE SET updated_at = CURRENT_TIMESTAMP
    """, (source.strip().lower(), relation.strip().lower(), target.strip().lower()))
    conn.commit()
    conn.close()
    return f"Graph relation added: ({source}) --[{relation}]--> ({target})"

def query_user_profile() -> Dict[str, List[str]]:
    """Retrieve full behavioral profile & graph summary for Jarvis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT category, behavior_pattern, frequency_score FROM user_behaviors ORDER BY frequency_score DESC")
    behaviors = cursor.fetchall()

    cursor.execute("SELECT source_entity, relation, target_entity FROM knowledge_graph ORDER BY updated_at DESC LIMIT 20")
    graph_edges = cursor.fetchall()
    conn.close()

    beh_list = [f"[{b[0]}] {b[1]} (observed {b[2]}x)" for b in behaviors]
    graph_list = [f"{g[0]} {g[1]} {g[2]}" for g in graph_edges]

    return {
        "behaviors": beh_list,
        "knowledge_graph": graph_list
    }

def get_jarvis_profile_context() -> str:
    """Generate system prompt context containing user behaviors and knowledge graph."""
    profile = query_user_profile()
    context_parts = []
    
    if profile["behaviors"]:
        context_parts.append("Observed User Behaviors & Routines:\n" + "\n".join(profile["behaviors"]))
    
    if profile["knowledge_graph"]:
        context_parts.append("Knowledge Graph Connections:\n" + "\n".join(profile["knowledge_graph"]))
    
    return "\n\n".join(context_parts)
