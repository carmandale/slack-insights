# Spec Requirements Document

> Spec: Extraction Quality Fixes
> Created: 2025-10-08
> GitHub Issue: #2
> Status: In Progress

## Overview

Fix critical extraction quality issues preventing the tool from extracting recent action items. Current state shows 0 extractions from the last 7 days despite clear action items in messages. This spec implements 5 critical fixes to make the tool functional for real-world use.

## Problem Statement

**Current State (Broken):**
- 9,959 messages imported
- 1,307 action items extracted (all from Jan 2025 timeframe)
- **0 action items from last 7 days** ❌
- 100% missing usernames (all NULL)
- No thread context handling

**Example Missed Items:**
```
"Did you make any progress on this stuff today? Let me know what you have."
"you were going to get a new video cut with some tweaks"
"Can you give me some screenshots of the iPad App?"
```

## Root Causes

Independent analyses identified 5 critical issues:

1. **Missing Display Names** - Only raw user IDs (U2X1504QH) instead of "Dan Ferguson"
2. **No Thread Context** - Thread replies lose parent message context
3. **Verbose Token Format** - 60% token waste on JSON formatting
4. **Prompt Too Formal** - Misses casual conversational requests
5. **No Batch Overlap** - Conversations cut mid-flow between batches

## User Stories

### Story 1: Username Resolution
As Dale, I want to see real names instead of user IDs in action items, so that I can understand who assigned tasks without looking up IDs.

**Workflow:**
1. System loads `users-T1YNKSBL5.txt` mapping
2. During import, resolves U2X1504QH → "Dan Ferguson"
3. Stores display_name alongside user_id
4. Backfills existing conversations with names
5. Action items show "Dan Ferguson" not "U2X1504QH"

**Problem Solved:** User IDs provide no semantic meaning to Claude. Real names enable better extraction accuracy.

### Story 2: Thread Context Preservation
As the extractor, I want to see parent messages for thread replies, so that I understand conversational context.

**Workflow:**
1. Message: "Did you make progress?" is a thread reply
2. System fetches up to 3 parent messages
3. Includes thread context: "Parent: I'll get you iPad screenshots"
4. Claude sees full conversation, not isolated question
5. Successfully extracts: "Get iPad screenshots" as action item

**Problem Solved:** Thread replies without context are meaningless. Parent messages provide necessary context.

### Story 3: Compact Transcript Format
As the system, I want to send compact transcripts to Claude, so that I can include more messages per batch with the same token budget.

**Workflow:**
1. **Before:** `{"user_id": "U2X1504QH", "timestamp": 1728133380, "text": "..."}`
2. **After:** `2025-10-05 14:23 — Dan Ferguson: Message text`
3. 60% token savings per message
4. 120 messages per batch vs 100
5. Better conversational context density

**Problem Solved:** Verbose JSON wastes tokens. Compact format maximizes context.

### Story 4: Conversational Prompt
As Claude, I want examples of casual requests in the prompt, so that I can recognize informal action items.

**Workflow:**
1. Prompt includes examples: "Did you...?", "Can you...?", "you were going to..."
2. Claude trained to recognize casual language
3. Extracts from: "Did you make progress?" → "Follow up on progress"
4. Extracts from: "you were going to get screenshots" → "Get screenshots"

**Problem Solved:** Formal prompt misses casual workplace communication style.

### Story 5: Sliding Window Batching
As the analyzer, I want overlapping batches, so that conversations aren't cut mid-thread.

**Workflow:**
1. Batch #99 ends: "I'll get you screenshots"
2. Batch #100 starts: Includes last 30 messages from #99 (overlap)
3. Reply "Did you make progress?" has parent context
4. Newest messages processed first (recent = more relevant)

**Problem Solved:** Hard batch boundaries break conversational flow.

## Spec Scope

### In Scope

1. **Username Resolution Module** (`src/slack_insights/user_lookup.py`)
   - Parse `users-T1YNKSBL5.txt` (tab-separated format)
   - Build user_id → display_name mapping
   - Global cache for performance
   - Support JSON and TXT formats

