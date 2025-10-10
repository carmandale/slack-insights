"""
Command-line interface for Slack Insights.

Provides commands:
- import: Import SlackDump JSON exports
- analyze: Extract action items using Claude AI
- query-person: Query action items by person name
"""

import os

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables from .env file
load_dotenv()

from slack_insights.database import (
	init_database,
	insert_action_item,
	insert_conversation,
)
from slack_insights.extractor import ExtractorError, extract_action_items
from slack_insights.parser import ParserError, parse_message, parse_slackdump
from slack_insights.query_engine import format_results_as_table, query_by_person
from slack_insights.query_service import QueryService
from slack_insights.user_lookup import load_user_map

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

		# Load user map for display name resolution
		user_map = None
		users_file = os.getenv("SLACK_USERS_FILE", "users-T1YNKSBL5.txt")
		try:
			if os.path.exists(users_file):
				user_map = load_user_map(users_file)
				console.print(f"[dim]Loaded {len(user_map)} users from {users_file}[/dim]")
			else:
				console.print(f"[yellow]Note:[/yellow] User mapping file not found: {users_file}")
				console.print("[dim]User IDs will not be resolved to display names[/dim]")
		except Exception as e:
			console.print(f"[yellow]Warning:[/yellow] Failed to load user map: {e}")
			console.print("[dim]Continuing with user IDs only[/dim]")

		# Initialize database
		db_path = get_db_path()
		conn = init_database(db_path)

		# Import messages with progress bar
		imported_count = 0

		with Progress(
			SpinnerColumn(),
			TextColumn("[progress.description]{task.description}"),
			console=console,
		) as progress:
			task = progress.add_task(f"Importing {len(messages)} messages...", total=len(messages))

			for raw_msg in messages:
				try:
					parsed_msg = parse_message(raw_msg, channel_id, channel_name, user_map)
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
		console.print("\n[green]✓[/green] Import complete!")
		console.print(f"  Messages processed: {len(messages)}")
		console.print(f"  Messages imported: {imported_count}")
		console.print(f"  Database: {db_path}")
		console.print(
			"\n[cyan]Next step:[/cyan] Run [bold]slack-insights analyze[/bold] "
			"to extract action items"
		)

	except Exception as e:
		console.print(f"[red]Error:[/red] {e}")
		raise typer.Exit(code=1)


