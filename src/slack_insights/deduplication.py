"""
Deduplication module for action items.

Prevents duplicate extraction from overlapping batches and provides
grouping capabilities for display.
"""

from datetime import datetime
from typing import Optional


def is_duplicate(
	existing_task: str,
	new_task: str,
	threshold: float = 0.85,
) -> bool:
	"""
	Check if two task descriptions are duplicates using simple similarity.
	
	Args:
		existing_task: Task description already in database
		new_task: New task description to check
		threshold: Similarity threshold (0.0-1.0)
	
	Returns:
		True if tasks are likely duplicates
	"""
	# Normalize
	task1 = existing_task.lower().strip()
	task2 = new_task.lower().strip()
	
	# Exact match
	if task1 == task2:
		return True
	
	# Simple token-based similarity
	tokens1 = set(task1.split())
	tokens2 = set(task2.split())
	
	if not tokens1 or not tokens2:
		return False
	
	# Jaccard similarity
	intersection = len(tokens1 & tokens2)
	union = len(tokens1 | tokens2)
	similarity = intersection / union if union > 0 else 0.0
	
	return similarity >= threshold


def find_duplicate_in_db(
	conn,
	task_description: str,
	assigner_username: Optional[str] = None,
	days_back: int = 30,
) -> Optional[int]:
	"""
	Search database for duplicate task.
	
	Args:
		conn: Database connection
		task_description: Task to search for
		assigner_username: Optional filter by assigner
		days_back: How many days to look back
	
	Returns:
		action_item_id of duplicate if found, None otherwise
	"""
	# Query recent similar tasks
	query = """
		SELECT ai.id, ai.task_description, ai.assigner_username, c.timestamp
		FROM action_items ai
		JOIN conversations c ON ai.conversation_id = c.id
		WHERE datetime(c.timestamp, 'unixepoch') >= datetime('now', ? || ' days')
	"""
	params = [f"-{days_back}"]
	
	if assigner_username:
		query += " AND ai.assigner_username = ?"
		params.append(assigner_username)
	
	query += " ORDER BY c.timestamp DESC LIMIT 100"
	
	cursor = conn.execute(query, params)
	existing = cursor.fetchall()
	
	# Check each existing task for similarity
	for row in existing:
		existing_task = row[1]  # task_description
		if is_duplicate(existing_task, task_description):
			return row[0]  # Return action_item_id
	
	return None


def group_similar_tasks_simple(results: list[dict]) -> list[dict]:
	"""
	Group similar tasks using simple text matching.
	
	Faster than AI-based grouping, good for large result sets.
	
	Args:
		results: List of action item dicts
	
	Returns:
		List of grouped tasks with counts and instances
	"""
	if not results:
		return []
	
	groups = []
	used = set()
	
	for i, item in enumerate(results):
		if i in used:
			continue
		
		# Start new group
		task = item.get("task_description", "")
		group = {
			"canonical_task": task,
			"instances": [item],
			"count": 1,
		}
		
		# Find similar tasks in remaining results
		for j, other in enumerate(results[i+1:], start=i+1):
			if j in used:
				continue
			
			other_task = other.get("task_description", "")
			if is_duplicate(task, other_task, threshold=0.80):
				group["instances"].append(other)
				group["count"] += 1
				used.add(j)
		
		# Add metadata
		instances = group["instances"]
		
		# Get date range
		dates = []
		for inst in instances:
			date_str = inst.get("date")
			if date_str:
				try:
					dates.append(datetime.fromisoformat(date_str.replace(" ", "T")))
				except:
					pass
		
		group["first_date"] = min(dates).strftime("%Y-%m-%d") if dates else None
		group["last_date"] = max(dates).strftime("%Y-%m-%d") if dates else None
		
		# Combined status
		statuses = [inst.get("status") for inst in instances]
		if all(s == "completed" for s in statuses):
			group["status"] = "completed"
		elif any(s == "open" for s in statuses):
			group["status"] = "open"
		else:
			group["status"] = statuses[0] if statuses else "unknown"
		
		# Get assigner
		group["assigner"] = instances[0].get("assigner_username", "Unknown")
		
		groups.append(group)
		used.add(i)
	
	return groups


def deduplicate_before_insert(
	conn,
	items: list[dict],
	days_back: int = 30,
) -> tuple[list[dict], list[dict]]:
	"""
	Filter out duplicate items before database insertion.
	
	Args:
		conn: Database connection
		items: List of extracted action items
		days_back: How many days to look back for duplicates
	
	Returns:
		Tuple of (new_items, duplicate_items)
	"""
	new_items = []
	duplicates = []
	
	for item in items:
		task_description = item.get("task", "") or item.get("task_description", "")
		assigner_username = item.get("assigner", "") or item.get("assigner_username", "")
		
		# Check if duplicate exists
		dup_id = find_duplicate_in_db(conn, task_description, assigner_username, days_back)
		
		if dup_id:
			item["duplicate_of"] = dup_id
			duplicates.append(item)
		else:
			new_items.append(item)
	
	return new_items, duplicates
