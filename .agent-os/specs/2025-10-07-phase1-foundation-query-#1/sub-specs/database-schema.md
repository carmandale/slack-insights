# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/spec.md

> Created: 2025-10-07
> Version: 1.0.0

## Schema Overview

Two core tables for Phase 1:
1. **conversations** - Raw Slack messages from SlackDump imports
2. **action_items** - Extracted tasks from Claude API analysis

## Table: conversations

Stores all imported Slack messages with full metadata.

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    channel_name TEXT,
    user_id TEXT NOT NULL,
    username TEXT,
    timestamp REAL NOT NULL,
    message_text TEXT NOT NULL,
    thread_ts REAL,
    message_type TEXT DEFAULT 'message',
    raw_json TEXT,
    imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, timestamp)
);

-- Indexes for fast queries
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX idx_conversations_channel_id ON conversations(channel_id);
CREATE INDEX idx_conversations_thread_ts ON conversations(thread_ts);
```

### Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | INTEGER | Auto-incrementing primary key | 1, 2, 3... |
| channel_id | TEXT | Slack channel/DM ID | "D3Y7V95DX" |
| channel_name | TEXT | Human-readable channel name | "Dan Ferguson" |
| user_id | TEXT | Slack user ID who sent message | "U2X1504QH" |
| username | TEXT | Display name of sender | "Dan Ferguson" |
| timestamp | REAL | Slack message timestamp (Unix epoch) | 1485881960.000002 |
| message_text | TEXT | Message content | "Can you review the PR?" |
| thread_ts | REAL | Thread parent timestamp (null if not threaded) | 1485881960.000002 |
| message_type | TEXT | Slack message type | "message", "edited", etc. |
| raw_json | TEXT | Full original JSON for reprocessing | {...} |
| imported_at | DATETIME | When message was imported | "2025-10-07 08:41:00" |

### Unique Constraint
`UNIQUE(channel_id, timestamp)` prevents duplicate imports of the same message.

### Rationale
- **Denormalized usernames**: Faster queries, no joins needed
- **raw_json storage**: Enables reprocessing with improved extraction logic
- **timestamp as REAL**: Matches Slack's format, supports fractional seconds
- **Indexes**: Optimize common queries (by user, date range, channel)

## Table: action_items

Stores extracted action items from Claude API analysis.

```sql
CREATE TABLE action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    task_description TEXT NOT NULL,
    assignee_user_id TEXT,
    assignee_username TEXT,
    assigner_user_id TEXT,
    assigner_username TEXT,
    mentioned_date TEXT,
    status TEXT DEFAULT 'open',
    urgency TEXT DEFAULT 'normal',
    context_quote TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Indexes for query performance
CREATE INDEX idx_action_items_assignee ON action_items(assignee_user_id);
CREATE INDEX idx_action_items_assigner ON action_items(assigner_user_id);
CREATE INDEX idx_action_items_status ON action_items(status);
CREATE INDEX idx_action_items_mentioned_date ON action_items(mentioned_date);
```

### Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | INTEGER | Auto-incrementing primary key | 1, 2, 3... |
| conversation_id | INTEGER | References conversations.id | 4582 |
| task_description | TEXT | What needs to be done | "Review Orchestrator App content" |
| assignee_user_id | TEXT | Who should do the task (Dale) | "U1234ABCD" |
| assignee_username | TEXT | Display name of assignee | "Dale Carman" |
| assigner_user_id | TEXT | Who requested the task (Dan) | "U2X1504QH" |
| assigner_username | TEXT | Display name of assigner | "Dan Ferguson" |
| mentioned_date | TEXT | Date task was mentioned | "2025-10-05" |
| status | TEXT | Task status | "open", "completed", "unknown" |
| urgency | TEXT | Task priority | "normal", "high", "low" |
| context_quote | TEXT | Relevant quote from conversation | "Did you review the content..." |
| extracted_at | DATETIME | When Claude extracted this item | "2025-10-07 08:41:00" |

### Foreign Key
`FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE` ensures data integrity. If a conversation is deleted, its action items are also removed.

### Rationale
- **Separate table**: Enables re-extraction without losing import data
- **Denormalized names**: Fast queries without joins to conversations table
- **mentioned_date as TEXT**: Easier date range queries (YYYY-MM-DD format)
- **context_quote**: Helps validate extraction accuracy
- **status field**: Enables filtering open vs completed tasks

## Migration: Initial Schema (001)

```sql
-- migrations/001_initial_schema.sql

