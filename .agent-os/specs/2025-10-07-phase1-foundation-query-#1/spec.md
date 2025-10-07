# Spec Requirements Document

> Spec: Phase 1 - Foundation & Basic Query
> Created: 2025-10-07
> GitHub Issue: #1
> Status: Planning

## Overview

Build the foundation of Slack Insights with working import, extraction, and query functionality. This phase delivers a functional CLI tool that imports Dan's Slack conversations from SlackDump exports, extracts action items using Claude API, and enables simple person-based queries.

## User Stories

### Story 1: Import Dan's Conversations
As Dale, I want to import my Slack conversations with Dan from a SlackDump export, so that I can analyze them for action items without manual parsing.

**Workflow:**
1. Export Dan's DMs using SlackDump (already completed in Phase 0)
2. Run: `slack-insights import dan-messages/D3Y7V95DX.json`
3. See progress bar showing import status
4. Receive confirmation: "Imported 9,960 messages from Dan Ferguson"
5. Messages stored in local SQLite database

**Problem Solved:** Manual tracking of Dan's requests across thousands of messages is impossible. Automated import makes the data queryable.

### Story 2: Extract Action Items with AI
As Dale, I want Claude to automatically extract action items from imported conversations, so that I don't have to read through every message manually.

**Workflow:**
1. After import, run: `slack-insights analyze`
2. See progress: "Analyzing 9,960 messages... Processing batch 1/100"
3. Claude extracts tasks, requests, and commitments
4. Results stored in database with context
5. Receive summary: "Found 247 action items (142 open, 105 completed)"

**Problem Solved:** Manually identifying action items in casual conversation is time-consuming and error-prone. AI extraction is faster and more consistent.

### Story 3: Query Dan's Action Items
As Dale, I want to query "what did Dan ask me to do?", so that I can see my outstanding tasks from him.

**Workflow:**
1. Run: `slack-insights query-person Dan`
2. See formatted table with:
   - Task description
   - Date mentioned
   - Status (open/completed)
   - Context quote from conversation
3. Filter results: `slack-insights query-person Dan --recent` (last 7 days)
4. Check specific status: `slack-insights query-person Dan --status open`

**Problem Solved:** Finding specific requests buried in Slack history takes too long. Direct queries provide instant answers.

## Spec Scope

1. **SlackDump JSON Parser** - Parse SlackDump export format, extract message metadata and text, handle threaded conversations and various message types
2. **SQLite Database Foundation** - Design schema for conversations and action_items tables, implement database initialization and migrations, create indexes for fast queries
3. **Anthropic API Integration** - Set up Claude API client with error handling, implement batch processing for efficiency, add retry logic for failed requests
4. **Action Item Extraction** - Use Claude to identify tasks, requests, and commitments from conversation text, extract assignee/assigner from context, determine urgency and status
5. **CLI Import Command** - `slack-insights import <file.json>` with progress bar, summary statistics, and error handling
6. **CLI Query Command** - `slack-insights query-person <name>` with filtering options (--recent, --status), formatted table output, and context display
7. **Project Setup** - Initialize Python project with uv, configure pytest/ruff/mypy, create .env.example and requirements.txt

## Out of Scope

- Multi-person support (Phase 2)
- Natural language queries beyond person name (Phase 3)
- Web interface or GUI
- Real-time Slack integration
- Export to external task managers
- Channel-based analysis (focus on DMs only for Phase 1)

## Expected Deliverable

1. Working CLI tool that imports Dan's 9,960 messages in under 2 minutes
2. Claude extraction finds action items with 80%+ accuracy (validated against Phase 0 results)
3. Query command returns results in under 2 seconds
4. Clean error messages for common failures (missing API key, invalid JSON, etc.)
5. Test coverage for parser, database, and extraction logic

## Spec Documentation

- Tasks: @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/tasks.md
- Technical Specification: @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/sub-specs/technical-spec.md
- Database Schema: @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/sub-specs/database-schema.md
- API Specification: @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/sub-specs/api-spec.md
- Tests: @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/sub-specs/tests.md
