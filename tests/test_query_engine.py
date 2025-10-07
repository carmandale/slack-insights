"""
Tests for query engine.

Tests action item querying and result formatting.
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta

import pytest

from slack_insights.database import init_database, insert_action_item, insert_conversation
from slack_insights.query_engine import format_results_as_table, query_by_person


@pytest.fixture
def db_with_action_items():
	"""Create database with sample action items."""
	fd, path = tempfile.mkstemp(suffix=".db")
	import os

	os.close(fd)

	conn = init_database(path)

	# Insert sample conversations
	msg1 = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": 1485881960.000002,
		"message_text": "Can you review the PR?",
		"raw_json": "{}",
	}
	conv_id1 = insert_conversation(conn, msg1)

	msg2 = {
		"channel_id": "D3Y7V95DX",
		"channel_name": "Dan Ferguson",
		"user_id": "U2X1504QH",
		"username": "Dan Ferguson",
		"timestamp": datetime.now().timestamp(),
		"message_text": "Deploy to staging",
		"raw_json": "{}",
	}
	conv_id2 = insert_conversation(conn, msg2)

	# Insert action items
	item1 = {
		"conversation_id": conv_id1,
		"task_description": "Review the PR",
		"assigner_username": "Dan Ferguson",
		"assignee_username": "Dale Carman",
		"mentioned_date": "2017-01-31",
		"status": "open",
		"urgency": "high",
	}
	insert_action_item(conn, item1)

	item2 = {
		"conversation_id": conv_id2,
		"task_description": "Deploy to staging",
		"assigner_username": "Dan Ferguson",
		"assignee_username": "Dale Carman",
		"mentioned_date": datetime.now().date().isoformat(),
		"status": "completed",
		"urgency": "normal",
	}
	insert_action_item(conn, item2)

	yield conn, path

	conn.close()
	import os

	if os.path.exists(path):
		os.unlink(path)


def test_query_by_person_basic(db_with_action_items):
	"""Test querying action items by person name."""
	conn, _ = db_with_action_items

	results = query_by_person(conn, "Dan")

	assert len(results) == 2
	assert results[0]["task_description"] in ["Review the PR", "Deploy to staging"]


def test_query_by_person_full_name(db_with_action_items):
	"""Test query with full person name."""
	conn, _ = db_with_action_items

	results = query_by_person(conn, "Dan Ferguson")

	assert len(results) == 2


def test_query_by_person_with_status_filter(db_with_action_items):
	"""Test filtering by status."""
	conn, _ = db_with_action_items

	open_results = query_by_person(conn, "Dan", status="open")
	assert len(open_results) == 1
	assert open_results[0]["status"] == "open"

	completed_results = query_by_person(conn, "Dan", status="completed")
	assert len(completed_results) == 1
	assert completed_results[0]["status"] == "completed"


def test_query_by_person_recent_filter(db_with_action_items):
	"""Test filtering by recent (last 7 days)."""
	conn, _ = db_with_action_items

	recent_results = query_by_person(conn, "Dan", recent=True)

	# Should only return the recent message (today's timestamp)
	assert len(recent_results) == 1
	assert recent_results[0]["task_description"] == "Deploy to staging"


def test_query_by_person_no_results(db_with_action_items):
	"""Test query with no matching results."""
	conn, _ = db_with_action_items

	results = query_by_person(conn, "NonExistent")

	assert results == []


def test_format_results_as_table_with_data(db_with_action_items):
	"""Test formatting results as rich table."""
	conn, _ = db_with_action_items

	results = query_by_person(conn, "Dan")
	table = format_results_as_table(results)

	# Should return a Rich Table object
	from rich.table import Table

	assert isinstance(table, Table)
	# Table should have columns
	assert len(table.columns) > 0


def test_format_results_as_table_empty():
	"""Test formatting empty results."""
	table = format_results_as_table([])

	from rich.table import Table

	assert isinstance(table, Table)


def test_query_by_person_combined_filters(db_with_action_items):
	"""Test combining status and recent filters."""
	conn, _ = db_with_action_items

	results = query_by_person(conn, "Dan", status="completed", recent=True)

	assert len(results) == 1
	assert results[0]["status"] == "completed"
	assert results[0]["task_description"] == "Deploy to staging"
