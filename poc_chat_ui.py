"""
POC: Natural Language Query Interface with Gradio Chat UI

Quick proof-of-concept for natural language queries over action items.
Install: pip install gradio
Run: python poc_chat_ui.py
"""

import os
from datetime import datetime

import anthropic
import gradio as gr
from dotenv import load_dotenv

from src.slack_insights.database import init_database

# Load environment
load_dotenv()


def query_database(sql: str, params: tuple = ()) -> list[dict]:
	"""Execute SQL query and return results."""
	conn = init_database("slack_insights.db")
	cursor = conn.execute(sql, params)
	results = [dict(row) for row in cursor.fetchall()]
	conn.close()
	return results


def natural_language_to_sql(user_query: str, api_key: str) -> tuple[str, str]:
	"""
	Convert natural language query to SQL using Claude.
	
	Returns:
		tuple of (sql_query, explanation)
	"""
	client = anthropic.Anthropic(api_key=api_key)
	
	# Database schema context
	schema = """
	Database Schema:
	
	Table: action_items
	- id INTEGER
	- conversation_id INTEGER (FK to conversations.id)
	- task_description TEXT
	- assignee_user_id TEXT
	- assignee_username TEXT
	- assigner_user_id TEXT
	- assigner_username TEXT
	- mentioned_date TEXT (YYYY-MM-DD)
	- status TEXT (open/completed)
	- urgency TEXT (low/normal/high)
	- context_quote TEXT
	- extracted_at DATETIME
	
	Table: conversations
	- id INTEGER
	- channel_id TEXT
	- channel_name TEXT
	- user_id TEXT
	- username TEXT
	- display_name TEXT (resolved name like "itzaferg", "carmandale")
	- timestamp REAL (unix timestamp)
	- message_text TEXT
	- thread_ts REAL
	- message_type TEXT
	- raw_json TEXT
	- imported_at DATETIME
	
	Common display_names:
	- "itzaferg" (Dan)
	- "carmandale" (Dale)
	"""
	
	prompt = f"""Convert this natural language query into SQL.

User Query: "{user_query}"

{schema}

Instructions:
- Generate a SELECT query to answer the user's question
- Always JOIN with conversations table to get message context and dates
- Use LIKE with % wildcards for name matching (case-insensitive)
- For date queries, use datetime() functions
- Order by timestamp DESC (most recent first)
- Limit to 50 results max
- Include task_description, assigner_username, assignee_username, status, urgency, context_quote

Return ONLY:
1. The SQL query (between ```sql and ```)
2. A brief explanation of what it does

Example:
Query: "What did Dan ask me to do?"
```sql
SELECT 
	ai.task_description,
	ai.assigner_username,
	ai.assignee_username,
	ai.status,
	ai.urgency,
	ai.context_quote,
	datetime(c.timestamp, 'unixepoch') as message_date
FROM action_items ai
JOIN conversations c ON ai.conversation_id = c.id
WHERE ai.assigner_username LIKE '%dan%' OR c.display_name LIKE '%dan%'
ORDER BY c.timestamp DESC
LIMIT 50
```
Explanation: Finds all action items where Dan was the assigner, showing most recent first.
"""
	
	response = client.messages.create(
		model="claude-sonnet-4-20250514",
		max_tokens=2048,
		messages=[{"role": "user", "content": prompt}]
	)
	
	response_text = response.content[0].text
	
	# Extract SQL from markdown
	sql_query = ""
	if "```sql" in response_text:
		start = response_text.find("```sql") + 6
		end = response_text.find("```", start)
		sql_query = response_text[start:end].strip()
	
	# Extract explanation
	explanation = ""
	if "Explanation:" in response_text:
		explanation = response_text.split("Explanation:")[1].strip()
	elif sql_query and "```" in response_text:
		# Get text after the SQL block
		after_sql = response_text[response_text.find("```", start + 1) + 3:].strip()
		explanation = after_sql[:200] if after_sql else "Query generated successfully."
	
	return sql_query, explanation


