-- migrations/001_initial_schema.sql
-- Initial database schema for Slack Insights
-- Created: 2025-10-07
-- Version: 1

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

-- Record migration (only if not already applied)
INSERT OR IGNORE INTO schema_versions (version) VALUES (1);
