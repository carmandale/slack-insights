"""Basic tests for chat functionality."""

import pytest
import tempfile
import os
from slack_insights.chat import ChatEngine, MessageHandler, ResponseFormatter
from slack_insights.database import init_database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Initialize database
    conn = init_database(path)
    
    # Add some test data
    conn.execute("""
        INSERT INTO conversations 
        (channel_id, channel_name, user_id, username, display_name, message_text, timestamp)
        VALUES 
        ('C123', 'test-channel', 'U123', 'testuser', 'Test User', 'Test message', 1234567890)
    """)
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


def test_chat_engine_initialization(temp_db):
    """Test that ChatEngine initializes correctly."""
    # Set API key for test
    os.environ['ANTHROPIC_API_KEY'] = 'test-key'
    
    engine = ChatEngine(temp_db)
    assert engine.db_path == temp_db
    assert engine.api_key == 'test-key'
    engine.close()


def test_chat_engine_start_session(temp_db):
    """Test starting a chat session."""
    os.environ['ANTHROPIC_API_KEY'] = 'test-key'
    
    engine = ChatEngine(temp_db)
    session_id = engine.start_session()
    
    assert session_id is not None
    assert len(session_id) > 0
    
    # Verify session exists in database
    cursor = engine.conn.execute(
        "SELECT session_id FROM chat_sessions WHERE session_id = ?",
        (session_id,)
    )
    assert cursor.fetchone() is not None
    
    engine.close()


def test_chat_engine_get_history(temp_db):
    """Test retrieving conversation history."""
    os.environ['ANTHROPIC_API_KEY'] = 'test-key'
    
    engine = ChatEngine(temp_db)
    session_id = engine.start_session()
    
    # Initially empty
    history = engine.get_history(session_id)
    assert len(history) == 0
    
    # Add a message manually
    engine.conn.execute(
        """INSERT INTO chat_messages 
           (session_id, role, content, timestamp) 
           VALUES (?, ?, ?, ?)""",
        (session_id, "user", "Test message", 1234567890.0)
    )
    engine.conn.commit()
    
    # Should have one message
    history = engine.get_history(session_id)
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Test message"
    
    engine.close()


def test_chat_engine_clear_session(temp_db):
    """Test clearing session history."""
    os.environ['ANTHROPIC_API_KEY'] = 'test-key'
    
    engine = ChatEngine(temp_db)
    session_id = engine.start_session()
    
    # Add a message
    engine.conn.execute(
        """INSERT INTO chat_messages 
           (session_id, role, content, timestamp) 
           VALUES (?, ?, ?, ?)""",
        (session_id, "user", "Test message", 1234567890.0)
    )
    engine.conn.commit()
    
    # Clear session
    engine.clear_session(session_id)
    
    # History should be empty
    history = engine.get_history(session_id)
    assert len(history) == 0
    
    engine.close()


def test_message_handler_is_followup():
    """Test follow-up question detection."""
    handler = MessageHandler(None)
    
    # Follow-up questions
    assert handler._is_followup_query("What about last week?") == True
    assert handler._is_followup_query("And what else?") == True
    assert handler._is_followup_query("Show me those") == True
    
    # Not follow-ups
    assert handler._is_followup_query("What did Dan ask me to do?") == False
    assert handler._is_followup_query("Show me all tasks") == False


def test_response_formatter_format_help():
    """Test help message formatting."""
    formatter = ResponseFormatter()
    help_text = formatter.format_help()
    
    assert "Available Commands" in help_text
    assert "/help" in help_text
    assert "/exit" in help_text
    assert "Example Queries" in help_text


def test_response_formatter_no_results():
    """Test formatting when no results found."""
    formatter = ResponseFormatter()
    response = formatter._format_no_results()
    
    assert "No results found" in response


def test_response_formatter_with_results():
    """Test formatting with actual results."""
    formatter = ResponseFormatter()
    
    results = [
        {
            "canonical_task": "Test task",
            "count": 1,
            "status": "open",
            "instances": [
                {
                    "assigner_username": "testuser",
                    "date": "2025-10-12",
                    "context_quote": "This is a test"
                }
            ]
        }
    ]
    
    response = formatter.format_response(results, "Test explanation")
    
    assert "Found 1 unique task" in response
    assert "Test task" in response
    assert "testuser" in response
