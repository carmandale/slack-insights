"""Main NiceGUI application for Slack Insights.

This module provides the web-based GUI for natural language querying of Slack action items.
"""

import time
from pathlib import Path
from typing import Any, Dict, List

from nicegui import ui

from .components.results_display import create_results_tree
from .utils.query_engine import QueryEngine

# Initialize query engine (will be set in create_app)
query_engine: QueryEngine | None = None


# Mock data for testing (fallback if database not available)
MOCK_RESULTS: List[Dict[str, Any]] = [
	{
		"canonical_task": "Deploy new API endpoint",
		"count": 4,
		"status": "open",
		"instances": [
			{
				"task_description": "Deploy new API endpoint to production",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 3600,  # 1 hour ago
				"status": "open",
				"context": "We need to deploy the new API endpoint before EOD. Can you handle this?",
			},
			{
				"task_description": "Deploy API endpoint",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 7200,  # 2 hours ago
				"status": "open",
				"context": "Just a reminder about the API endpoint deployment.",
			},
			{
				"task_description": "Deploy the API",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 86400,  # 1 day ago
				"status": "open",
				"context": "Did you get a chance to deploy the API?",
			},
			{
				"task_description": "Deploy new endpoint",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 172800,  # 2 days ago
				"status": "open",
				"context": "We really need that API deployed soon.",
			},
		],
	},
	{
		"canonical_task": "Provide PSD file",
		"count": 3,
		"status": "completed",
		"instances": [
			{
				"task_description": "Send PSD file for review",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 259200,  # 3 days ago
				"status": "completed",
				"context": "Can you send me the PSD file when you get a chance?",
			},
			{
				"task_description": "Share PSD",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 345600,  # 4 days ago
				"status": "completed",
				"context": "I need the PSD file to update the design.",
			},
			{
				"task_description": "Send design file",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 432000,  # 5 days ago
				"status": "completed",
				"context": "Please send the PSD file when ready.",
			},
		],
	},
	{
		"canonical_task": "Update documentation",
		"count": 1,
		"status": "open",
		"instances": [
			{
				"task_description": "Update project documentation",
				"assigner_username": "itzaferg",
				"timestamp": time.time() - 518400,  # 6 days ago
				"status": "open",
				"context": "The documentation needs to be updated with the latest changes.",
			},
		],
	},
]


def create_app() -> None:
	"""Create and configure the NiceGUI application."""
	global query_engine

	# Initialize query engine
	db_path = Path.cwd() / "slack_insights.db"
	try:
		query_engine = QueryEngine(str(db_path))
		ui.notify("✓ Connected to database", type="positive", position="top")
	except FileNotFoundError:
		ui.notify(
			f"⚠ Database not found at {db_path}. Using mock data.",
			type="warning",
			position="top",
		)
		query_engine = None

	# Set page configuration
	ui.page_title("Slack Insights")

	# Container for results (will be updated dynamically)
	results_container = None
	query_input_ref = None

	def handle_search():
		"""Handle search button click."""
		nonlocal results_container

		if not query_input_ref:
			return

		query_text = query_input_ref.value.strip()

		if not query_text:
			ui.notify("Please enter a query", type="warning")
			return

		# Clear previous results
		if results_container:
			results_container.clear()

		# Show loading state
		with results_container:
			with ui.row().classes("w-full justify-center items-center gap-4 p-8"):
				ui.spinner(size="lg")
				ui.label("Searching...").classes("text-gray-600")

		# Execute query
		if query_engine:
			# Use real backend
			try:
				results = query_engine.execute_query(query_text)
				ui.timer(0.1, lambda: display_results(results_container, results), once=True)
			except Exception as e:
				results_container.clear()
				with results_container:
					with ui.card().classes("w-full p-4 bg-red-50"):
						ui.label(f"❌ Error: {str(e)}").classes("text-red-700")
		else:
			# Use mock data
			ui.timer(
				1.0,  # 1 second delay to simulate API call
				lambda: display_results(results_container, MOCK_RESULTS),
				once=True,
			)

	def display_results(container, results):
		"""Display search results."""
		container.clear()
		with container:
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
	create_app()
	ui.run(
		title="Slack Insights",
		port=8080,
		reload=True,
		show=True,
	)


if __name__ in {"__main__", "__mp_main__"}:
	main()
