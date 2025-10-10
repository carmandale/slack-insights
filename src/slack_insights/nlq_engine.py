"""Natural Language Query Engine - extracted from proven POC.

This module preserves the POC's successful approach to NL→SQL conversion.
Includes security hardening to prevent SQL injection attacks.

The approach:
1. User asks natural language question
2. Claude converts to SQL query
3. SQL is VALIDATED for security (SELECT-only, no dangerous keywords)
4. SQL executes against database (read-only mode)
5. Results are grouped and displayed

This is extracted from poc_chat_terminal.py which was validated with real data.
"""

import os
import re
import sqlite3

import anthropic

from .database import init_database


def validate_sql_query(sql: str) -> bool:
	"""Validate that AI-generated SQL is safe to execute.

	Security checks:
	1. Must start with SELECT (read-only operations)
	2. No dangerous keywords (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, ATTACH, PRAGMA)
	3. Must include LIMIT clause (prevent massive result sets)
	4. Only queries allowed tables (action_items, conversations, query_history)

	Args:
		sql: SQL query string to validate

	Returns:
		True if safe

	Raises:
		ValueError: If SQL fails security validation with specific reason

	Examples:
		>>> validate_sql_query("SELECT * FROM action_items LIMIT 10")
		True
		>>> validate_sql_query("DROP TABLE action_items")
		ValueError: Only SELECT queries allowed
	"""
	if not sql or not sql.strip():
		raise ValueError("SQL query is empty")

	sql_upper = sql.upper().strip()

	# Must be SELECT only
	if not sql_upper.startswith("SELECT"):
		raise ValueError("Only SELECT queries allowed. Generated query must start with SELECT.")

	# Block dangerous keywords (word boundary check to avoid false positives)
	dangerous_keywords = [
		"DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
		"CREATE", "ATTACH", "PRAGMA", "REPLACE", "DETACH"
	]

	# Split into words for accurate keyword detection
	sql_words = set(re.findall(r'\b\w+\b', sql_upper))

	for keyword in dangerous_keywords:
		if keyword in sql_words:
			raise ValueError(f"SQL contains forbidden keyword: {keyword}")

	# Ensure LIMIT clause exists (prevent massive queries)
	if "LIMIT" not in sql_upper:
		raise ValueError("SQL queries must include LIMIT clause for safety")

	# Verify table allowlist (check that only approved tables are used)
	allowed_tables = {"ACTION_ITEMS", "CONVERSATIONS", "QUERY_HISTORY"}

	# Extract table names after FROM and JOIN
	table_pattern = r'\b(?:FROM|JOIN)\s+(\w+)'
	found_tables = set(re.findall(table_pattern, sql_upper))

	if found_tables and not found_tables.issubset(allowed_tables):
		invalid_tables = found_tables - allowed_tables
		raise ValueError(f"SQL queries must use only allowed tables. Invalid tables: {invalid_tables}")

	return True


def natural_language_to_sql(user_query: str, api_key: str) -> tuple[str, str]:
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
	"""Execute SQL query with security validation and read-only access.

	SECURITY: This function validates SQL before execution to prevent SQL injection.
	Opens database in read-only mode as defense-in-depth measure.

	Extracted from poc_chat_terminal.py:25-31 with security hardening added.

	Args:
		sql: SQL query string (will be validated before execution)
		db_path: Path to SQLite database (default: slack_insights.db)

	Returns:
		List of result dictionaries with column names as keys

	Raises:
		ValueError: If SQL fails security validation
		sqlite3.OperationalError: If query attempts write operation on readonly DB

	Example:
		results = query_database("SELECT * FROM action_items LIMIT 5")
		# results = [{"task_description": "...", "status": "open"}, ...]
	"""
	# SECURITY: Validate SQL before execution
	validate_sql_query(sql)

	# Defense-in-depth: Open database in read-only mode
	conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
	conn.row_factory = sqlite3.Row

	try:
		cursor = conn.execute(sql)
		results = [dict(row) for row in cursor.fetchall()]
		return results
	except sqlite3.OperationalError as e:
		if "readonly database" in str(e).lower():
			raise ValueError("Attempted write operation blocked by read-only database") from e
		raise
	finally:
		conn.close()


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
