"""Main chat engine for managing interactive LLM conversations."""

import os
import sqlite3
import time
import uuid
from typing import Optional

from ..database import init_database
from ..nlq_engine import natural_language_to_sql, query_database
from ..deduplication import group_similar_tasks_simple
from .message_handler import MessageHandler
from .response_formatter import ResponseFormatter


class ChatEngine:
    """
    Interactive chat engine for natural language queries about Slack data.
    
    Manages conversation sessions, context, and integrates with the NLQ engine
    to provide intelligent responses to user queries.
    """
    
    def __init__(self, db_path: str = "slack_insights.db", api_key: Optional[str] = None):
        """
        Initialize chat engine.
        
        Args:
            db_path: Path to SQLite database
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        
        Raises:
            ValueError: If API key is not provided and not in environment
        """
        self.db_path = db_path
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please configure your API key in .env file."
            )
        
        self.conn = init_database(db_path)
        self.message_handler = MessageHandler(self.conn)
        self.response_formatter = ResponseFormatter()
        
        # Initialize chat tables if they don't exist
        self._init_chat_tables()
    
    def _init_chat_tables(self):
        """Create chat-related tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                started_at REAL NOT NULL,
                last_activity REAL NOT NULL,
                channel_filter TEXT,
                project_filter TEXT
            );
            
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                sql_query TEXT,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session 
                ON chat_messages(session_id, timestamp);
        """)
        self.conn.commit()
    
    def start_session(self) -> str:
        """
        Start a new chat session.
        
        Returns:
            session_id: Unique identifier for the session
        """
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        self.conn.execute(
            """INSERT INTO chat_sessions 
               (session_id, started_at, last_activity) 
               VALUES (?, ?, ?)""",
            (session_id, current_time, current_time)
        )
        self.conn.commit()
        
        return session_id
    
    def send_message(
        self, 
        session_id: str, 
        user_message: str,
        channel_filter: Optional[str] = None,
        project_filter: Optional[str] = None
    ) -> dict:
        """
        Process user message and generate response.
        
        Args:
            session_id: Session identifier
            user_message: User's natural language query
            channel_filter: Optional channel name to filter by
            project_filter: Optional project/topic to filter by
        
        Returns:
            Response dictionary with:
                - response: Formatted response text
                - results: List of result dictionaries
                - sql_query: Generated SQL query
                - context: Additional context information
        
        Raises:
            ValueError: If session doesn't exist or query fails
        """
        # Verify session exists
        cursor = self.conn.execute(
            "SELECT session_id FROM chat_sessions WHERE session_id = ?",
            (session_id,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Session {session_id} not found")
        
        # Update session activity
        self.conn.execute(
            "UPDATE chat_sessions SET last_activity = ? WHERE session_id = ?",
            (time.time(), session_id)
        )
        
        # Update filters if provided
        if channel_filter is not None or project_filter is not None:
            updates = []
            params = []
            if channel_filter is not None:
                updates.append("channel_filter = ?")
                params.append(channel_filter)
            if project_filter is not None:
                updates.append("project_filter = ?")
                params.append(project_filter)
            params.append(session_id)
            
            self.conn.execute(
                f"UPDATE chat_sessions SET {', '.join(updates)} WHERE session_id = ?",
                params
            )
        
        self.conn.commit()
        
        # Get conversation history for context
        history = self.get_history(session_id, limit=5)
        
        # Get current filters
        cursor = self.conn.execute(
            "SELECT channel_filter, project_filter FROM chat_sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        current_channel = row[0] if row else None
        current_project = row[1] if row else None
        
        # Save user message
        self.conn.execute(
            """INSERT INTO chat_messages 
               (session_id, role, content, timestamp) 
               VALUES (?, ?, ?, ?)""",
            (session_id, "user", user_message, time.time())
        )
        self.conn.commit()
        
        # Enhance query with context and filters
        enhanced_query = self.message_handler.enhance_query(
            user_message,
            history=history,
            channel_filter=current_channel,
            project_filter=current_project
        )
        
        # Convert to SQL using NLQ engine
        sql_query, explanation = natural_language_to_sql(enhanced_query, self.api_key)
        
        # Execute query
        raw_results = query_database(sql_query, self.db_path)
        
        # Group similar results
        grouped_results = []
        if raw_results:
            grouped_results = group_similar_tasks_simple(raw_results)
        
        # Format response
        response_text = self.response_formatter.format_response(
            grouped_results,
            explanation,
            channel_filter=current_channel,
            project_filter=current_project
        )
        
        # Save assistant response
        self.conn.execute(
            """INSERT INTO chat_messages 
               (session_id, role, content, timestamp, sql_query) 
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, "assistant", response_text, time.time(), sql_query)
        )
        self.conn.commit()
        
        return {
            "response": response_text,
            "results": grouped_results,
            "sql_query": sql_query,
            "explanation": explanation,
            "context": {
                "channel_filter": current_channel,
                "project_filter": current_project
            }
        }
    
    def get_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
        
        Returns:
            List of message dictionaries with role, content, timestamp
        """
        cursor = self.conn.execute(
            """SELECT role, content, timestamp, sql_query 
               FROM chat_messages 
               WHERE session_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (session_id, limit)
        )
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "role": row[0],
                "content": row[1],
                "timestamp": row[2],
                "sql_query": row[3]
            })
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    def clear_session(self, session_id: str):
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        self.conn.execute(
            "DELETE FROM chat_messages WHERE session_id = ?",
            (session_id,)
        )
        self.conn.execute(
            """UPDATE chat_sessions 
               SET channel_filter = NULL, project_filter = NULL 
               WHERE session_id = ?""",
            (session_id,)
        )
        self.conn.commit()
    
    def set_channel_filter(self, session_id: str, channel_name: Optional[str]):
        """
        Set or clear channel filter for a session.
        
        Args:
            session_id: Session identifier
            channel_name: Channel name to filter by, or None to clear
        """
        self.conn.execute(
            "UPDATE chat_sessions SET channel_filter = ? WHERE session_id = ?",
            (channel_name, session_id)
        )
        self.conn.commit()
    
    def set_project_filter(self, session_id: str, project_name: Optional[str]):
        """
        Set or clear project filter for a session.
        
        Args:
            session_id: Session identifier
            project_name: Project name to filter by, or None to clear
        """
        self.conn.execute(
            "UPDATE chat_sessions SET project_filter = ? WHERE session_id = ?",
            (project_name, session_id)
        )
        self.conn.commit()
    
    def get_available_channels(self) -> list[str]:
        """
        Get list of available channel names from the database.
        
        Returns:
            List of unique channel names
        """
        cursor = self.conn.execute(
            """SELECT DISTINCT channel_name 
               FROM conversations 
               WHERE channel_name IS NOT NULL AND channel_name != ''
               ORDER BY channel_name"""
        )
        return [row[0] for row in cursor.fetchall()]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Remove sessions older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Get old session IDs
        cursor = self.conn.execute(
            "SELECT session_id FROM chat_sessions WHERE last_activity < ?",
            (cutoff_time,)
        )
        old_sessions = [row[0] for row in cursor.fetchall()]
        
        # Delete messages and sessions
        for session_id in old_sessions:
            self.conn.execute(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,)
            )
            self.conn.execute(
                "DELETE FROM chat_sessions WHERE session_id = ?",
                (session_id,)
            )
        
        self.conn.commit()
        
        return len(old_sessions)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

