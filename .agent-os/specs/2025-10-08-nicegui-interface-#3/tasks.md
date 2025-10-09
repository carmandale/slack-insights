# Tasks: NiceGUI Interface Implementation

**Issue:** #3  
**Spec:** `spec.md`  
**Timeline:** 2-3 weeks

---

## Phase 1: Foundation (Days 1-2) - 8-16 hours

### Setup & Environment
- [ ] Install NiceGUI: `pip install nicegui`
- [ ] Create directory structure: `src/slack_insights/gui/`
- [ ] Create `app.py` with basic "Hello World"
- [ ] Verify app launches at `http://localhost:8080`

### Main Layout
- [ ] Create header with app title "🔍 Slack Insights"
- [ ] Add query input field with placeholder text
- [ ] Create results container/placeholder
- [ ] Add footer (optional)
- [ ] Test responsive layout

### Mock Data Display
- [ ] Create mock grouped results data structure
- [ ] Implement tree component with mock data
- [ ] Add expand/collapse functionality
- [ ] Test interaction smoothness
- [ ] Verify no console errors

**Phase 1 Deliverable:** Working prototype with mock data

---

## Phase 2: Backend Integration (Day 3) - 6-10 hours

### Query Processing
- [ ] Import `extractor.py` for Claude API integration
- [ ] Connect query input to `on_change` or `on_submit` event
- [ ] Parse natural language with Claude
- [ ] Generate SQL query from natural language
- [ ] Add loading state indicator

### Database Integration
- [ ] Import `database.py` for SQLite access
- [ ] Execute generated SQL query
- [ ] Fetch action items from `slack_insights.db`
- [ ] Import `deduplication.py` for grouping logic
- [ ] Apply grouping to results

### Dynamic Results
- [ ] Clear previous results before new query
- [ ] Populate tree/accordion with real data
- [ ] Format: task, status, assigner, date, context
- [ ] Handle "no results found" case
- [ ] Display result count

### Error Handling
- [ ] Show error messages for failed queries
- [ ] Timeout handling (>5 seconds)
- [ ] Validate input before processing
- [ ] Log errors for debugging

**Phase 2 Deliverable:** Functional queries with real Slack data

---

## Phase 3: Visual Polish (Days 4-5) - 12-20 hours

### Visual Hierarchy
- [ ] Add status icons: ⏳ (open), ✅ (completed), ❓ (unknown)
- [ ] Implement frequency badges: "⚠ 4x"
- [ ] Color code by status: yellow (pending), green (completed), gray (unknown)
- [ ] Format dates: relative ("2 days ago") or absolute
- [ ] Truncate long context with "..." and expand on click

### Styling
- [ ] Apply Quasar theme or custom Tailwind CSS
- [ ] Consistent spacing and padding
- [ ] Hover effects on expandable items
- [ ] Smooth expand/collapse animations
- [ ] Professional color scheme

### UX Refinements
- [ ] Implement query history (last 10 queries)
- [ ] Add clear button for input field
- [ ] Create keyboard shortcuts:
  - [ ] `/` or `Ctrl+K`: Focus query input
  - [ ] `Ctrl+R`: Refresh results
  - [ ] `Esc`: Clear/close
- [ ] Display shortcut hints in UI
- [ ] Make layout responsive

### Performance Testing
- [ ] Test with 10 results
- [ ] Test with 50 results
- [ ] Test with 100+ results
- [ ] Ensure smooth scrolling
- [ ] No lag during expand/collapse
- [ ] Optimize if bottlenecks found

**Phase 3 Deliverable:** Production-ready MVP with polish

---

## Phase 4: Iteration (Week 2) - 20-30 hours

### Daily Usage Testing
- [ ] Use tool for actual Slack queries (5+ days)
- [ ] Document friction points
- [ ] Collect feature requests
- [ ] Prioritize improvements

### Bug Fixes
- [ ] Fix issues discovered during usage
- [ ] Handle edge cases:
  - [ ] Empty query
  - [ ] Very long results (>200)
  - [ ] Special characters in queries
  - [ ] Network errors
- [ ] Test error scenarios

