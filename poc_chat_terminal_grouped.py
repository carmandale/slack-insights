"""
POC: Natural Language Query with Smart Grouping/Deduplication

Groups similar requests together with expand/collapse.
Run: python poc_chat_terminal_grouped.py
"""

import os
from collections import defaultdict
from datetime import datetime

import anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from src.slack_insights.database import init_database

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


def group_similar_tasks(results: list[dict], api_key: str) -> list[dict]:
	"""
	Group similar/duplicate tasks using Claude.
	
	Returns list of groups, each with:
	- canonical_task: The main task description
	- count: Number of instances
	- instances: List of original items
	- first_date: Earliest mention
	- last_date: Latest mention
	- status: Combined status
	"""
	if len(results) <= 1:
		return [{"canonical_task": r.get("task_description", ""), "count": 1, "instances": [r]} for r in results]
	
	# Use Claude to identify duplicates/similar items
	client = anthropic.Anthropic(api_key=api_key)
	
	tasks_list = "\n".join([f"{i+1}. {r.get('task_description', '')}" for i, r in enumerate(results)])
	
	prompt = f"""Analyze these action items and identify which ones are duplicates or very similar.

Tasks:
{tasks_list}

Return a JSON array where each group contains the task numbers that are similar/duplicate.
Example: [[1,2,3], [4], [5,6], [7]]

Only group tasks that are clearly about the same thing. Different tasks should be separate.

Return ONLY the JSON array, nothing else.
"""
	
	try:
		response = client.messages.create(
			model="claude-sonnet-4-20250514",
			max_tokens=1024,
			messages=[{"role": "user", "content": prompt}]
		)
		
		response_text = response.content[0].text.strip()
		
		# Extract JSON
		import json
		if "```json" in response_text:
			start = response_text.find("```json") + 7
			end = response_text.find("```", start)
			response_text = response_text[start:end].strip()
		elif "```" in response_text:
			start = response_text.find("```") + 3
			end = response_text.find("```", start)
			response_text = response_text[start:end].strip()
		
		groups_indices = json.loads(response_text)
		
		# Build grouped results
		grouped = []
		for group_indices in groups_indices:
			instances = [results[i-1] for i in group_indices if 0 <= i-1 < len(results)]
			
			if not instances:
				continue
			
			# Get canonical task (first one)
			canonical = instances[0].get("task_description", "")
			
			# Get date range
			dates = []
			for inst in instances:
				if "date" in inst and inst["date"]:
					try:
						dates.append(datetime.fromisoformat(inst["date"].replace(" ", "T")))
					except:
						pass
			
			first_date = min(dates).strftime("%Y-%m-%d") if dates else None
			last_date = max(dates).strftime("%Y-%m-%d") if dates else None
			
			# Determine combined status
			statuses = [inst.get("status") for inst in instances]
			if all(s == "completed" for s in statuses):
				status = "completed"
			elif any(s == "open" for s in statuses):
				status = "open"
			else:
				status = statuses[0] if statuses else "unknown"
			
			grouped.append({
				"canonical_task": canonical,
				"count": len(instances),
				"instances": instances,
				"first_date": first_date,
				"last_date": last_date,
				"status": status,
			})
		
		return grouped
	
	except Exception as e:
		console.print(f"[dim]Note: Grouping failed ({e}), showing all results[/dim]")
		# Return ungrouped
		return [{"canonical_task": r.get("task_description", ""), "count": 1, "instances": [r]} for r in results]


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
	
	Key names: "itzaferg" = Dan, "carmandale" = Dale
	"""
	
	prompt = f"""Convert this natural language query into SQL for a Slack action items database.

User Query: "{user_query}"

{schema}

Generate a SELECT query that:
1. JOINs action_items with conversations
2. Uses LIKE with % wildcards for name matching
3. Orders by timestamp DESC
4. Limits to 50 results
5. Includes: task_description, assigner_username, status, context_quote, datetime(c.timestamp, 'unixepoch') as date

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
	
	explanation = response_text.split("```")[0].strip() or "Query generated"
	
	return sql_query, explanation


