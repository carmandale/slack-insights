# Interactive Expansion Feature

## What's New

The terminal POC now supports **interactive expansion** - you can dig into grouped tasks to see all individual instances!

---

## How It Works

### 1. Run a query
```bash
python poc_chat_terminal.py
```

Query: "What did Dan ask me to do for Orchestrator?"

### 2. See numbered, grouped results
```
Found 6 unique task(s) (20 total mentions)

1. ⏳ Create icon for The Orchestrator Stream Kit
├── From: itzaferg │ Status: open
├── ⚠ Mentioned 4 times (2025-10-06 to 2025-10-07) (type '1' to expand)
└── "I need an icon for the The Orchestrator Stream Kit..."

2. ⏳ Help with words/descriptions of the Orchestrator App
├── From: itzaferg │ Status: open
├── ⚠ Mentioned 4 times (2025-10-06 to 2025-10-07) (type '2' to expand)
└── "Can you help me with some words/descriptions..."

3. ✅ Provide PSD file of AVP orchestrator app
├── From: itzaferg │ Status: completed
├── ⚠ Mentioned 3 times (2025-10-06 to 2025-10-07) (type '3' to expand)
└── "Can i get a PSD of this? I need to put it into..."

💡 Tip: Type a number (e.g., '1') to see all instances of that task
```

### 3. Type a number to expand
```
You: 1
```

### 4. See all instances
```
📋 All 4 instances of:
Create icon for The Orchestrator Stream Kit

⏳ Instance 1 - 2025-10-07 12:22:17
├── Status: open
└── Context:
    I need an icon for the The Orchestrator Stream Kit - An APK that 
    allows 3rd party developers to integrate their apps into our 
    platform for seamless AR experiences.

⏳ Instance 2 - 2025-10-07 12:21:49
├── Status: open
└── Context:
    I need an icon for the The Orchestrator Stream Kit - An APK that 
    allows 3rd party developers to integrate their apps...

⏳ Instance 3 - 2025-10-06 23:13:53
├── Status: open
└── Context:
    I need an icon for the The Orchestrator Stream Kit...

⏳ Instance 4 - 2025-10-06 13:35:04
├── Status: open
└── Context:
    I need an icon for the The Orchestrator Stream Kit...
```

### 5. Continue with new queries
```
You: What AT&T tasks are still open?
```

---

## Key Features

**✅ Numbered Groups**
- Each task group gets a number (1, 2, 3...)
- Easy reference for expansion

**✅ Expand Hint**
- Groups with multiple instances show: `(type '1' to expand)`
- Tooltip at bottom: `💡 Tip: Type a number...`

**✅ Full Context**
- Expansion shows complete context from each instance
- See exact dates for each mention
- Understand patterns (was it repeated over days? same day?)

**✅ Smart Flow**
- After expanding, ask another question
- Or expand another group by typing its number
- Type `exit` to quit anytime

---

## Example Session

```
You: What did Dan ask me to do for Orchestrator?

Found 6 unique task(s) (20 total mentions)

1. ⏳ Create icon for The Orchestrator Stream Kit
   ⚠ Mentioned 4 times (2025-10-06 to 2025-10-07) (type '1' to expand)

2. ⏳ Help with words/descriptions of the Orchestrator App  
   ⚠ Mentioned 4 times (2025-10-06 to 2025-10-07) (type '2' to expand)

💡 Tip: Type a number (e.g., '1') to see all instances

You: 1

📋 All 4 instances of:
Create icon for The Orchestrator Stream Kit

[Shows all 4 instances with dates and contexts]

You: What about AT&T?

Found 15 unique task(s) (45 total mentions)

1. ⏳ Brainstorm on new AT&T project
   ⚠ Mentioned 3 times (2025-10-06 to 2025-10-07)

2. ⏳ Complete AT&T storyboards by EOD Tuesday
   Date: 2025-10-07

...

You: exit
```

---

## Benefits

### For You
- **See patterns** - Is Dan asking repeatedly? Or just duplicates from extraction?
- **Full context** - Read exact wording from each mention
- **Quick scanning** - Grouped view shows unique tasks fast
- **Deep dive** - Expand only what you need

### For the Tool
- **Better UX** - Collapsed by default, expandable on demand
- **Flexible** - Works for any query result
- **Fast** - Expansion is instant (no API call)
- **Progressive disclosure** - Show high-level first, details on request

---

## Technical Details

**Grouping Algorithm:**
- Text-based similarity (80% Jaccard similarity threshold)
- Groups by task description + assigner
- Shows first instance as canonical
- Counts all matches

**Expansion:**
- Stores last query's groups in memory
- User types number → shows all instances
- Shows full context, dates, status for each
- No database query needed (already loaded)

**State Management:**
- Groups stored in `last_groups` variable
- Cleared on new query
- Persists between expansions

---

## Try It Now!

```bash
python poc_chat_terminal.py
```

**Suggested test flow:**
1. Ask: "What did Dan ask me to do for Orchestrator?"
2. Notice numbered groups with counts
3. Type: `1` to expand first group
4. See all 4 instances
5. Ask another question
6. Type `2` to expand that group

---

## Next Steps

Once you validate this UX works:

1. **Integrate to CLI** - Add as `slack-insights query` command
2. **Add keyboard shortcuts** - Arrow keys to navigate, Enter to expand
3. **Add filtering** - Only show open items, recent items, etc.
4. **Save expansions** - Export expanded view to file

This interactive expansion makes the tool much more powerful for understanding patterns and context!
