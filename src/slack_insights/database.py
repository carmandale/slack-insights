"""
Database operations for Slack Insights.

Handles SQLite database initialization, migrations, and CRUD operations.
"""

import sqlite3
from pathlib import Path
from typing import Optional


def init_database(db_path: str = "slack_insights.db") -> sqlite3.Connection:
	"""
	Initialize SQLite database with schema and run all migrations.

	Args:
		db_path: Path to database file

	Returns:
		SQLite connection object with foreign keys enabled
	"""
	# Create database connection
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row  # Enable column access by name

	# Enable WAL mode for concurrent access (web GUI support)
	conn.execute("PRAGMA journal_mode=WAL")

	# Set busy timeout for concurrent access (5 seconds)
	conn.execute("PRAGMA busy_timeout = 5000")

	# Enable foreign key constraints
	conn.execute("PRAGMA foreign_keys = ON")

	# Get migrations directory
	migrations_dir = Path(__file__).parent.parent.parent / "migrations"

	if not migrations_dir.exists():
		return conn

	# Get all migration files sorted by name
	migration_files = sorted(migrations_dir.glob("*.sql"))

	# Run each migration
	for migration_file in migration_files:
		# Extract version number from filename (e.g., "001_initial_schema.sql" -> 1)
		version = int(migration_file.stem.split("_")[0])
		
		# Check if schema_versions table exists first
		cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_versions'")
		table_exists = cursor.fetchone() is not None
		
		# Check if this migration was already applied (only if table exists)
		if table_exists:
			cursor = conn.execute("SELECT version FROM schema_versions WHERE version = ?", (version,))
			if cursor.fetchone():
				continue  # Skip already applied migrations

		# Run migration
		with open(migration_file, "r") as f:
			migration_sql = f.read()
			conn.executescript(migration_sql)
			conn.commit()

	return conn


def insert_conversation(conn: sqlite3.Connection, message: dict) -> int:
	"""
	Insert conversation message into database.

	Handles duplicate detection using UNIQUE constraint on (channel_id, timestamp).
	If message already exists, returns existing conversation_id instead of raising error.

	Args:
		conn: Database connection
		message: Parsed message dict with keys:
			- channel_id (required)
			- channel_name (optional)
			- user_id (required)
			- username (optional, deprecated)
			- display_name (optional)
			- timestamp (required)
			- message_text (required)
			- thread_ts (optional)
			- message_type (optional, defaults to 'message')
			- raw_json (optional)

	Returns:
		conversation_id (int)
	"""
	# Check if message already exists
	cursor = conn.execute(
		"SELECT id FROM conversations WHERE channel_id = ? AND timestamp = ?",
		(message.get("channel_id"), message.get("timestamp")),
	)
	existing = cursor.fetchone()

	if existing:
		return int(existing[0])

	# Insert new conversation
	cursor = conn.execute(
		"""
		INSERT INTO conversations
			(channel_id, channel_name, user_id, username, display_name, timestamp,
			message_text, thread_ts, message_type, raw_json)
		VALUES
			(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		(
			message.get("channel_id"),
			message.get("channel_name"),
			message.get("user_id"),
			message.get("username"),
			message.get("display_name"),
			message.get("timestamp"),
			message.get("message_text"),
			message.get("thread_ts"),
			message.get("message_type", "message"),
			message.get("raw_json"),
		),
	)
	conn.commit()
	return int(cursor.lastrowid or 0)


def insert_action_item(conn: sqlite3.Connection, item: dict) -> int:
	"""
	Insert extracted action item into database.

	Args:
		conn: Database connection
		item: Extracted action item dict with keys:
			- conversation_id (required)
			- task_description (required)
			- assignee_user_id (optional)
			- assignee_username (optional)
			- assigner_user_id (optional)
			- assigner_username (optional)
			- mentioned_date (optional)
			- status (optional, defaults to 'open')
			- urgency (optional, defaults to 'normal')
			- context_quote (optional)

	Returns:
		action_item_id (int)

	Raises:
		sqlite3.IntegrityError: If conversation_id doesn't exist (foreign key constraint)
	"""
	cursor = conn.execute(
		"""
		INSERT INTO action_items
			(conversation_id, task_description, assignee_user_id,
			assignee_username, assigner_user_id, assigner_username,
			mentioned_date, status, urgency, context_quote)
		VALUES
			(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		(
			item.get("conversation_id"),
			item.get("task_description"),
			item.get("assignee_user_id"),
			item.get("assignee_username"),
			item.get("assigner_user_id"),
			item.get("assigner_username"),
			item.get("mentioned_date"),
			item.get("status", "open"),
			item.get("urgency", "normal"),
			item.get("context_quote"),
		),
	)
	conn.commit()
	return int(cursor.lastrowid or 0)


def get_conversation(conn: sqlite3.Connection, conversation_id: int) -> Optional[dict]:
	"""
	Retrieve a conversation by ID.

	Args:
		conn: Database connection
		conversation_id: ID of conversation to retrieve

	Returns:
		dict with conversation data, or None if not found
	"""
	cursor = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
	row = cursor.fetchone()

	if row:
		return dict(row)
	return None


def get_action_items_by_assigner(
	conn: sqlite3.Connection,
	assigner_name: str,
	status: Optional[str] = None,
	recent_days: Optional[int] = None,
) -> list[dict]:
	"""
	Query action items by assigner username.

	Args:
		conn: Database connection
		assigner_name: Name of person who assigned tasks (e.g., "Dan Ferguson")
		status: Optional filter by status ("open", "completed", etc.)
		recent_days: Optional filter to last N days

	Returns:
		List of action item dicts with conversation context
	"""
	# Escape LIKE wildcards to prevent unintended matches
	escaped_name = assigner_name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

	query = """
		SELECT
			ai.id,
			ai.task_description,
			ai.mentioned_date,
			ai.status,
			ai.urgency,
			ai.context_quote,
			ai.assignee_username,
			ai.assigner_username,
			c.timestamp as original_timestamp,
			c.channel_name,
			c.message_text
		FROM action_items ai
		JOIN conversations c ON ai.conversation_id = c.id
		WHERE ai.assigner_username LIKE ? ESCAPE '\\'
	"""

	params = [f"%{escaped_name}%"]

	if status:
		query += " AND ai.status = ?"
		params.append(status)

	if recent_days:
		query += " AND date(c.timestamp, 'unixepoch') >= date('now', ? || ' days')"
		params.append(f"-{recent_days}")

	query += " ORDER BY c.timestamp DESC"

	cursor = conn.execute(query, params)
	return [dict(row) for row in cursor.fetchall()]
