# Smart Grouping Enhancement

## The Problem You Identified

Your query "What did Dan ask me to do for Orchestrator?" returned 20 results, but many were duplicates:

```
Create icon for The Orchestrator Stream Kit    (4 times)
Help with words/descriptions of the App        (4 times)
Provide PSD file of AVP orchestrator app       (4 times)
Review content for Orchestrator App document   (4 times)
...
```

**Root Cause:** Sliding window overlap causes the same task to be extracted from multiple batches at different timestamps.

---

## The Solution: Smart Grouping

### Approach 1: Display-Time Deduplication (Implemented)

**What:** Group similar tasks when displaying results, not in database

**Files:**
- `src/slack_insights/deduplication.py` - Grouping logic
- `poc_chat_terminal.py` - Updated to use grouping

**Display Format:**
```
Found 6 unique task(s) (20 total mentions)

⏳ Create icon for The Orchestrator Stream Kit
├─ From: itzaferg │ Status: open
├─ ⚠ Mentioned 4 times (2025-10-06 to 2025-10-07)
└─ "I need an icon for the The Orchestrator Stream Kit..."

⏳ Help with words/descriptions of the Orchestrator App
├─ From: itzaferg │ Status: open
├─ ⚠ Mentioned 4 times (2025-10-06 to 2025-10-07)
└─ "Can you help me with some words/descriptions..."

✅ Provide PSD file of AVP orchestrator app
├─ From: itzaferg │ Status: completed
├─ ⚠ Mentioned 4 times (2025-10-06 to 2025-10-07)
└─ "Can i get a PSD of this? I need to put it into..."
```

**Benefits:**
- ✅ Clean, scannable output
- ✅ Shows duplicate frequency
- ✅ Date range visible
- ✅ Keeps all data in database (no data loss)
- ✅ Fast (text-based similarity)

**Tradeoff:** Duplicates still in database (storage overhead)

---

### Approach 2: Insert-Time Deduplication (Available)

**What:** Prevent duplicate insertion during extraction

**Implementation:**
```python
from slack_insights.deduplication import deduplicate_before_insert

# In cli.py analyze command, before inserting:
new_items, duplicates = deduplicate_before_insert(conn, items, days_back=30)

# Only insert new_items
for item in new_items:
    insert_action_item(conn, item)

# Log duplicates
if duplicates:
    console.print(f"[dim]Skipped {len(duplicates)} duplicate items[/dim]")
```

**Benefits:**
- ✅ Cleaner database
- ✅ Accurate counts
- ✅ No storage waste
- ✅ Better for analytics

**Tradeoff:** Might miss legitimate repeat requests

---

## Which Approach to Use?

### Recommended: Both!

**1. Insert-time deduplication** (for clean data)
- Prevents obvious duplicates during extraction
- Looks back 30 days for similar tasks
- Skips if found

**2. Display-time grouping** (for UX)
- Groups remaining similar items in query results
- Shows frequency/patterns
- User can see if task was repeated

---

## Implementation Options

### Option A: Display Grouping Only (Current - Works Now!)

**Status:** ✅ Implemented in `poc_chat_terminal.py`

**Test it:**
```bash
python poc_chat_terminal.py
```

Try: "What did Dan ask me to do for Orchestrator?"

You'll see grouped results with counts.

---

### Option B: Add Insert-Time Deduplication (30 min)

**Modify:** `src/slack_insights/cli.py` in analyze command

```python
# After extraction, before insertion:
new_items, duplicates = deduplicate_before_insert(conn, items, days_back=30)

# Report
if duplicates:
    console.print(f"[dim]  Skipped {len(duplicates)} duplicates[/dim]")

# Only insert new items
for item in new_items:
    # ... existing insertion code ...
```

**Impact:** Cleaner database, prevents future duplicates

---

### Option C: Both (Full Solution - 1 hour)

1. Add deduplication to CLI analyze command (30 min)
2. Add grouping to CLI query command (30 min)
3. Update POCs to use both

**Result:** Clean data + great UX

---

## Quick Fix for Existing Duplicates

If you want to clean up the current database:

```sql
-- Find duplicate tasks (same description + assigner + within 7 days)
WITH duplicates AS (
  SELECT 
    ai1.id,
    ai1.task_description,
    MIN(ai2.id) as keep_id
  FROM action_items ai1
  JOIN action_items ai2 
    ON ai1.task_description = ai2.task_description
    AND ai1.assigner_username = ai2.assigner_username
    AND ai1.id > ai2.id
  JOIN conversations c1 ON ai1.conversation_id = c1.id
  JOIN conversations c2 ON ai2.conversation_id = c2.id
  WHERE ABS(c1.timestamp - c2.timestamp) < 604800  -- 7 days
  GROUP BY ai1.id
)
DELETE FROM action_items WHERE id IN (SELECT id FROM duplicates);
```

**WARNING:** Test on a database copy first!

---

## My Recommendation

**For POC/Testing (Now):**
- ✅ Use updated `poc_chat_terminal.py` with grouping
- Test if grouped view is better
- Gather feedback

**For Production (After POC validation):**
1. Add insert-time deduplication to CLI (30 min)
2. Add display grouping to `query` command (30 min)
3. Clean existing duplicates with SQL (10 min)

**Total time:** 1 hour to fully solve

---

## Testing the Grouped POC

**Run it:**
```bash
python poc_chat_terminal.py
```

**Try these queries:**
1. "What did Dan ask me to do for Orchestrator?"
2. "Show me AT&T tasks"
3. "What's still open?"

**Look for:**
- ✅ Tasks grouped with counts
- ✅ "⚠ Mentioned 4 times" indicators
- ✅ Date ranges shown
- ✅ Cleaner, more scannable output

**Decide:**
- Is grouped view better than raw list?
- Should we deduplicate at insert time too?
- What threshold works best (currently 80% similarity)?

---

## What would you like to do?

1. **Test the grouped POC** (poc_chat_terminal.py) now
2. **Add deduplication to extraction** (prevents future duplicates)
3. **Clean existing duplicates** in database
4. **All of the above** (full solution)

The grouped POC is ready to test right now - just run `python poc_chat_terminal.py` and try the same Orchestrator query to see the difference!
