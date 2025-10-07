"""
AI-powered action item extraction using Claude API.

Handles Claude API calls, prompt engineering, and response parsing.
"""

from typing import Any, Dict, List, Optional


def extract_action_items(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""
	Extract action items from message batch using Claude API.

	Args:
		messages: List of message dicts

	Returns:
		List of extracted action item dicts
	"""
	# TODO: Implement in Task 4
	pass


def format_messages_for_claude(messages: List[Dict[str, Any]]) -> str:
	"""
	Format messages into readable conversation text for Claude.

	Args:
		messages: List of message dicts

	Returns:
		Formatted conversation string
	"""
	# TODO: Implement in Task 4
	pass


def call_claude_with_retry(prompt: str, max_retries: int = 3) -> Optional[str]:
	"""
	Call Claude API with exponential backoff retry logic.

	Args:
		prompt: Extraction prompt
		max_retries: Maximum retry attempts

	Returns:
		Claude's response text or None if all retries fail
	"""
	# TODO: Implement in Task 4
	pass


def parse_extraction_response(response_text: str) -> List[Dict[str, Any]]:
	"""
	Parse JSON array from Claude's response.

	Args:
		response_text: Raw text from Claude API

	Returns:
		List of action item dicts
	"""
	# TODO: Implement in Task 4
	pass
