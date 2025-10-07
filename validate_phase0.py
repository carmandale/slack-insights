#!/usr/bin/env python3
"""
Phase 0 Validation Script
Tests Claude AI extraction on Dan's Slack conversations
"""

import json
import os
from datetime import datetime, timezone
from anthropic import Anthropic

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def load_dan_messages(filepath, limit=50):
	"""Load recent messages from Dan"""
	with open(filepath, 'r') as f:
		data = json.load(f)

	messages = data['messages']
	print(f"Total messages: {len(messages)}")

	# Get most recent messages (sorted by timestamp)
	sorted_msgs = sorted(messages, key=lambda x: float(x['ts']), reverse=True)
	recent = sorted_msgs[:limit]

	return recent

def format_messages_for_claude(messages):
	"""Format messages into readable text for Claude"""
	formatted = []
	for msg in messages:
		ts = datetime.fromtimestamp(float(msg["ts"]), tz=timezone.utc)
		user = "Dan" if msg.get('user') == "U2X1504QH" else "Dale"
		text = msg.get('text', '')
		formatted.append(f"[{ts.strftime('%Y-%m-%d %H:%M')} UTC] {user}: {text}")

	return "\n".join(formatted)

def extract_action_items(conversation_text):
	"""Use Claude to extract action items"""
	client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

	prompt = f"""Analyze this Slack conversation between Dan (marketing lead) and Dale (developer).

Extract all action items, tasks, and requests that Dan asked Dale to do.

For each action item, provide:
- Task description
- Date mentioned
- Status (open/completed based on conversation)
- Urgency (if mentioned)

Conversation:
{conversation_text}

Return results as JSON array:
[
  {{
    "task": "description",
    "date": "YYYY-MM-DD",
    "status": "open",
    "urgency": "normal",
    "context": "relevant quote from conversation"
  }}
]
"""

	response = client.messages.create(
		model="claude-sonnet-4-20250514",
		max_tokens=4096,
		messages=[{"role": "user", "content": prompt}]
	)

	return response.content[0].text

def main():
	print("=" * 60)
	print("PHASE 0: Slack Insights Validation")
	print("=" * 60)
	print()

	# Load messages
	messages = load_dan_messages('dan-messages/D3Y7V95DX.json', limit=100)
	print(f"Analyzing last 100 messages...")
	print()

	# Format for Claude
	conversation = format_messages_for_claude(messages)

	# Extract action items
	print("Sending to Claude API for extraction...")
	results = extract_action_items(conversation)

	print()
	print("=" * 60)
	print("EXTRACTED ACTION ITEMS:")
	print("=" * 60)
	print(results)
	print()

	# Save results
	with open('phase0_results.json', 'w') as f:
		f.write(results)

	print("✅ Results saved to phase0_results.json")
	print()
	print("VALIDATION QUESTIONS:")
	print("1. Are these action items accurate?")
	print("2. Did it miss any important tasks?")
	print("3. Are there false positives?")
	print("4. Is this useful enough to build the full tool?")

if __name__ == "__main__":
	main()
