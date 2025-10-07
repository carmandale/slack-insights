"""
Utility functions for Slack Insights.

Shared helpers for date parsing, formatting, and common operations.
"""

from datetime import datetime


def parse_slack_timestamp(ts: str) -> datetime:
	"""
	Parse Slack timestamp to datetime object.

	Args:
		ts: Slack timestamp (Unix epoch with microseconds)

	Returns:
		datetime object
	"""
	return datetime.fromtimestamp(float(ts))


def format_date(dt: datetime) -> str:
	"""
	Format datetime as YYYY-MM-DD string.

	Args:
		dt: datetime object

	Returns:
		Formatted date string
	"""
	return dt.strftime("%Y-%m-%d")
