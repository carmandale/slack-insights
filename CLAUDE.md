# CLAUDE.md

> Agent OS Project Documentation
> Last Updated: 2025-10-07

## Purpose

This file directs Claude Code to use Agent OS standards for this project. It references both global user standards and project-specific documentation.

## Project Overview

**Product:** Slack Insights
**Type:** Python CLI Tool
**Purpose:** AI-powered action item extraction and natural language querying for Slack conversations

## Project Documentation

### Product Documentation
- **Mission & Vision:** @.agent-os/product/mission.md
- **Technical Stack:** @.agent-os/product/tech-stack.md
- **Product Roadmap:** @.agent-os/product/roadmap.md
- **Decisions Log:** @.agent-os/product/decisions.md

### Development Standards
These project-specific files override global standards when present:
- Project tech stack defined in: @.agent-os/product/tech-stack.md
- Development best practices: Use global @~/.agent-os/standards/best-practices.md
- Code style preferences: Use global @~/.agent-os/standards/code-style.md

## Agent OS Workflow Commands

Use these commands to work within the Agent OS framework:

- `/create-spec` - Create a new feature specification
- `/execute-task` - Implement tasks from a spec
- `/update-roadmap` - Modify the product roadmap
- `/log-decision` - Record a product or technical decision

## Tech Stack Summary

**Language:** Python 3.11+ with uv package manager
**Database:** SQLite 3
**AI:** Anthropic Claude API (claude-sonnet-4-20250514)
**CLI:** typer or click (to be decided)
**Output:** rich for formatted terminal display

## Project Structure

```
slack-insights/
├── .agent-os/          # Agent OS documentation
│   ├── product/        # Product vision and decisions
│   └── specs/          # Feature specifications
├── src/                # Source code
├── tests/              # Test suite
├── migrations/         # Database migrations
└── .env.example        # Environment template
```

## Development Standards

### Code Style
- Use tabs for indentation (4-space display)
- Python: snake_case functions, PascalCase classes
- Type hints on all function signatures
- Docstrings for public functions

### Git Workflow
- All work starts with a GitHub issue
- All commits reference issue numbers: `feat: add parser #123`
- All PRs link to issues: `Fixes #123`
- Keep commits focused and descriptive

### Testing Requirements
- Write tests for new functionality
- Maintain test coverage >80%
- Use pytest for all tests
- Mock Anthropic API calls in tests

## Environment Setup

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run tests
pytest
```

## Important Notes

- **Privacy First:** All data stored locally, no cloud sync
- **API Costs:** Anthropic API charges per token, batch efficiently
- **SlackDump Format:** Only supports SlackDump JSON export format
- **Python 3.11+:** Required for modern type hints and performance

## Agent OS Instructions

When working on this project, Claude should:
1. Review relevant product documentation before making changes
2. Create specs for new features before implementation
3. Update tasks.md as work progresses
4. Log significant decisions in decisions.md
5. Follow the roadmap phases defined in roadmap.md

---

*This project uses Agent OS for structured AI-assisted development. Learn more at [buildermethods.com/agent-os](https://buildermethods.com/agent-os)*
