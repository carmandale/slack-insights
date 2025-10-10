"""Natural Language Query Engine - extracted from proven POC.

This module preserves the POC's successful approach to NL→SQL conversion.
DO NOT modify the core query parsing logic - it works perfectly as-is.

The approach:
1. User asks natural language question
2. Claude converts to SQL query
3. SQL executes against database
4. Results are grouped and displayed

This is extracted from poc_chat_terminal.py which was validated with real data.
"""

import os
from typing import Tuple

import anthropic

from .database import init_database


def natural_language_to_sql(user_query: str, api_key: str) -> Tuple[str, str]:
	"""Convert natural language query to SQL using Claude.

	This is the PROVEN approach from poc_chat_terminal.py that works.
	Extracted from poc_chat_terminal.py:34-98 (validated with real data).

	Args:
		user_query: Natural language query (e.g., "What did Dan ask me to do?")
		api_key: Anthropic API key

	Returns:
		Tuple of (sql_query, explanation)

	Example:
		sql, explanation = natural_language_to_sql("What did Dan ask me to do?", api_key)
		# sql = "SELECT ai.task_description, ai.assigner_username, ..."
		# explanation = "Query finds all action items from Dan"
	"""
	client = anthropic.Anthropic(api_key=api_key)

	schema = """
	Database Schema:

	Table: action_items (joined with conversations)
	- task_description TEXT
	- assigner_username TEXT (e.g., "itzaferg" for Dan)
	- assignee_username TEXT
	- status TEXT (open/completed)
	- urgency TEXT (low/normal/high)
	- context_quote TEXT

	Table: conversations
	- display_name TEXT (e.g., "itzaferg", "carmandale")
	- timestamp REAL (unix timestamp)
	- message_text TEXT

	Key names in database:
	- Dan = "itzaferg"
	- Dale = "carmandale"
	"""

	prompt = f"""Convert this natural language query into SQL for a Slack action items database.

User Query: "{user_query}"

{schema}

Generate a SELECT query that:
1. JOINs action_items with conversations
2. Uses LIKE with % wildcards for name matching
3. Orders by timestamp DESC
4. Limits to 20 results
5. Includes: task_description, assigner_username, status, context_quote, and datetime(c.timestamp, 'unixepoch') as date

Return format:
```sql
[SQL query here]
```

Brief explanation in one sentence.
"""

	response = client.messages.create(
		model="claude-sonnet-4-20250514",
		max_tokens=1024,
		messages=[{"role": "user", "content": prompt}]
	)

	response_text = response.content[0].text

	# Extract SQL
	sql_query = ""
	if "```sql" in response_text:
		start = response_text.find("```sql") + 6
		end = response_text.find("```", start)
		sql_query = response_text[start:end].strip()

	# Extract explanation (first line before or after SQL)
	explanation = response_text.split("```")[0].strip() or "Query generated"

	return sql_query, explanation


def query_database(sql: str, db_path: str = "slack_insights.db") -> list[dict]:
	"""Execute SQL query and return results.

	Extracted from poc_chat_terminal.py:25-31 (validated approach).

	Args:
		sql: SQL query string
		db_path: Path to SQLite database (default: slack_insights.db)

	Returns:
		List of result dictionaries with column names as keys

	Example:
		results = query_database("SELECT * FROM action_items LIMIT 5")
		# results = [{"task_description": "...", "status": "open"}, ...]
	"""
	conn = init_database(db_path)
	cursor = conn.execute(sql)
	results = [dict(row) for row in cursor.fetchall()]
	conn.close()

	return results


def execute_nl_query(
	user_query: str,
	db_path: str = "slack_insights.db",
	api_key: str | None = None,
	group_results: bool = True
) -> tuple[list[dict], str, str]:
	"""Execute complete natural language query flow (POC approach).

	This combines the POC's proven steps:
	1. Convert NL to SQL using Claude
	2. Execute SQL against database
	3. Group similar results (optional)

	Args:
		user_query: Natural language question
		db_path: Path to database
		api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
		group_results: Whether to group similar tasks (default: True)

	Returns:
		Tuple of (results, sql_query, explanation)
		- results: List of grouped tasks if group_results=True, else raw results
		- sql_query: Generated SQL for transparency
		- explanation: Claude's explanation of the query

	Example:
		results, sql, explanation = execute_nl_query("What did Dan ask me to do?")
		# results = [{"canonical_task": "...", "count": 3, "instances": [...]}]
		# sql = "SELECT ai.task_description, ..."
		# explanation = "Finds all action items from Dan"
	"""
	# Get API key
	if api_key is None:
		api_key = os.getenv("ANTHROPIC_API_KEY")
		if not api_key:
			raise ValueError(
				"ANTHROPIC_API_KEY environment variable not set. "
				"Please configure your API key in .env file."
			)

	# Step 1: Convert NL to SQL (POC approach)
	sql_query, explanation = natural_language_to_sql(user_query, api_key)

	# Step 2: Execute SQL
	raw_results = query_database(sql_query, db_path)

	# Step 3: Group results if requested (POC grouping)
	if group_results and raw_results:
		from .deduplication import group_similar_tasks_simple
		grouped = group_similar_tasks_simple(raw_results)
		return grouped, sql_query, explanation

	return raw_results, sql_query, explanation
