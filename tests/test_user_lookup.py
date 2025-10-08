"""
Tests for user_lookup module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from slack_insights.user_lookup import (
	clear_cache,
	load_user_map,
	resolve_user_id,
)


@pytest.fixture(autouse=True)
def clear_user_cache():
	"""Clear cache before each test."""
	clear_cache()
	yield
	clear_cache()


@pytest.fixture
def sample_txt_file():
	"""Create a sample TXT format user file."""
	content = """Name                   ID           Bot?  Email                                              Deleted?  Restricted?
                                                                                                       
dan.ferguson           U2X1504QH          dan@groovejones.com                                          
dale.carman            U2YFMSK3N          dale@groovejones.com                                         
wade                   U03G9TC23          wade@groovejones.com                              deleted   
bot                    BSLACKBOT    bot   bot@slack.com                                                
                       U04EMPTY           empty@example.com                                 deleted   
"""

	with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
		f.write(content)
		temp_path = f.name

	yield temp_path

	# Cleanup
	Path(temp_path).unlink()


@pytest.fixture
def sample_json_file():
	"""Create a sample JSON format user file."""
	data = [
		{"id": "U2X1504QH", "name": "Dan Ferguson"},
		{"id": "U2YFMSK3N", "name": "Dale Carman"},
		{"id": "U03G9TC23", "name": "Wade"},
	]

	with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
		json.dump(data, f)
		temp_path = f.name

	yield temp_path

	# Cleanup
	Path(temp_path).unlink()


def test_load_user_map_txt_format(sample_txt_file):
	"""Test loading user map from TXT format."""
	user_map = load_user_map(sample_txt_file)

	assert isinstance(user_map, dict)
	assert len(user_map) >= 3

	# Check specific mappings
	assert user_map.get("U2X1504QH") == "dan.ferguson"
	assert user_map.get("U2YFMSK3N") == "dale.carman"
	assert user_map.get("U03G9TC23") == "wade"


def test_load_user_map_json_format(sample_json_file):
	"""Test loading user map from JSON format."""
	user_map = load_user_map(sample_json_file)

	assert isinstance(user_map, dict)
	assert len(user_map) == 3

	# Check specific mappings
	assert user_map["U2X1504QH"] == "Dan Ferguson"
	assert user_map["U2YFMSK3N"] == "Dale Carman"
	assert user_map["U03G9TC23"] == "Wade"


def test_load_user_map_file_not_found():
	"""Test error handling for missing file."""
	with pytest.raises(FileNotFoundError):
		load_user_map("nonexistent_file.txt")


def test_load_user_map_caching(sample_txt_file):
	"""Test that user map is cached after first load."""
	# First load
	user_map1 = load_user_map(sample_txt_file)

	# Second load should return cached version
	user_map2 = load_user_map(sample_txt_file)

	# Should be the same object (cached)
	assert user_map1 is user_map2


def test_resolve_user_id_found():
	"""Test resolving user ID when found in map."""
	user_map = {"U2X1504QH": "Dan Ferguson", "U2YFMSK3N": "Dale Carman"}

	result = resolve_user_id("U2X1504QH", user_map)
	assert result == "Dan Ferguson"


def test_resolve_user_id_not_found():
	"""Test resolving user ID when not in map."""
	user_map = {"U2X1504QH": "Dan Ferguson"}

	# Should return original ID if not found
	result = resolve_user_id("U_UNKNOWN", user_map)
	assert result == "U_UNKNOWN"


def test_resolve_user_id_no_map():
	"""Test resolving user ID without a map."""
	result = resolve_user_id("U2X1504QH", None)
	assert result == "U2X1504QH"


def test_clear_cache(sample_txt_file):
	"""Test clearing the cache."""
	# Load and cache
	user_map1 = load_user_map(sample_txt_file)

	# Clear cache
	clear_cache()

	# Load again should create new object
	user_map2 = load_user_map(sample_txt_file)

	# Should not be the same object
	assert user_map1 is not user_map2


def test_empty_txt_file():
	"""Test handling empty TXT file."""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
		f.write("")
		temp_path = f.name

	try:
		user_map = load_user_map(temp_path)
		assert user_map == {}
	finally:
		Path(temp_path).unlink()
		clear_cache()


def test_malformed_json():
	"""Test handling malformed JSON file."""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
		f.write("{not valid json}")
		temp_path = f.name

	try:
		with pytest.raises(json.JSONDecodeError):
			load_user_map(temp_path)
	finally:
		Path(temp_path).unlink()
		clear_cache()
