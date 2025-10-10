"""Query engine for natural language Slack queries."""

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from ...database import get_action_items_by_assigner, init_database
from ...deduplication import group_similar_tasks_simple


class QueryEngine:
	"""Handles natural language queries for action items."""

	def __init__(self, db_path: Optional[str] = None):
		"""Initialize query engine with database connection.

		Args:
			db_path: Path to SQLite database (defaults to slack_insights.db in current dir)
		"""
		if db_path is None:
			db_path = "slack_insights.db"

		# Ensure database exists
		if not Path(db_path).exists():
			raise FileNotFoundError(f"Database not found: {db_path}")

		self.db_path = db_path
		self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

	def _get_connection(self) -> sqlite3.Connection:
		"""Get a database connection."""
		return init_database(self.db_path)

	def parse_query(self, query: str) -> Dict[str, Any]:
		"""Parse natural language query into structured parameters using Claude.

		Args:
			query: Natural language query (e.g., "What did Dan ask me to do?")

		Returns:
			Dict with parsed parameters:
				- assigner_name: str or None
				- status: str or None ('open', 'completed')
				- recent_days: int or None
				- keywords: List[str] or []
		"""
		# Use Claude to parse the query
		prompt = f"""Parse this natural language Slack query and extract search parameters.

Query: "{query}"

Respond with ONLY a JSON object (no markdown, no explanation) with these fields:
{{
	"assigner_name": "name if mentioned, else null",
	"status": "open/completed/null",
	"recent_days": "number if mentioned (e.g. 'last 7 days'), else null",
	"keywords": ["list", "of", "keywords"]
}}

Examples:
- "What did Dan ask me to do?" → {{"assigner_name": "Dan", "status": "open", "recent_days": null, "keywords": []}}
- "Show me urgent tasks" → {{"assigner_name": null, "status": "open", "recent_days": null, "keywords": ["urgent"]}}
- "What's still open for TMA?" → {{"assigner_name": "TMA", "status": "open", "recent_days": null, "keywords": []}}
- "List completed items from last week" → {{"assigner_name": null, "status": "completed", "recent_days": 7, "keywords": []}}

Now parse the query above and return ONLY the JSON object:"""

		try:
			response = self.client.messages.create(
				model="claude-sonnet-4-20250514",
				max_tokens=500,
				messages=[{"role": "user", "content": prompt}],
			)

			# Extract JSON from response
			content = response.content[0].text.strip()

			# Remove markdown code fences if present
			if content.startswith("```"):
				# Remove opening ```json or ```
				content = content.split("\n", 1)[1] if "\n" in content else content
				# Remove closing ```
				content = content.rsplit("```", 1)[0] if "```" in content else content

			# Parse JSON
			import json

			params = json.loads(content.strip())

			# Ensure all fields exist
			return {
				"assigner_name": params.get("assigner_name"),
				"status": params.get("status"),
				"recent_days": params.get("recent_days"),
				"keywords": params.get("keywords", []),
			}

		except Exception as e:
			# Fallback: basic keyword extraction
			print(f"Query parsing failed: {e}. Using fallback.")
			query_lower = query.lower()

			# Try to extract assigner name
			assigner_name = None
			for name in ["dan", "ferguson", "itzaferg", "tma", "att", "at&t"]:
				if name in query_lower:
					assigner_name = name
					break

			# Detect status
			status = None
			if "open" in query_lower or "still" in query_lower or "pending" in query_lower:
				status = "open"
			elif "completed" in query_lower or "done" in query_lower or "finished" in query_lower:
				status = "completed"

			# Detect time range
			recent_days = None
			if "last 7 days" in query_lower or "past week" in query_lower:
				recent_days = 7
			elif "last 30 days" in query_lower or "last month" in query_lower:
				recent_days = 30

			return {
				"assigner_name": assigner_name,
				"status": status,
				"recent_days": recent_days,
				"keywords": [],
			}

	def execute_query(self, query: str) -> List[Dict[str, Any]]:
		"""Execute a natural language query and return grouped results.

		Args:
			query: Natural language query

		Returns:
			List of grouped action items with structure:
				[{
					'canonical_task': str,
					'count': int,
					'status': str,
					'first_date': str,
					'last_date': str,
					'assigner': str,
					'instances': [{
						'task_description': str,
						'assigner_username': str,
						'timestamp': float,
						'status': str,
						'context': str,
						'date': str
					}, ...]
				}, ...]
		"""
		# Parse query
		params = self.parse_query(query)

		# Query database
		conn = self._get_connection()
		try:
			# Get all action items matching filters
			results = []

			if params["assigner_name"]:
				# Query by assigner
				results = get_action_items_by_assigner(
					conn,
					params["assigner_name"],
					status=params["status"],
					recent_days=params["recent_days"],
				)
			else:
				# Query all action items with filters
				query_sql = """
					SELECT
						ai.id,
						ai.task_description,
						ai.mentioned_date,
						ai.status,
						ai.urgency,
						ai.context_quote,
						ai.assignee_username,
						ai.assigner_username,
						c.timestamp as original_timestamp,
						c.channel_name,
						c.message_text
					FROM action_items ai
					JOIN conversations c ON ai.conversation_id = c.id
					WHERE 1=1
				"""
				query_params = []

				if params["status"]:
					query_sql += " AND ai.status = ?"
					query_params.append(params["status"])

				if params["recent_days"]:
					query_sql += " AND date(c.timestamp, 'unixepoch') >= date('now', ? || ' days')"
					query_params.append(f"-{params['recent_days']}")

				query_sql += " ORDER BY c.timestamp DESC"

				cursor = conn.execute(query_sql, query_params)
				results = [dict(row) for row in cursor.fetchall()]

			# Convert to format expected by grouping function
			formatted_results = []
			for item in results:
				formatted_results.append(
					{
						"task_description": item["task_description"],
						"assigner_username": item.get("assigner_username", "Unknown"),
						"assignee_username": item.get("assignee_username", "Unknown"),
						"status": item.get("status", "unknown"),
						"date": item.get("mentioned_date")
						or (
							item.get("original_timestamp")
							and str(item["original_timestamp"])
						),
						"context": item.get("context_quote") or item.get("message_text", ""),
						"timestamp": float(item.get("original_timestamp", 0)),
					}
				)

			# Group similar tasks
			grouped = group_similar_tasks_simple(formatted_results)

			return grouped

		finally:
			conn.close()
