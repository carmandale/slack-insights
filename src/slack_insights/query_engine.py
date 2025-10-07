"""
Query engine for action items.

Handles database queries and result formatting using rich tables.
"""

import sqlite3
from typing import Any, Optional

from rich.table import Table

from slack_insights.database import get_action_items_by_assigner


def query_by_person(
	conn: sqlite3.Connection,
	person_name: str,
	status: Optional[str] = None,
	recent: bool = False,
) -> list[dict[str, Any]]:
	"""
	Query action items by person name.

	This is a convenience wrapper around database.get_action_items_by_assigner
	that handles the recent_days conversion.

	Args:
		conn: Database connection
		person_name: Name of person to query (assigner)
		status: Filter by status (open/completed)
		recent: Show only last 7 days

	Returns:
		List of action item dicts with conversation context
	"""
	recent_days = 7 if recent else None
	return get_action_items_by_assigner(conn, person_name, status, recent_days)


def format_results_as_table(items: list[dict[str, Any]]) -> Table:
	"""
	Format query results as rich table for display.

	Args:
		items: List of action item dicts from query

	Returns:
		Rich Table object ready for console display
	"""
	table = Table(title="Action Items", show_header=True, header_style="bold cyan")

	# Add columns
	table.add_column("Task", style="white", no_wrap=False, width=40)
	table.add_column("Date", style="yellow", width=12)
	table.add_column("Status", style="green", width=10)
	table.add_column("Urgency", style="magenta", width=10)
	table.add_column("Assigner", style="cyan", width=15)

	if not items:
		# Add empty row with message
		table.add_row("No action items found", "", "", "", "")
		return table

	# Add rows
	for item in items:
		task = item.get("task_description", "")
		date = item.get("mentioned_date", "Unknown")
		status = item.get("status", "unknown")
		urgency = item.get("urgency", "normal")
		assigner = item.get("assigner_username", "Unknown")

		# Color code status
		if status == "open":
			status_display = f"[bold red]{status}[/bold red]"
		elif status == "completed":
			status_display = f"[bold green]{status}[/bold green]"
		else:
			status_display = status

		# Color code urgency
		if urgency == "high":
			urgency_display = f"[bold red]{urgency}[/bold red]"
		elif urgency == "low":
			urgency_display = f"[dim]{urgency}[/dim]"
		else:
			urgency_display = urgency

		table.add_row(task, date, status_display, urgency_display, assigner)

	return table
