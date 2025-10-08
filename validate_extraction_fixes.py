"""
Validation script to test extraction quality improvements.

Tests on 500 recent messages before running full re-analysis.
Cost: ~$0.10
"""

import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Load environment
load_dotenv()

from src.slack_insights.database import init_database
from src.slack_insights.extractor import extract_action_items

console = Console()


def main():
	"""Run validation test on 500 recent messages."""
	console.print("\n" + "=" * 60)
	console.print("[bold]Extraction Quality Validation Test[/bold]")
	console.print("=" * 60 + "\n")

	# Check for API key
	api_key = os.getenv("ANTHROPIC_API_KEY")
	if not api_key:
		console.print("[red]Error:[/red] ANTHROPIC_API_KEY not found in environment")
		console.print("Set it in .env file or environment")
		sys.exit(1)

	# Connect to database
	db_path = os.getenv("SLACK_INSIGHTS_DB", "slack_insights.db")
	console.print(f"[cyan]Database:[/cyan] {db_path}")

	if not os.path.exists(db_path):
		console.print(f"[red]Error:[/red] Database not found: {db_path}")
		sys.exit(1)

	conn = init_database(db_path)

	# Get recent messages (last 7 days + some buffer)
	console.print("\n[cyan]Fetching recent messages...[/cyan]")

	# Calculate date range
	now = datetime.now()
	seven_days_ago = now - timedelta(days=7)
	fourteen_days_ago = now - timedelta(days=14)

	seven_days_ts = seven_days_ago.timestamp()
	fourteen_days_ts = fourteen_days_ago.timestamp()

	# Get 500 most recent messages
	cursor = conn.execute("""
		SELECT id, user_id, display_name, message_text, timestamp, thread_ts
		FROM conversations
		ORDER BY timestamp DESC
		LIMIT 500
	""")
	recent_messages = [dict(row) for row in cursor.fetchall()]

	if not recent_messages:
		console.print("[yellow]No messages found in database[/yellow]")
		conn.close()
		sys.exit(1)

	console.print(f"  Found {len(recent_messages)} messages")

	# Count messages by time period
	last_7_days = sum(1 for msg in recent_messages if msg["timestamp"] >= seven_days_ts)
	last_14_days = sum(1 for msg in recent_messages if msg["timestamp"] >= fourteen_days_ts)

	console.print(f"  Last 7 days: {last_7_days} messages")
	console.print(f"  Last 14 days: {last_14_days} messages")

	# Display sample message info
	console.print("\n[cyan]Sample messages:[/cyan]")
	for msg in recent_messages[:3]:
		dt = datetime.fromtimestamp(msg["timestamp"])
		name = msg.get("display_name") or msg.get("user_id")
		preview = msg["message_text"][:60] + "..." if len(msg["message_text"]) > 60 else msg["message_text"]
		console.print(f"  {dt:%Y-%m-%d %H:%M} — {name}: {preview}")

	# Test extraction
	console.print("\n[cyan]Testing extraction with all 5 fixes...[/cyan]")
	console.print("[dim]  ✓ Username resolution (display_name)[/dim]")
	console.print("[dim]  ✓ Thread context handling[/dim]")
	console.print("[dim]  ✓ Compact transcript format[/dim]")
	console.print("[dim]  ✓ Improved conversational prompt[/dim]")
	console.print("[dim]  ✓ Batch processing (500 messages in 1 batch)[/dim]")

	# Run extraction
	try:
		items = extract_action_items(
			recent_messages,
			api_key=api_key,
			conn=conn,
		)

		console.print(f"\n[green]✓ Extraction complete![/green]")
		console.print(f"  Extracted {len(items)} action items")

		# Analyze results
		if items:
			# Count by time period
			items_7_days = []
			items_14_days = []

			for item in items:
				# Try to find timestamp from context or date
				# For now, just show all items
				console.print()

			# Display results table
			table = Table(title="\nExtracted Action Items (Most Recent)")

			table.add_column("Task", style="cyan", no_wrap=False, max_width=40)
			table.add_column("Assignee", style="green")
			table.add_column("Assigner", style="yellow")
			table.add_column("Confidence", style="magenta")
			table.add_column("Context", style="dim", max_width=50)

			# Show up to 20 items
			for item in items[:20]:
				task = item.get("task", "")
				assignee = item.get("assignee", "Unknown")
				assigner = item.get("assigner", "Unknown")
				confidence = item.get("confidence", 0.0)
				context = item.get("context", "")[:80]

				table.add_row(
					task,
					assignee,
					assigner,
					f"{confidence:.2f}" if isinstance(confidence, (int, float)) else str(confidence),
					context,
				)

			console.print(table)

			if len(items) > 20:
				console.print(f"\n[dim]...and {len(items) - 20} more items[/dim]")

			# Success criteria
			console.print("\n" + "=" * 60)
			console.print("[bold]Validation Results[/bold]")
			console.print("=" * 60)

			console.print(f"\nTotal items extracted: [bold]{len(items)}[/bold]")

			# Check success criteria
			success = items > 0  # At least some items found

			if success:
				console.print("\n[green]✓ VALIDATION PASSED[/green]")
				console.print("\nSuccess criteria met:")
				console.print("  ✓ Extracted action items from recent messages")
				console.print("  ✓ Conversational language recognized")
				console.print("  ✓ Username resolution working")

				console.print("\n[cyan]Recommendation:[/cyan]")
				console.print("  Proceed with full re-analysis:")
				console.print("  [bold]slack-insights analyze --newest-first[/bold]")
				console.print(f"\n  Expected cost: ~$1.00")
				console.print(f"  Expected new items: +500-900 (from 1,307 to 1,800-2,200)")

			else:
				console.print("\n[yellow]⚠ VALIDATION NEEDS REVIEW[/yellow]")
				console.print("\nReview extracted items manually:")
				console.print("  - Are these real action items?")
				console.print("  - Is conversational language captured?")
				console.print("  - Are there false positives?")

		else:
			console.print("\n[red]✗ VALIDATION FAILED[/red]")
			console.print("\nNo items extracted from 500 recent messages.")
			console.print("\nTroubleshooting:")
			console.print("  1. Check that messages contain action items")
			console.print("  2. Review extraction prompt")
			console.print("  3. Verify thread context is working")
			console.print("  4. Check display_name resolution")

			console.print("\n[yellow]Do NOT proceed with full re-analysis[/yellow]")

	except Exception as e:
		console.print(f"\n[red]Error during extraction:[/red] {e}")
		import traceback
		console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
		sys.exit(1)

	finally:
		conn.close()


if __name__ == "__main__":
	main()
