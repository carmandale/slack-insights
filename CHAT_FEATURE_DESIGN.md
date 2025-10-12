# LLM Chat Feature Design

## Overview

This document outlines the design for adding an interactive LLM chat interface to slack-insights that allows users to ask natural language questions about their Slack channels.

## Requirements

The feature should support queries like:
- "What did Dan ask me to do for the Orchestrator app?"
- "What is the latest update in the TMA Disasterville channel?"
- "Show me all open tasks from last week"
- "What urgent items are pending?"

## Architecture

### Components

1. **Chat Interface Module** (`src/slack_insights/chat/`)
   - `chat_engine.py` - Main chat engine with conversation history
   - `message_handler.py` - Handles message processing and context management
   - `response_formatter.py` - Formats responses for display

2. **Enhanced Query Engine**
   - Extend existing `nlq_engine.py` to support:
     - Multi-turn conversations
     - Context awareness (remember previous queries)
     - Channel-specific filtering
     - Project/topic filtering

3. **CLI Command**
   - New `chat` command for interactive chat sessions
   - Maintains conversation history during session
   - Supports both terminal and potential web interface

### Data Flow

```
User Query
    ↓
Chat Engine (manages context)
    ↓
Enhanced NLQ Engine (converts to SQL with context)
    ↓
Database Query (with channel/project filters)
    ↓
Result Grouping & Formatting
    ↓
Response to User
```

### Key Features

1. **Conversation Memory**
   - Track conversation history within a session
   - Allow follow-up questions that reference previous context
   - Example: "What about last week?" after asking "What did Dan ask me to do?"

2. **Channel Awareness**
   - Filter queries by specific Slack channels
   - Support channel name matching (e.g., "TMA Disasterville")
   - Allow switching context between channels

3. **Project/Topic Extraction**
   - Extract project names from queries (e.g., "Orchestrator app")
   - Use semantic search in task descriptions and context
   - Filter results by relevance to mentioned projects

4. **Enhanced Context**
   - Include message thread context in responses
   - Show related messages for better understanding
   - Link to original Slack messages when available

## Implementation Plan

### Phase 1: Core Chat Engine
- Create chat module structure
- Implement conversation history management
- Add context-aware query generation
- Integrate with existing nlq_engine

### Phase 2: Enhanced Filtering
- Add channel filtering to database queries
- Implement project/topic keyword extraction
- Add semantic search for better matching

### Phase 3: Interactive CLI
- Create `chat` command with REPL interface
- Add conversation history display
- Implement context commands (/channel, /project, /clear)

### Phase 4: Response Enhancement
- Improve response formatting with context
- Add message threading visualization
- Include relevance scoring

## Database Schema Extensions

### New Table: chat_sessions
```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    started_at REAL NOT NULL,
    last_activity REAL NOT NULL
);
```

### New Table: chat_messages
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    sql_query TEXT, -- for assistant messages
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
```

## API Design

### ChatEngine Class

```python
class ChatEngine:
    def __init__(self, db_path: str, api_key: str):
        """Initialize chat engine with database and API credentials."""
        
    def start_session(self) -> str:
        """Start a new chat session, returns session_id."""
        
    def send_message(self, session_id: str, user_message: str) -> dict:
        """
        Process user message and return response.
        
        Returns:
            {
                'response': str,
                'results': list[dict],
                'sql_query': str,
                'context': dict
            }
        """
        
    def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        
    def clear_session(self, session_id: str):
        """Clear session history."""
```

### Enhanced NLQ Prompt

The prompt will be enhanced to include:
- Conversation history (last 3-5 exchanges)
- Current channel filter (if set)
- Current project/topic context (if set)
- Available channel names from database

## CLI Usage Examples

```bash
# Start interactive chat session
slack-insights chat

# Example interaction:
> What did Dan ask me to do?
Found 12 action items from Dan:
1. Provide iPad screenshots for demo
2. Review Orchestrator documentation
...

> What about for the Orchestrator app?
Filtering by: Orchestrator
Found 3 action items:
1. Review Orchestrator documentation
2. Test Orchestrator API endpoint
...

> Show me only open items
Found 2 open items:
1. Review Orchestrator documentation (Status: open)
2. Test Orchestrator API endpoint (Status: open)

> /channel TMA Disasterville
Switched to channel: TMA Disasterville

> What's the latest update?
Latest message in TMA Disasterville:
From: Dale • 2 days ago
"Project is on track, deployment scheduled for Friday"
```

## Security Considerations

1. **SQL Injection Prevention**
   - Reuse existing `validate_sql_query()` function
   - Maintain read-only database access
   - Continue using parameterized queries where possible

2. **API Key Security**
   - Use existing environment variable approach
   - No changes to current security model

3. **Session Management**
   - Sessions stored locally in database
   - Auto-expire after 24 hours of inactivity
   - No sensitive data in session storage

## Testing Strategy

1. **Unit Tests**
   - Chat engine message handling
   - Context management
   - Query enhancement with history

2. **Integration Tests**
   - End-to-end chat flows
   - Multi-turn conversations
   - Channel and project filtering

3. **Manual Testing**
   - Real conversation scenarios
   - Edge cases (ambiguous queries, context switching)
   - Performance with large result sets

## Future Enhancements

1. **Web Interface**
   - Integrate with existing NiceGUI interface
   - Add chat widget to GUI
   - Real-time streaming responses

2. **Advanced Features**
   - Export chat transcripts
   - Save favorite queries
   - Query suggestions based on history
   - Sentiment analysis of action items

3. **Multi-Channel Support**
   - Query across multiple channels simultaneously
   - Channel comparison queries
   - Cross-channel task tracking

## Migration Path

This feature will be developed on a new branch: `feature/llm-chat`

The implementation will:
1. Not break existing functionality
2. Be fully backward compatible
3. Add new commands without modifying existing ones
4. Reuse existing infrastructure (database, nlq_engine, etc.)

## Success Metrics

- Users can successfully query across channels
- Follow-up questions work with context
- Project/topic filtering improves result relevance
- Response time remains under 5 seconds
- No SQL injection vulnerabilities

