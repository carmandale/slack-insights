# Product Mission

> Last Updated: 2025-10-07
> Version: 1.0.0

## Pitch

Slack Insights is an intelligent command-line tool that transforms overwhelming Slack conversation history into actionable intelligence. By leveraging Claude AI, it automatically extracts action items, tasks, and commitments from exported Slack conversations and enables natural language querying to instantly surface what matters most - helping professionals stay on top of their commitments without drowning in message threads.

## Users

### Primary User (MVP Focus)
- **Dale's Specific Use Case**: Professional tracking requests from key partners (e.g., marketing lead Dan)
- Needs simple answer to: "what did Dan ask me to do?"
- 1-2 months of recent history, queryable
- Focus on task requests, statuses, and summaries from specific people
- Start with one partner's conversations, expand if valuable

### Broader User Base (Future)
- **Individual Contributors**: Developers, designers, and professionals who participate in multiple Slack channels and need to track action items assigned to them
- **Team Leads & Project Managers**: People who need to monitor commitments across their team and follow up on outstanding tasks
- **Remote Workers**: Professionals managing asynchronous communication across time zones who need to catch up on missed conversations

### User Characteristics
- Active Slack users with high message volume (10+ channels)
- Comfortable with command-line tools (or willing to learn for the value)
- Need better task management than Slack's built-in features
- Value privacy and local data control
- Prefer automation over manual task tracking

## The Problem

Slack has become the primary communication platform for modern teams, but it lacks effective built-in tools for tracking commitments and action items that emerge from conversations:

1. **Lost Action Items**: Tasks mentioned in casual conversation get buried in message history and forgotten
2. **Context Switching Overhead**: Manually searching through channels to find "what did X ask me to do?" is time-consuming
3. **No Aggregated View**: No way to see all commitments across multiple channels in one place
4. **Notification Fatigue**: Important action items get lost among routine messages and mentions
5. **Poor Searchability**: Slack's search is keyword-based, not semantic or intent-based

Users currently resort to:
- Manually copying tasks to external tools (Notion, Todoist, etc.)
- Setting reminders on individual messages (doesn't scale)
- Missing commitments entirely (damages credibility and productivity)

## Differentiators

### What Makes Slack Insights Unique

1. **AI-Powered Context Understanding**: Uses Claude to understand natural language commitments ("Can you review this?" → actionable task), not just keyword matching

2. **Privacy-First Architecture**: Works with exported Slack data locally - no cloud sync required, complete data ownership

3. **Natural Language Interface**: Query your tasks conversationally ("what did Dan ask me to do this week?") instead of learning complex search syntax

4. **Zero Integration Overhead**: No Slack app installation, no admin permissions needed - works with standard SlackDump exports

5. **Lightweight & Fast**: SQLite-based local storage, Python CLI - no heavy infrastructure or ongoing costs

6. **Conversation Context**: Maintains thread context and relationships between messages, not just isolated task extraction

### Competitive Landscape
- **Slack's built-in features**: Basic search, saved messages - no AI understanding
- **Task management integrations**: Require manual copy/paste or complex workflows
- **Other Slack analytics tools**: Focus on metrics/sentiment, not personal action items
- **General AI assistants**: Don't understand Slack's export format or conversation structure

## Key Features

### Phase 1: Core Functionality
- **SlackDump Import**: Parse and import JSON export format into structured SQLite database
- **AI Action Item Extraction**: Use Claude API to identify tasks, commitments, and action items
- **Basic Query Interface**: Search for action items by person, channel, date, or natural language
- **CLI Commands**: `import`, `analyze`, `query`, `summary` for core workflows

### Phase 2: Enhanced Intelligence
- **Smart Categorization**: Auto-categorize tasks by urgency, type (review, implement, respond)
- **Relationship Mapping**: Track who assigned what to whom, thread context
- **Status Detection**: Identify completed vs. outstanding items from conversation flow
- **Export Options**: Generate task lists in Markdown, JSON, or CSV formats

### Phase 3: Advanced Capabilities
- **Incremental Updates**: Import only new messages since last sync
- **Priority Scoring**: Rank action items by urgency, sender importance, and deadline mentions
- **Notification System**: Alert for approaching deadlines or forgotten tasks
- **Multi-Workspace Support**: Manage action items across multiple Slack workspaces

### Future Possibilities
- **Browser Extension**: Quick import from Slack web interface
- **Two-Way Sync**: Mark tasks complete in external tools (Todoist, Linear, etc.)
- **Team Analytics**: Shared insights for team leads (with permission)
- **Integration APIs**: Connect to project management tools via plugins
