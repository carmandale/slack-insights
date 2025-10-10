# Feature Specification: NiceGUI Interface for Natural Language Queries

**Issue:** #3  
**Created:** 2025-10-08  
**Status:** Planning → Implementation  
**Timeline:** 2-3 weeks

---

## Overview

Build a production-ready web-based GUI using NiceGUI to replace the terminal POC with a polished, professional interface for natural language queries of Slack action items.

---

## Problem Statement

### Current State
- Terminal POC (`poc_chat_terminal.py`) validates the natural language query concept
- Smart grouping and interactive expansion work well
- Tested with 13,904 messages (9,959 DM + 3,945 channel)
- 4,730 action items extracted with 66 from last 7 days

### Limitations of Terminal POC
- Terminal UI not ideal for daily desktop usage
- Limited visual polish (no colors/icons in all terminals)
- Hard to share or demo to non-technical users
- Not easily accessible from Spotlight/Raycast
- Mouse interaction limited

### Desired State
- Professional web-based GUI accessible from browser
- Modern UI with visual hierarchy (icons, colors, badges)
- Smooth expand/collapse interactions for grouped results
- Quick to launch (<3 seconds)
- Can be packaged as desktop app if needed
- Maintains privacy-first, local-only architecture

---

## Research Summary

### Framework Decision: NiceGUI

**Research conducted:** October 2025  
**Models evaluated:** Claude Opus, Grok, OpenAI o1  
**Frameworks compared:** 13 total (Streamlit, NiceGUI, Textual, PyQt6, FastAPI+React, etc.)

**Consensus:**
- **NiceGUI:** 4.35/5.0 average (Grok: 4.6, OpenAI: 4.3, Claude: 4.15)
- **Textual:** 4.07/5.0 average (Claude: 4.40, Grok: 4.3, OpenAI: 3.5)

**Why NiceGUI won:**
1. Python-native (no JavaScript required)
2. Modern Quasar/Vue components provide professional appearance
3. Event-driven architecture (no Streamlit-style full reruns)
4. Native tree/accordion support for hierarchical data
5. 3-6 day MVP timeline
6. Can package as desktop app with PyWebView
7. Better for demos and sharing than terminal UI

**Research location:** `.agent-os/research/ui-options-2025-10/`

---

## Requirements

### Functional Requirements

#### Core Features (Must Have)
1. **Natural Language Query Input**
   - Single text input field with placeholder: "What did Dan ask me to do?"
   - Submit on Enter key or button click
   - Clear visual feedback during query processing

2. **Hierarchical Results Display**
   - Group similar/duplicate tasks (e.g., "⚠ Mentioned 4 times")
   - Tree or accordion structure for expand/collapse
   - Show: task description, status, assigner, date
   - Context quote preview (truncated)

3. **Interactive Expansion**
   - Click to expand/collapse grouped items
   - Smooth animations (no flicker)
   - Show all instances within a group when expanded
   - Each instance shows: date, status, full context

4. **Visual Hierarchy**
   - Status icons: ⏳ open, ✅ completed, ❓ unknown
   - Frequency indicators: "⚠ Mentioned 4 times"
   - Date formatting: relative (e.g., "2 days ago") or absolute
   - Color coding: pending (yellow), completed (green)

5. **Backend Integration**
   - Connect to existing `src/slack_insights/` modules
   - Use deduplication logic from `deduplication.py`
   - Query parsing via Claude API (natural language → SQL)
   - Real-time data from `slack_insights.db`

#### Enhanced Features (Nice to Have)
6. **Query History**
   - Show recent 10 queries
   - Click to re-run previous query
   - Store in local storage (no database needed)

7. **Keyboard Shortcuts**
   - `/` or `Ctrl+K`: Focus query input
   - `Ctrl+R`: Refresh results
   - `Esc`: Close/clear

8. **Export Results**
   - Export visible results to markdown
   - Copy to clipboard option

9. **Dark Mode**
   - Toggle light/dark theme
   - System preference detection

10. **Desktop App Packaging**
    - Use PyWebView for native window
    - One-click launch (no browser UI)
    - macOS menu bar icon (optional)

### Non-Functional Requirements

1. **Performance**
   - Query response: <2 seconds for 100 results
   - App launch: <3 seconds
   - Smooth scrolling with 100+ results
   - No lag during expand/collapse

2. **Privacy & Security**
   - All data stays local (no cloud sync)
   - No telemetry or tracking
   - Database remains `slack_insights.db`

