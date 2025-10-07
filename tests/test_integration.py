"""
Integration tests for full workflow.

Tests end-to-end functionality: import -> analyze -> query
"""

import json
import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from slack_insights.cli import app
from slack_insights.database import init_database
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def sample_conversation_file():
	"""Create sample conversation file with action items."""
	data = {
		"channel_id": "D3Y7V95DX",
		"name": "Dan Ferguson",
		"messages": [
			{
				"type": "message",
				"user": "U2X1504QH",
				"text": "Can you review the PR by Friday?",
				"ts": "1485881960.000002",
			},
			{
				"type": "message",
				"user": "U2YFMSK3N",
				"text": "Sure, I'll take a look today",
				"ts": "1485883487.000003",
			},
			{
				"type": "message",
				"user": "U2X1504QH",
				"text": "Also, can you deploy to staging when ready?",
				"ts": "1485883600.000004",
			},
		],
	}

	fd, path = tempfile.mkstemp(suffix=".json")
	with os.fdopen(fd, "w") as f:
		json.dump(data, f)
	yield path
	if os.path.exists(path):
		os.unlink(path)


@pytest.fixture
def temp_db_path():
	"""Create temporary database path."""
	fd, path = tempfile.mkstemp(suffix=".db")
	os.close(fd)
	yield path
	if os.path.exists(path):
		os.unlink(path)


def test_full_workflow_import_analyze_query(
	sample_conversation_file, temp_db_path, monkeypatch
):
	"""Test complete workflow: import -> analyze -> query."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db_path)

	# Step 1: Import
	import_result = runner.invoke(app, ["import", sample_conversation_file])
	assert import_result.exit_code == 0
	assert "import" in import_result.stdout.lower()

	# Verify messages imported
	conn = init_database(temp_db_path)
	cursor = conn.execute("SELECT COUNT(*) FROM conversations")
	msg_count = cursor.fetchone()[0]
	conn.close()
	assert msg_count == 3

	# Step 2: Analyze (mocked Claude API)
	with patch("slack_insights.cli.extract_action_items") as mock_extract:
		mock_extract.return_value = [
			{
				"task": "Review the PR",
				"assigner": "Dan Ferguson",
				"assignee": "Dale Carman",
				"date": "2017-01-31",
				"status": "open",
				"urgency": "high",
				"context": "Can you review the PR by Friday?",
			},
			{
				"task": "Deploy to staging",
				"assigner": "Dan Ferguson",
				"assignee": "Dale Carman",
				"date": "2017-01-31",
				"status": "open",
				"urgency": "normal",
				"context": "Can you deploy to staging when ready?",
			},
		]

		analyze_result = runner.invoke(app, ["analyze"])
		assert analyze_result.exit_code == 0
		assert "analyz" in analyze_result.stdout.lower() or "complete" in analyze_result.stdout.lower()

	# Verify action items extracted
	conn = init_database(temp_db_path)
	cursor = conn.execute("SELECT COUNT(*) FROM action_items")
	item_count = cursor.fetchone()[0]
	conn.close()
	assert item_count == 2

	# Step 3: Query
	query_result = runner.invoke(app, ["query-person", "Dan"])
	assert query_result.exit_code == 0
	assert "action items" in query_result.stdout.lower() or "dan" in query_result.stdout.lower()


def test_idempotency_reimporting(sample_conversation_file, temp_db_path, monkeypatch):
	"""Test that re-importing same file doesn't create duplicates."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db_path)

	# Import once
	result1 = runner.invoke(app, ["import", sample_conversation_file])
	assert result1.exit_code == 0

	# Check count
	conn = init_database(temp_db_path)
	cursor = conn.execute("SELECT COUNT(*) FROM conversations")
	count1 = cursor.fetchone()[0]
	conn.close()

	# Import again
	result2 = runner.invoke(app, ["import", sample_conversation_file])
	assert result2.exit_code == 0

	# Verify same count (no duplicates)
	conn = init_database(temp_db_path)
	cursor = conn.execute("SELECT COUNT(*) FROM conversations")
	count2 = cursor.fetchone()[0]
	conn.close()

	assert count1 == count2 == 3


def test_query_filters_work_correctly(sample_conversation_file, temp_db_path, monkeypatch):
	"""Test that query filters (status, recent) work correctly."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db_path)

	# Import and analyze
	runner.invoke(app, ["import", sample_conversation_file])

	with patch("slack_insights.cli.extract_action_items") as mock_extract:
		mock_extract.return_value = [
			{
				"task": "Open task",
				"assigner": "Dan",
				"status": "open",
				"date": "2017-01-31",
			},
			{
				"task": "Completed task",
				"assigner": "Dan",
				"status": "completed",
				"date": "2017-01-31",
			},
		]
		runner.invoke(app, ["analyze"])

	# Query with status filter
	open_result = runner.invoke(app, ["query-person", "Dan", "--status", "open"])
	assert open_result.exit_code == 0

	completed_result = runner.invoke(app, ["query-person", "Dan", "--status", "completed"])
	assert completed_result.exit_code == 0


def test_empty_database_query(temp_db_path, monkeypatch):
	"""Test querying when database has no action items."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db_path)

	# Initialize empty database
	conn = init_database(temp_db_path)
	conn.close()

	# Query should succeed but show no results
	result = runner.invoke(app, ["query-person", "Dan"])
	assert result.exit_code == 0
	assert "no action items" in result.stdout.lower() or "0 items" in result.stdout.lower()
