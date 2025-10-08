"""
User lookup module for resolving Slack user IDs to display names.

Supports parsing SlackDump user export files in TXT and JSON formats.
"""

import json
from pathlib import Path
from typing import Optional

# Global cache for user mappings to avoid re-parsing
_USER_MAP_CACHE: Optional[dict[str, str]] = None


def load_user_map(file_path: str) -> dict[str, str]:
	"""
	Load user ID to display name mapping from file.

	Supports two formats:
	1. Tab-separated TXT (from SlackDump: `users-{workspace}.txt`)
	2. JSON array with id/name fields

	Args:
		file_path: Path to users file

	Returns:
		Dictionary mapping user_id -> display_name

	Raises:
		FileNotFoundError: If file doesn't exist
		ValueError: If file format is unrecognized

	Example TXT format:
		Name                   ID           Bot?  Email
		Dan Ferguson          U2X1504QH          dan@example.com
		Dale Carman           U2YFMSK3N          dale@example.com

	Example JSON format:
		[
			{"id": "U2X1504QH", "name": "Dan Ferguson"},
			{"id": "U2YFMSK3N", "name": "Dale Carman"}
		]
	"""
	global _USER_MAP_CACHE

	# Check cache first
	if _USER_MAP_CACHE is not None:
		return _USER_MAP_CACHE

	file_path_obj = Path(file_path)

	if not file_path_obj.exists():
		raise FileNotFoundError(f"User mapping file not found: {file_path}")

	# Determine format by extension
	if file_path_obj.suffix.lower() == ".json":
		user_map = _parse_json_format(file_path_obj)
	else:
		# Assume TXT format (default for SlackDump)
		user_map = _parse_txt_format(file_path_obj)

	# Cache result
	_USER_MAP_CACHE = user_map

	return user_map


def _parse_txt_format(file_path: Path) -> dict[str, str]:
	"""
	Parse tab-separated TXT format from SlackDump.

	Format:
		Name                   ID           Bot?  Email
		Dan Ferguson          U2X1504QH          dan@example.com

	Args:
		file_path: Path to TXT file

	Returns:
		Dictionary mapping user_id -> display_name
	"""
	user_map = {}

	with open(file_path, "r", encoding="utf-8") as f:
		lines = f.readlines()

	if not lines:
		return user_map

	# Skip header row (first line)
	for line in lines[1:]:
		line = line.strip()
		if not line:
			continue

		# Split by whitespace (columns are space/tab separated)
		parts = line.split()

		if len(parts) < 2:
			# Skip malformed lines
			continue

		# First column is name (may be empty for deleted users)
		# Second column is ID
		name = parts[0] if parts[0] else None
		user_id = parts[1] if len(parts) > 1 else None

		if user_id:
			# Use name if available, otherwise use user_id as fallback
			display_name = name if name else user_id
			user_map[user_id] = display_name

	return user_map


def _parse_json_format(file_path: Path) -> dict[str, str]:
	"""
	Parse JSON format user mapping.

	Expected format:
		[
			{"id": "U123", "name": "John Doe"},
			{"id": "U456", "name": "Jane Smith"}
		]

	Args:
		file_path: Path to JSON file

	Returns:
		Dictionary mapping user_id -> display_name

	Raises:
		ValueError: If JSON format is invalid
	"""
	with open(file_path, "r", encoding="utf-8") as f:
		data = json.load(f)

	if not isinstance(data, list):
		raise ValueError("JSON user file must contain an array of user objects")

	user_map = {}

	for user in data:
		if not isinstance(user, dict):
			continue

		user_id = user.get("id")
		name = user.get("name") or user.get("real_name") or user.get("display_name")

		if user_id and name:
			user_map[user_id] = name

	return user_map


def resolve_user_id(user_id: str, user_map: Optional[dict[str, str]] = None) -> str:
	"""
	Resolve a user ID to display name.

	Args:
		user_id: Slack user ID (e.g., "U2X1504QH")
		user_map: Optional pre-loaded user map. If None, returns user_id

	Returns:
		Display name if found in map, otherwise original user_id
	"""
	if not user_map:
		return user_id

	return user_map.get(user_id, user_id)


def clear_cache() -> None:
	"""Clear the global user map cache. Useful for testing."""
	global _USER_MAP_CACHE
	_USER_MAP_CACHE = None