3. **Usability**
   - Professional appearance (not prototype-y)
   - Intuitive interactions (no learning curve)
   - Error messages are helpful
   - Loading states are clear

4. **Maintainability**
   - Pure Python codebase
   - Minimal dependencies (NiceGUI + existing)
   - Clear code structure
   - Documented functions

---

## Technical Architecture

### Technology Stack

**Framework:** NiceGUI 1.4+ (latest stable)  
**Backend:** FastAPI (built into NiceGUI)  
**Database:** SQLite (existing `slack_insights.db`)  
**AI:** Anthropic Claude API (existing integration)  
**Language:** Python 3.11+

### Component Structure

```
src/slack_insights/
├── gui/
│   ├── __init__.py
│   ├── app.py              # Main NiceGUI app
│   ├── components/
│   │   ├── query_input.py  # Search input component
│   │   ├── results_tree.py # Hierarchical results display
│   │   └── status_icons.py # Visual indicators
│   └── utils/
│       ├── formatting.py   # Date/text formatting
│       └── state.py        # App state management
├── database.py             # Existing (database access)
├── extractor.py            # Existing (Claude integration)
└── deduplication.py        # Existing (grouping logic)
```

### Data Flow

```
User Input → NiceGUI App → Query Parser (Claude) → SQL Generation
    ↓
Database Query → Results → Deduplication/Grouping → Display
    ↓
Tree/Accordion Component → Expand/Collapse Events → State Update
```

### Key NiceGUI Components

**Query Input:**
```python
query_input = ui.input(
    label='Natural language query',
    placeholder='What did Dan ask me to do?',
    on_change=lambda e: handle_query(e.value)
).classes('w-full')
```

**Results Tree:**
```python
tree = ui.tree(
    grouped_results,
    label_key='canonical_task',
    on_select=handle_expand
).classes('w-full')
```

**Or Accordion (alternative):**
```python
for group in grouped_results:
    with ui.expansion(f"⚠ {group['canonical_task']} ({group['count']}x)"):
        for item in group['instances']:
            ui.label(f"• {item['date']} - {item['context']}")
```

---

## Implementation Plan

### Phase 1: Foundation (Days 1-2)

**Goal:** Working prototype with mock data

**Tasks:**
1. Set up NiceGUI environment
   - Install: `pip install nicegui`
   - Create `src/slack_insights/gui/app.py`
   - Basic "Hello World" NiceGUI app

2. Create main layout
   - Header with app title
   - Query input field
   - Results placeholder
   - Footer (optional)

3. Mock data display
   - Hard-coded grouped results
   - Tree or accordion component
   - Test expand/collapse behavior

**Acceptance Criteria:**
- [ ] NiceGUI app launches at `http://localhost:8080`
- [ ] Query input field visible and functional
- [ ] Mock results display with expand/collapse
- [ ] No errors in console

**Estimated Time:** 8-16 hours

---

### Phase 2: Backend Integration (Day 3)

**Goal:** Real queries returning actual Slack data

**Tasks:**
1. Connect query input to backend
   - Import existing `extractor.py` logic
   - Parse natural language with Claude
   - Generate SQL query

2. Execute database queries
   - Use `database.py` for SQLite access
   - Fetch action items matching query
   - Apply deduplication from `deduplication.py`

3. Dynamic results display
   - Populate tree/accordion with real data
   - Format dates, statuses, context
   - Handle "no results found"

4. Error handling
   - Show loading state during query
   - Display errors gracefully
   - Timeout handling (>5 seconds)

**Acceptance Criteria:**
- [ ] Typing a query triggers Claude API call
- [ ] Real action items display from database
- [ ] Grouping works (shows frequency)
- [ ] Expand shows all instances with context
- [ ] Loading state visible during processing
- [ ] Error messages appear when query fails

**Estimated Time:** 6-10 hours

---

### Phase 3: Visual Polish (Days 4-5)

**Goal:** Production-ready professional appearance

**Tasks:**
1. Visual hierarchy
   - Add status icons (⏳ ✅ ❓)
   - Color code by status (yellow, green, gray)
   - Badge for frequency ("4x")
   - Date formatting (relative or absolute)

2. Styling improvements
   - Apply Quasar theme or custom CSS
   - Consistent spacing and alignment
   - Hover effects on interactive elements
   - Smooth animations for expand/collapse

3. UX refinements
   - Query history (last 10 queries)
   - Clear button for input
   - Keyboard shortcut hints
   - Responsive layout (window resize)

