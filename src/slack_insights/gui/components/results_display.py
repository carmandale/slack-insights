"""Results display components for grouped action items."""

from typing import Any, Dict, List

from nicegui import ui

from slack_insights.gui.utils.formatting import (
	format_date,
	format_frequency_badge,
	get_status_color,
	get_status_icon,
	truncate_text,
)


def create_results_tree(grouped_results: List[Dict[str, Any]]) -> None:
	"""Create a tree view of grouped action items with expand/collapse.

	Uses POC-proven data format from deduplication.group_similar_tasks_simple().

	Args:
		grouped_results: List of grouped action items with POC structure:
			[{
				'canonical_task': str,
				'count': int,
				'status': str,
				'first_date': str (YYYY-MM-DD),
				'last_date': str (YYYY-MM-DD),
				'assigner': str,
				'instances': [{
					'task_description': str,
					'assigner_username': str,
					'timestamp': float,
					'status': str,
					'context': str or 'context_quote': str
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
		first_date = group.get("first_date", "Unknown")
		last_date = group.get("last_date", "Unknown")
		assigner = group.get("assigner", "Unknown")

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

				# Show from/date info (POC format)
				ui.label(f"From: {assigner}").classes("text-sm text-gray-600")

				if count > 1 and first_date and last_date:
					if first_date == last_date:
						ui.label(f"⚠ Mentioned {count} times on {first_date}").classes(
							"text-sm text-orange-600 font-semibold"
						)
					else:
						ui.label(f"⚠ Mentioned {count} times ({first_date} to {last_date})").classes(
							"text-sm text-orange-600 font-semibold"
						)
				else:
					ui.label(f"Date: {first_date}").classes("text-sm text-gray-600")

				# Show first instance context preview
				if instances:
					first = instances[0]
					# Handle both 'context' and 'context_quote' field names (POC compatibility)
					context = first.get("context_quote") or first.get("context", "")
					if context:
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
						# Handle both POC format (date string) and timestamp
						date_value = instance.get("date")
						if date_value:
							date_str = date_value  # Already formatted in POC
						else:
							timestamp = instance.get("timestamp", 0)
							date_str = format_date(timestamp, relative=False)

						# Handle both 'context' and 'context_quote' field names
						context = instance.get("context_quote") or instance.get("context", "")
						inst_status = instance.get("status", "unknown")
						inst_status_icon = get_status_icon(inst_status)

						# Instance header
						ui.label(f"{inst_status_icon} Instance {idx} - {date_str}").classes(
							"font-semibold text-sm"
						)
						ui.label(f"Status: {inst_status}").classes(
							f"text-xs {get_status_color(inst_status)}"
						)

						# Context quote
						if context:
							with ui.card().classes("w-full bg-white p-2 mt-2 border-l-4 border-blue-400"):
								ui.label(context).classes("text-sm text-gray-700 italic")
