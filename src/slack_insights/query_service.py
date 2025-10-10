"""Shared query service for natural language queries of action items.

This module provides unified query processing for both CLI and GUI interfaces,
eliminating code duplication and ensuring consistent behavior.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from .database import get_action_items_by_assigner, init_database
from .deduplication import group_similar_tasks_simple

# Load environment variables
load_dotenv()


# Error message constants
DB_NOT_FOUND_MSG = "Database not found: {}"
API_KEY_MISSING_MSG = (
	"ANTHROPIC_API_KEY environment variable not set. "
	"Please configure your API key in .env file."
)


class QueryParams:
	"""Structured parameters extracted from natural language query."""

	def __init__(
		self,
		assigner_name: Optional[str] = None,
		status: Optional[str] = None,
		recent_days: Optional[int] = None,
		keywords: Optional[list[str]] = None,
	):
		self.assigner_name = assigner_name
		self.status = status
		self.recent_days = recent_days
		self.keywords = keywords or []

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> "QueryParams":
		"""Create QueryParams from dict (e.g., from JSON parsing)."""
		return cls(
			assigner_name=data.get("assigner_name"),
			status=data.get("status"),
			recent_days=data.get("recent_days"),
			keywords=data.get("keywords", []),
		)


class QueryService:
	"""Shared service for natural language query processing.

	This service handles:
	- Natural language query parsing using Claude API
	- Database query execution with filters
	- Result grouping and deduplication
	"""

	def __init__(self, db_path: str, api_key: Optional[str] = None):
		"""Initialize query service.

		Args:
			db_path: Path to SQLite database
			api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

		Raises:
			FileNotFoundError: If database file doesn't exist
			ValueError: If API key not provided and not in environment
		"""
		# Validate database exists
		if not Path(db_path).exists():
			raise FileNotFoundError(DB_NOT_FOUND_MSG.format(db_path))

		self.db_path = db_path

		# Get API key from parameter or environment
		self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

		# Validate API key is configured
		if not self.api_key:
			raise ValueError(API_KEY_MISSING_MSG)

	def _get_connection(self) -> sqlite3.Connection:
		"""Get a database connection.

		Returns:
			SQLite connection with WAL mode and foreign keys enabled
		"""
		return init_database(self.db_path)

	def parse_natural_language(self, query: str) -> QueryParams:
		"""Parse natural language query into structured parameters using Claude.

		Args:
			query: Natural language query (e.g., "What did Dan ask me to do?")

		Returns:
			QueryParams object with extracted filters

		Raises:
			Exception: If Claude API call fails and fallback parsing also fails
		"""
		# Build prompt for Claude
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
			# Use Anthropic client as context manager for proper resource cleanup
			with Anthropic(api_key=self.api_key) as client:
				response = client.messages.create(
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
			params_dict = json.loads(content.strip())
			return QueryParams.from_dict(params_dict)

		except (json.JSONDecodeError, KeyError, ValueError) as e:
			# Fallback: basic keyword extraction
			print(f"Query parsing failed: {e}. Using fallback parsing.")
			return self._fallback_parse(query)

	def _fallback_parse(self, query: str) -> QueryParams:
		"""Basic keyword-based query parsing when Claude API fails.

		Args:
			query: Natural language query

		Returns:
			QueryParams with basic extracted parameters
		"""
		query_lower = query.lower()

		# Try to extract assigner name (basic pattern matching)
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

		return QueryParams(
			assigner_name=assigner_name,
			status=status,
			recent_days=recent_days,
			keywords=[],
		)

	def execute_query(
		self, query: str, group_results: bool = True
	) -> list[dict[str, Any]]:
		"""Execute a natural language query and return results.

		Args:
			query: Natural language query string
			group_results: If True, group similar tasks (default: True)

		Returns:
			List of action items (grouped if group_results=True)
		"""
		# Parse query into structured parameters
		params = self.parse_natural_language(query)

		# Query database
		conn = self._get_connection()
		try:
			results = []

			if params.assigner_name:
				# Query by assigner
				results = get_action_items_by_assigner(
					conn,
					params.assigner_name,
					status=params.status,
					recent_days=params.recent_days,
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

				if params.status:
					query_sql += " AND ai.status = ?"
					query_params.append(params.status)

				if params.recent_days:
					query_sql += " AND date(c.timestamp, 'unixepoch') >= date('now', ? || ' days')"
					query_params.append(f"-{params.recent_days}")

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
						or (item.get("original_timestamp") and str(item["original_timestamp"])),
						"context": item.get("context_quote") or item.get("message_text", ""),
						"timestamp": float(item.get("original_timestamp", 0)),
					}
				)

			# Group similar tasks if requested
			if group_results:
				return group_similar_tasks_simple(formatted_results)

			return formatted_results

		finally:
			conn.close()
