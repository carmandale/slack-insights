"""
SlackDump JSON parser.

Parses SlackDump export format and extracts message data for database storage.
"""

import json
from pathlib import Path
from typing import Optional


class ParserError(Exception):
	"""Custom exception for parser errors."""

	pass


def parse_slackdump(file_path: str) -> dict:
	"""
	Load and parse SlackDump JSON export file.

	Args:
		file_path: Path to SlackDump JSON file

	Returns:
		dict containing channel_id, name, and messages array

	Raises:
		ParserError: If file not found or JSON is invalid
	"""
	path = Path(file_path)

	if not path.exists():
		raise ParserError(f"File not found: {file_path}")

	try:
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
	except json.JSONDecodeError as e:
		raise ParserError(f"Invalid JSON in {file_path}: {e}")
	except Exception as e:
		raise ParserError(f"Error reading {file_path}: {e}")

	return data


def parse_message(
	raw_message: dict,
	channel_id: str,
	channel_name: Optional[str] = None,
	users_json_path: Optional[str] = None,
) -> dict:
	"""
	Parse a single Slack message into database-ready format.

	Args:
		raw_message: Raw message dict from SlackDump JSON
		channel_id: Channel/DM ID this message belongs to
		channel_name: Optional human-readable channel name
		users_json_path: Optional path to users.json for username lookup (not implemented yet)

	Returns:
		dict with keys:
			- channel_id
			- channel_name
			- user_id
			- username (extracted from user_id if users_json provided)
			- timestamp (as float)
			- message_text
			- thread_ts (as float or None)
			- message_type
			- raw_json (original message as JSON string)

	Raises:
		ParserError: If required fields are missing
	"""
	# Validate required fields
	required_fields = ["user", "ts"]
	for field in required_fields:
		if field not in raw_message:
			raise ParserError(f"Missing required field: {field}")

	# Extract timestamp (convert string to float)
	try:
		timestamp = float(raw_message["ts"])
	except (ValueError, TypeError) as e:
		raise ParserError(f"Invalid timestamp format: {raw_message.get('ts')}")

	# Extract thread timestamp if present
	thread_ts = None
	if "thread_ts" in raw_message and raw_message["thread_ts"]:
		try:
			thread_ts = float(raw_message["thread_ts"])
		except (ValueError, TypeError):
			# If thread_ts is invalid, just skip it
			pass

	# Extract message text (default to empty string if missing)
	message_text = raw_message.get("text", "")

	# Determine message type
	message_type = raw_message.get("type", "message")

	# Username lookup (placeholder for future implementation)
	username = None
	if users_json_path:
		# TODO: Implement username lookup from users.json
		# For now, just return None
		pass

	# Preserve raw JSON for potential reprocessing
	raw_json = json.dumps(raw_message)

	return {
		"channel_id": channel_id,
		"channel_name": channel_name,
		"user_id": raw_message["user"],
		"username": username,
		"timestamp": timestamp,
		"message_text": message_text,
		"thread_ts": thread_ts,
		"message_type": message_type,
		"raw_json": raw_json,
	}
