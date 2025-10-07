# Product Roadmap

> Last Updated: 2025-10-07
> Version: 1.0.0
> Status: Planning

## Phase 0: Quick Validation (2-4 hours)

**Goal:** Prove the concept works with Dale's actual data before building full system.

**Success Criteria:**
- Export Dan's DMs successfully using SlackDump
- Extract action items from real conversations
- Dale validates that results are useful and accurate
- Confirm approach is worth full implementation

### Must-Have Tasks

1. **SlackDump Setup**
   - Install SlackDump: `brew install slackdump`
   - Get Slack user token from https://api.slack.com/custom-integrations/legacy-tokens
   - Verify token works with `slackdump -list-channels`

2. **Export Dan's Conversations**
   - Identify Dan's user ID or channel
   - Export last 2 months: `slackdump -export dan-convos.zip -dm @Dan`
   - Verify JSON export format and content

3. **Quick Python Script**
   - Load JSON file
   - Send to Claude API with prompt: "Extract all tasks, requests, and action items that Dan requested from Dale"
   - Output results to terminal or markdown file

4. **Validation**
   - Dale reviews extracted action items
   - Confirms accuracy (does it find real tasks?)
   - Identifies missing items or false positives
   - Decision: proceed to Phase 1 or adjust approach

**Estimated Effort:** 2-4 hours
**Dependencies:** None
**Risks:** SlackDump token issues, Dan's messages not in expected format

**Deliverable:** Proof that AI can extract useful action items from real Slack data

---

## Phase 1: Foundation & Basic Query (2-3 weeks)

**Goal:** Import Dan's conversations AND answer "what did Dan ask me to do?" - delivering immediate value.

**Success Criteria:**
- Successfully parse SlackDump JSON export files
- Store conversations in structured SQLite database
- Extract action items from Dan's messages using Claude
- Simple query command: `slack-insights query-person Dan`
- Results show: task description, date, context link
- Handle malformed data gracefully with error reporting
- CLI provides clear feedback on import and analysis progress

### Must-Have Features

1. **Project Setup & Structure**
   - Initialize Python project with uv
   - Set up directory structure and package layout
   - Configure development tools (pytest, ruff, mypy)
   - Create .env.example and .gitignore

2. **SlackDump JSON Parser**
   - Parse SlackDump export JSON format
   - Extract message metadata (user, timestamp, channel, thread)
   - Handle message types (regular, threaded, edited)
   - Validate JSON structure and report errors

3. **Database Foundation**
   - Design and implement SQLite schema
   - Create `conversations` table with indexes
   - Build database initialization and migration system
   - Implement basic CRUD operations

4. **Anthropic API Integration**
   - Set up anthropic Python SDK
   - Implement API key management via .env
   - Create basic prompt for action item extraction
   - Add error handling for API calls

5. **Action Item Extraction (Basic)**
   - Extract tasks from imported conversations
   - Identify assignee (Dale) and assigner (Dan)
   - Store in `action_items` table with link to source message
   - Basic categorization (task description, date)

6. **CLI Import Command**
   - `slack-insights import <file.json>` command
   - Progress bar for large imports using rich
   - Summary statistics (messages imported, channels found)
   - Automatically triggers analysis after import
   - Error handling and validation feedback

7. **CLI Query Command (Simple)**
   - `slack-insights query-person <name>` command
   - Display action items in rich formatted table
   - Show: task description, date, status, message context
   - Filter options: --recent (last 7 days), --status (open/closed)

**Estimated Effort:** 20-28 hours
**Dependencies:** Phase 0 validation complete
**Risks:** SlackDump format changes, Claude API accuracy, edge cases in message structures

---

## Phase 2: Enhanced Extraction & Multi-Person Support (2-3 weeks)

**Goal:** Improve extraction accuracy and support multiple people beyond Dan.

**Success Criteria:**
- Extract action items with 85%+ accuracy on test dataset
- Support querying multiple people (Dan, other partners, channels)
- Better context understanding (urgency, deadlines, dependencies)
- Batch processing for efficiency
- Handle API rate limits and errors gracefully

### Must-Have Features

1. **Improved Extraction Prompts**
   - Enhanced few-shot examples for better accuracy
   - Urgency detection (ASAP, urgent, by EOD, etc.)
   - Deadline extraction (dates, relative times)
   - Context preservation (why task matters, dependencies)

2. **Batch Processing**
   - Process conversations in batches of ~50 messages
   - Optimize API calls for cost efficiency
   - Add retry logic and exponential backoff
   - Rate limit handling (requests per minute)

3. **Multi-Person Support**
   - Import and analyze conversations from multiple people
   - Query by person: `slack-insights query-person <name>`
   - List all people with action items
   - Compare action items across people

4. **Enhanced Database Schema**
   - Add fields: urgency, deadline, dependencies
   - Store extraction confidence scores
   - Add person/channel aggregation tables
   - Improve indexes for multi-person queries

5. **CLI Enhancements**
   - `slack-insights analyze --person <name>` for targeted analysis
   - `slack-insights list-people` to see all contacts
   - Better progress indicators for batch processing
   - Summary report with accuracy metrics

