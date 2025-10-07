# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/spec.md

> Created: 2025-10-07
> Version: 1.0.0

## Technical Requirements

### Project Structure
- Python 3.11+ with uv package manager
- Virtual environment: `.venv/`
- Source code: `src/slack_insights/`
- Tests: `tests/`
- Database: `slack_insights.db` (gitignored)
- Environment: `.env` (gitignored)

### SlackDump JSON Parser
- Parse SlackDump export format (validated structure from Phase 0)
- Handle message types: regular, threaded, edited
- Extract fields: user, text, timestamp, thread_ts, team, channel
- Support large files (9MB+ tested in Phase 0)
- Error handling for malformed JSON

### SQLite Database
- Schema version tracking for migrations
- Two core tables: conversations, action_items
- Indexes on: timestamp, user_id, channel_id, status
- No ORM (use built-in sqlite3 module)
- Database location: project root (configurable)

### Anthropic API Integration
- Model: claude-sonnet-4-20250514
- Batch size: ~100 messages per request (based on Phase 0 validation)
- Max tokens: 4096 per response
- Error handling: retry with exponential backoff (3 attempts)
- Rate limiting: respect Anthropic's limits
- API key from environment variable: ANTHROPIC_API_KEY

### CLI Framework
- Library: typer (modern, type-hint based)
- Output formatting: rich library
- Progress bars: rich.progress
- Commands: import, analyze, query-person
- Global flags: --verbose, --help

### Performance Requirements
- Import: Process 10,000 messages in < 2 minutes
- Analysis: Batch processing with progress feedback
- Query: Results in < 2 seconds
- Memory: Handle 10MB+ JSON files without loading entire file into memory

## Approach

### Selected Approach: Batch Processing with Local Storage

**Architecture:**
1. Import phase: Parse JSON → Store in SQLite
2. Analysis phase: Load batches → Send to Claude → Store results
3. Query phase: SQL queries with filtering

**Rationale:**
- **Separation of concerns**: Import once, analyze once, query many times
- **Cost efficiency**: Only call Claude API during analysis phase
- **Fast queries**: SQLite indexes enable sub-second responses
- **Reliability**: If API call fails mid-analysis, can resume from last batch

### Alternative Considered: Real-time Analysis During Import

**Rejected because:**
- Slower import (blocked on API calls)
- No ability to re-analyze with improved prompts
- Higher cost (re-import = re-analyze)

## External Dependencies

### Core Dependencies
- **anthropic** (>=0.18.0) - Official Anthropic Python SDK for Claude API
  - **Justification:** First-party SDK, well-maintained, handles auth/retry logic
- **typer** (>=0.9.0) - Modern CLI framework with type hints
  - **Justification:** Better DX than click, automatic help generation, type safety
- **rich** (>=13.7.0) - Terminal formatting and progress bars
  - **Justification:** Beautiful output, built-in progress bars, widely used
- **python-dotenv** (>=1.0.0) - Environment variable management
  - **Justification:** Standard for .env files, simple API

### Development Dependencies
- **pytest** (>=7.4.0) - Test framework
  - **Justification:** Industry standard, great plugin ecosystem
- **pytest-cov** (>=4.1.0) - Coverage reporting
  - **Justification:** Integrates with pytest, clear reports
- **ruff** (>=0.1.0) - Fast linter and formatter
  - **Justification:** Replaces multiple tools (black, isort, flake8), 10x faster

### No Additional Dependencies Needed
- **SQLite**: Built into Python (sqlite3 module)
- **JSON parsing**: Built into Python (json module)
- **HTTP client**: Included in anthropic SDK

## Code Organization

### Module Structure
```
src/slack_insights/
├── __init__.py
├── cli.py              # Main CLI entry point (typer app)
├── database.py         # SQLite operations and schema
├── parser.py           # SlackDump JSON parser
├── extractor.py        # Claude API extraction logic
├── query_engine.py     # Query execution and formatting
└── utils.py            # Shared helpers (date parsing, etc.)
```

### Testing Strategy
```
tests/
├── test_parser.py      # Unit tests for JSON parsing
├── test_database.py    # Database schema and queries
├── test_extractor.py   # Extraction logic (mocked API)
├── test_query.py       # Query engine tests
└── fixtures/
    └── sample_export.json  # Small test dataset
```

## Configuration

### Environment Variables (.env)
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...  # For future comparison
DATABASE_PATH=slack_insights.db
LOG_LEVEL=INFO
```

### Package Configuration (pyproject.toml)
```toml
[project]
name = "slack-insights"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.18.0",
    "typer>=0.9.0",
    "rich>=13.7.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
slack-insights = "slack_insights.cli:app"
```

## Error Handling Strategy

### Import Errors
- File not found: Clear message with path
- Invalid JSON: Show line number and error
- Unknown message format: Log warning, continue import

### API Errors
- Missing API key: Point to .env.example
- Rate limit exceeded: Wait and retry
- Network error: Retry with exponential backoff
- Invalid response: Log error, mark batch as failed

### Query Errors
- No results: "No action items found for Dan"
- Database locked: Wait and retry
- Invalid filter: Show available options
