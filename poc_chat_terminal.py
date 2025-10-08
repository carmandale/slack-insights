"""
POC: Natural Language Query - Simple Terminal Version

No dependencies beyond what's already installed.
Run: python poc_chat_terminal.py
"""

import os

import anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.slack_insights.database import init_database
from src.slack_insights.deduplication import group_similar_tasks_simple

# Load environment
load_dotenv()
console = Console()


def query_database(sql: str, params: tuple = ()) -> list[dict]:
	"""Execute SQL query and return results."""
	conn = init_database("slack_insights.db")
	cursor = conn.execute(sql, params)
	results = [dict(row) for row in cursor.fetchall()]
	conn.close()
	return results


def natural_language_to_sql(user_query: str, api_key: str) -> tuple[str, str]:
	"""Convert natural language query to SQL using Claude."""
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


def display_results(results: list[dict], query: str, sql: str):
	"""Display results with smart grouping and interactive expansion."""
	from rich.tree import Tree
	
	# Show query understanding
	console.print(Panel(query, title="[cyan]Your Question", border_style="cyan"))
	
	# Show SQL (collapsible)
	console.print(f"\n[dim]Generated SQL: {sql[:80]}...[/dim]\n")
	
	# Show results
	if not results:
		console.print("[yellow]No results found[/yellow]\n")
		return
	
	# Group similar tasks
	groups = group_similar_tasks_simple(results)
	
	# Summary
	total_unique = len(groups)
	total_instances = len(results)
	
	if total_unique < total_instances:
		console.print(f"[cyan]Found {total_unique} unique task(s) ({total_instances} total mentions)[/cyan]\n")
	else:
		console.print(f"[cyan]Found {total_unique} task(s)[/cyan]\n")
	
	# Display each group
	display_limit = min(15, len(groups))
	for i, group in enumerate(groups[:display_limit], 1):
		task = group["canonical_task"]
		count = group["count"]
		status = group["status"]
		first_date = group.get("first_date", "Unknown")
		last_date = group.get("last_date", "Unknown")
		assigner = group.get("assigner", "Unknown")
		
		# Status emoji
		status_icon = "✅" if status == "completed" else "⏳" if status == "open" else "❓"
		
		# Build display with number prefix
		title = f"[bold cyan]{i}.[/bold cyan] {status_icon} {task[:80]}"
		
		# Create tree
		tree = Tree(title)
		
		# Add metadata
		tree.add(f"[dim]From:[/dim] {assigner} [dim]│[/dim] [dim]Status:[/dim] {status}")
		
		if count > 1:
			# Multiple mentions - add expand hint
			if first_date == last_date:
				tree.add(f"[yellow]⚠ Mentioned {count} times on {first_date}[/yellow] [dim](type '{i}' to expand)[/dim]")
			else:
				tree.add(f"[yellow]⚠ Mentioned {count} times ({first_date} to {last_date})[/yellow] [dim](type '{i}' to expand)[/dim]")
		else:
			# Single mention
			tree.add(f"[dim]Date:[/dim] {first_date}")
		
		# Show context from first instance
		if group["instances"] and group["instances"][0].get("context_quote"):
			context = group["instances"][0]["context_quote"][:100]
			tree.add(f"[dim]\"{context}...\"[/dim]")
		
		console.print(tree)
		console.print()
	
	if len(groups) > 15:
		console.print(f"[dim]...and {len(groups) - 15} more unique tasks[/dim]\n")
	
	# Return groups for expansion
	return groups[:display_limit]


def expand_group(group: dict):
	"""Show all instances within a group."""
	from rich.tree import Tree
	
	task = group["canonical_task"]
	count = group["count"]
	
	console.print(f"\n[bold cyan]📋 All {count} instances of:[/bold cyan]")
	console.print(f"[bold]{task}[/bold]\n")
	
	# Show each instance
	for i, instance in enumerate(group["instances"], 1):
		date = instance.get("date", "Unknown")
		status = instance.get("status", "unknown")
		context = instance.get("context_quote", "")
		
		status_icon = "✅" if status == "completed" else "⏳" if status == "open" else "❓"
		
		tree = Tree(f"{status_icon} Instance {i} - {date}")
		tree.add(f"[dim]Status:[/dim] {status}")
		
		if context:
			# Show full context
			tree.add(f"[dim]Context:[/dim]\n{context}")
		
		console.print(tree)
	
	console.print()


def main():
	"""Main terminal chat loop."""
	
	# Check environment
	api_key = os.getenv("ANTHROPIC_API_KEY")
	if not api_key:
		console.print("[red]Error: ANTHROPIC_API_KEY not found in .env[/red]")
		return
	
	if not os.path.exists("slack_insights.db"):
		console.print("[red]Error: slack_insights.db not found[/red]")
		console.print("Run: [cyan]slack-insights import <file>[/cyan] first")
		return
	
	# Welcome
	console.print("\n[bold cyan]🤖 Slack Insights - Natural Language Query POC[/bold cyan]")
	console.print("[dim]Ask questions in plain English. Type 'exit' to quit.[/dim]\n")
	
	# Example queries
	examples = [
		"What did Dan ask me to do?",
		"Show me urgent tasks",
		"What's still open?",
		"List completed items from last week",
	]
	
	console.print("[cyan]Example queries:[/cyan]")
	for ex in examples:
		console.print(f"  • {ex}")
	console.print()
	
	# Chat loop
	last_groups = None  # Store groups for expansion
	
	while True:
		try:
			# Get user input
			console.print("[bold green]You:[/bold green] ", end="")
			user_query = input().strip()
			
			if not user_query:
				continue
			
			if user_query.lower() in ['exit', 'quit', 'q']:
				console.print("\n[cyan]Goodbye![/cyan]\n")
				break
			
			# Check if user wants to expand a group
			if user_query.isdigit():
				group_num = int(user_query)
				if last_groups and 1 <= group_num <= len(last_groups):
					expand_group(last_groups[group_num - 1])
					continue
				else:
					console.print("[yellow]Invalid group number. Ask a new question instead.[/yellow]\n")
					continue
			
			# Process query
			console.print("\n[dim]Thinking...[/dim]")
			
			try:
				sql_query, explanation = natural_language_to_sql(user_query, api_key)
				
				if not sql_query:
					console.print("[yellow]Couldn't generate SQL. Try rephrasing?[/yellow]\n")
					continue
				
				# Execute
				results = query_database(sql_query)
				
				# Display and save groups for expansion
				console.print(f"\n[cyan]Understanding:[/cyan] {explanation}\n")
				last_groups = display_results(results, user_query, sql_query)
				
				# Show expansion hint if there are groups with multiple instances
				if last_groups and any(g["count"] > 1 for g in last_groups):
					console.print("[dim]💡 Tip: Type a number (e.g., '1') to see all instances of that task[/dim]\n")
			
			except Exception as e:
				console.print(f"[red]Error:[/red] {e}\n")
		
		except KeyboardInterrupt:
			console.print("\n\n[cyan]Goodbye![/cyan]\n")
			break
		except EOFError:
			console.print("\n\n[cyan]Goodbye![/cyan]\n")
			break


if __name__ == "__main__":
	main()
