# POC: Natural Language Query Interface

Two ready-to-run options for testing natural language queries. Choose based on your preference.

---

## Option 1: Gradio Web UI ⭐ Recommended

**Best for:** Visual interface, easy sharing, looks professional

### Setup (5 minutes)
```bash
# 1. Install Gradio
pip install gradio

# 2. Run the POC
python poc_chat_ui.py

# 3. Open browser to http://localhost:7860
```

### Features
- ✅ Modern chat interface (like ChatGPT)
- ✅ Example queries provided as buttons
- ✅ Shows SQL query + explanation + results
- ✅ Retry/Undo/Clear buttons
- ✅ Can share with others via public URL (optional)

### What You'll See
```
┌─────────────────────────────────────────┐
│ 🤖 Slack Insights - Natural Language   │
│                                         │
│ Ask questions in plain English!         │
│                                         │
│ [What did Dan ask me to do?]  [Try it] │
│ [Show me urgent tasks]         [Try it] │
│                                         │
│ You: What's still open from Dan?        │
│                                         │
│ Bot: Found 15 results:                  │
│ 1. Provide iPad screenshots...          │
│ 2. Review Orchestrator document...      │
│ ...                                     │
└─────────────────────────────────────────┘
```

---

## Option 2: Terminal Chat

**Best for:** Quick testing, no browser needed, lightweight

### Setup (30 seconds)
```bash
# Just run it (no dependencies to install)
python poc_chat_terminal.py
```

### Features
- ✅ Runs in your terminal
- ✅ Rich formatted output (colored, tables)
- ✅ Shows SQL query and explanation
- ✅ Uses existing dependencies (rich, anthropic)

### What You'll See
```
🤖 Slack Insights - Natural Language Query POC
Ask questions in plain English. Type 'exit' to quit.

Example queries:
  • What did Dan ask me to do?
  • Show me urgent tasks
  • What's still open?

You: what did dan ask me to do?

Understanding: Finds all action items where Dan was the assigner

┌─────────────────────────────────────────┐
│           Found 12 result(s)            │
├───────────────┬───────────┬─────────────┤
│ Task          │ Status    │ Date        │
├───────────────┼───────────┼─────────────┤
│ Screenshots   │ open      │ 2025-10-07  │
│ Video cut     │ open      │ 2025-10-06  │
└───────────────┴───────────┴─────────────┘

You: 
```

---

## Comparison

| Feature | Gradio Web UI | Terminal Chat |
|---------|---------------|---------------|
| Setup time | 5 min (install gradio) | 30 sec (no install) |
| Interface | Modern web UI | Terminal text |
| Sharing | Can share URL | Local only |
| Polish | Professional | Simple |
| Dependencies | +1 (gradio) | 0 (existing) |
| Best for | Demos, sharing | Quick testing |

---

## How It Works

Both options use the same approach:

1. **User asks in natural language**  
   "What did Dan ask me to do last week?"

2. **Claude converts to SQL**
   ```sql
   SELECT ai.task_description, ai.status, datetime(c.timestamp, 'unixepoch')
   FROM action_items ai
   JOIN conversations c ON ai.conversation_id = c.id
   WHERE c.display_name LIKE '%dan%' 
     AND datetime(c.timestamp, 'unixepoch') >= datetime('now', '-7 days')
   ORDER BY c.timestamp DESC
   LIMIT 20
   ```

3. **Query runs on local database**  
   (No data leaves your machine)

4. **Results displayed**  
   Formatted as table or list

---

## Example Queries to Try

### By Person
- "What did Dan ask me to do?"
- "Show me tasks from itzaferg"
- "List all items assigned by Dan"

### By Time
- "What's from last week?"
- "Show me recent requests"
- "What tasks are from yesterday?"

### By Status
- "What's still open?"
- "Show completed tasks"
- "List urgent items"

### Combined
- "What urgent tasks did Dan give me this week?"
- "Show me open items from last month"
- "What has Dan requested that's still incomplete?"

---

## POC Goals

This POC tests whether natural language queries are:

1. **Useful** - Do they make the tool easier to use?
2. **Accurate** - Does Claude generate correct SQL?
3. **Fast** - Are responses quick enough?
4. **Worth building** - Should this become a real feature?

### Success Criteria

✅ **POC is successful if:**
- Claude generates correct SQL 80%+ of the time
- Queries return relevant results
- Response time is acceptable (2-5 seconds)
- Natural language is easier than CLI flags

❌ **POC reveals issues if:**
- SQL is often incorrect
- Results are irrelevant
- Too slow to be useful
- CLI flags are actually easier

---

## Testing Plan

### Phase 1: Basic Queries (15 minutes)
Test simple person/status queries:
- "What did Dan ask me to do?"
- "Show me open tasks"
- "List completed items"

**Look for:** Does it understand basic intent?

### Phase 2: Complex Queries (15 minutes)
Test combined filters:
- "What urgent tasks from Dan are still open?"
- "Show me completed items from last week"
- "What has Dale requested this month?"

**Look for:** Can it handle multiple filters?

### Phase 3: Edge Cases (10 minutes)
Test ambiguous/tricky queries:
- "What's urgent?" (no person specified)
- "What did I agree to do?" (reverse lookup)
- "Show everything" (unbounded query)

**Look for:** How does it handle ambiguity?

### Phase 4: User Experience (10 minutes)
Compare to existing CLI:
- CLI: `slack-insights query-person Dan --recent --status open`
- NL: "What open tasks from Dan are recent?"

**Decide:** Which is easier/better?

---

## Cost Analysis

**POC Testing (1 hour):**
- ~20-30 queries
- ~$0.05-0.10 total
- Negligible cost

**Production Implementation:**
- Each query: ~$0.005 (0.5 cents)
- 100 queries/day: ~$0.50/day
- 1000 queries/day: ~$5/day

**Tradeoff:** Convenience vs cost. Decide if worth it based on usage.

---

## Next Steps After POC

### If POC Succeeds ✅

**Immediate (4 hours):**
1. Add `query` command to CLI
2. Integrate with existing codebase
3. Add error handling
4. Write tests

**Future Enhancements:**
- Query history and learning
- Suggested queries based on patterns
- Multi-turn conversations
- Query refinement

### If POC Has Issues ❌

**Fallback Options:**
1. Add more CLI shortcuts (aliases)
2. Interactive CLI with prompts
3. Query builder wizard
4. Keep structured commands

---

## My Recommendation

**Start with Terminal Chat** (poc_chat_terminal.py):
1. No new dependencies
2. Test in 2 minutes
3. Quick feedback loop
4. See if concept works

**Then try Gradio** if terminal works well:
1. Better for demos
2. More polished
3. Can share with others
4. Easier to iterate UI

**Total POC time:** 1 hour of testing + 30 min evaluation

---

## Ready to Try?

### Terminal Version (Quickest):
```bash
python poc_chat_terminal.py
```

### Gradio Version (Best UX):
```bash
pip install gradio
python poc_chat_ui.py
# Opens browser to http://localhost:7860
```

Both are ready to run right now. Which would you like to try first?