-- Version tracking table
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    channel_name TEXT,
    user_id TEXT NOT NULL,
    username TEXT,
    timestamp REAL NOT NULL,
    message_text TEXT NOT NULL,
    thread_ts REAL,
    message_type TEXT DEFAULT 'message',
    raw_json TEXT,
    imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_channel_id ON conversations(channel_id);
CREATE INDEX IF NOT EXISTS idx_conversations_thread_ts ON conversations(thread_ts);

-- Action items table
CREATE TABLE IF NOT EXISTS action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    task_description TEXT NOT NULL,
    assignee_user_id TEXT,
    assignee_username TEXT,
    assigner_user_id TEXT,
    assigner_username TEXT,
    mentioned_date TEXT,
    status TEXT DEFAULT 'open',
    urgency TEXT DEFAULT 'normal',
    context_quote TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_action_items_assignee ON action_items(assignee_user_id);
CREATE INDEX IF NOT EXISTS idx_action_items_assigner ON action_items(assigner_user_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
CREATE INDEX IF NOT EXISTS idx_action_items_mentioned_date ON action_items(mentioned_date);

-- Record migration
INSERT INTO schema_versions (version) VALUES (1);
```

## Query Examples

### Import Phase Queries

**Insert conversation:**
```sql
INSERT INTO conversations
    (channel_id, channel_name, user_id, username, timestamp, message_text, thread_ts, raw_json)
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?);
```

**Check for existing message (avoid duplicates):**
```sql
SELECT id FROM conversations
WHERE channel_id = ? AND timestamp = ?;
```

### Analysis Phase Queries

**Get unanalyzed conversations:**
```sql
SELECT id, user_id, message_text, timestamp
FROM conversations
WHERE id NOT IN (SELECT conversation_id FROM action_items)
ORDER BY timestamp ASC
LIMIT 100;
```

**Insert extracted action item:**
```sql
INSERT INTO action_items
    (conversation_id, task_description, assignee_user_id, assignee_username,
     assigner_user_id, assigner_username, mentioned_date, status, urgency, context_quote)
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
```

### Query Phase Queries

**Query action items by person (assigner):**
```sql
SELECT
    task_description,
    mentioned_date,
    status,
    urgency,
    context_quote,
    c.timestamp as original_timestamp
FROM action_items ai
JOIN conversations c ON ai.conversation_id = c.id
WHERE ai.assigner_username LIKE ?
ORDER BY c.timestamp DESC;
```

**Filter by status:**
```sql
SELECT task_description, mentioned_date, context_quote
FROM action_items ai
JOIN conversations c ON ai.conversation_id = c.id
WHERE ai.assigner_username LIKE ?
  AND ai.status = ?
ORDER BY c.timestamp DESC;
```

**Filter by date range (recent - last 7 days):**
```sql
SELECT task_description, mentioned_date, status, context_quote
FROM action_items ai
JOIN conversations c ON ai.conversation_id = c.id
WHERE ai.assigner_username LIKE ?
  AND date(c.timestamp, 'unixepoch') >= date('now', '-7 days')
ORDER BY c.timestamp DESC;
```

## Performance Considerations

### Index Strategy
- **Primary queries**: Filter by assigner_username (Dan) + status + date
- **Indexes cover**: All WHERE clause fields for fast lookups
- **Trade-off**: Slower writes, faster reads (acceptable for batch imports)

### Expected Performance
- **Import**: 10,000 inserts in ~30 seconds (with transaction batching)
- **Query**: Sub-second results for typical filters (1000s of action items)
- **Storage**: ~1KB per message, ~500 bytes per action item

### Optimization Notes
- Use transactions for batch imports (`BEGIN; ... COMMIT;`)
- VACUUM database periodically to reclaim space
- ANALYZE tables after large imports to update query planner stats
