# Importing and Querying a Slack Channel

Guide for testing natural language queries on project channels.

---

## Step 1: Export the Channel with SlackDump

### Option A: Using SlackDump CLI

```bash
# Export a specific channel by ID
slackdump export -o channel-export.zip C0880B0EQPM

# Or export by channel name
slackdump export -o channel-export.zip -c "channel-name"

# Extract the exported data
unzip channel-export.zip -d channel-data/
```

**Channel ID:** `C0880B0EQPM` (from the URL)

### Option B: Export Multiple Channels

```bash
# Export all channels you're a member of
slackdump export -o all-channels.zip

# Or export specific workspace
slackdump export -o workspace.zip -w "Groove Jones"
```

### Getting Your Slack Token

If you don't have a token yet:

1. Visit: https://api.slack.com/custom-integrations/legacy-tokens
2. Click "Create token" for your workspace
3. Copy the token (starts with `xoxp-`)
4. Set it as environment variable:
   ```bash
   export SLACK_TOKEN="xoxp-your-token-here"
   ```

---

## Step 2: Import into Slack Insights

```bash
# Activate virtual environment
cd "/Users/dalecarman/Groove Jones Dropbox/Dale Carman/Projects/dev/slack-insights"
source .venv/bin/activate

# Import the channel data
slack-insights import channel-data/C0880B0EQPM.json

# Or if you have a different structure:
slack-insights import channel-export/channels/C0880B0EQPM.json
```

**Expected output:**
```
✓ Imported 1,234 messages
✓ Date range: 2024-01-15 to 2025-10-08
✓ Participants: 12 users
```

---

## Step 3: Analyze to Extract Action Items

```bash
# Run extraction with newest-first (default)
slack-insights analyze

# Or with specific filters for the channel
slack-insights analyze --newest-first --batch-size 120 --overlap 30
```

**Expected output:**
```
Processing 1,234 messages...
[███████████████████] 100% Complete
✓ Extracted 87 action items
Cost: ~$0.15
```

---

## Step 4: Test Natural Language Queries

```bash
# Start the POC terminal
python poc_chat_terminal.py
```

### Example Queries for Project Channel

Since this is a project channel, try queries like:

**By Person:**
- "What tasks did Dan assign?"
- "What did Sarah ask people to do?"
- "Show me action items from the team"

**By Project/Topic:**
- "What tasks are related to the iOS app?"
- "Show me design-related requests"
- "What needs to be done for the demo?"

**By Time:**
- "What was requested this week?"
- "Show me tasks from last month"
- "What's still open from the sprint?"

**By Status:**
- "What tasks are incomplete?"
- "Show me completed items"
- "What's urgent?"

**Combined:**
- "What did Dan ask about the iOS app this week?"
- "Show me open design tasks from Sarah"
- "What urgent items are still pending?"

---

## Differences: DM vs Channel

### Direct Message (what you tested before)
- Usually 2 people
- "What did Dan ask me to do?" → clear context
- Personal tasks and requests

### Project Channel (what you're testing now)
- Multiple participants
- Group conversations
- Mix of requests, discussions, updates
- More complex thread structures

### Query Adjustments

**DM queries:**
- "What did Dan ask me to do?" ✓

**Channel queries:**
- "What did Dan ask?" (no "me" - could be asking anyone)
- "What tasks were assigned to Dale?"
- "Show me all action items from the team"

---

## Step 5: Evaluate Channel-Specific Patterns

Watch for:

### Thread Complexity
- Channels use threads heavily
- Parent-child context is critical
- Example: "Can someone take this?" → Reply: "I'll do it"

### Multiple Assigners
- DMs: One person asking
- Channels: Multiple people assigning tasks
- Query: "Who asked for what?"

### Ambiguous Assignments
- "Can someone review the PR?" (no specific assignee)
- "We need to fix the bug" (group responsibility)
- POC should handle these gracefully

### Status Tracking
- Channels often have status updates
- "Done ✓" or "Completed" messages
- Should affect status field

---

## Testing Checklist

- [ ] Export channel C0880B0EQPM
- [ ] Import successfully
- [ ] Run analyze command
- [ ] Verify action items extracted
- [ ] Test basic queries (by person, date, status)
- [ ] Test complex queries (combined filters)
- [ ] Test grouping/expansion on duplicates
- [ ] Note any channel-specific issues

---

## Expected Challenges

### 1. Group Assignments
**Challenge:** "Can someone handle this?"  
**Current:** Might not extract (no clear assignee)  
**Solution:** Extract with assignee=NULL or assignee="team"

### 2. Cross-References
**Challenge:** "See Sarah's comment above"  
**Current:** No link to referenced message  
**Solution:** Thread context should help

### 3. Status Updates
**Challenge:** "Fixed!" in reply to task  
**Current:** Separate message, might not update status  
**Solution:** Future enhancement - link replies to tasks

### 4. More Noise
**Challenge:** Discussions, updates, not just requests  
**Current:** Might extract non-tasks  
**Solution:** Confidence scoring should filter

---

## Troubleshooting

### "Channel not found in export"

```bash
# List what's in the export
unzip -l channel-export.zip

# Look for JSON files
find channel-data/ -name "*.json" -type f
```

### "No messages imported"

```bash
# Check the JSON structure
head -50 channel-data/C0880B0EQPM.json

# Verify it's SlackDump format (not official Slack export)
```

### "Import error: Invalid format"

The tool expects **SlackDump** format, not Slack's official export format.

**SlackDump format:**
```json
[
  {
    "user": "U123",
    "text": "Message",
    "ts": "1234567890.123456",
    "thread_ts": "1234567890.000000"
  }
]
```

**Official Slack export (not supported):**
```json
{
  "channels": [...],
  "users": [...],
  "messages": [...]
}
```

---

## Quick Start (TL;DR)

```bash
# 1. Export channel
slackdump export -o channel.zip C0880B0EQPM
unzip channel.zip -d channel-data/

# 2. Import and analyze
cd "/Users/dalecarman/Groove Jones Dropbox/Dale Carman/Projects/dev/slack-insights"
source .venv/bin/activate
slack-insights import channel-data/C0880B0EQPM.json
slack-insights analyze

# 3. Query
python poc_chat_terminal.py
```

---

## What to Look For

**Success indicators:**
- ✅ Multiple participants' tasks extracted
- ✅ Thread context preserved
- ✅ Natural language queries return relevant results
- ✅ Grouping works for repeated topics
- ✅ Can filter by person, date, status

**Potential issues:**
- ❌ Too many false positives (discussions mistaken for tasks)
- ❌ Missing group assignments ("can someone...")
- ❌ Lost context in complex threads
- ❌ Queries too specific for channel data

---

## After Testing

Document findings:
1. What queries worked well?
2. What queries failed?
3. Channel-specific issues discovered?
4. Prompt improvements needed?
5. Is the POC useful for project channels?

This will inform whether to:
- Productionize the POC
- Improve extraction for channels
- Add channel-specific features
- Pivot to different use case

---

## Need Help?

**SlackDump docs:** https://github.com/rusq/slackdump  
**Slack API tokens:** https://api.slack.com/custom-integrations/legacy-tokens  

**Common issues:**
- Token permissions: Needs `channels:history` scope
- Private channels: Must be a member
- Rate limits: SlackDump handles automatically
