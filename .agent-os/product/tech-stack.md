# Technical Stack

> Last Updated: 2025-10-07
> Version: 1.0.0

## Application Architecture

- **Type:** Command-line application (CLI)
- **Structure:** backend_only (no frontend)
- **Deployment:** Local installation via uv/pip
- **Future Consideration:** While CLI is MVP focus, user feedback may indicate web UI is better for daily use. Keep architecture modular to enable web interface in Phase 6+

## Core Technology

### Language & Runtime
- **Language:** Python 3.11+
- **Package Manager:** uv (modern, fast replacement for pip)
- **Virtual Environment:** uv venv

### Command-Line Interface
- **CLI Framework:** typer or click
- **Output Formatting:** rich (for beautiful terminal output)
- **Progress Indicators:** rich.progress for long-running operations

## Data Layer

### Database
- **Primary Database:** SQLite 3
- **ORM:** None (using built-in sqlite3 module for simplicity)
- **Schema Management:** SQL migration scripts in `migrations/` directory

### Database Schema (Initial)
```sql
-- conversations table
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    channel_id TEXT NOT NULL,
    channel_name TEXT,
    user_id TEXT NOT NULL,
    username TEXT,
    timestamp REAL NOT NULL,
    message_text TEXT NOT NULL,
    thread_ts REAL,
    raw_json TEXT,
    imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- action_items table
CREATE TABLE action_items (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    assignee_user_id TEXT,
    assignee_username TEXT,
    assigner_user_id TEXT,
    assigner_username TEXT,
    task_description TEXT NOT NULL,
    category TEXT,
    urgency TEXT,
    status TEXT DEFAULT 'open',
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- query_history table (for caching and learning)
CREATE TABLE query_history (
    id INTEGER PRIMARY KEY,
    query_text TEXT NOT NULL,
    results_json TEXT,
    queried_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## AI & Machine Learning

### LLM Integration
- **Provider:** Anthropic
- **Model:** claude-sonnet-4-20250514
- **SDK:** anthropic (official Python SDK)
- **Use Cases:**
  - Action item extraction from conversation text
  - Natural language query understanding
  - Context-aware summarization

### Prompt Engineering
- **Strategy:** Few-shot prompting with examples
- **Context Window:** Utilize full conversation threads for better context
- **Output Format:** Structured JSON for reliable parsing

## Development Tools

### Environment Management
- **Configuration:** python-dotenv for .env file handling
- **Secrets:** Local .env file (never committed)

### Testing
- **Framework:** pytest
- **Coverage:** pytest-cov
- **Test Types:** Unit tests, integration tests for AI calls

### Code Quality
- **Linting:** ruff (fast Python linter)
- **Formatting:** ruff format (replaces black)
- **Type Checking:** mypy (optional, for type hints)

## External Dependencies

### Python Packages (requirements.txt)
```
# Core dependencies
anthropic>=0.18.0
typer>=0.9.0
rich>=13.7.0
python-dotenv>=1.0.0

# Development dependencies
pytest>=7.4.0
pytest-cov>=4.1.0
ruff>=0.1.0
```

## SlackDump Integration

### Installation
```bash
# macOS
brew install slackdump

# Linux (download binary from GitHub releases)
# https://github.com/rusq/slackdump/releases
```

### Getting Slack User Token
1. Visit https://api.slack.com/custom-integrations/legacy-tokens
2. Generate token for your workspace (starts with `xoxp-`)
3. Add to .env file: `SLACK_USER_TOKEN=xoxp-...`
4. **Note:** This token has read access to all your conversations

### Exporting Conversations
```bash
# List available channels and DMs
slackdump -list-channels

# Export specific user's DMs (last 2 months)
slackdump -export dan-convos.zip -dm @Dan

# Export specific channel
slackdump -export channel-export.zip -channel C01234567

# Export with date range
slackdump -export recent.zip -dm @Dan -oldest 2024-08-01
```

### Expected JSON Format
SlackDump exports match Slack's official export format. Parser handles:
- Direct messages (DMs)
- Private channels
- Public channels
- Threaded conversations
- File attachments (metadata only)

## Data Formats

### Input Format
- **SlackDump Export:** JSON format (array of message objects)
- **Expected Structure:**
```json
[
  {
    "client_msg_id": "...",
    "type": "message",
    "text": "Can you review the PR by EOD?",
    "user": "U01234567",
    "ts": "1609459200.000000",
    "team": "T01234567",
    "channel": "C01234567",
    "thread_ts": "1609459200.000000"
  }
]
```

### Output Formats
- **Console:** Rich formatted tables and text
- **Export:** JSON, CSV, Markdown

## File Structure

```
slack-insights/
├── .agent-os/
│   ├── product/
│   │   ├── mission.md
│   │   ├── tech-stack.md
│   │   ├── roadmap.md
│   │   └── decisions.md
│   └── specs/
├── src/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── database.py         # Database operations
│   ├── parser.py           # SlackDump JSON parser
│   ├── extractor.py        # AI-powered action item extraction
│   ├── query_engine.py     # Natural language query handler
│   └── utils.py            # Helper functions
├── tests/
│   ├── test_parser.py
│   ├── test_extractor.py
│   └── test_query_engine.py
├── migrations/
│   └── 001_initial_schema.sql
├── .env.example
├── .gitignore
├── pyproject.toml          # Project metadata and dependencies
├── requirements.txt        # Pin specific versions
├── CLAUDE.md              # Agent OS documentation
└── README.md
```

## Security Considerations

### API Key Management
- Store Anthropic API key in `.env` file (gitignored)
- Never log or expose API keys in output
- Validate environment variables on startup

### Data Privacy
- All data stored locally (no cloud sync)
- Database file can be encrypted at rest (user's responsibility)
- No telemetry or usage tracking

## Performance Requirements

### Expected Load
- Import: Handle 10,000+ messages without memory issues
- Query: Return results in < 2 seconds for typical queries
- Analysis: Process 100 messages per API call batch

### Optimization Strategies
- Batch API calls to reduce latency
- Index database columns for fast queries
- Cache frequently accessed data
- Stream large imports rather than loading all into memory

## Development Environment Setup

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY

# Run database migrations
python -m src.database --migrate

# Run tests
pytest

# Run CLI
python -m src.cli --help
```

## Deployment

- **Distribution:** PyPI package (future)
- **Installation:** `uv pip install slack-insights`
- **Updates:** `uv pip install --upgrade slack-insights`
- **Platform Support:** macOS, Linux, Windows (via WSL or native Python)
