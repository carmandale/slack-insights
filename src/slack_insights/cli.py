"""
Command-line interface for Slack Insights.

Provides commands:
- import: Import SlackDump JSON exports
- analyze: Extract action items using Claude AI
- query-person: Query action items by person name
"""

import os
import sys

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from slack_insights.database import init_database, insert_conversation
from slack_insights.parser import ParserError, parse_message, parse_slackdump

app = typer.Typer(
	name="slack-insights",
	help="AI-powered action item extraction from Slack conversations",
)
console = Console()


def get_db_path() -> str:
	"""Get database path from environment or use default."""
	return os.getenv("SLACK_INSIGHTS_DB", "slack_insights.db")


@app.command(name="import")
def import_conversations(file_path: str) -> None:
	"""Import Slack conversations from SlackDump JSON export."""
	try:
		# Parse SlackDump file
		console.print(f"[cyan]Importing from:[/cyan] {file_path}")

		try:
			data = parse_slackdump(file_path)
		except ParserError as e:
			console.print(f"[red]Error:[/red] {e}")
			raise typer.Exit(code=1)

		messages = data.get("messages", [])
		channel_id = data.get("channel_id", "unknown")
		channel_name = data.get("name", "")

		if not messages:
			console.print("[yellow]Warning:[/yellow] No messages found in file")
			return

		# Initialize database
		db_path = get_db_path()
		conn = init_database(db_path)

		# Import messages with progress bar
		imported_count = 0
		duplicate_count = 0

		with Progress(
			SpinnerColumn(),
			TextColumn("[progress.description]{task.description}"),
			console=console,
		) as progress:
			task = progress.add_task(
				f"Importing {len(messages)} messages...", total=len(messages)
			)

			for raw_msg in messages:
				try:
					parsed_msg = parse_message(raw_msg, channel_id, channel_name)
					conversation_id = insert_conversation(conn, parsed_msg)

					# Check if it was a duplicate (would have same ID as previous)
					if conversation_id:
						imported_count += 1

					progress.update(task, advance=1)

				except Exception as e:
					# Log error but continue with other messages
					console.print(f"[yellow]Warning:[/yellow] Failed to import message: {e}")
					progress.update(task, advance=1)
					continue

		conn.close()

		# Display summary
		console.print(f"\n[green]✓[/green] Import complete!")
		console.print(f"  Messages processed: {len(messages)}")
		console.print(f"  Messages imported: {imported_count}")
		console.print(f"  Database: {db_path}")
		console.print(
			f"\n[cyan]Next step:[/cyan] Run [bold]slack-insights analyze[/bold] "
			"to extract action items"
		)

	except Exception as e:
		console.print(f"[red]Error:[/red] {e}")
		raise typer.Exit(code=1)


@app.command()
def analyze() -> None:
	"""Analyze imported conversations and extract action items using Claude AI."""
	typer.echo("Analyzing conversations...")
	# TODO: Implement in Task 6


@app.command()
def query_person(
	name: str,
	recent: bool = typer.Option(False, "--recent", help="Show only last 7 days"),
	status: str = typer.Option(None, "--status", help="Filter by status (open/completed)"),
) -> None:
	"""Query action items by person name."""
	typer.echo(f"Querying action items from: {name}")
	# TODO: Implement in Task 7


if __name__ == "__main__":
	app()
