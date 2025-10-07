# Slack Insights

AI-powered action item extraction and natural language querying for Slack conversations.

## Overview

Slack Insights transforms overwhelming Slack conversation history into actionable intelligence. Using Claude AI, it automatically extracts action items, tasks, and commitments from exported Slack conversations and enables simple queries to find what matters most.

## Features

- **Import** Slack conversations from SlackDump exports
- **Extract** action items automatically using Claude AI
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

```bash
# Import Slack conversations
slack-insights import dan-messages/D3Y7V95DX.json

# Analyze and extract action items
slack-insights analyze

# Query action items from Dan
slack-insights query-person Dan

# Filter by status
slack-insights query-person Dan --status open

# Show only recent (last 7 days)
slack-insights query-person Dan --recent
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

## Project Status

**Phase:** Phase 1 - Foundation & Basic Query
**Status:** In Development
**GitHub Issue:** #1
