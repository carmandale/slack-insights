# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/spec.md

> Created: 2025-10-07
> Version: 1.0.0

## Test Coverage Strategy

**Target:** 80%+ code coverage for Phase 1
**Framework:** pytest with pytest-cov
**Mocking:** unittest.mock for external dependencies (Anthropic API)

## Unit Tests

### test_parser.py - SlackDump JSON Parser

**Module:** `src/slack_insights/parser.py`

**Tests:**
```python
def test_parse_slackdump_valid_json():
    """Load and parse valid SlackDump export"""
    # Given: Valid JSON file with messages
    # When: parse_slackdump(file_path)
    # Then: Returns list of Message objects

def test_parse_slackdump_invalid_json():
    """Handle malformed JSON gracefully"""
    # Given: Invalid JSON file
    # When: parse_slackdump(file_path)
    # Then: Raises ParseError with helpful message

def test_parse_message_extract_fields():
    """Extract all required fields from message"""
    # Given: Raw message dict from SlackDump
    # When: parse_message(raw_msg)
    # Then: Returns Message with user_id, text, timestamp, etc.

def test_parse_threaded_message():
    """Handle threaded conversations"""
    # Given: Message with thread_ts field
    # When: parse_message(raw_msg)
    # Then: Returns Message with thread_ts populated

def test_parse_message_missing_fields():
    """Handle messages with missing optional fields"""
    # Given: Message without thread_ts or blocks
    # When: parse_message(raw_msg)
    # Then: Returns Message with None for missing fields

def test_large_file_streaming():
    """Parse large file without loading into memory"""
    # Given: 10MB+ JSON file
    # When: parse_slackdump(file_path)
    # Then: Processes without MemoryError
```

### test_database.py - SQLite Operations

**Module:** `src/slack_insights/database.py`

**Tests:**
```python
def test_init_database_creates_tables():
    """Initialize database with schema"""
    # Given: Empty database file
    # When: init_database(db_path)
    # Then: Creates conversations and action_items tables

def test_insert_conversation():
    """Insert message into conversations table"""
    # Given: Parsed Message object
    # When: insert_conversation(db, message)
    # Then: Returns conversation_id

def test_insert_duplicate_conversation():
    """Prevent duplicate message imports"""
    # Given: Message already in database
    # When: insert_conversation(db, message)
    # Then: Raises IntegrityError or returns existing ID

def test_insert_action_item():
    """Store extracted action item"""
    # Given: Extracted ActionItem dict
    # When: insert_action_item(db, item)
    # Then: Returns action_item_id

def test_query_action_items_by_assigner():
    """Query action items by person name"""
    # Given: Database with action items from Dan and others
    # When: query_action_items(db, assigner="Dan")
    # Then: Returns only Dan's action items

def test_query_action_items_filter_status():
    """Filter by status (open/completed)"""
    # Given: Mix of open and completed items
    # When: query_action_items(db, assigner="Dan", status="open")
    # Then: Returns only open items

def test_query_action_items_recent():
    """Filter by date range (last 7 days)"""
    # Given: Action items across multiple dates
    # When: query_action_items(db, assigner="Dan", days=7)
    # Then: Returns items from last 7 days only

def test_database_transaction_rollback():
    """Handle errors with transaction rollback"""
    # Given: Database with data
    # When: Insert fails mid-transaction
    # Then: Rollback preserves database integrity
```

### test_extractor.py - Claude API Extraction

**Module:** `src/slack_insights/extractor.py`

**Tests:**
```python
@patch('anthropic.Anthropic')
def test_extract_action_items_valid_response(mock_anthropic):
    """Extract action items from Claude response"""
    # Given: Mocked Claude API returning valid JSON
    # When: extract_action_items(messages)
    # Then: Returns list of ActionItem dicts

@patch('anthropic.Anthropic')
def test_extract_action_items_no_tasks_found(mock_anthropic):
    """Handle response with no action items"""
    # Given: Claude returns empty array
    # When: extract_action_items(messages)
    # Then: Returns empty list (not error)

@patch('anthropic.Anthropic')
def test_extract_action_items_invalid_json(mock_anthropic):
    """Handle malformed JSON in response"""
    # Given: Claude returns invalid JSON
    # When: extract_action_items(messages)
    # Then: Logs error, returns empty list

@patch('anthropic.Anthropic')
def test_extract_action_items_rate_limit_retry(mock_anthropic):
    """Retry on rate limit error"""
    # Given: First call raises RateLimitError, second succeeds
    # When: extract_action_items(messages)
    # Then: Retries and returns results

@patch('anthropic.Anthropic')
def test_extract_action_items_max_retries_exceeded(mock_anthropic):
    """Fail after max retries"""
    # Given: All calls raise RateLimitError
    # When: extract_action_items(messages)
    # Then: Raises RateLimitError after 3 attempts

def test_format_messages_for_claude():
    """Format messages into readable conversation"""
    # Given: List of Message objects
    # When: format_messages_for_claude(messages)
    # Then: Returns formatted string with timestamps and speakers

def test_parse_extraction_response():
    """Parse JSON from Claude response"""
    # Given: Valid JSON string from Claude
    # When: parse_extraction_response(response_text)
    # Then: Returns list of dicts

def test_parse_extraction_response_markdown_wrapped():
    """Handle JSON wrapped in markdown code block"""
    # Given: Response with ```json ... ``` wrapper
    # When: parse_extraction_response(response_text)
    # Then: Extracts and parses JSON correctly
```

### test_query_engine.py - Query Execution

**Module:** `src/slack_insights/query_engine.py`