4. Performance testing
   - Test with 100+ results
   - Ensure smooth scrolling
   - No lag during interactions
   - Optimize if needed

**Acceptance Criteria:**
- [ ] Professional appearance (not prototype-y)
- [ ] Icons and colors consistent
- [ ] Smooth animations
- [ ] Query history works
- [ ] Handles 100+ results smoothly
- [ ] Keyboard shortcuts functional

**Estimated Time:** 12-20 hours

---

### Phase 4: Iteration & Enhancement (Week 2)

**Goal:** Production-ready based on real usage

**Tasks:**
1. Daily usage testing
   - Use tool for actual Slack queries
   - Note friction points
   - Collect feature requests

2. Bug fixes
   - Address issues discovered
   - Edge cases (empty queries, large results)
   - Error scenarios

3. Nice-to-have features (priority based on usage)
   - Export to markdown
   - Saved queries/bookmarks
   - Dark mode toggle
   - Advanced filters

4. Documentation
   - Usage guide in README
   - Screenshots of UI
   - Keyboard shortcuts reference

**Acceptance Criteria:**
- [ ] Tool used daily without major friction
- [ ] All critical bugs fixed
- [ ] At least 2 nice-to-have features implemented
- [ ] Documentation updated

**Estimated Time:** 20-30 hours

---

### Phase 5: Packaging (Optional, Week 3)

**Goal:** Desktop app for easier access

**Tasks:**
1. Desktop mode setup
   - Use NiceGUI's `native=True` mode
   - Configure PyWebView settings
   - Test window size/positioning

2. Build script
   - Create launcher script
   - Package with PyInstaller (optional)
   - macOS app bundle (optional)

3. Distribution
   - Installation instructions
   - One-click launch method
   - Update mechanism (if packaged)

**Acceptance Criteria:**
- [ ] App launches as desktop window
- [ ] No browser UI visible
- [ ] Quick launch (<3 seconds)
- [ ] Easy to install for others

**Estimated Time:** 8-12 hours

---

## Design Mockups

### Main Interface (Concept)

```
┌─────────────────────────────────────────────────────┐
│  🔍 Slack Insights                                  │
├─────────────────────────────────────────────────────┤
│  What did Dan ask me to do?          [Search]      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ▼ ⚠ Mentioned 4 times                             │
│    ⏳ Deploy new API endpoint                      │
│       From: itzaferg | 2025-10-06                  │
│       "We need to deploy the new API..."           │
│                                                     │
│  ► ⚠ Mentioned 3 times                             │
│    ✅ Provide PSD file                             │
│                                                     │
│  ► 📅 Last 7 days                                  │
│    ⏳ Update documentation                         │
│                                                     │
│  Found 6 unique tasks (20 total mentions)          │
└─────────────────────────────────────────────────────┘
```

### Expanded Group

```
▼ ⚠ Mentioned 4 times
  ⏳ Deploy new API endpoint - @itzaferg
  
  Instance 1 - 2025-10-07 12:22
  Status: open
  "We need to deploy the new API endpoint before EOD.
   Can you handle this?"
  
  Instance 2 - 2025-10-07 12:21
  Status: open
  "Just a reminder about the API endpoint deployment."
  
  Instance 3 - 2025-10-06 23:13
  Status: open
  "Did you get a chance to deploy the API?"
  
  Instance 4 - 2025-10-06 13:35
  Status: open
  "We really need that API deployed soon."
```

---

## Testing Strategy

### Unit Tests
- Query parsing logic
- Database query generation
- Deduplication algorithm
- Date formatting functions

### Integration Tests
- End-to-end query flow
- Database connectivity
- API error handling
- State management

### Manual Testing Checklist
- [ ] Launch app successfully
- [ ] Query input accepts text
- [ ] Results display for various queries
- [ ] Expand/collapse works smoothly
- [ ] Status icons display correctly
- [ ] Frequency counts accurate
- [ ] Query history persists
- [ ] Keyboard shortcuts work
- [ ] Performance with 100+ results
- [ ] Error messages appear correctly
- [ ] Dark mode toggle (if implemented)
- [ ] Export functionality (if implemented)

### Test Queries
1. "What did Dan ask me to do?"
2. "Show me urgent tasks"
3. "What's still open for TMA?"
4. "List completed items from last week"
5. "What does Dan want for AT&T?"

---

## Success Metrics

### Development Metrics
- [ ] MVP completed in Week 1 (5 days)
- [ ] Production-ready in Week 2 (10 days total)
- [ ] No critical bugs blocking daily use
- [ ] <10 dependencies added (only NiceGUI + essentials)

