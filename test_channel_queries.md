# Testing Natural Language Queries on Channel Data

## Database Status

**After importing TMA National Guard channel (C0880B0EQPM):**
- Total messages: 13,904 (9,959 DM + 3,945 channel)
- Total action items extracted: 3,342
- Recent items (last 7 days): 66

**Channel details:**
- Name: tma_nationalguard_disasterville
- Date range: January 2024 - October 2025
- Message files: 158 daily JSON files
- Time to export: 4 minutes
- Time to import: <1 minute

---

## Queries to Test

### Project-Specific Queries

**For TMA/National Guard project:**
```
What tasks need to be done for TMA?
Show me National Guard project action items
What did the team request for Disasterville?
What's still open for the TMA project?
```

### Multi-Person Queries

**Unlike DMs (1-on-1), channels have multiple participants:**
```
Who assigned tasks this week?
What did Dan ask the team to do?
Show me tasks assigned by Sarah
What requests came from the team?
```

### Project Timeline Queries

```
What was requested for TMA in September?
Show me tasks from the last sprint
What's due this week for National Guard?
What urgent items are pending?
```

### Status and Progress Queries

```
What TMA tasks are completed?
Show me open items for the project
What's blocking progress?
What needs review?
```

---

## Running the Test

```bash
cd "/Users/dalecarman/Groove Jones Dropbox/Dale Carman/Projects/dev/slack-insights"
source .venv/bin/activate

# Start the POC terminal
python poc_chat_terminal.py
```

**Try these queries:**
1. "What tasks were assigned for TMA?"
2. "Show me action items from the team"
3. "What's still open from last month?"
4. "Who asked for what?"

---

## Expected Behavior

### Good Signs ✅
- Returns relevant TMA/National Guard tasks
- Groups duplicate requests
- Shows multiple assigners (not just Dan)
- Handles project-specific keywords ("TMA", "National Guard", "Disasterville")
- Time-based filtering works

### Potential Issues ❌
- Too many false positives (discussions vs tasks)
- Missing group assignments ("can someone...")
- Lost context in threads
- Project keywords not recognized
- Wrong person attribution in group discussions

---

## Comparison: DM vs Channel

| Aspect | DM (Before) | Channel (Now) |
|--------|-------------|---------------|
| Participants | 2 (Dan, Dale) | Multiple team members |
| Message count | 9,959 | 3,945 |
| Conversations | 1-on-1 requests | Group discussions |
| Query style | "What did Dan ask me?" | "Who asked what?" |
| Assignments | Clear (Dan → Dale) | Ambiguous (team → anyone) |
| Context | Direct | Threaded discussions |

---

## Analysis Progress

The analyze command is currently running on all 13,904 messages:
- Batch size: 120 messages
- Overlap: 30 messages
- Order: newest-first
- Estimated time: 10-15 minutes
- Estimated cost: ~$1.50

**Progress monitoring:**
```bash
# Check if still running
ps aux | grep "slack-insights analyze"

# Check log
tail -f channel-analyze.log

# Check action item count
sqlite3 slack_insights.db "SELECT COUNT(*) FROM action_items"
```

---

## Next Steps

1. **Wait for analysis to complete** (~10 minutes remaining)
2. **Test queries** with poc_chat_terminal.py
3. **Document findings:**
   - What queries work well?
   - What queries fail?
   - Channel-specific issues?
   - Prompt improvements needed?
4. **Compare results:**
   - DM extraction quality
   - Channel extraction quality
   - False positive rate
   - Missing assignments

---

## Success Criteria

**POC is successful for channel data if:**
- ✅ Extracts tasks from multi-person conversations
- ✅ Natural language queries return relevant results
- ✅ Grouping works for repeated topics
- ✅ Can filter by person, project, time
- ✅ Handles project-specific terminology

**POC needs improvement if:**
- ❌ Too many false positives (discussions → tasks)
- ❌ Missing group assignments
- ❌ Lost context in complex threads
- ❌ Project keywords not recognized
- ❌ Query results irrelevant

---

## Files Created

- `groovejones-channel.zip` - SlackDump export (1.1MB, no files)
- `groovejones-channel-combined.json` - Combined 158 daily files
- `groovejones-channel-wrapped.json` - Formatted for import (3,945 messages)
- `slack_insights.db` - Updated database with channel data
- `slack_insights_dm_backup.db` - Backup of DM-only database
- `channel-analyze.log` - Analysis progress log

---

## Cost Summary

| Operation | Time | Cost |
|-----------|------|------|
| SlackDump export | 4 min | $0 |
| Import | <1 min | $0 |
| Analysis (in progress) | ~15 min | ~$1.50 |
| **Total** | **~20 min** | **~$1.50** |

---

## Ready to Test

Once analysis completes, you can:

```bash
# Test natural language queries
python poc_chat_terminal.py

# Example queries
What tasks need to be done for TMA?
Who assigned work this week?
Show me open items for National Guard
What's still pending from last month?
```

The POC will show if natural language querying works well for multi-person channel data!
