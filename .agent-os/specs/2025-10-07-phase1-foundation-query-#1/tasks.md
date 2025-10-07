# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-10-07-phase1-foundation-query-#1/spec.md

> Created: 2025-10-07
> Status: Ready for Implementation
> GitHub Issue: #1

## Tasks

- [x] 1. Project Setup & Foundation
  - [x] 1.1 Create Python project structure with uv
  - [x] 1.2 Configure pyproject.toml with dependencies
  - [x] 1.3 Create requirements.txt with pinned versions
  - [x] 1.4 Set up .gitignore for Python (exclude .venv, .env, *.db, __pycache__)
  - [x] 1.5 Initialize src/slack_insights/ package structure
  - [x] 1.6 Configure pytest, ruff, and mypy
  - [x] 1.7 Verify virtual environment and dependencies install correctly

- [x] 2. Database Foundation
  - [x] 2.1 Write tests for database initialization (test_database.py)
  - [x] 2.2 Create database.py module with init_database()
  - [x] 2.3 Implement conversations table schema
  - [x] 2.4 Implement action_items table schema
  - [x] 2.5 Add indexes for query performance
  - [x] 2.6 Create migration script (migrations/001_initial_schema.sql)
  - [x] 2.7 Implement insert_conversation() with duplicate detection
  - [x] 2.8 Implement insert_action_item() with foreign key handling
  - [x] 2.9 Verify all database tests pass

- [x] 3. SlackDump JSON Parser
  - [x] 3.1 Write tests for parser (test_parser.py)
  - [x] 3.2 Create parser.py module
  - [x] 3.3 Implement parse_slackdump() to load JSON file
  - [x] 3.4 Implement parse_message() to extract fields
  - [x] 3.5 Handle threaded messages (thread_ts)
  - [x] 3.6 Handle missing optional fields gracefully
  - [x] 3.7 Add error handling for malformed JSON
  - [x] 3.8 Verify all parser tests pass

- [x] 4. Anthropic API Integration
  - [x] 4.1 Write tests for extractor with mocked API (test_extractor.py)
  - [x] 4.2 Create extractor.py module
  - [x] 4.3 Implement format_messages_for_claude()
  - [x] 4.4 Implement build_extraction_prompt()
  - [x] 4.5 Implement call_claude_with_retry() with exponential backoff
  - [x] 4.6 Implement parse_extraction_response() for JSON parsing
  - [x] 4.7 Implement extract_action_items() main function
  - [x] 4.8 Add error handling (auth, rate limit, server errors)
  - [x] 4.9 Verify all extractor tests pass

- [x] 5. CLI Import Command
  - [x] 5.1 Write tests for CLI import command (test_cli.py)
  - [x] 5.2 Create cli.py with typer app
  - [x] 5.3 Implement import command with file path argument
  - [x] 5.4 Add progress bar using rich.progress
  - [x] 5.5 Display summary statistics after import
  - [x] 5.6 Add error handling (file not found, invalid JSON)
  - [x] 5.7 Verify import command tests pass
  - [x] 5.8 Test import with dan-messages/D3Y7V95DX.json (9,960 messages)

- [ ] 6. CLI Analyze Command
  - [ ] 6.1 Write tests for analyze command (test_cli.py)
  - [ ] 6.2 Implement analyze command in cli.py
  - [ ] 6.3 Add batch processing logic (100 messages per batch)
  - [ ] 6.4 Display progress bar for analysis
  - [ ] 6.5 Store extracted action items in database
  - [ ] 6.6 Display summary (total items, open vs completed)
  - [ ] 6.7 Verify analyze command tests pass
  - [ ] 6.8 Test analyze with real Dan data

- [ ] 7. Query Engine & CLI Query Command
  - [ ] 7.1 Write tests for query engine (test_query_engine.py)
  - [ ] 7.2 Create query_engine.py module
  - [ ] 7.3 Implement query_by_person() with filters
  - [ ] 7.4 Add --status filter (open/completed)
  - [ ] 7.5 Add --recent filter (last 7 days)
  - [ ] 7.6 Implement format_results_as_table() using rich
  - [ ] 7.7 Implement query-person CLI command
  - [ ] 7.8 Verify all query tests pass
  - [ ] 7.9 Test query-person Dan with various filters

- [ ] 8. Integration & End-to-End Testing
  - [ ] 8.1 Write integration tests (test_integration.py)
  - [ ] 8.2 Test full workflow: import → analyze → query
  - [ ] 8.3 Test idempotency (re-importing same file)
  - [ ] 8.4 Verify test coverage >80% (pytest --cov)
  - [ ] 8.5 Fix any failing tests or coverage gaps
  - [ ] 8.6 Run full test suite and verify all pass

- [ ] 9. Documentation & Polish
  - [ ] 9.1 Create README.md with installation instructions
  - [ ] 9.2 Document CLI commands with examples
  - [ ] 9.3 Add troubleshooting guide
  - [ ] 9.4 Update .env.example with all required keys
  - [ ] 9.5 Add docstrings to all public functions
  - [ ] 9.6 Run ruff format and ruff check
  - [ ] 9.7 Verify code style and type hints

- [ ] 10. Phase 1 Validation
  - [ ] 10.1 Import Dan's full conversation history (9,960 messages)
  - [ ] 10.2 Run analysis and extract action items
  - [ ] 10.3 Compare results with Phase 0 validation (16 items found)
  - [ ] 10.4 Query Dan's action items with various filters
  - [ ] 10.5 Verify performance (<2 min import, <2s query)
  - [ ] 10.6 Document any issues or improvements needed
  - [ ] 10.7 Update roadmap status to Phase 1 Complete