2. **Thread Context Module** (`src/slack_insights/thread_context.py`)
   - Fetch parent messages for thread replies
   - Support up to 3 parent messages
   - Handle missing parents gracefully
   - Add inline to transcript

3. **Database Migration** (`migrations/002_add_display_names.sql`)
   - Add `display_name` column to conversations
   - Backfill from user lookup
   - Add index on display_name

4. **Compact Formatter** (modify `src/slack_insights/extractor.py`)
   - Replace JSON with transcript format
   - Format: `YYYY-MM-DD HH:MM — Name: Message`
   - Include thread parents indented
   - 60% token reduction

5. **Improved Prompt** (modify `src/slack_insights/extractor.py`)
   - Add conversational examples
   - Recognize casual language patterns
   - Support JSON Lines output
   - Include confidence scoring

6. **Sliding Window** (modify `src/slack_insights/cli.py`)
   - 30-message overlap between batches
   - Newest-first ordering option
   - CLI flags: `--overlap`, `--newest-first`
   - Batch size configurable (default 120)

7. **Validation Test** (`tests/test_validation.py`)
   - Test on 500 recent messages
   - Check for 3+ items from last 7 days
   - Verify username resolution >95%
   - Validate thread context working

### Out of Scope

- Re-analysis of all messages (separate manual step)
- UI for validation results
- Advanced thread analysis (multi-level threading)
- Automatic re-extraction on schema changes
- Performance optimization (future phase)

## Technical Specifications

### Username Resolution

**Input:** `users-T1YNKSBL5.txt`
```
Name                   ID           Bot?  Email
Dan Ferguson          U2X1504QH          dan@example.com
Dale Carman           U2YFMSK3N          dale@example.com
```

**Output:** Python dict
```python
{
    "U2X1504QH": "Dan Ferguson",
    "U2YFMSK3N": "Dale Carman"
}
```

**Implementation:**
```python
def load_user_map(file_path: str) -> dict[str, str]:
    """Parse users file and return user_id -> display_name mapping."""
    # Parse tab-separated file
    # Skip header row
    # Build mapping dict
    # Cache globally
```

### Thread Context

**Schema:**
```sql
-- conversations table already has thread_ts column
-- Use it to fetch parents
SELECT * FROM conversations 
WHERE thread_ts = ? AND timestamp < ?
ORDER BY timestamp ASC LIMIT 3
```

**Implementation:**
```python
def get_thread_parents(conn, message: dict, max=3) -> list[dict]:
    """Fetch parent messages for a thread reply."""
    thread_ts = message.get("thread_ts")
    if not thread_ts:
        return []
    
    # Query for parent messages
    # Return list of parent dicts
```

### Compact Format

**Before:**
```json
[
  {"user_id": "U2X1504QH", "timestamp": 1728133380.123, "message_text": "Can you review?"}
]
```

**After:**
```text
2025-10-05 14:23 — Dan Ferguson: Can you review?
```

**With Threads:**
```
2025-10-05 14:23 — Dan Ferguson: I'll get screenshots
  ↳ 14:45 Dale Carman: Did you make progress?
```

### Improved Prompt

```
Analyze this Slack conversation and extract all action items, tasks, and requests.

IMPORTANT: Recognize both formal and casual language patterns:
- Formal: "Please review the PR"
- Casual: "Did you get a chance to look at the PR?"
- Implicit: "you were going to send me screenshots"
- Questions: "Can you give me an update?"

Examples:
1. "Did you make any progress on this?" → Action: Follow up on progress
2. "you were going to get a video cut" → Action: Create video cut
3. "Can you give me screenshots?" → Action: Provide screenshots

Transcript:
[messages here]

Return JSON Lines format (one JSON object per line):
{"task": "...", "assigner": "...", "assignee": "...", "confidence": 0.9}
```

### Sliding Window

**Batch Strategy:**
- Batch size: 120 messages
- Overlap: 30 messages
- Order: Newest first (more relevant)