### User Experience Metrics
- [ ] App launches in <3 seconds
- [ ] Query response in <2 seconds for 100 results
- [ ] 0 friction points during daily use
- [ ] Can demo to stakeholders without embarrassment

### Technical Metrics
- [ ] Code coverage >80% for new modules
- [ ] No performance degradation vs terminal POC
- [ ] All existing tests still passing
- [ ] Clean git history with meaningful commits

---

## Risks & Mitigation

### Risk 1: NiceGUI Tree Component Limitations
**Probability:** Medium (30%)  
**Impact:** High  
**Description:** Tree widget may not support nested interactions we need

**Mitigation:**
- Build quick prototype (Day 1) to validate tree component
- Test with mock data before full integration
- Fallback: Use accordion/expansion panels instead of tree
- Ultimate fallback: Switch to Textual (2-3 days to rebuild)

### Risk 2: Performance with Large Result Sets
**Probability:** Low (15%)  
**Impact:** Medium  
**Description:** 100+ results might cause lag in browser

**Mitigation:**
- Implement pagination (show 20-50 at a time)
- Lazy loading for expanded groups
- Virtualization if needed (render only visible items)
- Test early with large datasets

### Risk 3: Claude API Cost/Latency
**Probability:** Low (10%)  
**Impact:** Low  
**Description:** Natural language parsing costs/delays

**Mitigation:**
- Cache common query patterns locally
- Show loading indicator during API call
- Allow manual SQL input as fallback
- Budget tracking for API costs

### Risk 4: Desktop Packaging Complexity
**Probability:** Medium (40%)  
**Impact:** Low (optional feature)  
**Description:** PyWebView/PyInstaller may have issues

**Mitigation:**
- Keep desktop packaging as optional Phase 5
- Web version (browser) is primary interface
- Document manual launch method as backup
- Don't block on packaging for v1.0

---

## Acceptance Criteria (Overall)

### MVP (End of Week 1)
- [ ] NiceGUI app launches locally
- [ ] Natural language query input functional
- [ ] Real Slack data displays from database
- [ ] Hierarchical grouping works
- [ ] Expand/collapse interactions smooth
- [ ] Basic visual hierarchy (icons, colors)

### Production-Ready (End of Week 2)
- [ ] Professional appearance
- [ ] All must-have features implemented
- [ ] Performance acceptable (tested with 100+ results)
- [ ] Error handling robust
- [ ] Documentation updated
- [ ] Tool used daily without friction

### Complete (End of Week 3, optional)
- [ ] Desktop app packaging working
- [ ] Nice-to-have features based on priorities
- [ ] Full test coverage
- [ ] Ready for team distribution

---

## Dependencies

### External Dependencies
- NiceGUI 1.4+ (`pip install nicegui`)
- Existing Python dependencies (anthropic, sqlite3, rich)
- PyWebView (optional, for desktop mode)

### Internal Dependencies
- Existing modules: `database.py`, `extractor.py`, `deduplication.py`
- User lookup system (already implemented)
- Thread context handling (already implemented)

### Blocked By
- None (all prerequisites complete)

### Blocks
- None (Phase 3 productionization can proceed)

---

## Future Enhancements (Post-MVP)

### Additional UI Features
- Multi-window support (multiple queries side-by-side)
- Customizable themes beyond dark/light
- Drag-to-reorder for manual prioritization
- Inline editing of status/notes

### Integration Features
- VS Code extension using same backend
- Textual CLI for terminal users
- Alfred/Raycast workflow
- API for external tools

### Data Features
- Import from multiple Slack workspaces
- Real-time sync with Slack (via webhooks)
- Team collaboration (shared queries/notes)
- Analytics dashboard (trends over time)

---

## Related Documents

- **Research:** `.agent-os/research/ui-options-2025-10/DECISION.md`
- **Comparison:** `.agent-os/research/ui-options-2025-10/comparison-analysis.md`
- **Terminal POC:** `poc_chat_terminal.py` (reference implementation)
- **GitHub Issue:** #3

---

## Approval

**Product Owner:** [User approval needed]  
**Technical Lead:** [Droid/AI assistance]  
**Timeline:** Start implementation immediately after approval  
**Budget:** No additional cost (using existing tools/APIs)

---

## Changelog

- **2025-10-08:** Initial spec created based on UI research
- **Status:** Awaiting approval to proceed with implementation
