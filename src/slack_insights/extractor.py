"""
Action item extractor using Claude API.

Extracts tasks, requests, and commitments from Slack conversations.
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from typing import Optional

import anthropic

from slack_insights.thread_context import format_thread_context, get_thread_parents


class ExtractorError(Exception):
	"""Custom exception for extractor errors."""

	pass


def format_messages_for_claude(
	messages: list[dict],
	conn: Optional[sqlite3.Connection] = None,
) -> str:
	"""
	Format messages into compact transcript format for Claude.

	New format saves ~60% tokens:
	- Before: [{"user_id": "U123", "timestamp": 1728133380, "text": "..."}, ...]
	- After: 2025-10-05 14:23 — Dan Ferguson: Message text

	Args:
		messages: List of parsed message dicts
		conn: Optional database connection for fetching thread parents

	Returns:
		Compact transcript string
	"""
	if not messages:
		return ""

	lines = []
	for msg in messages:
		# Use display_name if available, fallback to username or user_id
		name = msg.get("display_name") or msg.get("username") or msg.get("user_id", "Unknown")
		timestamp = msg.get("timestamp", 0)
		text = msg.get("message_text", "")

		# Format timestamp as compact date
		try:
			ts = float(timestamp)
			dt = datetime.fromtimestamp(ts)
			date_str = dt.strftime("%Y-%m-%d %H:%M")
		except (ValueError, OSError, TypeError):
			date_str = "????-??-?? ??:??"

		# Compact format: YYYY-MM-DD HH:MM — Name: Message
		lines.append(f"{date_str} — {name}: {text}")

		# Add thread context if available
		if conn:
			parents = get_thread_parents(conn, msg, max_parents=3)
			if parents:
				# Insert parent context above current message
				parent_lines = format_thread_context(parents)
				# Insert before current line
				for parent_line in reversed(parent_lines):
					lines.insert(-1, parent_line)

	return "\n".join(lines)


def build_extraction_prompt(
	messages: list[dict],
	assigner_name: Optional[str] = None,
	conn: Optional[sqlite3.Connection] = None,
) -> str:
	"""
	Build complete prompt for Claude API with conversational examples.

	Args:
		messages: List of parsed message dicts
		assigner_name: Optional name of person assigning tasks (e.g., "Dan")
		conn: Optional database connection for thread context

	Returns:
		Complete prompt string
	"""
	conversation = format_messages_for_claude(messages, conn)

	assigner_context = f" from {assigner_name}" if assigner_name else ""

	prompt = f"""Analyze this Slack conversation and extract all action items, \
tasks, and requests{assigner_context}.

**IMPORTANT: Recognize both formal AND casual language patterns:**

Formal examples:
- "Please review the PR"
- "Can you send me the report?"
- "I need the screenshots by EOD"

Casual/conversational examples:
- "Did you get a chance to look at this?"
- "Did you make any progress on this stuff today?"
- "you were going to send me screenshots"
- "Let me know what you have"
- "Can you give me an update?"

Implicit requests (look for commitments):
- "I'll get you the screenshots" → Future action item
- "you said you'd send the video" → Past commitment

For each action item, provide:
- task: Clear description of what needs to be done
- assigner: Name of person who requested/assigned the task
- assignee: Name of person who should do the task (often implicit)
- date: Date from conversation (YYYY-MM-DD) or estimate from timestamp
- status: "open" or "completed" (infer from context)
- urgency: "low", "normal", or "high" (ASAP/urgent = high)
- context: Brief quote from conversation (1-2 sentences max)
- confidence: 0.0-1.0 (how confident you are this is a real action item)

Conversation:
{conversation}

Return results as a JSON array. If no action items found, return [].

