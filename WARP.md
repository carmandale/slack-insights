# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

**Slack Insights** is an AI-powered Python CLI tool that transforms Slack conversation history into actionable intelligence by extracting tasks, action items, and commitments using Claude AI.

### Core Architecture

```
Data Flow:
SlackDump Export → Parser → SQLite → AI Extractor → Query Engine → CLI Output
```

**Key Components:**
- **Parser** (`src/slack_insights/parser.py`) - Converts SlackDump JSON exports to database records
- **Database** (`src/slack_insights/database.py`) - SQLite operations with migration support
- **Extractor** (`src/slack_insights/extractor.py`) - Claude API integration for action item extraction
- **Query Engine** (`src/slack_insights/query_engine.py`) - Structured querying of extracted data
- **CLI** (`src/slack_insights/cli.py`) - Typer-based command interface using Rich for output

**Database Schema:**
- `conversations` table stores imported Slack messages with thread context
- `action_items` table stores AI-extracted tasks with assignee/assigner tracking
- `schema_versions` table manages database migrations

## Environment Setup

### Prerequisites
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure Python 3.11+
python --version  # Must be 3.11 or higher
```

### Quick Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies (includes dev tools)
uv pip install -e ".[dev]"

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Verify setup
slack-insights --help
```

## Development Commands

### Essential Commands
```bash
# Run full test suite with coverage
uv run pytest

# Run single test file
uv run pytest tests/test_parser.py

# Run tests with coverage report
uv run pytest --cov

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy src/

# Run application
slack-insights --help
```

### Application Usage
```bash
# 1. Import Slack data (requires SlackDump JSON export)
slack-insights import path/to/exported-messages.json

# 2. Extract action items using Claude AI
slack-insights analyze

# 3. Query extracted items
slack-insights query-person "Dan" --status open --recent
```

### Proof of Concept Testing
```bash
# Terminal-based natural language query interface
python poc_chat_terminal.py

# Gradio web interface (requires: pip install gradio)
python poc_chat_ui.py
```

## Database & Migrations

### Schema Overview
The database uses SQLite with two main tables:

```sql
-- Core message storage with duplicate prevention
conversations (
  id, channel_id, user_id, display_name, 
  timestamp, message_text, thread_ts, ...
  UNIQUE(channel_id, timestamp)  -- Prevents duplicates
)

-- AI-extracted action items
action_items (
  id, conversation_id, task_description,
  assignee_username, assigner_username,
  status, urgency, mentioned_date, ...
  FOREIGN KEY (conversation_id) REFERENCES conversations(id)
)
```

### Migration System
Migrations live in `migrations/` and are SQL files prefixed with version numbers:
- `001_initial_schema.sql` - Creates base tables and indexes
- `002_add_display_names.sql` - Adds display name support

The database automatically runs pending migrations on connection.

### Sample Queries
```bash
# Connect to database for manual inspection
sqlite3 slack_insights.db

# Check imported data
.tables
SELECT COUNT(*) FROM conversations;
SELECT COUNT(*) FROM action_items;

# View recent action items
SELECT ai.task_description, c.display_name, ai.status 
FROM action_items ai 
JOIN conversations c ON ai.conversation_id = c.id 
ORDER BY c.timestamp DESC 
LIMIT 10;
```

## Testing Strategy

The project uses pytest with comprehensive coverage (95%+ target):

```bash
# Run all tests
pytest

# Run with verbose output and coverage
pytest -v --cov=src/slack_insights --cov-report=html

# Run specific test categories
pytest tests/test_parser.py  # Parser tests
pytest tests/test_extractor.py  # AI extraction tests
pytest tests/test_integration.py  # End-to-end tests

# Run tests that hit external APIs (mocked)
pytest -k "extract"
```

**Test Structure:**
- Unit tests for each module (`test_*.py` files)
- Integration tests for CLI commands
- Mocked Anthropic API calls to avoid costs
- Temporary databases for isolation

## Key Development Patterns

### Code Style (enforced by ruff)
- Tab indentation (4-space display width)
- Type hints on all function signatures
- Snake_case for functions, PascalCase for classes
- Docstrings for public functions

### Error Handling
- Custom exceptions (`ParserError`, `ExtractorError`) for domain-specific issues
- Graceful degradation when user mapping fails
- Database constraint violations handled (duplicate prevention)

### AI Integration
- Compact transcript format saves ~60% tokens vs JSON
- Sliding window batching with overlap for context preservation
- Thread context injection for conversational flow
- Confidence scoring for extracted items

## Architecture Details

### Thread Context System
The `thread_context.py` module preserves conversational flow by:
1. Detecting threaded replies via `thread_ts`
2. Fetching parent messages (up to 3 levels)
3. Injecting context into AI prompts
4. Maintaining chronological order

### User Resolution
The `user_lookup.py` system:
- Maps Slack user IDs to display names using `users-T1YNKSBL5.txt`
- Falls back gracefully when mapping file is missing
- Supports backfill operations for existing data

### Batch Processing
The extractor uses intelligent batching:
- Default 120 messages per batch with 30-message overlap
- Newest-first processing prioritizes recent conversations
- Configurable batch size and overlap for tuning

## Troubleshooting

### Common Issues

**"Database not found" error:**
```bash
# Ensure you've imported data first
slack-insights import your-export.json
# Check database file exists
ls -la slack_insights.db
```

**"Invalid API key" error:**
```bash
# Verify .env configuration
cat .env | grep ANTHROPIC_API_KEY
# Ensure key starts with sk-ant-
```

**No action items extracted:**
- Check for imported conversations: `SELECT COUNT(*) FROM conversations;`
- Try smaller batch size: `--batch-size 50`
- Verify assigner name filtering isn't too restrictive

**Duplicate import errors:**
The system prevents duplicates via `UNIQUE(channel_id, timestamp)` constraint. Re-importing the same file is safe.

### Debug Mode
```bash
# Set environment for verbose output
export SLACK_INSIGHTS_DEBUG=1
export SLACK_INSIGHTS_DB=debug.db

# Run with detailed logging
slack-insights analyze --batch-size 10
```

### Performance Optimization
```bash
# For large imports, use larger batches
slack-insights analyze --batch-size 200 --overlap 50

# Process oldest messages first (legacy behavior)
slack-insights analyze --oldest-first
```

## Agent OS Integration

This project follows Agent OS standards:
- Product documentation in `.agent-os/product/`
- Feature specifications in `.agent-os/specs/`
- Technical decisions logged in `decisions.md`
- Roadmap-driven development phases

### Key Files
- `CLAUDE.md` - Claude Code integration guide
- `.agent-os/product/tech-stack.md` - Technology choices and rationale
- `.agent-os/product/roadmap.md` - Development phases and features

### Development Workflow
1. Create feature specifications before implementation
2. Reference issue numbers in commits: `feat: add parser #123`
3. Maintain >80% test coverage
4. Mock external API calls in tests

## Current Status & Roadmap

**Completed Phases:**
- ✅ Phase 1: Foundation & Basic Query (66 tests, 95% coverage)
- ✅ Phase 2: Extraction Quality Fixes (21/21 tests passing)
- ✅ Phase 3: Natural Language Query POC

**In Progress:**
- Natural language CLI integration
- Enhanced grouping and deduplication

**Next Steps:**
See `.agent-os/product/roadmap.md` for detailed feature pipeline including summaries, reporting, and performance optimization.