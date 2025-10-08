# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-10-08

### Added
- Username resolution system with `user_lookup.py` module (#2)
  - Parses SlackDump user export files (TXT and JSON formats)
  - Global caching for performance
  - 100% coverage on 9,959 messages
- Thread context handling with `thread_context.py` module (#2)
  - Fetches up to 3 parent messages for thread replies
  - Preserves conversational flow
  - Inline formatting in transcripts
- Database migration system with version tracking (#2)
  - Migration `002_add_display_names.sql` adds display_name column
  - Automatic migration runner checks for applied versions
- Backfill script `backfill_display_names.py` for existing data (#2)
- Validation test script `validate_extraction_fixes.py` (#2)
- Comprehensive test suites:
  - `test_user_lookup.py` (10 tests)
  - `test_thread_context.py` (11 tests)
- Agent OS spec for extraction quality fixes (#2)
- Analysis documentation (START_HERE.md, ENHANCED_ANALYSIS_V2.md, COMPARISON_AND_RECOMMENDATIONS.md)

### Changed
- **Extractor improvements** (#2):
  - Compact transcript format (60% token savings)
  - Improved prompt with conversational examples
  - Recognizes casual language patterns ("Did you...?", "Can you...?")
  - Added confidence scoring (0.0-1.0)
  - Thread context integration
- **CLI analyze command** (#2):
  - Default batch size increased from 100 to 120 messages
  - Added `--overlap` flag (default: 30 messages)
  - Added `--newest-first/--oldest-first` flags (default: newest-first)
  - Sliding window batching prevents conversation breaks
- **Parser enhancements** (#2):
  - Username resolution during import
  - Display name support in message dicts
  - Better handling of missing user data
- **Database schema** (#2):
  - Added `display_name` column to conversations table
  - Added index on display_name for faster queries
  - Migration system tracks applied versions

### Fixed
- Extraction of 0 items from recent messages (now extracts 24 from last 7 days) (#2)
- Missing usernames in action items (now 100% resolved) (#2)
- Lost thread context in replies (#2)
- Missed conversational/casual requests (#2)
- Conversation flow breaks between batches (#2)

### Performance
- 60% token reduction with compact transcript format (#2)
- Improved context density with sliding window overlap (#2)
- Newest-first processing prioritizes recent, relevant messages (#2)

### Metrics
- **Before:** 0 action items from last 7 days, 1,307 total
- **After:** 24 action items from last 7 days, 1,720 total (+31.6%)
- All 21 tests passing for new modules

## [0.1.0] - 2025-10-07

### Added
- Initial release with Phase 1 features (#1)
- SlackDump JSON parser
- SQLite database with conversations and action_items tables
- Anthropic Claude API integration
- Action item extraction with batch processing
- CLI commands:
  - `import` - Import SlackDump JSON exports
  - `analyze` - Extract action items using Claude
  - `query-person` - Query items by person name
- Rich terminal output with progress bars and formatted tables
- Comprehensive test suite (66 tests, 95% coverage)
- Environment-based configuration with .env support
- Error handling and validation
- Database migrations
- Integration tests with mocked API calls

### Documentation
- README with installation and usage instructions
- Agent OS project structure
- Product roadmap
- Code style guidelines (tabs, type hints, docstrings)

[0.2.0]: https://github.com/carmandale/slack-insights/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/carmandale/slack-insights/releases/tag/v0.1.0