def display_grouped_results(groups: list[dict], show_details: bool = False):
	"""Display grouped results in a tree structure."""
	
	if not groups:
		console.print("[yellow]No results found[/yellow]\n")
		return
	
	# Summary
	total_unique = len(groups)
	total_instances = sum(g["count"] for g in groups)
	
	console.print(f"\n[cyan]Found {total_unique} unique task(s) ({total_instances} total mentions)[/cyan]\n")
	
	# Create tree for each group
	for i, group in enumerate(groups, 1):
		task = group["canonical_task"]
		count = group["count"]
		status = group["status"]
		first_date = group.get("first_date", "Unknown")
		last_date = group.get("last_date", "Unknown")
		
		# Status emoji
		status_icon = "✅" if status == "completed" else "⏳" if status == "open" else "❓"
		
		# Count badge
		count_badge = f"[{count}x]" if count > 1 else ""
		
		# Title
		title = f"{status_icon} {task[:70]}"
		if count > 1:
			title += f" [dim]{count_badge}[/dim]"
		
		# Create tree
		tree = Tree(title)
		
		# Add metadata
		tree.add(f"[dim]Status:[/dim] {status}")
		
		if count > 1:
			tree.add(f"[dim]Mentioned:[/dim] {count} times")
			if first_date == last_date:
				tree.add(f"[dim]Date:[/dim] {first_date}")
			else:
				tree.add(f"[dim]First:[/dim] {first_date}")
				tree.add(f"[dim]Last:[/dim] {last_date}")
		else:
			tree.add(f"[dim]Date:[/dim] {first_date or 'Unknown'}")
		
		# Add assignee
		if group["instances"]:
			assigner = group["instances"][0].get("assigner_username", "Unknown")
			tree.add(f"[dim]From:[/dim] {assigner}")
		
		# Show context from first instance
		if group["instances"] and group["instances"][0].get("context_quote"):
			context = group["instances"][0]["context_quote"][:100]
			tree.add(f"[dim]Context:[/dim] \"{context}...\"")
		
		# If multiple instances, show option to expand
		if count > 1 and show_details:
			details = tree.add("[dim]All instances:[/dim]")
			for inst in group["instances"][:5]:  # Limit to 5
				date = inst.get("date", "Unknown")
				details.add(f"• {date}")
		
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
	console.print("\n[bold cyan]🤖 Slack Insights - Natural Language Query POC (Grouped)[/bold cyan]")
	console.print("[dim]Ask questions in plain English. Similar tasks are automatically grouped.[/dim]")
	console.print("[dim]Type 'exit' to quit.[/dim]\n")
	
	# Example queries
	examples = [
		"What did Dan ask me to do for Orchestrator?",
		"Show me urgent tasks",
		"What's still open?",
		"What AT&T tasks are incomplete?",
	]
	
	console.print("[cyan]Example queries:[/cyan]")
	for ex in examples:
		console.print(f"  • {ex}")
	console.print()
	
	# Chat loop
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
			
			# Process query
			console.print("\n[dim]🔍 Analyzing query...[/dim]")
			
			try:
				# Convert to SQL
				sql_query, explanation = natural_language_to_sql(user_query, api_key)
				
				if not sql_query:
					console.print("[yellow]Couldn't generate SQL. Try rephrasing?[/yellow]\n")
					continue
				
				# Execute query
				console.print(f"[dim]📊 Running query...[/dim]")
				results = query_database(sql_query)
				
				if not results:
					console.print("[yellow]No results found[/yellow]\n")
					continue
				
				# Group similar tasks
				console.print(f"[dim]🧩 Grouping similar tasks...[/dim]")
				grouped = group_similar_tasks(results, api_key)
				
				# Display
				console.print(Panel(user_query, title="[cyan]Your Question", border_style="cyan"))
				console.print(f"\n[dim]Understanding:[/dim] {explanation}\n")
				
				display_grouped_results(grouped)
				
				# Show SQL (optional)
				console.print(f"[dim]Generated SQL: {sql_query[:80]}...[/dim]\n")
			
			except Exception as e:
				console.print(f"[red]Error:[/red] {e}\n")
				import traceback
				console.print(f"[dim]{traceback.format_exc()}[/dim]\n")
		
		except KeyboardInterrupt:
			console.print("\n\n[cyan]Goodbye![/cyan]\n")
			break
		except EOFError:
			console.print("\n\n[cyan]Goodbye![/cyan]\n")
			break


if __name__ == "__main__":
	main()
