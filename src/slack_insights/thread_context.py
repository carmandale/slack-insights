"""
Thread context module for fetching parent messages in Slack threads.

Preserves conversational context when messages are thread replies.
"""

import sqlite3
from typing import Optional


def get_thread_parents(
	conn: sqlite3.Connection,
	message: dict,
	max_parents: int = 3,
) -> list[dict]:
	"""
	Fetch parent messages for a thread reply.

	Args:
		conn: Database connection
		message: Message dict with potential thread_ts field
		max_parents: Maximum number of parent messages to return (default 3)

	Returns:
		List of parent message dicts, ordered chronologically (oldest first).
		Returns empty list if message is not a thread reply or parents not found.
	"""
	# Check if this message is a thread reply
	thread_ts = message.get("thread_ts")

	if not thread_ts:
		return []

	# Get current message timestamp to filter parents (must be before this message)
	current_ts = message.get("timestamp")

	if not current_ts:
		return []

	# Query for parent messages in the same thread
	# Filter for messages before current timestamp
	# Order by timestamp ascending (oldest first)
	# Limit to max_parents
	query = """
		SELECT 
			id,
			user_id,
			display_name,
			message_text,
			timestamp,
			thread_ts
		FROM conversations
		WHERE thread_ts = ?
		  AND timestamp < ?
		ORDER BY timestamp ASC
		LIMIT ?
	"""

	try:
		cursor = conn.execute(query, (thread_ts, current_ts, max_parents))
		parents = [dict(row) for row in cursor.fetchall()]
		return parents
	except sqlite3.Error:
		# Return empty list on database errors
		return []


def has_thread_context(message: dict) -> bool:
	"""
	Check if a message is part of a thread.

	Args:
		message: Message dict

	Returns:
		True if message has thread_ts field, False otherwise
	"""
	return "thread_ts" in message and message["thread_ts"] is not None


def format_thread_context(
	parent_messages: list[dict],
	indent: str = "  ↳ ",
) -> list[str]:
	"""
	Format parent messages for display.

	Args:
		parent_messages: List of parent message dicts
		indent: String to use for indentation (default "  ↳ ")

	Returns:
		List of formatted strings, one per parent message
	"""
	from datetime import datetime

	formatted = []

	for msg in parent_messages:
		# Format timestamp
		timestamp = msg.get("timestamp")
		if timestamp:
			try:
				dt = datetime.fromtimestamp(float(timestamp))
				time_str = dt.strftime("%H:%M")
			except (ValueError, OSError, TypeError):
				time_str = "??:??"
		else:
			time_str = "??:??"

		# Get display name or user ID
		name = msg.get("display_name") or msg.get("user_id") or "Unknown"

		# Get message text
		text = msg.get("message_text", "")

		# Format line
		line = f"{indent}{time_str} {name}: {text}"
		formatted.append(line)

	return formatted
