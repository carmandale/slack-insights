"""
Command-line interface for Slack Insights.

Provides commands:
- import: Import SlackDump JSON exports
- analyze: Extract action items using Claude AI
- query-person: Query action items by person name
"""

import typer

app = typer.Typer(
	name="slack-insights",
	help="AI-powered action item extraction from Slack conversations",
)


@app.command()
def import_conversations(file_path: str) -> None:
	"""Import Slack conversations from SlackDump JSON export."""
	typer.echo(f"Importing from: {file_path}")
	# TODO: Implement in Task 5


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
