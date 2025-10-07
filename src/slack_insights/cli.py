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

from slack_insights.database import (
	get_action_items_by_assigner,
	init_database,
	insert_action_item,
	insert_conversation,
)
from slack_insights.extractor import ExtractorError, extract_action_items
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
def analyze(
	batch_size: int = typer.Option(100, "--batch-size", help="Messages per batch"),
	assigner: str = typer.Option(None, "--assigner", help="Filter by assigner name"),
) -> None:
	"""Analyze imported conversations and extract action items using Claude API."""
	try:
		db_path = get_db_path()

		if not os.path.exists(db_path):
			console.print("[red]Error:[/red] Database not found. Run import first.")
			raise typer.Exit(code=1)

		# Connect to database
		conn = init_database(db_path)

		# Get all conversations
		cursor = conn.execute(
			"SELECT id, user_id, username, message_text, timestamp FROM conversations "
			"ORDER BY timestamp ASC"
		)
		all_messages = [dict(row) for row in cursor.fetchall()]

		if not all_messages:
			console.print("[yellow]No messages to analyze.[/yellow]")
			console.print("Run [bold]slack-insights import <file>[/bold] first.")
			conn.close()
			return

		console.print(
			f"[cyan]Analyzing {len(all_messages)} messages in batches of {batch_size}...[/cyan]"
		)

		# Process in batches
		total_items_extracted = 0
		batches = [
			all_messages[i : i + batch_size]
			for i in range(0, len(all_messages), batch_size)
		]

		with Progress(
			SpinnerColumn(),
			TextColumn("[progress.description]{task.description}"),
			console=console,
		) as progress:
			task = progress.add_task(
				f"Processing {len(batches)} batches...", total=len(batches)
			)

			for batch_num, batch in enumerate(batches, 1):
				try:
					# Extract action items from batch
					items = extract_action_items(batch, assigner_name=assigner)

					# Store extracted items
					for item in items:
						# Find conversation_id from first message in context
						# For now, use first message in batch as reference
						conversation_id = batch[0]["id"] if batch else None

						if conversation_id:
							action_item = {
								"conversation_id": conversation_id,
								"task_description": item.get("task", ""),
								"mentioned_date": item.get("date"),
								"status": item.get("status", "open"),
								"urgency": item.get("urgency", "normal"),
								"context_quote": item.get("context", ""),
								"assigner_username": assigner,
							}
							insert_action_item(conn, action_item)
							total_items_extracted += 1

					progress.update(task, advance=1)

				except ExtractorError as e:
					console.print(f"\n[yellow]Warning:[/yellow] Batch {batch_num} failed: {e}")
					progress.update(task, advance=1)
					continue

		conn.close()

		# Display summary
		console.print(f"\n[green]✓[/green] Analysis complete!")
		console.print(f"  Messages analyzed: {len(all_messages)}")
		console.print(f"  Action items extracted: {total_items_extracted}")
		console.print(
			f"\n[cyan]Next step:[/cyan] Run [bold]slack-insights query-person <name>[/bold] "
			"to view action items"
		)

	except Exception as e:
		console.print(f"[red]Error:[/red] {e}")
		raise typer.Exit(code=1)


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
