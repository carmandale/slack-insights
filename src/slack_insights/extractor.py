"""
Action item extractor using Claude API.

Extracts tasks, requests, and commitments from Slack conversations.
"""

import json
import os
import time
from datetime import datetime
from typing import Optional

import anthropic


class ExtractorError(Exception):
	"""Custom exception for extractor errors."""

	pass


def format_messages_for_claude(messages: list[dict]) -> str:
	"""
	Format messages into readable conversation text for Claude.

	Args:
		messages: List of parsed message dicts with user_id, username, timestamp, message_text

	Returns:
		Formatted conversation string
	"""
	if not messages:
		return ""

	lines = []
	for msg in messages:
		username = msg.get("username") or msg.get("user_id", "Unknown")
		timestamp = msg.get("timestamp", 0)
		text = msg.get("message_text", "")

		# Format timestamp as readable date
		try:
			dt = datetime.fromtimestamp(timestamp)
			date_str = dt.strftime("%Y-%m-%d %H:%M")
		except (ValueError, OSError):
			date_str = "Unknown date"

		lines.append(f"[{date_str}] {username}: {text}")

	return "\n".join(lines)


def build_extraction_prompt(
	messages: list[dict], assigner_name: Optional[str] = None
) -> str:
	"""
	Build complete prompt for Claude API.

	Args:
		messages: List of parsed message dicts
		assigner_name: Optional name of person assigning tasks (e.g., "Dan")

	Returns:
		Complete prompt string
	"""
	conversation = format_messages_for_claude(messages)

	assigner_context = f" from {assigner_name}" if assigner_name else ""

	prompt = f"""Analyze this Slack conversation and extract all action items, \
tasks, and requests{assigner_context}.

For each action item, provide:
- task: Clear description of what needs to be done
- date: Date mentioned in the conversation (YYYY-MM-DD format, or estimate from timestamp)
- status: "open" or "completed" (infer from conversation context)
- urgency: "low", "normal", or "high" (infer from language like "ASAP", "urgent", "when you can")
- context: Brief relevant quote from the conversation (1-2 sentences max)

Conversation:
{conversation}

Return results as a JSON array. If no action items are found, return an empty array [].

Example format:
[
  {{
    "task": "Review the PR before EOD",
    "date": "2025-10-05",
    "status": "open",
    "urgency": "high",
    "context": "Can you review the PR by EOD?"
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

	# Build prompt
	prompt = build_extraction_prompt(messages, assigner_name)

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
