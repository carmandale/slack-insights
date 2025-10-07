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
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
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
pytest

# Run with coverage
pytest --cov

# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy src/
```

## License

MIT

## Project Status

**Phase:** Phase 1 - Foundation & Basic Query
**Status:** In Development
**GitHub Issue:** #1