**Example:**
```
Batch 1: messages 9959-9840 (120 messages)
Batch 2: messages 9869-9750 (120 messages, 30 overlap)
Batch 3: messages 9779-9660 (120 messages, 30 overlap)
```

## Expected Deliverable

1. ✅ Username resolution working (>95% coverage)
2. ✅ Thread context fetching implemented
3. ✅ Compact transcript format in use
4. ✅ Improved prompt with conversational examples
5. ✅ Sliding window with 30-message overlap
6. ✅ Validation test extracts 3+ items from last 7 days
7. ✅ All existing tests still passing
8. ✅ Database migration completed

## Success Metrics

| Metric | Before | After | Success Criteria |
|--------|--------|-------|------------------|
| Recent items (7 days) | 0 | Target: 15-30 | ≥3 items |
| Total items | 1,307 | Target: 1,800-2,200 | +400 items |
| Usernames resolved | 0% | Target: 95%+ | >90% |
| Thread context | Missing | Preserved | All threads have parents |
| Token efficiency | Baseline | +60% | Measured in logs |

## Validation Strategy

1. **Implementation** (7 hours)
   - Implement all 5 fixes
   - Write unit tests for each module
   - Update integration tests

2. **Validation Test** (1 hour, ~$0.10)
   - Run on 500 recent messages
   - Manual review of extractions
   - Verify all 5 fixes working
   - Check success criteria met

3. **Decision Gate**
   - ✅ If ≥3 items from last 7 days → Proceed to full re-analysis
   - ❌ If still 0 items → Debug and retry validation

4. **Full Re-Analysis** (5 min, ~$1.00)
   - Re-analyze all 9,959 messages
   - Compare before/after metrics
   - Document results

## Files to Create

```text
src/slack_insights/
  ├── user_lookup.py           # Username resolution
  └── thread_context.py        # Thread parent fetching

migrations/
  └── 002_add_display_names.sql  # Schema update

tests/
  ├── test_user_lookup.py
  ├── test_thread_context.py
  └── test_validation.py
```

## Files to Modify

```text
src/slack_insights/
  ├── extractor.py             # Compact format + improved prompt
  ├── cli.py                   # Sliding window batching
  ├── database.py              # Schema updates
  └── parser.py                # Add display_name support
```

## Testing Plan

### Unit Tests

1. **test_user_lookup.py**
   - Parse TXT format correctly
   - Handle missing file gracefully
   - Cache works efficiently
   - Edge cases (deleted users, bots)

2. **test_thread_context.py**
   - Fetch correct parent messages
   - Handle missing thread_ts
   - Limit to max parents
   - Order parents correctly

3. **test_compact_format.py**
   - Format timestamp correctly
   - Handle missing display_name
   - Include thread parents
   - Token count reduced

### Integration Tests

1. **test_validation.py**
   - End-to-end extraction on 500 messages
   - Verify recent extractions present
   - Check all 5 fixes integrated
   - Measure improvement metrics

## Cost Analysis

| Phase | Time | API Cost |
|-------|------|----------|
| Implementation | 7 hrs | $0 |
| Validation test | 1 hr | $0.10 |
| Full re-analysis | 5 min | $1.00 |
| **TOTAL** | **8 hrs** | **$1.10** |

**ROI:** Tool becomes functional for real work. Current state extracts 0 recent items (unusable).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Username file format changes | HIGH | Support multiple formats (JSON, TXT) |
| Thread context missing from data | MEDIUM | Graceful fallback, log warnings |
| Prompt still misses casual language | MEDIUM | Validation test catches this early |
| Token format breaks existing code | LOW | Comprehensive tests before deploy |
| Re-analysis cost exceeds budget | LOW | Validation test gates $1 spend |

## Spec Documentation

- Tasks: @.agent-os/specs/2025-10-08-extraction-quality-fixes-#2/tasks.md
- Implementation Guide: See START_HERE.md, ENHANCED_ANALYSIS_V2.md
- Reference Analysis: COMPARISON_AND_RECOMMENDATIONS.md
