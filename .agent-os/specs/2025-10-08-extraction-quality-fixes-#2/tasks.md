# Tasks: Extraction Quality Fixes (#2)

> Last Updated: 2025-10-08
> Status: In Progress
> Estimated Total: 7 hours

## Phase 1: Username Resolution (2 hours)

### Task 1.1: Create user_lookup.py module
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 45 min

**Implementation:**
- [ ] Create `src/slack_insights/user_lookup.py`
- [ ] Implement `load_user_map(file_path: str) -> dict[str, str]`
- [ ] Parse tab-separated format from `users-T1YNKSBL5.txt`
- [ ] Handle header row correctly
- [ ] Build user_id → display_name mapping
- [ ] Add global caching mechanism
- [ ] Handle missing file gracefully
- [ ] Support both TXT and JSON formats

**Acceptance Criteria:**
- Correctly parses `users-T1YNKSBL5.txt`
- Returns dict with ~50+ user mappings
- Cache avoids re-parsing file
- Graceful error for missing file

---

### Task 1.2: Database migration for display_name
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Create `migrations/002_add_display_names.sql`
- [ ] Add `display_name TEXT` column to conversations
- [ ] Add index on `display_name` for queries
- [ ] Create migration runner that tracks version
- [ ] Test migration on copy of database first

**Acceptance Criteria:**
- Migration adds column without data loss
- Index created successfully
- Migration can be rolled back if needed
- schema_versions table updated

---

### Task 1.3: Integrate username resolution in parser
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Modify `src/slack_insights/parser.py`
- [ ] Load user map once at start
- [ ] Resolve user_id to display_name in `parse_message()`
- [ ] Add display_name to returned dict
- [ ] Handle missing users gracefully (keep user_id)
- [ ] Update parser tests

**Acceptance Criteria:**
- Messages include display_name field
- Falls back to user_id if name not found
- Existing tests still pass

---

### Task 1.4: Backfill existing conversations
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 15 min

**Implementation:**
- [ ] Create backfill script/command
- [ ] Load user map
- [ ] Update all conversations with display_name
- [ ] Show progress for 9,959 records
- [ ] Validate results with sample queries

**Acceptance Criteria:**
- >95% of conversations have display_name
- NULL only for deleted/unknown users
- Completes in <1 minute

---

## Phase 2: Thread Context (2 hours)

### Task 2.1: Create thread_context.py module
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 45 min

**Implementation:**
- [ ] Create `src/slack_insights/thread_context.py`
- [ ] Implement `get_thread_parents(conn, message, max=3) -> list[dict]`
- [ ] Query conversations by thread_ts
- [ ] Filter for messages before current timestamp
- [ ] Order by timestamp ASC
- [ ] Limit to max parents
- [ ] Return list of parent message dicts
- [ ] Handle missing thread_ts gracefully

**Acceptance Criteria:**
- Fetches correct parent messages
- Returns empty list for non-thread messages
- Limited to specified max (default 3)
- Parents ordered chronologically

---

### Task 2.2: Integrate thread context in extractor
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 45 min

**Implementation:**
- [ ] Modify `src/slack_insights/extractor.py`
- [ ] Import thread_context module
- [ ] Pass database connection to formatter
- [ ] Fetch parents for each message
- [ ] Include parents in transcript (indented)
- [ ] Format: `  ↳ HH:MM Name: Message`
- [ ] Update tests

**Acceptance Criteria:**
- Thread replies show parent context
- Parents are indented/formatted clearly
- Non-thread messages unchanged
- Tests verify thread context included

---

### Task 2.3: Test thread context with real data
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Identify thread messages in database
- [ ] Test `get_thread_parents()` on real examples
- [ ] Verify correct parents returned
- [ ] Check edge cases (orphaned threads, missing parents)
- [ ] Document findings

**Acceptance Criteria:**
- Real thread examples work correctly
- Edge cases handled gracefully
- Performance acceptable (<100ms per fetch)

---

## Phase 3: Compact Format (1 hour)

### Task 3.1: Implement compact formatter
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 45 min

**Implementation:**
- [ ] Modify `format_messages_for_claude()` in extractor.py
- [ ] Change from JSON to transcript format
- [ ] Format: `YYYY-MM-DD HH:MM — Name: Message text`
- [ ] Use display_name if available, fallback to user_id
- [ ] Include thread parents inline with indentation
- [ ] Remove JSON serialization
- [ ] Update function docstring

**Acceptance Criteria:**
- Compact format matches specification
- Thread parents indented correctly
- Token count reduced by ~60%
- Timestamp formatting correct

---

### Task 3.2: Test token efficiency
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 15 min

**Implementation:**
- [ ] Create test comparing old vs new format
- [ ] Measure token count for same 100 messages
- [ ] Use tiktoken library (cl100k_base encoding)
- [ ] Document token savings
- [ ] Verify readability maintained

**Acceptance Criteria:**
- Token reduction ≥50%
- Format remains readable
- No information loss

---

## Phase 4: Improved Prompt (1 hour)

