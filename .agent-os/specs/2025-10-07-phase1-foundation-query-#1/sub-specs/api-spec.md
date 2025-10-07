# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/spec.md

> Created: 2025-10-07
> Version: 1.0.0

## Overview

Phase 1 integrates with Anthropic's Claude API for action item extraction. No custom API endpoints are created in this phase - we only consume the Anthropic API.

## External API: Anthropic Claude

### Endpoint

**POST** `https://api.anthropic.com/v1/messages`

**Purpose:** Extract action items from Slack conversation batches

**Authentication:** Bearer token in header
```
x-api-key: ${ANTHROPIC_API_KEY}
```

### Request Format

```python
{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4096,
    "messages": [
        {
            "role": "user",
            "content": "<prompt with conversation data>"
        }
    ]
}
```

### Prompt Structure

**System Context:**
```
You are analyzing Slack conversations between Dan (marketing lead) and Dale (developer).
Extract all action items, tasks, and requests that Dan asked Dale to do.
```

**User Prompt Template:**
```
Analyze this Slack conversation and extract action items.

For each action item, provide:
- task: Clear description of what needs to be done
- date: Date mentioned (YYYY-MM-DD format)
- status: "open" or "completed" (infer from conversation)
- urgency: "low", "normal", or "high"
- context: Relevant quote from the conversation

Conversation:
[Formatted message batch]

Return results as JSON array:
[
  {
    "task": "description",
    "date": "YYYY-MM-DD",
    "status": "open",
    "urgency": "normal",
    "context": "quote from conversation"
  }
]
```

### Response Format

**Success (200):**
```json
{
    "id": "msg_01...",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": "[{\"task\": \"...\", ...}]"
        }
    ],
    "model": "claude-sonnet-4-20250514",
    "stop_reason": "end_turn",
    "usage": {
        "input_tokens": 1250,
        "output_tokens": 450
    }
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
    "type": "error",
    "error": {
        "type": "authentication_error",
        "message": "invalid x-api-key"
    }
}
```

**429 Rate Limit:**
```json
{
    "type": "error",
    "error": {
        "type": "rate_limit_error",
        "message": "Rate limit exceeded"
    }
}
```

**529 Overloaded:**
```json
{
    "type": "error",
    "error": {
        "type": "overloaded_error",
        "message": "Anthropic servers are temporarily overloaded"
    }
}
```

## Integration Logic

### Batch Processing

**Function:** `extract_action_items(messages: list[Message]) -> list[ActionItem]`

**Input:** Batch of ~100 Slack messages
**Output:** List of extracted action items

**Process:**
1. Format messages into readable conversation text
2. Build prompt with context and instructions
3. Call Anthropic API with retry logic
4. Parse JSON response
5. Validate extracted items
6. Return structured action items

### Error Handling

**Authentication Error (401):**
- Check if ANTHROPIC_API_KEY is set
- Validate key format (starts with "sk-ant-")
- Guide user to https://console.anthropic.com/settings/keys

**Rate Limit (429):**
- Wait for retry-after header duration
- Implement exponential backoff: 1s, 2s, 4s
- Max 3 retries before failing batch

**Server Error (529):**
- Retry with exponential backoff
- Log error for user awareness
- Continue to next batch if persistent

**Network Error:**
- Retry with exponential backoff
- Timeout after 30 seconds per request
- Fail batch after 3 attempts

### Retry Logic

```python
import time
from typing import Optional

def call_claude_with_retry(prompt: str, max_retries: int = 3) -> Optional[str]:
	"""Call Claude API with exponential backoff retry logic"""
	for attempt in range(max_retries):
		try:
			response = anthropic.messages.create(
				model="claude-sonnet-4-20250514",
				max_tokens=4096,
				messages=[{"role": "user", "content": prompt}]
			)
			return response.content[0].text

		except anthropic.RateLimitError as e:
			if attempt < max_retries - 1:
				wait_time = 2 ** attempt  # 1s, 2s, 4s
				time.sleep(wait_time)
			else:
				raise

		except anthropic.APIError as e:
			if attempt < max_retries - 1 and e.status_code >= 500:
				wait_time = 2 ** attempt
				time.sleep(wait_time)
			else:
				raise

	return None
```

### Response Parsing

**Parse JSON from Claude Response:**
```python
import json
from typing import List, Dict

def parse_extraction_response(response_text: str) -> List[Dict]:
	"""Parse JSON array from Claude's response"""
	try:
		# Claude returns JSON in markdown code block sometimes
		if "```json" in response_text:
			# Extract JSON from markdown
			start = response_text.find("[")
			end = response_text.rfind("]") + 1
			json_str = response_text[start:end]
		else:
			json_str = response_text

		items = json.loads(json_str)
		return items if isinstance(items, list) else []

	except json.JSONDecodeError as e:
		# Log error and return empty list
		print(f"Failed to parse JSON: {e}")
		return []
```

## Rate Limits & Costs

### Anthropic API Limits
- **Rate limit:** 50 requests per minute (default tier)
- **Token limit:** 100,000 tokens per minute
- **Concurrent requests:** 5

### Cost Estimation (Phase 1)

**Input:**
- 9,960 messages from Dan
- ~100 messages per batch = 100 batches
- ~1,000 tokens per batch (average)

**Cost per batch:**
- Input: 1,000 tokens × $0.003/1K = $0.003
- Output: 500 tokens × $0.015/1K = $0.0075
- Total per batch: ~$0.01

**Total Phase 1 cost:** ~$1.00 for initial analysis

**Re-analysis cost:** Same (~$1.00 per full re-analysis)

### Performance Expectations

**Single batch timing:**
- API call: ~2-5 seconds
- Parsing: <0.1 seconds
- Database insert: <0.1 seconds
- Total: ~3-6 seconds per batch

**Full analysis (100 batches):**
- Sequential: ~5-10 minutes
- With rate limiting delays: ~5-10 minutes
- Progress updates every batch

## Testing Strategy

### Mock API for Tests

**Use fixture responses in tests:**
```python
# tests/fixtures/claude_responses.py

SAMPLE_EXTRACTION_RESPONSE = {
	"id": "msg_test123",
	"type": "message",
	"role": "assistant",
	"content": [{
		"type": "text",
		"text": json.dumps([{
			"task": "Review the PR",
			"date": "2025-10-05",
			"status": "open",
			"urgency": "normal",
			"context": "Can you review the PR by EOD?"
		}])
	}]
}
```

**Mock Anthropic client in tests:**
```python
from unittest.mock import Mock, patch

@patch('anthropic.Anthropic')
def test_extract_action_items(mock_anthropic):
	mock_client = Mock()
	mock_client.messages.create.return_value = SAMPLE_EXTRACTION_RESPONSE
	mock_anthropic.return_value = mock_client

	# Test extraction logic
	items = extract_action_items(sample_messages)
	assert len(items) == 1
	assert items[0]["task"] == "Review the PR"
```

### Integration Test (Real API)

**Optional integration test with real API:**
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="No API key")
def test_real_claude_extraction():
	"""Test against real Claude API (requires API key)"""
	sample_conversation = [
		Message(user="Dan", text="Can you review this?", ts=1234567890)
	]

	items = extract_action_items(sample_conversation)
	assert len(items) > 0
	assert "review" in items[0]["task"].lower()
```
