"""
Tests for database operations.

Tests database initialization, schema creation, and CRUD operations.
"""

import os
import sqlite3
import tempfile

import pytest

from slack_insights.database import (
	get_action_items_by_assigner,
	get_conversation,
	init_database,
	insert_action_item,
	insert_conversation,
)


@pytest.fixture
def temp_db():
	"""Create temporary database for testing."""
	fd, path = tempfile.mkstemp(suffix=".db")
	os.close(fd)
	yield path
	if os.path.exists(path):
		os.unlink(path)


@pytest.fixture
def db_conn(temp_db):
	"""Initialize database and return connection."""
	conn = init_database(temp_db)
	yield conn
	conn.close()


def test_init_database_creates_file(temp_db):
	"""Test that init_database creates database file."""
	conn = init_database(temp_db)
	assert os.path.exists(temp_db)
	conn.close()


def test_init_database_creates_conversations_table(db_conn):
	"""Test that conversations table is created with correct schema."""
	cursor = db_conn.execute(
		"SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
	)
	assert cursor.fetchone() is not None


def test_init_database_creates_action_items_table(db_conn):
	"""Test that action_items table is created with correct schema."""
	cursor = db_conn.execute(
		"SELECT name FROM sqlite_master WHERE type='table' AND name='action_items'"
	)
	assert cursor.fetchone() is not None


def test_init_database_creates_schema_versions_table(db_conn):
	"""Test that schema_versions table is created."""
	cursor = db_conn.execute(
		"SELECT name FROM sqlite_master WHERE type='table' AND name='schema_versions'"
	)
	assert cursor.fetchone() is not None


def test_init_database_records_migration_version(db_conn):
	"""Test that migration version is recorded."""
	cursor = db_conn.execute("SELECT version FROM schema_versions WHERE version = 1")
	assert cursor.fetchone() is not None


def test_init_database_creates_indexes(db_conn):
	"""Test that required indexes are created."""
	cursor = db_conn.execute(
		"SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
	)
	indexes = {row[0] for row in cursor.fetchall()}

	expected_indexes = {
		"idx_conversations_user_id",
		"idx_conversations_timestamp",
		"idx_conversations_channel_id",
		"idx_conversations_thread_ts",
		"idx_action_items_assignee",
		"idx_action_items_assigner",
		"idx_action_items_status",
		"idx_action_items_mentioned_date",
	}
	assert expected_indexes.issubset(indexes)


def test_insert_conversation(db_conn):
	"""Test inserting a conversation message."""
	message = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881960.000002,
		"message_text": "Can you review the PR?",
		"thread_ts": None,
		"message_type": "message",
		"raw_json": '{"type": "message", "text": "Can you review the PR?"}',
	}

	conversation_id = insert_conversation(db_conn, message)
	assert conversation_id is not None
	assert isinstance(conversation_id, int)


def test_insert_conversation_duplicate_prevention(db_conn):
	"""Test that duplicate conversations are detected."""
	message = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881960.000002,
		"message_text": "Can you review the PR?",
		"thread_ts": None,
		"message_type": "message",
		"raw_json": '{"type": "message"}',
	}

	# Insert once
	conversation_id1 = insert_conversation(db_conn, message)
	assert conversation_id1 is not None

	# Try to insert same message again (same channel_id and timestamp)
	conversation_id2 = insert_conversation(db_conn, message)

	# Should return existing conversation_id, not create new one
	assert conversation_id2 == conversation_id1


def test_insert_conversation_with_thread(db_conn):
	"""Test inserting a threaded conversation message."""
	message = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881970.000001,
		"message_text": "Following up on the PR",
		"thread_ts": 1485881960.000002,
		"message_type": "message",
		"raw_json": '{"type": "message", "thread_ts": "1485881960.000002"}',
	}

	conversation_id = insert_conversation(db_conn, message)
	assert conversation_id is not None

	# Verify thread_ts was stored
	cursor = db_conn.execute("SELECT thread_ts FROM conversations WHERE id = ?", (conversation_id,))
	result = cursor.fetchone()
	assert result[0] == 1485881960.000002


def test_insert_action_item(db_conn):
	"""Test inserting an action item."""
	# First insert a conversation
	message = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881960.000002,
		"message_text": "Can you review the PR by EOD?",
		"thread_ts": None,
		"message_type": "message",
		"raw_json": '{"type": "message"}',
	}
	conversation_id = insert_conversation(db_conn, message)

	# Insert action item
	action_item = {
		"conversation_id": conversation_id,
		"task_description": "Review the PR",
		"assignee_user_id": "U1234ABCD",
		"assignee_username": "Dale Carman",
		"assigner_user_id": "U2X1504QH",
		"assigner_username": "Dan Ferguson",
		"mentioned_date": "2025-10-05",
		"status": "open",
		"urgency": "high",
		"context_quote": "Can you review the PR by EOD?",
	}

	action_item_id = insert_action_item(db_conn, action_item)
	assert action_item_id is not None
	assert isinstance(action_item_id, int)


def test_insert_action_item_with_minimal_fields(db_conn):
	"""Test inserting action item with only required fields."""
	# Insert conversation
	message = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881960.000002,
		"message_text": "Can you help?",
		"thread_ts": None,
		"message_type": "message",
		"raw_json": "{}",
	}
	conversation_id = insert_conversation(db_conn, message)

	# Insert action item with minimal fields
	action_item = {
		"conversation_id": conversation_id,
		"task_description": "Help with something",
	}

	action_item_id = insert_action_item(db_conn, action_item)
	assert action_item_id is not None


def test_get_conversation(db_conn):
	"""Test retrieving a conversation by ID."""
	message = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881960.000002,
		"message_text": "Test message",
		"thread_ts": None,
		"message_type": "message",
		"raw_json": "{}",
	}
	conversation_id = insert_conversation(db_conn, message)

	# Retrieve conversation
	result = get_conversation(db_conn, conversation_id)
	assert result is not None
	assert result["id"] == conversation_id
	assert result["message_text"] == "Test message"
	assert result["username"] == "Dan Ferguson"


def test_get_action_items_by_assigner(db_conn):
	"""Test querying action items by assigner username."""
	# Insert conversation
	message = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881960.000002,
		"message_text": "Can you review the PR?",
		"thread_ts": None,
		"message_type": "message",
		"raw_json": "{}",
	}
	conversation_id = insert_conversation(db_conn, message)

	# Insert action items
	action_item1 = {
		"conversation_id": conversation_id,
		"task_description": "Review the PR",
		"assigner_username": "Dan Ferguson",
		"status": "open",
	}
	insert_action_item(db_conn, action_item1)

	action_item2 = {
		"conversation_id": conversation_id,
		"task_description": "Deploy to staging",
		"assigner_username": "Dan Ferguson",
		"status": "completed",
	}
	insert_action_item(db_conn, action_item2)

	# Query all action items from Dan
	results = get_action_items_by_assigner(db_conn, "Dan Ferguson")
	assert len(results) == 2

	# Query only open items
	open_results = get_action_items_by_assigner(db_conn, "Dan Ferguson", status="open")
	assert len(open_results) == 1
	assert open_results[0]["task_description"] == "Review the PR"


def test_foreign_key_constraint(db_conn):
	"""Test that foreign key constraint is enforced."""
	# Try to insert action item with invalid conversation_id
	action_item = {
		"conversation_id": 99999,  # Non-existent ID
		"task_description": "Invalid task",
	}

	with pytest.raises(sqlite3.IntegrityError):
		insert_action_item(db_conn, action_item)
