"""
Test script to reconstruct what batch #100 prompt looked like.
DO NOT RUN - just for analysis.
"""

import sqlite3
from src.slack_insights.extractor import build_extraction_prompt

# Connect to database
conn = sqlite3.connect('slack_insights.db')

# Get messages for batch 100 (last 59 messages)
cursor = conn.execute("""
    SELECT id, user_id, username, message_text, timestamp
    FROM conversations
    ORDER BY timestamp ASC
    LIMIT 59 OFFSET 9900
""")

messages = [dict(row) for row in cursor.fetchall()]
conn.close()

# Build the prompt that would have been sent to Claude
prompt = build_extraction_prompt(messages, assigner_name=None)

# Print for analysis
print("=" * 80)
print("BATCH #100 PROMPT (Last 59 messages, oldest to newest)")
print("=" * 80)
print(f"\nMessage date range: {len(messages)} messages")
print("\nFull prompt:")
print(prompt)