**Tests:**
```python
def test_query_by_person():
    """Execute person-based query"""
    # Given: Database with action items
    # When: query_by_person(db, "Dan")
    # Then: Returns matching ActionItem objects

def test_query_by_person_case_insensitive():
    """Handle case-insensitive person names"""
    # Given: Database with "Dan Ferguson"
    # When: query_by_person(db, "dan")
    # Then: Returns results for Dan

def test_query_no_results():
    """Handle queries with no matches"""
    # Given: Database with no items from "Bob"
    # When: query_by_person(db, "Bob")
    # Then: Returns empty list

def test_format_results_as_table():
    """Format query results as rich table"""
    # Given: List of ActionItem objects
    # When: format_results_as_table(items)
    # Then: Returns rich.Table with columns

def test_format_results_empty():
    """Handle empty results gracefully"""
    # Given: Empty list of items
    # When: format_results_as_table([])
    # Then: Returns "No action items found" message
```

### test_cli.py - CLI Commands

**Module:** `src/slack_insights/cli.py`

**Tests:**
```python
def test_import_command_valid_file(cli_runner):
    """Import command with valid JSON file"""
    # Given: Valid SlackDump export file
    # When: cli.invoke(["import", "file.json"])
    # Then: Exit code 0, success message displayed

def test_import_command_missing_file(cli_runner):
    """Handle missing file gracefully"""
    # Given: Non-existent file path
    # When: cli.invoke(["import", "missing.json"])
    # Then: Exit code 1, error message displayed

def test_analyze_command(cli_runner):
    """Analyze command processes messages"""
    # Given: Database with imported messages
    # When: cli.invoke(["analyze"])
    # Then: Exit code 0, progress bar shown, summary displayed

def test_query_person_command(cli_runner):
    """Query command displays results"""
    # Given: Database with analyzed action items
    # When: cli.invoke(["query-person", "Dan"])
    # Then: Exit code 0, results table displayed

def test_query_person_with_status_filter(cli_runner):
    """Query with status filter"""
    # Given: Database with items
    # When: cli.invoke(["query-person", "Dan", "--status", "open"])
    # Then: Shows only open items

def test_query_person_recent_flag(cli_runner):
    """Query with recent flag (last 7 days)"""
    # Given: Database with items across dates
    # When: cli.invoke(["query-person", "Dan", "--recent"])
    # Then: Shows only recent items
```

## Integration Tests

### test_integration.py - End-to-End Workflows

**Tests:**
```python
def test_full_workflow_import_analyze_query():
    """Complete workflow from import to query"""
    # Given: Fresh database and SlackDump file
    # When:
    #   1. Import conversations
    #   2. Analyze with Claude (mocked)
    #   3. Query results
    # Then: Results match expected action items

def test_reimport_idempotency():
    """Importing same file twice doesn't duplicate"""
    # Given: Already imported file
    # When: Import same file again
    # Then: No duplicates created, counts unchanged

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="No API key")
def test_real_claude_extraction():
    """Test with real Claude API (optional)"""
    # Given: Small batch of real messages
    # When: Call real Claude API
    # Then: Returns valid action items
```

## Mocking Requirements

### Anthropic API Client

**Mock Strategy:**
```python
from unittest.mock import Mock, patch

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client for tests"""
    with patch('anthropic.Anthropic') as mock:
        mock_client = Mock()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text='[{"task": "Test", "date": "2025-10-07", "status": "open", "urgency": "normal", "context": "Test context"}]')]
        )
        mock.return_value = mock_client
        yield mock
```

### File System

**Mock Strategy:**
```python
@pytest.fixture
def temp_database(tmp_path):
    """Create temporary database for tests"""
    db_path = tmp_path / "test.db"
    init_database(db_path)
    return db_path

@pytest.fixture
def sample_export_file(tmp_path):
    """Create sample SlackDump export file"""
    file_path = tmp_path / "sample.json"
    with open(file_path, 'w') as f:
        json.dump({
            "channel_id": "D3Y7V95DX",
            "name": "Dan Ferguson",
            "messages": [
                {
                    "type": "message",
                    "user": "U2X1504QH",
                    "text": "Can you review this?",
                    "ts": "1234567890.000000"
                }
            ]
        }, f)
    return file_path
```

## Test Data Fixtures

### fixtures/sample_export.json

**Small test dataset (10 messages):**
```json
{
    "channel_id": "D3Y7V95DX",
    "name": "Dan Ferguson",
    "messages": [
        {
            "type": "message",
            "user": "U2X1504QH",
            "text": "Can you review the PR by EOD?",
            "ts": "1696532802.522919"
        },
        // ... 9 more messages
    ]
}
```

### fixtures/claude_responses.py

**Sample Claude API responses:**
```python
VALID_EXTRACTION = {
    "id": "msg_123",
    "content": [{
        "text": '[{"task": "Review PR", "date": "2025-10-05", "status": "open", "urgency": "high", "context": "Can you review the PR by EOD?"}]'
    }]
}

EMPTY_EXTRACTION = {
    "id": "msg_456",
    "content": [{"text": "[]"}]
}

MALFORMED_JSON = {
    "id": "msg_789",
    "content": [{"text": "This is not JSON"}]
}
```

## Test Coverage Goals

**Target:** 80%+ overall coverage

**Module breakdown:**
- `parser.py`: 90%+ (simple, testable logic)
- `database.py`: 85%+ (cover all queries)
- `extractor.py`: 80%+ (mock API calls)
- `query_engine.py`: 85%+ (straightforward logic)
- `cli.py`: 70%+ (integration-focused)

**Run coverage:**
```bash
pytest --cov=src/slack_insights --cov-report=html
```

## Continuous Testing

**Run tests on every commit:**
```bash
# In pre-commit hook or CI
pytest -v
```

**Run with coverage report:**
```bash
pytest --cov=src/slack_insights --cov-report=term-missing
```

**Skip slow tests during development:**
```bash
pytest -m "not integration"
```
