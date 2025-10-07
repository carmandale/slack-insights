"""
Tests for action item extractor using Claude API.

Tests extraction logic with mocked Anthropic API calls.
"""

import json
from unittest.mock import Mock, patch

import pytest

from slack_insights.extractor import (
	ExtractorError,
	build_extraction_prompt,
	extract_action_items,
	format_messages_for_claude,
	parse_extraction_response,
)


@pytest.fixture
def sample_messages():
	"""Create sample parsed messages for testing."""
	return [
		{
			"user_id": "U2X1504QH",
			"username": "Dan Ferguson",
			"timestamp": 1485881960.000002,
			"message_text": "Can you review the PR by EOD?",
		},
		{
			"user_id": "U2YFMSK3N",
			"username": "Dale Carman",
			"timestamp": 1485883487.000003,
			"message_text": "Sure, I'll take a look",
		},
		{
			"user_id": "U2X1504QH",
			"username": "Dan Ferguson",
			"timestamp": 1485958855.000006,
			"message_text": "Do you have any imagery for our AR capabilities?",
		},
	]


@pytest.fixture
def mock_claude_response():
	"""Create mock Claude API response."""
	return Mock(
		id="msg_test123",
		type="message",
		role="assistant",
		content=[
			Mock(
				type="text",
				text=json.dumps([
					{
						"task": "Review the PR",
						"date": "2017-01-31",
						"status": "open",
						"urgency": "high",
						"context": "Can you review the PR by EOD?",
					},
					{
						"task": "Provide imagery for AR capabilities",
						"date": "2017-02-01",
						"status": "open",
						"urgency": "normal",
						"context": "Do you have any imagery for our AR capabilities?",
					},
				]),
			)
		],
		usage=Mock(input_tokens=1250, output_tokens=450),
	)


def test_format_messages_for_claude(sample_messages):
	"""Test formatting messages for Claude prompt."""
	formatted = format_messages_for_claude(sample_messages)

	assert isinstance(formatted, str)
	assert "Dan Ferguson" in formatted
	assert "Can you review the PR by EOD?" in formatted
	assert "Dale Carman" in formatted
	assert "Sure, I'll take a look" in formatted


def test_format_messages_preserves_order(sample_messages):
	"""Test that message order is preserved in formatting."""
	formatted = format_messages_for_claude(sample_messages)

	# First message should appear before second
	dan_first = formatted.find("Dan Ferguson")
	dale_second = formatted.find("Dale Carman")
	dan_third = formatted.rfind("Dan Ferguson")

	assert dan_first < dale_second < dan_third


def test_build_extraction_prompt(sample_messages):
	"""Test building complete extraction prompt."""
	prompt = build_extraction_prompt(sample_messages)

	assert isinstance(prompt, str)
	assert "action items" in prompt.lower()
	assert "task" in prompt.lower()
	assert "status" in prompt.lower()
	# Should include formatted conversation
	assert "Can you review the PR by EOD?" in prompt


def test_build_extraction_prompt_with_context():
	"""Test prompt includes necessary context."""
	messages = [
		{
			"user_id": "U2X1504QH",
			"username": "Dan Ferguson",
			"timestamp": 1485881960.000002,
			"message_text": "Review this",
		}
	]

	prompt = build_extraction_prompt(messages, assigner_name="Dan Ferguson")

	assert "Dan Ferguson" in prompt or "Dan" in prompt
	# Should guide Claude to extract tasks from specific person
	assert "action items" in prompt.lower() or "tasks" in prompt.lower()


def test_parse_extraction_response_valid_json():
	"""Test parsing valid JSON response from Claude."""
	response_text = json.dumps([
		{
			"task": "Review the PR",
			"date": "2025-10-05",
			"status": "open",
			"urgency": "normal",
			"context": "Can you review the PR?",
		}
	])

	items = parse_extraction_response(response_text)

	assert len(items) == 1
	assert items[0]["task"] == "Review the PR"
	assert items[0]["status"] == "open"


def test_parse_extraction_response_markdown_wrapped():
	"""Test parsing JSON wrapped in markdown code block."""
	response_text = """Here are the action items:

```json
[
  {
    "task": "Review the PR",
    "date": "2025-10-05",
    "status": "open",
    "urgency": "normal",
    "context": "Can you review the PR?"
  }
]
```
"""

	items = parse_extraction_response(response_text)

	assert len(items) == 1
	assert items[0]["task"] == "Review the PR"


def test_parse_extraction_response_invalid_json():
	"""Test handling of invalid JSON response."""
	response_text = "This is not valid JSON"

	items = parse_extraction_response(response_text)

	# Should return empty list instead of raising exception
	assert items == []


def test_parse_extraction_response_empty_array():
	"""Test parsing empty action items array."""
	response_text = "[]"

	items = parse_extraction_response(response_text)

	assert items == []


