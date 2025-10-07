"""
Tests for SlackDump JSON parser.

Tests parsing of SlackDump export format and message extraction.
"""

import json
import os
import tempfile

import pytest

from slack_insights.parser import (
	ParserError,
	parse_message,
	parse_slackdump,
)


@pytest.fixture
def sample_slackdump_json():
	"""Create sample SlackDump JSON structure."""
	return {
		"channel_id": "D3Y7V95DX",
		"name": "Dan Ferguson",
		"messages": [
			{
				"type": "message",
				"user": "U2X1504QH",
				"text": "Can you review the PR by EOD?",
				"ts": "1485881960.000002",
				"team": "T1YNKSBL5",
			},
			{
				"type": "message",
				"user": "U2YFMSK3N",
				"text": "I'll take a look",
				"ts": "1485883850.000003",
				"team": "T1YNKSBL5",
			},
		],
	}


@pytest.fixture
def sample_json_file(sample_slackdump_json):
	"""Create temporary JSON file with sample data."""
	fd, path = tempfile.mkstemp(suffix=".json")
	with os.fdopen(fd, "w") as f:
		json.dump(sample_slackdump_json, f)
	yield path
	if os.path.exists(path):
		os.unlink(path)


def test_parse_slackdump_loads_file(sample_json_file):
	"""Test that parse_slackdump loads JSON file."""
	data = parse_slackdump(sample_json_file)
	assert data is not None
	assert "channel_id" in data
	assert "messages" in data


def test_parse_slackdump_returns_messages(sample_json_file):
	"""Test that parse_slackdump returns message array."""
	data = parse_slackdump(sample_json_file)
	assert isinstance(data["messages"], list)
	assert len(data["messages"]) == 2


def test_parse_slackdump_file_not_found():
	"""Test error handling for missing file."""
	with pytest.raises(ParserError, match="File not found"):
		parse_slackdump("/nonexistent/path.json")


def test_parse_slackdump_invalid_json():
	"""Test error handling for malformed JSON."""
	fd, path = tempfile.mkstemp(suffix=".json")
	with os.fdopen(fd, "w") as f:
		f.write("{invalid json}")

	try:
		with pytest.raises(ParserError, match="Invalid JSON"):
			parse_slackdump(path)
	finally:
		os.unlink(path)


def test_parse_message_basic():
	"""Test parsing basic message."""
	raw_message = {
		"type": "message",
		"user": "U2X1504QH",
		"text": "Can you review the PR?",
		"ts": "1485881960.000002",
		"team": "T1YNKSBL5",
	}
	channel_id = "D3Y7V95DX"
	channel_name = "Dan Ferguson"

	parsed = parse_message(raw_message, channel_id, channel_name)

	assert parsed["channel_id"] == "D3Y7V95DX"
	assert parsed["channel_name"] == "Dan Ferguson"
	assert parsed["user_id"] == "U2X1504QH"
	assert parsed["message_text"] == "Can you review the PR?"
	assert parsed["timestamp"] == 1485881960.000002
	assert parsed["message_type"] == "message"
	assert parsed["thread_ts"] is None


def test_parse_message_with_thread():
	"""Test parsing threaded message."""
	raw_message = {
		"type": "message",
		"user": "U2X1504QH",
		"text": "Following up",
		"ts": "1485881970.000001",
		"thread_ts": "1485881960.000002",
		"team": "T1YNKSBL5",
	}
	channel_id = "D3Y7V95DX"
	channel_name = "Dan Ferguson"

	parsed = parse_message(raw_message, channel_id, channel_name)

	assert parsed["thread_ts"] == 1485881960.000002


def test_parse_message_missing_optional_fields():
	"""Test parsing message with missing optional fields."""
	raw_message = {
		"type": "message",
		"user": "U2X1504QH",
		"text": "Minimal message",
		"ts": "1485881960.000002",
	}
	channel_id = "D3Y7V95DX"

	parsed = parse_message(raw_message, channel_id)

	assert parsed["channel_name"] is None
	assert parsed["thread_ts"] is None
	assert parsed["message_type"] == "message"


def test_parse_message_preserves_raw_json():
	"""Test that raw JSON is preserved for reprocessing."""
	raw_message = {
		"type": "message",
		"user": "U2X1504QH",
		"text": "Test",
		"ts": "1485881960.000002",
		"extra_field": "some value",
	}
	channel_id = "D3Y7V95DX"

	parsed = parse_message(raw_message, channel_id)

	assert "raw_json" in parsed
	raw_data = json.loads(parsed["raw_json"])
	assert raw_data["extra_field"] == "some value"


def test_parse_message_file_upload():
	"""Test parsing message with file upload."""
	raw_message = {
		"type": "message",
		"user": "U2X1504QH",
		"text": "<@U2X1504QH|itzaferg> uploaded a file: <https://example.com/file.pdf|File.pdf>",
		"ts": "1485881960.000002",
		"files": [
			{
				"id": "F48UX5X9C",
				"name": "File.pdf",
				"mimetype": "application/pdf",
			}
		],
	}
	channel_id = "D3Y7V95DX"

	parsed = parse_message(raw_message, channel_id)

	# Should still parse text even if it contains file references
	assert "uploaded a file" in parsed["message_text"]


def test_parse_message_empty_text():
	"""Test parsing message with empty or missing text."""
	raw_message = {
		"type": "message",
		"user": "U2X1504QH",
		"text": "",
		"ts": "1485881960.000002",
	}
	channel_id = "D3Y7V95DX"

	parsed = parse_message(raw_message, channel_id)

	# Empty text should be preserved
	assert parsed["message_text"] == ""


def test_parse_message_missing_required_fields():
	"""Test error handling for missing required fields."""
	raw_message = {
		"type": "message",
		# missing user
		"text": "Test",
		# missing ts
	}
	channel_id = "D3Y7V95DX"

	with pytest.raises(ParserError, match="Missing required field"):
		parse_message(raw_message, channel_id)


def test_parse_slackdump_integration(sample_json_file):
	"""Test full workflow: load file and parse messages."""
	data = parse_slackdump(sample_json_file)

	# Parse all messages
	parsed_messages = []
	for raw_msg in data["messages"]:
		parsed = parse_message(raw_msg, data["channel_id"], data.get("name"))
		parsed_messages.append(parsed)

	assert len(parsed_messages) == 2
	assert all(msg["channel_id"] == "D3Y7V95DX" for msg in parsed_messages)
	assert parsed_messages[0]["message_text"] == "Can you review the PR by EOD?"
	assert parsed_messages[1]["message_text"] == "I'll take a look"


def test_parse_slackdump_empty_messages():
	"""Test handling of empty messages array."""
	data = {
		"channel_id": "D3Y7V95DX",
		"name": "Test",
		"messages": [],
	}

	fd, path = tempfile.mkstemp(suffix=".json")
	with os.fdopen(fd, "w") as f:
		json.dump(data, f)

	try:
		result = parse_slackdump(path)
		assert len(result["messages"]) == 0
	finally:
		os.unlink(path)