**Estimated Effort:** 18-25 hours
**Dependencies:** Phase 1 complete
**Risks:** API costs, prompt engineering complexity, accuracy tuning

---

## Phase 3: Natural Language Query Interface (1-2 weeks)

**Goal:** Enable users to query their action items using natural language.

**Success Criteria:**
- Answer queries like "what did Dan ask me to do?"
- Return relevant results ranked by relevance
- Support filtering by person, channel, date, status
- Query response time < 2 seconds

### Must-Have Features

1. **Query Understanding Layer**
   - Use Claude to parse natural language queries
   - Extract search parameters (person, date, channel, keywords)
   - Map natural language to database query structure
   - Handle ambiguous queries with clarifying questions

2. **Query Execution Engine**
   - Build dynamic SQL query generator
   - Implement full-text search on task descriptions
   - Add filters for date ranges, channels, users
   - Rank results by relevance and recency

3. **CLI Query Command**
   - `slack-insights query "what did X ask me to do?"` command
   - Display results in formatted rich tables
   - Show context (link to conversation, date, channel)
   - Option to export results to JSON/CSV

4. **Query History & Caching**
   - Store queries in `query_history` table
   - Cache common query patterns
   - Learn from query refinements
   - Suggest related queries

**Estimated Effort:** 12-18 hours
**Dependencies:** Phase 2 complete
**Risks:** Query ambiguity, performance on large datasets

---

## Phase 4: Summaries & Reporting (1 week)

**Goal:** Generate actionable summaries and reports from extracted data.

**Success Criteria:**
- Generate daily/weekly summary of action items
- Identify overdue or forgotten tasks
- Export reports in multiple formats
- Visual progress indicators in terminal

### Must-Have Features

1. **Summary Generation**
   - Daily/weekly action item digest
   - Group by assignee, channel, or urgency
   - Highlight new vs. outstanding tasks
   - Use Claude to generate natural language summaries

2. **CLI Summary Command**
   - `slack-insights summary [--period=week]` command
   - Rich formatted output with colors and tables
   - Option to filter by user, channel, or date
   - Export to Markdown or plain text

3. **Status Tracking**
   - Detect task completion from conversation context
   - Mark tasks as open/in-progress/completed
   - Track task age and identify stale items
   - Command to manually update task status

4. **Export Functionality**
   - Export to Markdown checklist format
   - Export to CSV for external tools
   - Export to JSON for API integration
   - Template customization for different formats

**Estimated Effort:** 8-12 hours
**Dependencies:** Phase 3 complete
**Risks:** Format compatibility, user workflow preferences

---

## Phase 5: Polish & Optimization (1-2 weeks)

**Goal:** Refine user experience, improve performance, and prepare for broader use.

**Success Criteria:**
- Comprehensive test coverage (>80%)
- Documentation complete (README, CLI help)
- Performance optimized for 50K+ messages
- Ready for beta user testing

### Must-Have Features

1. **Performance Optimization**
   - Batch API calls for faster analysis
   - Database query optimization and indexing
   - Streaming import for large files
   - Caching strategy for repeated queries

2. **Error Handling & Validation**
   - Graceful failure for API errors
   - Clear error messages with suggested fixes
   - Validate user inputs comprehensively
   - Retry logic with exponential backoff

3. **Testing & Quality**
   - Unit tests for all core functions
   - Integration tests for API calls (mocked)
   - End-to-end CLI tests
   - Test coverage reporting

4. **Documentation & Help**
   - Comprehensive README with examples
   - CLI help text for all commands
   - Troubleshooting guide
   - Sample SlackDump export for testing

5. **Configuration & Customization**
   - Config file for user preferences
   - Customize action item categories
   - Adjust Claude prompt templates
   - Configure output formatting

**Estimated Effort:** 10-15 hours
**Dependencies:** Phases 1-4 complete
**Risks:** Scope creep, over-engineering

---

## Post-MVP Enhancements (Future)

### Incremental Import (Phase 6)
- Import only new messages since last sync
- Detect duplicate messages
- Update existing conversations

### Advanced AI Features (Phase 7)
- Priority scoring for action items
- Deadline extraction from text
- Sentiment analysis for urgency
- Smart notifications

### Multi-Workspace Support (Phase 8)
- Manage multiple Slack workspaces
- Unified query across workspaces
- Workspace-specific configurations

### Integration Ecosystem (Phase 9)
- Export to Todoist, Linear, Notion
- Browser extension for quick import
- API for third-party integrations

---

## Total Estimated Timeline

- **Phase 0:** 2-4 hours (validation)
- **Phase 1:** 2-3 weeks
- **Phase 2:** 2-3 weeks
- **Phase 3:** 1-2 weeks
- **Phase 4:** 1 week
- **Phase 5:** 1-2 weeks

**Total MVP Delivery:** 7-11 weeks + initial validation (37-59 hours of focused development)

## Success Metrics

- **Technical:** Successfully process 10K+ messages, 90%+ extraction accuracy
- **Usage:** Beta users find 50+ action items in their Slack history
- **Performance:** Query results in <2s, import at 100+ messages/second
- **Quality:** <5 critical bugs reported in first month of beta
