# Slack Insights

AI-powered action item extraction and natural language querying for Slack conversations.

## Overview

Slack Insights transforms overwhelming Slack conversation history into actionable intelligence. Using Claude AI, it automatically extracts action items, tasks, and commitments from exported Slack conversations and enables simple queries to find what matters most.

## Features

- **Import** Slack conversations from SlackDump exports with username resolution
- **Extract** action items automatically using Claude AI with:
  - Thread context preservation for conversational flow
  - Compact transcript format (60% token savings)
  - Recognition of casual/conversational requests
  - Sliding window batching with overlap
- **Query** tasks by person, date, or status
- **Privacy-first** - all data stored locally in SQLite

## Installation

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies (dev extras included)
uv pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Quick Start

```bash
# 1. Import Slack conversations from SlackDump JSON export
slack-insights import dan-messages/D3Y7V95DX.json

# 2. Analyze and extract action items using Claude AI
slack-insights analyze

# 3. Query action items from a specific person
slack-insights query-person Dan
```

### Query Options

```bash
# Filter by status (open or completed)
slack-insights query-person Dan --status open
slack-insights query-person Dan --status completed

# Show only recent items (last 7 days)
slack-insights query-person Dan --recent

# Combine filters
slack-insights query-person Dan --status open --recent
```

### Advanced Options

```bash
# Analyze with improved batching (default: 120 messages, 30 overlap, newest-first)
slack-insights analyze --newest-first

# Customize batch settings
slack-insights analyze --batch-size 100 --overlap 20

# Process oldest messages first (legacy behavior)
slack-insights analyze --oldest-first

# Filter analysis by assigner name
slack-insights analyze --assigner "Dan Ferguson"
```

## Exporting Slack Data with SlackDump

Before using Slack Insights, you need to export your Slack conversations:

```bash
# Install SlackDump
brew install slackdump  # macOS
# Or download from https://github.com/rusq/slackdump/releases

# Get Slack user token
# Visit: https://api.slack.com/custom-integrations/legacy-tokens
# Generate token (starts with xoxp-)

# Export direct messages with a specific person
slackdump export -o dan-export.zip -dm @Dan

# Extract the JSON file
unzip dan-export.zip -d dan-messages/
```

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy src/
```

## License

MIT

## Troubleshooting

**Database not found error:**
```bash
# Ensure you've run import first
slack-insights import <your-file.json>
```

**Invalid API key:**
```bash
# Check your .env file contains ANTHROPIC_API_KEY
cat .env | grep ANTHROPIC_API_KEY
```

**No action items found:**
- Verify data was imported: Check for `slack_insights.db` file
- Run analyze command after import
- Try querying with different person names (case-insensitive partial match)

## Project Status

**Phase 1:** Foundation & Basic Query ✅ Complete (66 tests passing, 95% coverage)  
**Phase 2:** Extraction Quality Fixes ✅ Complete (21/21 tests passing)  
**Phase 3:** Natural Language Query POC ✅ Complete

**Recent Improvements (Issue #2):**
- Username resolution with 100% coverage
- Thread context handling for conversational flow
- Compact transcript format (60% token savings)
- Improved prompt for casual language recognition
- Sliding window batching with overlap
- **Result:** 24 action items from last 7 days (previously 0)

**Natural Language Query POC (Phase 3):**
- Terminal chat interface for natural language queries
- Smart grouping/deduplication of similar tasks
- Interactive expansion to see all instances
- Example queries:
  - "What did Dan ask me to do for Orchestrator?"
  - "Show me urgent tasks from last week"
  - "What AT&T tasks are still open?"

**Try the POC:**
```bash
python poc_chat_terminal.py
```

See [POC_NATURAL_LANGUAGE.md](POC_NATURAL_LANGUAGE.md) for complete guide.

## What's Next

See [roadmap.md](.agent-os/product/roadmap.md) for upcoming features:
- Phase 3: Productionize natural language query as CLI command
- Phase 4: Summaries and reporting
- Phase 5: Performance optimization and polish