@app.command()
def analyze(
	batch_size: int = typer.Option(120, "--batch-size", help="Messages per batch"),
	assigner: str = typer.Option(None, "--assigner", help="Filter by assigner name"),
	overlap: int = typer.Option(30, "--overlap", help="Messages to overlap between batches"),
	newest_first: bool = typer.Option(True, "--newest-first/--oldest-first", help="Process newest messages first"),
) -> None:
	"""Analyze imported conversations and extract action items using Claude API.
	
	Improved batching:
	- Default 120 messages per batch (was 100)
	- 30-message overlap preserves conversation flow
	- Newest-first ordering prioritizes recent messages
	"""
	conn = None
	try:
		db_path = get_db_path()

		if not os.path.exists(db_path):
			console.print("[red]Error:[/red] Database not found. Run import first.")
			raise typer.Exit(code=1)

		# Connect to database
		conn = init_database(db_path)

		# Get all conversations with display names
		order_by = "DESC" if newest_first else "ASC"
		cursor = conn.execute(
			f"SELECT id, user_id, username, display_name, message_text, timestamp, thread_ts "
			f"FROM conversations ORDER BY timestamp {order_by}"
		)
		all_messages = [dict(row) for row in cursor.fetchall()]

		if not all_messages:
			console.print("[yellow]No messages to analyze.[/yellow]")
			console.print("Run [bold]slack-insights import <file>[/bold] first.")
			conn.close()
			return

		console.print(
			f"[cyan]Analyzing {len(all_messages)} messages...[/cyan]"
		)
		console.print(f"[dim]  Batch size: {batch_size}, Overlap: {overlap}, Order: {'newest-first' if newest_first else 'oldest-first'}[/dim]")

		# Process in batches with sliding window
		total_items_extracted = 0
		
		# Create batches with overlap
		batches = []
		if overlap >= batch_size:
			console.print(f"[yellow]Warning:[/yellow] Overlap ({overlap}) >= batch size ({batch_size}). Setting overlap to {batch_size - 1}.")
			overlap = batch_size - 1
		
		for i in range(0, len(all_messages), batch_size - overlap):
			batch = all_messages[i : i + batch_size]
			if batch:  # Only add non-empty batches
				batches.append(batch)
				# Stop if we've covered all messages
				if i + batch_size >= len(all_messages):
					break

		with Progress(
			SpinnerColumn(),
			TextColumn("[progress.description]{task.description}"),
			console=console,
		) as progress:
			task = progress.add_task(f"Processing {len(batches)} batches...", total=len(batches))

			for batch_num, batch in enumerate(batches, 1):
				try:
					# Extract action items from batch with thread context
					items = extract_action_items(batch, assigner_name=assigner, conn=conn)

					# Store extracted items
					# NOTE: Using first message in batch as conversation_id reference
					# Future enhancement: have Claude return source_message_id per item
					default_conversation_id = batch[0]["id"] if batch else None

					for item in items:
						# Get source info from item if available, else use batch default
						conversation_id = item.get("source_message_id", default_conversation_id)

						if conversation_id:
							action_item = {
								"conversation_id": conversation_id,
								"task_description": item.get("task", ""),
								"assignee_username": item.get("assignee"),
								"assigner_username": item.get("assigner"),
								"mentioned_date": item.get("date"),
								"status": item.get("status", "open"),
								"urgency": item.get("urgency", "normal"),
								"context_quote": item.get("context", ""),
							}
							insert_action_item(conn, action_item)
							total_items_extracted += 1
						else:
							# Log warning for skipped items
							console.print(
								f"\n[yellow]Warning:[/yellow] Skipping item without "
								f"conversation_id: {item.get('task', 'Unknown task')}"
							)

					progress.update(task, advance=1)

				except ExtractorError as e:
					console.print(f"\n[yellow]Warning:[/yellow] Batch {batch_num} failed: {e}")
					progress.update(task, advance=1)
					continue

		# Display summary
		console.print("\n[green]✓[/green] Analysis complete!")
		console.print(f"  Messages analyzed: {len(all_messages)}")
		console.print(f"  Action items extracted: {total_items_extracted}")
		console.print(
			"\n[cyan]Next step:[/cyan] Run [bold]slack-insights query-person <name>[/bold] "
			"to view action items"
		)

	except Exception as e:
		console.print(f"[red]Error:[/red] {e}")
		raise typer.Exit(code=1)
	finally:
		if conn:
			conn.close()


@app.command()
def query_person(
	name: str,
	recent: bool = typer.Option(False, "--recent", help="Show only last 7 days"),
	status: str = typer.Option(None, "--status", help="Filter by status (open/completed)"),
) -> None:
	"""Query action items by person name."""
	conn = None
	try:
		db_path = get_db_path()

		if not os.path.exists(db_path):
			console.print("[red]Error:[/red] Database not found.")
			console.print("Run [bold]slack-insights import <file>[/bold] first.")
			raise typer.Exit(code=1)

		# Connect to database
		conn = init_database(db_path)

		# Query action items
		results = query_by_person(conn, name, status=status, recent=recent)

		# Format and display results
		table = format_results_as_table(results)
		console.print(f"\n[cyan]Action items from:[/cyan] {name}\n")
		console.print(table)

		if results:
			console.print(f"\n[dim]Total: {len(results)} items[/dim]")

	except Exception as e:
		console.print(f"[red]Error:[/red] {e}")
		raise typer.Exit(code=1)
	finally:
		if conn:
			conn.close()