### Task 4.1: Design conversational prompt
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Modify `build_extraction_prompt()` in extractor.py
- [ ] Add section on casual language patterns
- [ ] Include 5-10 conversational examples
- [ ] Add patterns: "Did you...?", "Can you...?", "you were going to..."
- [ ] Specify JSON Lines output format
- [ ] Add confidence scoring field
- [ ] Test prompt with real examples

**Acceptance Criteria:**
- Prompt recognizes casual requests
- Examples cover common patterns
- Maintains formal request extraction
- Clear output format specified

---

### Task 4.2: Update response parser
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Modify `parse_extraction_response()` in extractor.py
- [ ] Support JSON Lines format (newline-separated JSON)
- [ ] Handle both array and JSON Lines responses
- [ ] Parse confidence scores
- [ ] Filter low-confidence items (optional)
- [ ] Update tests

**Acceptance Criteria:**
- Parses both JSON array and JSON Lines
- Extracts confidence scores
- Backwards compatible with old format
- Tests cover new format

---

## Phase 5: Sliding Window (1 hour)

### Task 5.1: Implement sliding window in CLI
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 45 min

**Implementation:**
- [ ] Modify `analyze()` command in cli.py
- [ ] Add `--overlap` flag (default 30)
- [ ] Add `--newest-first` flag (default True)
- [ ] Implement sliding window logic
- [ ] Adjust batch size to 120
- [ ] Order messages by timestamp DESC if newest-first
- [ ] Create batches with overlap
- [ ] Update progress display

**Acceptance Criteria:**
- Batches overlap by specified amount
- Newest-first ordering works
- No messages skipped
- Progress bar shows correct count

---

### Task 5.2: Test batching logic
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 15 min

**Implementation:**
- [ ] Create unit test for batch creation
- [ ] Test with various message counts
- [ ] Verify overlap correctness
- [ ] Check edge cases (messages < batch_size)
- [ ] Validate no duplicates in storage

**Acceptance Criteria:**
- Batches created correctly
- Overlap prevents context loss
- Edge cases handled
- No duplicate extractions

---

## Phase 6: Validation (1 hour)

### Task 6.1: Create validation test script
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Create `tests/test_validation.py`
- [ ] Test on 500 most recent messages
- [ ] Run full extraction pipeline
- [ ] Count items from last 7 days
- [ ] Check username resolution coverage
- [ ] Verify thread context working
- [ ] Output detailed report

**Acceptance Criteria:**
- Extracts items from recent messages
- ≥3 items from last 7 days
- >90% usernames resolved
- Thread context visible in logs

---

### Task 6.2: Manual review validation
**Status:** 🔲 Not Started  
**Assignee:** Dale  
**Estimate:** 30 min

**Implementation:**
- [ ] Review extracted items from validation test
- [ ] Check against known action items
- [ ] Identify false positives
- [ ] Identify false negatives
- [ ] Verify casual language extraction working
- [ ] Document findings

**Acceptance Criteria:**
- Sample of 20-30 items reviewed
- False positive rate <20%
- Casual requests being captured
- Decision made on full re-analysis

---

## Phase 7: Testing & Documentation (ongoing)

### Task 7.1: Unit tests
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 1 hour (parallel to implementation)

**Implementation:**
- [ ] `tests/test_user_lookup.py` - Username resolution
- [ ] `tests/test_thread_context.py` - Thread fetching
- [ ] `tests/test_compact_format.py` - Format conversion
- [ ] `tests/test_improved_prompt.py` - Prompt generation
- [ ] `tests/test_sliding_window.py` - Batch creation
- [ ] All tests pass with pytest

**Acceptance Criteria:**
- Test coverage >80%
- All critical paths tested
- Edge cases covered
- Tests run in <10 seconds

---

### Task 7.2: Integration tests
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Update existing integration tests
- [ ] Test full import → analyze → query pipeline
- [ ] Verify all 5 fixes working together
- [ ] Test with real data sample
- [ ] Mock Anthropic API calls

**Acceptance Criteria:**
- End-to-end tests pass
- All fixes integrated correctly
- Performance acceptable
- No regressions

---

### Task 7.3: Update documentation
**Status:** 🔲 Not Started  
**Assignee:** Claude  
**Estimate:** 30 min

**Implementation:**
- [ ] Update README with new features
- [ ] Document CLI flags (--overlap, --newest-first)
- [ ] Add section on username resolution
- [ ] Explain thread context handling
- [ ] Update examples with new output format
- [ ] Add troubleshooting for common issues

**Acceptance Criteria:**
- README reflects all changes
- Examples are accurate
- Clear upgrade path documented
- Known issues listed

---

## Summary

**Total Tasks:** 24
**Completed:** 0
**In Progress:** 0
**Not Started:** 24

**Estimated Time:** 7 hours implementation + 1 hour validation

**Critical Path:**
1. Username resolution (blocks all others)
2. Thread context (blocks validation)
3. Compact format (blocks validation)
4. Improved prompt (blocks validation)
5. Sliding window (blocks validation)
6. Validation test (decision gate)

**Blockers:** None

**Next Action:** Begin Task 1.1 (Create user_lookup.py module)
