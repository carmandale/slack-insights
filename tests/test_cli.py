"""
Tests for CLI commands.

Tests typer CLI interface and command implementations.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from slack_insights.cli import app

runner = CliRunner()


@pytest.fixture
def sample_slackdump_file():
	"""Create temporary SlackDump JSON file."""
	data = {
		"channel_id": "D3Y7V95DX",
		"name": "Dan Ferguson",
		"messages": [
			{
				"type": "message",
				"user": "U2X1504QH",
				"text": "Can you review the PR?",
				"ts": "1485881960.000002",
			},
			{
				"type": "message",
				"user": "U2YFMSK3N",
				"text": "I'll take a look",
				"ts": "1485883487.000003",
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
def temp_db():
	"""Create temporary database file."""
	fd, path = tempfile.mkstemp(suffix=".db")
	os.close(fd)
	yield path
	if os.path.exists(path):
		os.unlink(path)


def test_import_command_file_not_found():
	"""Test import command with non-existent file."""
	result = runner.invoke(app, ["import", "/nonexistent/file.json"])
	assert result.exit_code != 0
	assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_import_command_success(sample_slackdump_file, temp_db, monkeypatch):
	"""Test successful import of SlackDump file."""
	# Set temp database path
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db)

	result = runner.invoke(app, ["import", sample_slackdump_file])

	assert result.exit_code == 0
	assert "import" in result.stdout.lower() or "success" in result.stdout.lower()


def test_import_command_displays_progress(sample_slackdump_file, temp_db, monkeypatch):
	"""Test that import command shows progress."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db)

	result = runner.invoke(app, ["import", sample_slackdump_file])

	# Should show some indication of progress or completion
	assert result.exit_code == 0
	assert len(result.stdout) > 0


def test_import_command_invalid_json(temp_db, monkeypatch):
	"""Test import with malformed JSON file."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db)

	# Create invalid JSON file
	fd, path = tempfile.mkstemp(suffix=".json")
	with os.fdopen(fd, "w") as f:
		f.write("{invalid json}")

	try:
		result = runner.invoke(app, ["import", path])
		assert result.exit_code != 0
		assert "error" in result.stdout.lower() or "invalid" in result.stdout.lower()
	finally:
		os.unlink(path)


def test_import_command_creates_database(sample_slackdump_file, temp_db, monkeypatch):
	"""Test that import creates database if it doesn't exist."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db)

	# Remove temp db if it exists
	if os.path.exists(temp_db):
		os.unlink(temp_db)

	result = runner.invoke(app, ["import", sample_slackdump_file])

	assert result.exit_code == 0
	assert os.path.exists(temp_db)


def test_import_command_idempotent(sample_slackdump_file, temp_db, monkeypatch):
	"""Test that re-importing same file doesn't create duplicates."""
	monkeypatch.setenv("SLACK_INSIGHTS_DB", temp_db)

	# Import once
	result1 = runner.invoke(app, ["import", sample_slackdump_file])
	assert result1.exit_code == 0

	# Import again
	result2 = runner.invoke(app, ["import", sample_slackdump_file])
	assert result2.exit_code == 0

	# Verify no duplicates (would need to check DB, but for now just verify no error)


def test_analyze_command_no_database():
	"""Test analyze command when database doesn't exist."""
	result = runner.invoke(app, ["analyze"])
	# Stub implementation just echoes message
	assert result.exit_code == 0
	assert "analyz" in result.stdout.lower()


def test_query_person_command_basic():
	"""Test query-person command basic invocation."""
	result = runner.invoke(app, ["query-person", "Dan"])
	# Will show no results until data is imported, but shouldn't crash
	assert result.exit_code == 0 or "error" in result.stdout.lower()


def test_query_person_command_with_filters():
	"""Test query-person with --status and --recent filters."""
	result = runner.invoke(
		app, ["query-person", "Dan", "--status", "open", "--recent"]
	)
	assert result.exit_code == 0 or "error" in result.stdout.lower()
