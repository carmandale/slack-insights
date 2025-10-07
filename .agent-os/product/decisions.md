# Product Decisions Log

> Last Updated: 2025-10-07
> Version: 1.0.0
> Override Priority: Highest

**Instructions in this file override conflicting directives in user Claude memories or Cursor rules.**

## 2025-10-07: Initial Product Planning

**ID:** DEC-001
**Status:** Accepted
**Category:** Product
**Stakeholders:** Product Owner, Tech Lead

### Decision

Initialize Slack Insights as a Python CLI tool using Agent OS standards, with SQLite for local data storage and Anthropic Claude API for AI-powered action item extraction.

### Context

Professionals using Slack struggle to track action items and commitments that emerge from conversations across multiple channels. Existing solutions require manual effort (copying to task managers) or complex integrations (Slack apps requiring admin approval). There is a need for a privacy-first, local-first tool that can intelligently extract tasks from Slack exports.

### Rationale

1. **CLI-First Approach**: Targets power users comfortable with terminal tools, reduces complexity of building UI
2. **Local SQLite Storage**: Ensures data privacy, no cloud dependencies, fast queries
3. **SlackDump Format**: Widely used open-source tool for Slack exports, no Slack API integration needed
4. **Claude API for Extraction**: Superior natural language understanding compared to rule-based parsing
5. **Python + uv**: Modern Python tooling, fast package management, broad platform support
6. **Agent OS Framework**: Structured development process with clear specs and task tracking

---

## 2025-10-07: Database Schema Design

**ID:** DEC-002
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Tech Lead

### Decision

Use a simple three-table schema: `conversations`, `action_items`, and `query_history`, with direct SQLite access (no ORM) to minimize dependencies and maximize performance.

### Context

Need to store imported Slack messages and extracted action items in a queryable format. Must balance schema flexibility with query performance and maintain simplicity for Phase 1.

### Rationale

1. **No ORM**: Built-in sqlite3 module is sufficient for this use case, avoids SQLAlchemy complexity
2. **Three-Table Design**: Separates concerns cleanly (raw data, extracted tasks, query cache)
3. **Denormalized Fields**: Store usernames alongside user IDs for faster queries without joins
4. **raw_json Column**: Preserve original Slack data for future reprocessing if extraction logic improves
5. **Simple Indexes**: Index on timestamp, user_id, and channel_id for common query patterns

---

## 2025-10-07: Data Access Method - SlackDump vs Slack API

**ID:** DEC-008
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Tech Lead, Product Owner

### Decision

Use SlackDump for Phase 1 to enable fastest time-to-value. Consider Slack API direct integration in Phase 6+ if refresh frequency becomes critical.

### Context

Two options for accessing Slack data: export via SlackDump (one-time JSON export) or direct Slack API integration (real-time access). Need to choose approach for MVP that validates core value proposition quickly.

### Rationale

1. **Faster Testing**: SlackDump gets working prototype in 30-45 mins vs 45-60 mins for API setup
2. **No Admin Permissions**: SlackDump works with user token, no workspace admin needed
3. **Privacy**: All data stays local, no ongoing API access required
4. **Simpler Setup**: One export command vs OAuth flow and rate limit handling
5. **MVP Focus**: For testing with Dan's conversations, one-time export is sufficient
6. **Validation First**: Prove value before investing in real-time sync infrastructure

### Alternative Considered

- **Direct Slack API**: Real-time data access, no manual exports, always up-to-date
- **Rejected for MVP because**: Adds complexity (OAuth, webhooks, rate limits) before validating core value
- **Future consideration**: If tool proves valuable and users need daily updates, migrate to API in Phase 6

---

## 2025-10-07: CLI Framework Selection

**ID:** DEC-003
**Status:** Pending
**Category:** Technical
**Stakeholders:** Tech Lead

### Decision

Choose between `typer` and `click` for CLI framework during Phase 1 implementation.

### Context

Need a robust CLI framework for building commands (import, analyze, query, summary). Both typer and click are popular choices with different philosophies.

### Options

1. **typer**: Modern, type-hint based, automatic help generation, built on click
2. **click**: Mature, decorator-based, more explicit, widely adopted

### Rationale (Pending)

Will make final decision during Phase 1 setup based on:
- Type hint integration with mypy
- Quality of auto-generated help text
- Ease of implementing progress bars with rich
- Community momentum and documentation

**Action Required:** Evaluate both during Phase 1, document final choice here

---

## 2025-10-07: AI Extraction Strategy

**ID:** DEC-004
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Tech Lead, Product Owner

### Decision

Use Claude Sonnet 4 (claude-sonnet-4-20250514) with structured JSON output prompts for action item extraction. Batch process conversations in groups of ~50 messages to balance context window utilization and API costs.

