"""
Tests for thread_context module.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from slack_insights.database import init_database, insert_conversation
from slack_insights.thread_context import (
	format_thread_context,
	get_thread_parents,
	has_thread_context,
)


@pytest.fixture
def test_db():
	"""Create a temporary test database with sample thread messages."""
	# Create temporary database
	with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
		db_path = f.name

	# Initialize database
	conn = init_database(db_path)

	# Insert thread parent message
	parent_msg = {
		"channel_id": "D123",
		"user_id": "U001",
		"display_name": "Alice",
		"timestamp": 1000.0,
		"thread_ts": 1000.0,  # Thread starts here
		"message_text": "I'll send you the screenshots",
	}
	insert_conversation(conn, parent_msg)

	# Insert thread replies
	reply1 = {
		"channel_id": "D123",
		"user_id": "U002",
		"display_name": "Bob",
		"timestamp": 1100.0,
		"thread_ts": 1000.0,  # Part of thread
		"message_text": "Great, thanks!",
	}
	insert_conversation(conn, reply1)

	reply2 = {
		"channel_id": "D123",
		"user_id": "U001",
		"display_name": "Alice",
		"timestamp": 1200.0,
		"thread_ts": 1000.0,  # Part of thread
		"message_text": "Here they are",
	}
	insert_conversation(conn, reply2)

	# Insert non-thread message
	standalone_msg = {
		"channel_id": "D123",
		"user_id": "U002",
		"display_name": "Bob",
		"timestamp": 1300.0,
		"message_text": "Separate message",
	}
	insert_conversation(conn, standalone_msg)

	yield conn

	# Cleanup
	conn.close()
	Path(db_path).unlink()


def test_get_thread_parents_with_context(test_db):
	"""Test fetching parent messages for a thread reply."""
	# Create a new reply to the thread
	new_reply = {
		"timestamp": 1250.0,
		"thread_ts": 1000.0,
	}

	parents = get_thread_parents(test_db, new_reply, max_parents=3)

	assert len(parents) == 3
	assert parents[0]["message_text"] == "I'll send you the screenshots"
	assert parents[1]["message_text"] == "Great, thanks!"
	assert parents[2]["message_text"] == "Here they are"


def test_get_thread_parents_limited(test_db):
	"""Test limiting number of parent messages returned."""
	new_reply = {
		"timestamp": 1250.0,
		"thread_ts": 1000.0,
	}

	parents = get_thread_parents(test_db, new_reply, max_parents=2)

	assert len(parents) == 2
	assert parents[0]["message_text"] == "I'll send you the screenshots"
	assert parents[1]["message_text"] == "Great, thanks!"


def test_get_thread_parents_no_thread(test_db):
	"""Test behavior for non-thread messages."""
	standalone_msg = {
		"timestamp": 1300.0,
		# No thread_ts
	}

	parents = get_thread_parents(test_db, standalone_msg)

	assert parents == []


def test_get_thread_parents_no_parents_yet(test_db):
	"""Test behavior for first message in thread (no parents yet)."""
	first_msg = {
		"timestamp": 999.0,  # Before any existing messages
		"thread_ts": 1000.0,
	}

	parents = get_thread_parents(test_db, first_msg)

	assert parents == []


def test_has_thread_context_true():
	"""Test thread detection for threaded messages."""
	threaded_msg = {"thread_ts": 1000.0, "timestamp": 1100.0}

	assert has_thread_context(threaded_msg) is True


def test_has_thread_context_false():
	"""Test thread detection for non-threaded messages."""
	standalone_msg = {"timestamp": 1100.0}

	assert has_thread_context(standalone_msg) is False


def test_has_thread_context_null():
	"""Test thread detection when thread_ts is None."""
	msg = {"thread_ts": None, "timestamp": 1100.0}

	assert has_thread_context(msg) is False


def test_format_thread_context():
	"""Test formatting parent messages."""
	parents = [
		{
			"timestamp": 1000.0,
			"display_name": "Alice",
			"message_text": "First message",
		},
		{
			"timestamp": 1100.0,
			"display_name": "Bob",
			"message_text": "Second message",
		},
	]

	formatted = format_thread_context(parents)

	assert len(formatted) == 2
	assert "Alice: First message" in formatted[0]
	assert "Bob: Second message" in formatted[1]
	assert formatted[0].startswith("  ↳")
	assert formatted[1].startswith("  ↳")


def test_format_thread_context_custom_indent():
	"""Test formatting with custom indentation."""
	parents = [
		{
			"timestamp": 1000.0,
			"display_name": "Alice",
			"message_text": "Message",
		}
	]

	formatted = format_thread_context(parents, indent=">>> ")

	assert formatted[0].startswith(">>>")


def test_format_thread_context_missing_fields():
	"""Test formatting handles missing fields gracefully."""
	parents = [
		{
			# Missing timestamp, display_name, message_text
			"user_id": "U001",
		}
	]

	formatted = format_thread_context(parents)

	assert len(formatted) == 1
	assert "U001" in formatted[0]  # Falls back to user_id
	assert "??:??" in formatted[0]  # Placeholder for missing timestamp


def test_get_thread_parents_chronological_order(test_db):
	"""Test that parents are returned in chronological order (oldest first)."""
	new_reply = {
		"timestamp": 1250.0,
		"thread_ts": 1000.0,
	}

	parents = get_thread_parents(test_db, new_reply)

	# Check timestamps are in ascending order
	timestamps = [p["timestamp"] for p in parents]
	assert timestamps == sorted(timestamps)
	assert timestamps[0] == 1000.0
	assert timestamps[1] == 1100.0
	assert timestamps[2] == 1200.0
