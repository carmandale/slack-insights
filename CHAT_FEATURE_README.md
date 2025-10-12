# Chat Feature - Interactive LLM Conversations

## Overview

The chat feature adds an interactive, context-aware interface for querying your Slack data using natural language. Unlike the single-query `slack-insights query` command, the chat interface maintains conversation history and allows follow-up questions.

## Key Features

- **Interactive Conversations**: Maintains context across multiple questions
- **Smart Filtering**: Filter by channel or project/topic
- **Rich Responses**: Grouped results with frequency counts and status indicators
- **Secure**: Read-only database access with SQL injection prevention

## Usage

### Starting a Chat Session

```bash
slack-insights chat
```

### Available Commands

- `/help` - Show help message
- `/history` - Show conversation history
- `/clear` - Clear conversation history
- `/channel <name>` - Set channel filter
- `/project <name>` - Set project filter
- `/clear-filters` - Clear all filters
- `/channels` - List available channels
- `/exit` or `/quit` - Exit chat

### Example Queries

**Basic queries:**
- "What did Dan ask me to do?"
- "Show me urgent tasks"
- "What's still open?"

**Channel-specific:**
- "What's the latest update in TMA Disasterville?"
- "/channel TMA Disasterville" then "What's new?"

**Project-specific:**
- "What tasks are related to the Orchestrator app?"
- "/project Orchestrator" then "Show me open items"

**Follow-up questions:**
- "What about last week?" (after asking about tasks)
- "Show me only the completed ones" (after a query)

## Architecture

### Components

1. **ChatEngine** (`chat_engine.py`)
   - Manages chat sessions and conversation history
   - Integrates with NLQ engine for query processing
   - Handles context and filters

2. **MessageHandler** (`message_handler.py`)
   - Enhances queries with context
   - Detects follow-up questions
   - Extracts channel and project mentions

3. **ResponseFormatter** (`response_formatter.py`)
   - Formats responses for display
   - Handles help messages and command output
   - Provides consistent formatting

4. **InteractiveChatCLI** (`cli_chat.py`)
   - REPL interface for terminal
   - Command processing
   - User interaction

### Database Schema

The chat feature adds two new tables:

```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    started_at REAL NOT NULL,
    last_activity REAL NOT NULL,
    channel_filter TEXT,
    project_filter TEXT
);

CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    sql_query TEXT,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
```

## How It Works

1. **User Input**: User types a natural language question
2. **Context Enhancement**: MessageHandler adds context from history and filters
3. **SQL Generation**: Enhanced query sent to Claude via NLQ engine
4. **Query Execution**: SQL executed against database (read-only)
5. **Result Grouping**: Similar tasks grouped with frequency counts
6. **Response Formatting**: Results formatted for display
7. **History Storage**: Query and response saved to session history

## Security

- **Read-only database access**: Queries cannot modify data
- **SQL validation**: All generated SQL validated before execution
- **No dangerous keywords**: DROP, DELETE, UPDATE, etc. blocked
- **LIMIT enforcement**: All queries must include LIMIT clause
- **Table allowlist**: Only approved tables can be queried

## Testing

Run tests for the chat feature:

```bash
pytest tests/test_chat_engine.py
pytest tests/test_message_handler.py
pytest tests/test_response_formatter.py
```

## Future Enhancements

- Web-based chat interface integration with NiceGUI
- Export chat transcripts
- Query suggestions based on history
- Multi-channel comparison queries
- Sentiment analysis of action items
- Voice input support

## Troubleshooting

**"Database not found" error:**
```bash
# Make sure you've imported data first
slack-insights import <your-file.json>
slack-insights analyze
```

**"ANTHROPIC_API_KEY not set" error:**
```bash
# Check your .env file
cat .env | grep ANTHROPIC_API_KEY
# Or set it directly
export ANTHROPIC_API_KEY=your-key-here
```

**Chat not remembering context:**
- Context is session-based and cleared when you exit
- Use `/history` to see what the chat remembers
- Use `/clear` to reset if needed

## API Usage

You can also use the chat engine programmatically:

```python
from slack_insights.chat import ChatEngine

# Initialize
engine = ChatEngine("slack_insights.db")
session_id = engine.start_session()

# Send messages
response = engine.send_message(session_id, "What did Dan ask me to do?")
print(response["response"])

# Set filters
engine.set_channel_filter(session_id, "TMA Disasterville")

# Get history
history = engine.get_history(session_id)

# Cleanup
engine.close()
```

## Contributing

To contribute to the chat feature:

1. Create a feature branch from `feature/llm-chat`
2. Make your changes
3. Add tests
4. Submit a pull request

## License

Same as main project (MIT)
