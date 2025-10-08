-- migrations/002_add_display_names.sql
-- Add display_name column for resolved user names
-- Created: 2025-10-08
-- Version: 2

-- Add display_name column to conversations
ALTER TABLE conversations ADD COLUMN display_name TEXT;

-- Create index for faster queries on display_name
CREATE INDEX IF NOT EXISTS idx_conversations_display_name ON conversations(display_name);

-- Record migration (only if not already applied)
INSERT OR IGNORE INTO schema_versions (version) VALUES (2);
