"""Main NiceGUI application for Slack Insights.

This module provides the web-based GUI for natural language querying of Slack action items.
Uses the proven POC approach: NL → SQL → Execute → Group
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from nicegui import ui

from slack_insights.gui.components.results_display import create_results_tree
from slack_insights.gui.utils.input_validator import QueryRateLimiter, validate_user_query
from slack_insights.nlq_engine import execute_nl_query

# Load environment variables
load_dotenv()


# Minimal mock data (fallback if database not available)
MOCK_RESULTS: List[Dict[str, Any]] = [
	{
		"canonical_task": "Deploy API endpoint",
		"count": 2,
		"status": "open",
		"instances": [
			{
				"task_description": "Deploy API endpoint",
				"assigner_username": "dan",
				"timestamp": time.time() - 86400,  # 1 day ago
				"status": "open",
				"context": "We need to deploy the API endpoint before EOD.",
			},
		],
	},
	{
		"canonical_task": "Review documentation",
		"count": 1,
		"status": "completed",
		"instances": [
			{
				"task_description": "Review documentation",
				"assigner_username": "dan",
				"timestamp": time.time() - 259200,  # 3 days ago
				"status": "completed",
				"context": "Can you review the updated docs?",
			},
		],
	},
]


@ui.page("/")
def index_page() -> None:
	"""Main page for Slack Insights GUI."""

	# Check database and API key
	db_path = Path.cwd() / "slack_insights.db"
	api_key = os.getenv("ANTHROPIC_API_KEY")
	database_available = db_path.exists()
	api_key_available = api_key is not None

	if database_available and api_key_available:
		ui.notify("✓ Connected to database", type="positive", position="top")
	elif not database_available:
		ui.notify(
			"⚠ Database not found. Using mock data.",
			type="warning",
			position="top",
		)
	elif not api_key_available:
		ui.notify(
			"⚠ ANTHROPIC_API_KEY not set. Using mock data.",
			type="warning",
			position="top",
		)

	# Container for results (will be updated dynamically)
	results_container = None
	query_input_ref = None
	last_sql_query = None
	last_explanation = None

	# Initialize rate limiter for this session
	rate_limiter = QueryRateLimiter(max_calls=10, period_seconds=60)

	def handle_search() -> None:
		"""Handle search button click using POC-proven approach."""
		nonlocal results_container, last_sql_query, last_explanation

		if not query_input_ref:
			return

		query_text = query_input_ref.value.strip()

		if not query_text:
			ui.notify("Please enter a query", type="warning")
			return

		# Validate input
		is_valid, error_msg = validate_user_query(query_text)
		if not is_valid:
			ui.notify(error_msg, type="warning")
			return

		# Check rate limit
		allowed, rate_msg = rate_limiter.check_limit()
		if not allowed:
			ui.notify(rate_msg, type="warning")
			return

		# Clear previous results
		if results_container:
			results_container.clear()

		# Show loading state
		with results_container:
			with ui.row().classes("w-full justify-center items-center gap-4 p-8"):
				ui.spinner(size="lg")
				ui.label("Thinking...").classes("text-gray-600")

		# Execute query using POC approach
		if database_available and api_key_available:
			# Use POC approach: NL → SQL → Execute → Group
			try:
				results, sql_query, explanation = execute_nl_query(
					query_text,
					db_path=str(db_path),
					api_key=api_key,
					group_results=True
				)
				last_sql_query = sql_query
				last_explanation = explanation
				display_results(results_container, results, explanation, sql_query)
			except Exception as e:
				# Handle errors gracefully without crashing the server
				import traceback
				print(f"\n❌ Query error: {e}")
				traceback.print_exc()
				print()

				results_container.clear()
				with results_container:
					with ui.card().classes("w-full p-4 bg-red-50"):
						ui.label(f"❌ Error: {str(e)}").classes("text-red-700 font-semibold")
						ui.label("The app is still running. You can try another query.").classes(
							"text-gray-600 text-sm mt-2"
						)

						# Show error details in expandable section
						with ui.expansion("Error Details", icon="bug_report").classes("mt-2"):
							error_details = traceback.format_exc()
							ui.label(error_details).classes(
								"text-xs font-mono text-gray-700 whitespace-pre-wrap"
							)
		else:
			# Use mock data (fallback when no database or API key)
			display_results(results_container, MOCK_RESULTS, "Using mock data", None)

	def display_results(
		container: ui.column,
		results: list[dict[str, Any]],
		explanation: str | None = None,
		sql_query: str | None = None
	) -> None:
		"""Display search results with explanation and SQL query."""
		container.clear()
		with container:
			# Show explanation if provided
			if explanation:
				with ui.card().classes("w-full p-3 bg-blue-50 mb-4"):
					ui.label(f"💡 {explanation}").classes("text-blue-700")

			# Show SQL query (collapsible) for transparency
			if sql_query:
				with ui.expansion("View SQL Query", icon="code").classes("w-full mb-4"):
					with ui.card().classes("w-full p-3 bg-gray-50"):
						ui.label(sql_query[:500] + ("..." if len(sql_query) > 500 else "")).classes(
							"text-sm font-mono text-gray-700 whitespace-pre-wrap"
						)

			# Show results
			if not results:
				with ui.card().classes("w-full p-8"):
					ui.label("No results found").classes("text-gray-500 text-center text-lg")
					ui.label("Try a different query or check your database.").classes(
						"text-gray-400 text-center text-sm mt-2"
					)
			else:
				create_results_tree(results)

	# Create main layout
	with ui.column().classes("w-full max-w-6xl mx-auto p-8 gap-6"):
		# Header
		with ui.row().classes("w-full items-center gap-4"):
			ui.label("🔍").classes("text-4xl")
			ui.label("Slack Insights").classes("text-3xl font-bold")

		# Description
		ui.label("Natural language queries for your Slack action items").classes(
			"text-lg text-gray-600"
		)

		# Query input with search button
		with ui.row().classes("w-full gap-2"):
			query_input = ui.input(
				label="Query",
				placeholder="What did Dan ask me to do?",
			).classes("flex-grow").on("keydown.enter", handle_search)
			query_input_ref = query_input

			ui.button("Search", icon="search", on_click=handle_search).classes(
				"bg-blue-600 text-white px-6"
			)

		# Example queries
		with ui.row().classes("w-full gap-2 flex-wrap"):
			ui.label("Examples:").classes("text-sm text-gray-500")
			for example in [
				"What did Dan ask me to do?",
				"Show me urgent tasks",
				"What's still open?",
			]:
				ui.button(
					example,
					on_click=lambda e=example: [
						setattr(query_input_ref, "value", e),
						handle_search(),
					],
				).classes("text-xs bg-gray-100 hover:bg-gray-200")

		# Results container
		with ui.column().classes("w-full mt-4") as container:
			results_container = container
			with ui.card().classes("w-full p-8"):
				ui.label("Enter a query and click Search to see results").classes(
					"text-gray-500 text-center"
				)
				ui.label("You can also press Enter to search").classes(
					"text-gray-400 text-center text-sm mt-2"
				)


def main() -> None:
	"""Run the NiceGUI application."""
	ui.run(
		title="Slack Insights",
		host="127.0.0.1",  # Bind to localhost only for security
		port=8080,
		reload=True,
		show=True,
	)


if __name__ in {"__main__", "__mp_main__"}:
	main()