@patch("anthropic.Anthropic")
def test_extract_action_items_success(mock_anthropic_class, sample_messages, mock_claude_response):
	"""Test successful action item extraction."""
	# Setup mock
	mock_client = Mock()
	mock_client.messages.create.return_value = mock_claude_response
	mock_anthropic_class.return_value = mock_client

	# Extract action items
	items = extract_action_items(sample_messages, api_key="test-key")

	assert len(items) == 2
	assert items[0]["task"] == "Review the PR"
	assert items[0]["status"] == "open"
	assert items[1]["task"] == "Provide imagery for AR capabilities"


@patch("anthropic.Anthropic")
def test_extract_action_items_with_metadata(
	mock_anthropic_class, sample_messages, mock_claude_response
):
	"""Test extraction preserves metadata."""
	mock_client = Mock()
	mock_client.messages.create.return_value = mock_claude_response
	mock_anthropic_class.return_value = mock_client

	items = extract_action_items(
		sample_messages,
		api_key="test-key",
		channel_id="D3Y7V95DX",
		assigner_name="Dan Ferguson",
	)

	# Items should have additional metadata
	assert len(items) > 0
	# Should have core extraction fields
	assert "task" in items[0]
	assert "status" in items[0]


@patch("anthropic.Anthropic")
def test_extract_action_items_authentication_error(mock_anthropic_class, sample_messages):
	"""Test handling of authentication error."""
	import anthropic

	mock_client = Mock()
	# Create proper mock exception
	mock_error = anthropic.AuthenticationError(
		"Invalid API key",
		response=Mock(status_code=401),
		body={"error": {"message": "Invalid API key"}},
	)
	mock_client.messages.create.side_effect = mock_error
	mock_anthropic_class.return_value = mock_client

	with pytest.raises(ExtractorError, match="Authentication failed"):
		extract_action_items(sample_messages, api_key="invalid-key")


@patch("anthropic.Anthropic")
def test_extract_action_items_rate_limit_retry(
	mock_anthropic_class, sample_messages, mock_claude_response
):
	"""Test retry logic on rate limit error."""
	import anthropic

	mock_client = Mock()
	# Fail twice, then succeed
	rate_error = anthropic.RateLimitError(
		"Rate limit exceeded",
		response=Mock(status_code=429),
		body={"error": {"message": "Rate limit exceeded"}},
	)
	mock_client.messages.create.side_effect = [
		rate_error,
		rate_error,
		mock_claude_response,
	]
	mock_anthropic_class.return_value = mock_client

	# Should succeed after retries
	items = extract_action_items(sample_messages, api_key="test-key", max_retries=3)

	assert len(items) == 2
	# Verify it was called 3 times (2 failures + 1 success)
	assert mock_client.messages.create.call_count == 3


@patch("anthropic.Anthropic")
def test_extract_action_items_max_retries_exceeded(mock_anthropic_class, sample_messages):
	"""Test failure after max retries exceeded."""
	import anthropic

	mock_client = Mock()
	rate_error = anthropic.RateLimitError(
		"Rate limit exceeded",
		response=Mock(status_code=429),
		body={"error": {"message": "Rate limit exceeded"}},
	)
	mock_client.messages.create.side_effect = rate_error
	mock_anthropic_class.return_value = mock_client

	with pytest.raises(ExtractorError, match="Rate limit"):
		extract_action_items(sample_messages, api_key="test-key", max_retries=2)


@patch("anthropic.Anthropic")
def test_extract_action_items_server_error_retry(
	mock_anthropic_class, sample_messages, mock_claude_response
):
	"""Test retry logic on server error."""
	import anthropic

	mock_client = Mock()
	# Fail once with server error, then succeed
	# Create a generic APIError with status_code attribute
	server_error = anthropic.InternalServerError(
		"Server error",
		response=Mock(status_code=529),
		body={"error": {"message": "Server error"}},
	)
	server_error.status_code = 529
	mock_client.messages.create.side_effect = [
		server_error,
		mock_claude_response,
	]
	mock_anthropic_class.return_value = mock_client

	items = extract_action_items(sample_messages, api_key="test-key")

	assert len(items) == 2
	assert mock_client.messages.create.call_count == 2


@patch("anthropic.Anthropic")
def test_extract_action_items_empty_messages(mock_anthropic_class):
	"""Test handling of empty message list."""
	items = extract_action_items([], api_key="test-key")

	# Should return empty list without calling API
	assert items == []


def test_extract_action_items_missing_api_key():
	"""Test error when API key is not provided."""
	with pytest.raises(ExtractorError, match="API key"):
		extract_action_items([{"text": "test"}], api_key=None)


@patch("anthropic.Anthropic")
def test_extract_action_items_malformed_response(mock_anthropic_class, sample_messages):
	"""Test handling of malformed API response."""
	mock_client = Mock()
	mock_response = Mock(
		content=[Mock(type="text", text="This is not JSON")],
	)
	mock_client.messages.create.return_value = mock_response
	mock_anthropic_class.return_value = mock_client

	# Should return empty list for unparseable response
	items = extract_action_items(sample_messages, api_key="test-key")

	assert items == []
