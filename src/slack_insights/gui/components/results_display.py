"""Results display components for grouped action items."""

from typing import Any, Dict, List

from nicegui import ui

from ..utils.formatting import (
	format_date,
	format_frequency_badge,
	get_status_color,
	get_status_icon,
	truncate_text,
)


def create_results_tree(grouped_results: List[Dict[str, Any]]) -> None:
	"""Create a tree view of grouped action items with expand/collapse.

	Args:
		grouped_results: List of grouped action items with structure:
			[{
				'canonical_task': str,
				'count': int,
				'status': str,
				'instances': [{
					'task_description': str,
					'assigner_username': str,
					'timestamp': float,
					'status': str,
					'context': str
				}, ...]
			}, ...]
	"""
	if not grouped_results:
		with ui.card().classes("w-full p-4"):
			ui.label("No results found").classes("text-gray-500 text-center")
		return

	# Display summary
	total_instances = sum(group["count"] for group in grouped_results)
	unique_tasks = len(grouped_results)

	ui.label(
		f"Found {unique_tasks} unique task{'s' if unique_tasks != 1 else ''} "
		f"({total_instances} total mention{'s' if total_instances != 1 else ''})"
	).classes("text-sm text-gray-600 mb-4")

	# Create accordion for each group
	for group in grouped_results:
		canonical_task = group["canonical_task"]
		count = group["count"]
		status = group.get("status", "unknown")
		instances = group["instances"]

		# Create expansion panel for each group
		status_icon = get_status_icon(status)
		status_color = get_status_color(status)
		frequency_badge = format_frequency_badge(count)

		# Build header text
		header_parts = []
		if frequency_badge:
			header_parts.append(frequency_badge)
		header_parts.append(status_icon)
		header_parts.append(canonical_task)
		header_text = " ".join(header_parts)

		with ui.expansion(header_text, icon="expand_more").classes("w-full"):
			# Show metadata
			with ui.column().classes("gap-2 p-2"):
				ui.label(f"Status: {status.capitalize() if status else 'Unknown'}").classes(
					f"text-sm {status_color}"
				)

				# Show first instance preview
				if instances:
					first = instances[0]
					assigner = first.get("assigner_username", "Unknown")
					timestamp = first.get("timestamp", 0)
					date_str = format_date(timestamp, relative=True)
					context = first.get("context", "")

					ui.label(f"From: {assigner} • {date_str}").classes("text-sm text-gray-600")
					ui.label(truncate_text(context, max_length=150)).classes(
						"text-sm text-gray-700 italic"
					)

				ui.separator()

				# Show all instances
				ui.label(f"All {count} instance{'s' if count != 1 else ''}:").classes(
					"font-semibold text-sm mt-2"
				)

				for idx, instance in enumerate(instances, 1):
					with ui.card().classes("w-full bg-gray-50 p-3 mt-1"):
						timestamp = instance.get("timestamp", 0)
						date_str = format_date(timestamp, relative=False)
						context = instance.get("context", "")
						inst_status = instance.get("status", "unknown")

						# Instance header
						ui.label(f"Instance {idx} - {date_str}").classes(
							"font-semibold text-sm"
						)
						ui.label(f"Status: {inst_status}").classes(
							f"text-xs {get_status_color(inst_status)}"
						)

						# Context quote
						if context:
							with ui.card().classes("w-full bg-white p-2 mt-2 border-l-4 border-blue-400"):
								ui.label(context).classes("text-sm text-gray-700 italic")


def create_results_list(grouped_results: List[Dict[str, Any]]) -> None:
	"""Create a simple list view of grouped action items (alternative to tree).

	Args:
		grouped_results: List of grouped action items (same structure as create_results_tree)
	"""
	if not grouped_results:
		with ui.card().classes("w-full p-4"):
			ui.label("No results found").classes("text-gray-500 text-center")
		return

	# Display summary
	total_instances = sum(group["count"] for group in grouped_results)
	unique_tasks = len(grouped_results)

	ui.label(
		f"Found {unique_tasks} unique task{'s' if unique_tasks != 1 else ''} "
		f"({total_instances} total mention{'s' if total_instances != 1 else ''})"
	).classes("text-sm text-gray-600 mb-4")

	# Create card for each group
	for group in grouped_results:
		canonical_task = group["canonical_task"]
		count = group["count"]
		status = group.get("status", "unknown")
		instances = group["instances"]

		status_icon = get_status_icon(status)
		status_color = get_status_color(status)
		frequency_badge = format_frequency_badge(count)

		with ui.card().classes("w-full p-4 mb-2 hover:shadow-lg transition-shadow"):
			# Header row
			with ui.row().classes("w-full items-center gap-2"):
				ui.label(status_icon).classes("text-2xl")
				ui.label(canonical_task).classes("text-lg font-semibold flex-grow")
				if frequency_badge:
					ui.badge(frequency_badge).classes("bg-orange-500 text-white")

			# Status and preview
			ui.label(f"Status: {status.capitalize() if status else 'Unknown'}").classes(
				f"text-sm {status_color} mt-2"
			)

			if instances:
				first = instances[0]
				assigner = first.get("assigner_username", "Unknown")
				timestamp = first.get("timestamp", 0)
				date_str = format_date(timestamp, relative=True)

				ui.label(f"From: {assigner} • {date_str}").classes("text-sm text-gray-600")
