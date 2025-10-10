"""GUI query engine wrapper around shared QueryService.

This module provides a thin compatibility layer for the GUI,
delegating all logic to the shared query_service module.
"""

from typing import Any, Optional

from ...query_service import QueryService


class QueryEngine:
	"""GUI-specific wrapper around shared QueryService.

	Provides backward compatibility for existing GUI code while
	delegating all logic to the shared QueryService module.
	"""

	def __init__(self, db_path: Optional[str] = None):
		"""Initialize query engine.

		Args:
			db_path: Path to SQLite database (defaults to slack_insights.db in current dir)

		Raises:
			FileNotFoundError: If database file doesn't exist
			ValueError: If ANTHROPIC_API_KEY environment variable not set
		"""
		if db_path is None:
			db_path = "slack_insights.db"

		# Delegate to shared service
		self.service = QueryService(db_path=db_path)

	def parse_query(self, query: str) -> dict[str, Any]:
		"""Parse natural language query into structured parameters.

		Args:
			query: Natural language query (e.g., "What did Dan ask me to do?")

		Returns:
			Dict with parsed parameters (for backward compatibility)
		"""
		params = self.service.parse_natural_language(query)

		# Convert QueryParams to dict for backward compatibility
		return {
			"assigner_name": params.assigner_name,
			"status": params.status,
			"recent_days": params.recent_days,
			"keywords": params.keywords,
		}

	def execute_query(self, query: str) -> list[dict[str, Any]]:
		"""Execute a natural language query and return grouped results.

		Args:
			query: Natural language query

		Returns:
			List of grouped action items ready for GUI display
		"""
		# Delegate to shared service with grouping enabled
		return self.service.execute_query(query, group_results=True)