Example output:
[
  {{
    "task": "Follow up on progress",
    "assigner": "Dan Ferguson",
    "assignee": "Dale Carman",
    "date": "2025-10-05",
    "status": "open",
    "urgency": "normal",
    "context": "Did you make any progress on this stuff today? Let me know what you have.",
    "confidence": 0.9
  }},
  {{
    "task": "Provide iPad app screenshots",
    "assigner": "Dan Ferguson",
    "assignee": "Dale Carman",
    "date": "2025-10-05",
    "status": "open",
    "urgency": "normal",
    "context": "Can you give me some screenshots of the iPad App?",
    "confidence": 0.95
  }}
]
"""

	return prompt


def parse_extraction_response(response_text: str) -> list[dict]:
	"""
	Parse JSON array from Claude's response.

	Handles responses wrapped in markdown code blocks.

	Args:
		response_text: Raw text response from Claude

	Returns:
		List of action item dicts, or empty list if parsing fails
	"""
	if not response_text:
		return []

	try:
		# Check if response is wrapped in markdown code block
		if "```json" in response_text or "```" in response_text:
			# Extract JSON from markdown
			start = response_text.find("[")
			end = response_text.rfind("]") + 1
			if start != -1 and end > start:
				json_str = response_text[start:end]
			else:
				return []
		else:
			json_str = response_text.strip()

		items = json.loads(json_str)
		return items if isinstance(items, list) else []

	except (json.JSONDecodeError, ValueError) as e:
		# Log error but don't crash - return empty list
		print(f"Warning: Failed to parse extraction response: {e}")
		return []


def extract_action_items(
	messages: list[dict],
	api_key: Optional[str] = None,
	channel_id: Optional[str] = None,
	assigner_name: Optional[str] = None,
	max_retries: int = 3,
	conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
	"""
	Extract action items from messages using Claude API.

	Args:
		messages: List of parsed message dicts
		api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
		channel_id: Optional channel ID for metadata
		assigner_name: Optional name of person assigning tasks
		max_retries: Maximum number of retry attempts for rate limits/server errors

	Returns:
		List of extracted action item dicts

	Raises:
		ExtractorError: If API call fails or authentication is invalid
	"""
	if not messages:
		return []

	# Get API key from parameter or environment
	api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
	if not api_key:
		raise ExtractorError(
			"API key required. Set ANTHROPIC_API_KEY environment variable "
			"or pass api_key parameter."
		)

	# Build prompt with thread context
	prompt = build_extraction_prompt(messages, assigner_name, conn)

	# Initialize Anthropic client
	client = anthropic.Anthropic(api_key=api_key)

	# Call API with retry logic
	for attempt in range(max_retries):
		try:
			response = client.messages.create(
				model="claude-sonnet-4-20250514",
				max_tokens=4096,
				messages=[{"role": "user", "content": prompt}],
			)

			# Extract text from response
			if not response or not response.content or len(response.content) == 0:
				return []

			first_block = response.content[0]
			if hasattr(first_block, "text"):
				response_text = first_block.text
			else:
				return []

			# Parse and return action items
			items = parse_extraction_response(response_text)
			return items

		except anthropic.AuthenticationError as e:
			raise ExtractorError(f"Authentication failed: {e}. Check your API key.")

		except anthropic.RateLimitError as e:
			if attempt < max_retries - 1:
				# Exponential backoff: 1s, 2s, 4s
				wait_time = 2**attempt
				print(f"Rate limit hit. Retrying in {wait_time}s...")
				time.sleep(wait_time)
			else:
				raise ExtractorError(f"Rate limit exceeded after {max_retries} attempts: {e}")

		except anthropic.APIError as e:
			# Retry on server errors (500+)
			if attempt < max_retries - 1 and hasattr(e, "status_code") and e.status_code >= 500:
				wait_time = 2**attempt
				print(f"Server error {e.status_code}. Retrying in {wait_time}s...")
				time.sleep(wait_time)
			else:
				raise ExtractorError(f"API error: {e}")

		except Exception as e:
			raise ExtractorError(f"Unexpected error during extraction: {e}")

	return []