### Nice-to-Have Features (Pick 2-3 based on priority)
- [ ] Export results to markdown
- [ ] Copy results to clipboard
- [ ] Saved queries/bookmarks
- [ ] Dark mode toggle
- [ ] Advanced filters (status, date range)
- [ ] Sort options (by date, status, frequency)

### Documentation
- [ ] Update README with NiceGUI usage
- [ ] Add screenshots of UI
- [ ] Document keyboard shortcuts
- [ ] Create user guide section
- [ ] Update CHANGELOG with v0.3.0

**Phase 4 Deliverable:** Production-ready, battle-tested

---

## Phase 5: Packaging (Optional, Week 3) - 8-12 hours

### Desktop Mode
- [ ] Enable NiceGUI `native=True` mode
- [ ] Configure PyWebView settings
- [ ] Test window size and positioning
- [ ] Add menu bar integration (macOS)

### Build Script
- [ ] Create launcher script (`slack-insights-gui`)
- [ ] Test one-click launch
- [ ] Package with PyInstaller (optional)
- [ ] Create macOS app bundle (optional)

### Distribution
- [ ] Write installation instructions
- [ ] Test installation on clean machine
- [ ] Document update mechanism
- [ ] Add to README

**Phase 5 Deliverable:** Desktop app for easier access

---

## Testing Checklist

### Unit Tests
- [ ] Test query parsing logic
- [ ] Test SQL generation
- [ ] Test deduplication grouping
- [ ] Test date formatting functions
- [ ] Test error handling

### Integration Tests
- [ ] End-to-end query flow
- [ ] Database connectivity
- [ ] Claude API integration
- [ ] State management

### Manual Testing
- [ ] Launch app successfully
- [ ] Query input accepts text and submits
- [ ] Test query: "What did Dan ask me to do?"
- [ ] Test query: "Show me urgent tasks"
- [ ] Test query: "What's still open for TMA?"
- [ ] Test query: "List completed items"
- [ ] Expand/collapse works smoothly
- [ ] Status icons display correctly
- [ ] Frequency counts accurate
- [ ] Query history persists
- [ ] Keyboard shortcuts functional
- [ ] Performance with 100+ results
- [ ] Error messages helpful
- [ ] Dark mode works (if implemented)
- [ ] Export works (if implemented)

---

## Blockers & Dependencies

### Current Blockers
- None (all prerequisites complete)

### Dependencies
- [ ] NiceGUI installed and working
- [ ] Existing modules accessible (`database.py`, `extractor.py`, `deduplication.py`)
- [ ] SQLite database available (`slack_insights.db`)
- [ ] Claude API key configured (`.env`)

---

## Progress Tracking

### Week 1 Goals
- [ ] Phase 1 complete (Foundation)
- [ ] Phase 2 complete (Backend Integration)
- [ ] Phase 3 complete (Visual Polish)
- **Target:** Working MVP by end of Week 1

### Week 2 Goals
- [ ] Phase 4 complete (Iteration)
- [ ] Tool used daily without issues
- [ ] Documentation updated
- **Target:** Production-ready by end of Week 2

### Week 3 Goals (Optional)
- [ ] Phase 5 complete (Packaging)
- [ ] Desktop app available
- [ ] Easy distribution
- **Target:** Polished desktop app

---

## Definition of Done

**For each phase:**
- [ ] All tasks in phase completed
- [ ] Code committed with meaningful messages
- [ ] No breaking changes to existing functionality
- [ ] Manual testing passed
- [ ] Documented in code comments

**For overall project:**
- [ ] All MVP features working
- [ ] Tool used daily for 5+ days
- [ ] No critical bugs
- [ ] Professional appearance
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Ready for demo

---

## Notes

**Priority:** High (Phase 3 of roadmap)  
**Complexity:** Medium (2-3 weeks)  
**Risk:** Low (NiceGUI validated by research)

**Success criteria:**
1. Launches in <3 seconds
2. Query response in <2 seconds
3. Professional appearance
4. No daily friction
5. Can demo to stakeholders

**Remember:** Start with MVP, iterate based on usage. Don't over-engineer.