@app.command()
def query(query_text: str) -> None:
	"""Query action items using natural language.

	Examples:
	  slack-insights query "What did Dan ask me to do?"
	  slack-insights query "Show me urgent tasks from last week"
	  slack-insights query "What's still open for AT&T?"
	"""
	try:
		db_path = get_db_path()

		if not os.path.exists(db_path):
			console.print("[red]Error:[/red] Database not found.")
			console.print("Run [bold]slack-insights import <file>[/bold] first.")
			raise typer.Exit(code=1)

		console.print(f"[cyan]Query:[/cyan] {query_text}\n")

		# Create query service
		try:
			query_service = QueryService(db_path)
		except ValueError as e:
			console.print(f"[red]Error:[/red] {e}")
			raise typer.Exit(code=1)

		# Execute natural language query
		grouped_results = query_service.execute_query(query_text, group_results=True)

		if not grouped_results:
			console.print("[yellow]No results found.[/yellow]")
			return

		# Display grouped results
		total_instances = sum(group["count"] for group in grouped_results)
		console.print(
			f"[dim]Found {len(grouped_results)} unique tasks "
			f"({total_instances} total mentions)[/dim]\n"
		)

		for group in grouped_results:
			canonical_task = group["canonical_task"]
			count = group["count"]
			status = group.get("status", "unknown")
			instances = group["instances"]

			# Header with frequency
			if count > 1:
				console.print(f"[bold cyan]⚠ {count}x[/bold cyan] {canonical_task}")
			else:
				console.print(f"[bold]{canonical_task}[/bold]")

			# Status
			status_color = "green" if status == "completed" else "yellow"
			console.print(f"  Status: [{status_color}]{status}[/{status_color}]")

			# Show first instance details
			if instances:
				first = instances[0]
				assigner = first.get("assigner_username", "Unknown")
				date = first.get("date", "Unknown")
				console.print(f"  From: {assigner} • {date}")

			console.print()  # Blank line between groups

	except Exception as e:
		console.print(f"[red]Error:[/red] {e}")
		raise typer.Exit(code=1)


@app.command()
def gui(
	port: int = typer.Option(8080, "--port", help="Port to run the web interface on"),
	reload: bool = typer.Option(False, "--reload", help="Enable auto-reload on code changes"),
) -> None:
	"""Launch the NiceGUI web interface for natural language queries.

	Opens a browser window with an interactive interface for querying
	Slack action items using natural language.
	"""
	try:
		db_path = get_db_path()

		if not os.path.exists(db_path):
			console.print("[yellow]Warning:[/yellow] Database not found at:", db_path)
			console.print("The GUI will launch with mock data.")
			console.print("\nTo use real data:")
			console.print("  1. Run [bold]slack-insights import <file>[/bold] to import Slack messages")
			console.print("  2. Run [bold]slack-insights analyze[/bold] to extract action items")
			console.print("  3. Run [bold]slack-insights gui[/bold] again\n")

		console.print(f"[cyan]Launching Slack Insights GUI...[/cyan]")
		console.print(f"[dim]Port: {port}[/dim]")
		console.print(f"[dim]Database: {db_path}[/dim]")
		console.print(f"\n[green]✓[/green] Opening browser at http://localhost:{port}\n")

		# Import and run the GUI
		from slack_insights.gui import app
		from nicegui import ui

		# Import the page decorator (registers routes)
		ui.run(
			title="Slack Insights",
			host="127.0.0.1",  # Bind to localhost only for security
			port=port,
			reload=reload,
			show=True,
		)

	except KeyboardInterrupt:
		console.print("\n[yellow]GUI stopped by user[/yellow]")
	except Exception as e:
		console.print(f"[red]Error launching GUI:[/red] {e}")
		raise typer.Exit(code=1)


if __name__ == "__main__":
	app()