def format_results(results: list[dict]) -> str:
	"""Format query results as readable text."""
	if not results:
		return "No results found."
	
	output = []
	output.append(f"Found {len(results)} result(s):\n")
	
	for i, item in enumerate(results, 1):
		output.append(f"**{i}. {item.get('task_description', 'No description')}**")
		
		if 'assigner_username' in item and item['assigner_username']:
			output.append(f"   From: {item['assigner_username']}")
		
		if 'assignee_username' in item and item['assignee_username']:
			output.append(f"   To: {item['assignee_username']}")
		
		if 'status' in item:
			output.append(f"   Status: {item['status']}")
		
		if 'urgency' in item and item['urgency'] != 'normal':
			output.append(f"   Urgency: {item['urgency']}")
		
		if 'message_date' in item:
			output.append(f"   Date: {item['message_date']}")
		
		if 'context_quote' in item and item['context_quote']:
			context = item['context_quote'][:100]
			output.append(f"   Context: \"{context}...\"")
		
		output.append("")  # Blank line between results
	
	return "\n".join(output)


def chat_interface(message: str, history: list) -> str:
	"""
	Main chat interface function.
	
	Args:
		message: User's message
		history: Chat history (list of [user_msg, bot_msg] pairs)
	
	Returns:
		Bot's response
	"""
	api_key = os.getenv("ANTHROPIC_API_KEY")
	if not api_key:
		return "❌ Error: ANTHROPIC_API_KEY not found in environment"
	
	try:
		# Convert natural language to SQL
		sql_query, explanation = natural_language_to_sql(message, api_key)
		
		if not sql_query:
			return "❌ Sorry, I couldn't generate a SQL query from that. Can you try rephrasing?"
		
		# Execute query
		results = query_database(sql_query)
		
		# Format response
		response = []
		response.append(f"🔍 **Query Understanding:**")
		response.append(f"{explanation}\n")
		
		response.append(f"📊 **Results:**")
		response.append(format_results(results))
		
		response.append(f"\n💻 **Generated SQL:**")
		response.append(f"```sql\n{sql_query}\n```")
		
		return "\n".join(response)
	
	except Exception as e:
		return f"❌ Error: {str(e)}\n\nTry a simpler query or check the logs."


def create_demo():
	"""Create Gradio chat interface."""
	
	# Example queries
	examples = [
		"What did Dan ask me to do?",
		"Show me urgent tasks",
		"What's still open from last week?",
		"List all action items from Dan",
		"Show me completed tasks",
		"What tasks are assigned to me?",
		"Show recent requests",
	]
	
	# Create interface
	demo = gr.ChatInterface(
		fn=chat_interface,
		title="🤖 Slack Insights - Natural Language Query POC",
		description="""
		Ask questions in plain English about your Slack action items!
		
		**Example queries:**
		- "What did Dan ask me to do?"
		- "Show me urgent tasks"
		- "What's still open from last week?"
		- "List completed items"
		
		**How it works:**
		1. You ask in natural language
		2. Claude converts it to SQL
		3. Query runs on your local database
		4. Results displayed in chat
		""",
		examples=examples,
		theme=gr.themes.Soft(),
		retry_btn="🔄 Retry",
		undo_btn="↩️ Undo",
		clear_btn="🗑️ Clear",
	)
	
	return demo


if __name__ == "__main__":
	# Check for API key
	load_dotenv()
	if not os.getenv("ANTHROPIC_API_KEY"):
		print("❌ Error: ANTHROPIC_API_KEY not found in .env file")
		exit(1)
	
	# Check for database
	if not os.path.exists("slack_insights.db"):
		print("❌ Error: slack_insights.db not found")
		print("Run 'slack-insights import <file>' first")
		exit(1)
	
	# Launch UI
	demo = create_demo()
	demo.launch(
		server_name="127.0.0.1",
		server_port=7860,
		share=False,
		show_error=True,
	)
