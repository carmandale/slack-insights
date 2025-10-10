"""Formatting utilities for the NiceGUI interface."""

from datetime import datetime
from typing import Optional


def format_date(timestamp: float, relative: bool = True) -> str:
	"""Format a Unix timestamp as a human-readable date.

	Args:
		timestamp: Unix timestamp in seconds
		relative: If True, return relative time (e.g., "2 days ago"), else absolute date

	Returns:
		Formatted date string
	"""
	dt = datetime.fromtimestamp(timestamp)

	if not relative:
		return dt.strftime("%Y-%m-%d %H:%M")

	now = datetime.now()
	diff = now - dt

	# Calculate relative time
	seconds = diff.total_seconds()
	if seconds < 60:
		return "just now"
	elif seconds < 3600:
		minutes = int(seconds / 60)
		return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
	elif seconds < 86400:
		hours = int(seconds / 3600)
		return f"{hours} hour{'s' if hours != 1 else ''} ago"
	elif seconds < 604800:
		days = int(seconds / 86400)
		return f"{days} day{'s' if days != 1 else ''} ago"
	elif seconds < 2592000:
		weeks = int(seconds / 604800)
		return f"{weeks} week{'s' if weeks != 1 else ''} ago"
	else:
		months = int(seconds / 2592000)
		return f"{months} month{'s' if months != 1 else ''} ago"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
	"""Truncate text to a maximum length with a suffix.

	Args:
		text: Text to truncate
		max_length: Maximum length before truncation
		suffix: String to append if truncated

	Returns:
		Truncated text with suffix if needed
	"""
	if len(text) <= max_length:
		return text
	return text[: max_length - len(suffix)] + suffix


def get_status_icon(status: Optional[str]) -> str:
	"""Get an icon for an action item status.

	Args:
		status: Status string ('open', 'completed', 'unknown', None)

	Returns:
		Emoji icon representing the status
	"""
	status_icons = {
		"open": "⏳",
		"completed": "✅",
		"unknown": "❓",
		None: "❓",
	}
	return status_icons.get(status, "❓")


def get_status_color(status: Optional[str]) -> str:
	"""Get a CSS color class for an action item status.

	Args:
		status: Status string ('open', 'completed', 'unknown', None)

	Returns:
		CSS color class name
	"""
	status_colors = {
		"open": "text-yellow-600",
		"completed": "text-green-600",
		"unknown": "text-gray-500",
		None: "text-gray-500",
	}
	return status_colors.get(status, "text-gray-500")


def format_frequency_badge(count: int) -> str:
	"""Format a frequency count as a badge string.

	Args:
		count: Number of mentions

	Returns:
		Formatted badge string (e.g., "⚠ 4x")
	"""
	if count <= 1:
		return ""
	return f"⚠ {count}x"