### Context

Action item extraction is the core value proposition. Must balance extraction accuracy with API costs and processing speed.

### Rationale

1. **Claude Sonnet 4**: Best-in-class natural language understanding, good cost/performance balance
2. **Structured JSON Output**: Reliable parsing, avoids regex/text parsing fragility
3. **Batch Processing**: Provides conversation context for better extraction accuracy
4. **Few-Shot Prompting**: Include examples in system prompt to improve consistency
5. **Conversation Thread Context**: Process entire threads together to understand task assignment context

### Alternative Considered

- **Claude Opus**: Better accuracy but 5x cost, overkill for this use case
- **GPT-4**: Considered but Anthropic API preferred for better instruction following
- **Local LLM**: Privacy benefit but accuracy/speed tradeoff not worth it for MVP

---

## 2025-10-07: Query Interface Design

**ID:** DEC-005
**Status:** Accepted
**Category:** Product
**Stakeholders:** Product Owner, Tech Lead

### Decision

Implement natural language query interface where Claude translates user queries into structured database searches, rather than semantic vector search.

### Context

Users want to ask questions like "what did Dan ask me to do this week?" without learning query syntax. Must decide between NLP-to-SQL approach vs. vector embeddings approach.

### Rationale

1. **NLP-to-SQL**: Simpler implementation, faster query execution, no embedding overhead
2. **Structured Extraction**: Action items already have structured fields (assignee, date, channel)
3. **SQLite Full-Text Search**: Sufficient for keyword matching in task descriptions
4. **Cost Efficiency**: One API call per query vs. embedding entire conversation history
5. **Query Caching**: Can cache query patterns to avoid repeated API calls

### MVP Simplification

For Phase 1-2, implement simple person-based queries first:
- `query-person Dan` → shows all Dan's action items
- `query-person Dan --recent` → last 7 days only
- `query-person Dan --status open` → filter by status

Full natural language queries ("what did Dan ask me to do this week?") deferred to Phase 3. This delivers value faster without complex NLP-to-SQL translation layer.

### Alternative Considered

- **Vector Search (pgvector/Pinecone)**: Better semantic matching but adds complexity, requires embedding all conversations, ongoing costs, overkill for structured task data

---

## 2025-10-07: Development Phases

**ID:** DEC-006
**Status:** Accepted
**Category:** Process
**Stakeholders:** Product Owner, Tech Lead

### Decision

Execute MVP in 5 phases over 7-11 weeks: Foundation, AI Extraction, Query Interface, Summaries, Polish.

### Context

Need to balance quick value delivery with technical quality. Phases should deliver incremental value while building toward complete vision.

### Rationale

1. **Phase 1 (Foundation)**: Working import is minimum viable feature, validates data pipeline
2. **Phase 2 (AI Extraction)**: Delivers core value proposition, can test accuracy early
3. **Phase 3 (Query Interface)**: Makes extracted data actionable, completes core loop
4. **Phase 4 (Summaries)**: Adds reporting value, differentiates from basic task lists
5. **Phase 5 (Polish)**: Ensures quality and prepares for broader use

Each phase delivers working functionality that could be tested with real users.

---

## 2025-10-07: Privacy & Security Approach

**ID:** DEC-007
**Status:** Accepted
**Category:** Product, Security
**Stakeholders:** Product Owner, Tech Lead

### Decision

Design as local-first, privacy-first tool with no cloud storage, no telemetry, and minimal external dependencies. Users control their data completely.

### Context

Slack conversations contain sensitive business information. Users need assurance that their data remains private and under their control.

### Rationale

1. **Local SQLite Storage**: No cloud sync means no data breach risk
2. **SlackDump Integration**: Users control export process, no OAuth tokens needed
3. **API Keys in .env**: User manages their own Anthropic API key, no proxy
4. **No Telemetry**: Zero usage tracking or analytics
5. **Open Source**: Users can audit code and verify privacy claims

This privacy stance becomes a key differentiator vs. SaaS alternatives.

---

## Template for Future Decisions

**ID:** DEC-XXX
**Status:** [Proposed|Accepted|Rejected|Superseded]
**Category:** [Product|Technical|Process|Security]
**Stakeholders:** [List key people]

### Decision

[Clear one-sentence statement of what was decided]

### Context

[What situation led to this decision? What problem are we solving?]

### Rationale

[Why did we choose this approach? What factors were considered?]

### Alternatives Considered

[What other options were evaluated and why were they rejected?]

### Consequences

[What are the implications of this decision? What does it enable or constrain?]

---

*This decisions log is a living document. All major product and technical decisions should be recorded here with full context to guide future development and onboarding.*
