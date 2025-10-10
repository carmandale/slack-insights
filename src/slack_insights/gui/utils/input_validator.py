"""Input validation and rate limiting for NiceGUI queries.

Provides security validation for user-submitted natural language queries to prevent:
- API abuse (extremely long queries)
- Injection attempts (SQL keywords, special characters)
- Rate limit violations (excessive query frequency)
- Resource exhaustion attacks
"""

import re
from datetime import datetime, timedelta


# Configuration constants
MAX_QUERY_LENGTH = 500
MIN_QUERY_LENGTH = 5
QUERY_RATE_LIMIT = 10  # queries per minute
ALLOWED_CHARS_PATTERN = r'^[a-zA-Z0-9\s\?\!\.\,\-\'\"@#&/]+$'


class QueryRateLimiter:
	"""Track and enforce query rate limits per session.

	Prevents API abuse by limiting the number of queries a user can make
	within a time window.
	"""

	def __init__(self, max_calls: int = 10, period_seconds: int = 60):
		"""Initialize rate limiter.

		Args:
			max_calls: Maximum number of calls allowed per period
			period_seconds: Time window in seconds
		"""
		self.max_calls = max_calls
		self.period = period_seconds
		self.query_times: list[datetime] = []

	def check_limit(self) -> tuple[bool, str]:
		"""Check if next query is within rate limit.

		Returns:
			Tuple of (allowed, error_message)
			- allowed: True if within limit, False if exceeded
			- error_message: Empty if allowed, descriptive message if blocked
		"""
		now = datetime.now()
		cutoff = now - timedelta(seconds=self.period)

		# Remove old queries outside the time window
		self.query_times = [t for t in self.query_times if t > cutoff]

		if len(self.query_times) >= self.max_calls:
			# Calculate how long to wait
			oldest_query = min(self.query_times)
			wait_seconds = int((oldest_query - cutoff).total_seconds()) + 1
			return False, f"Rate limit exceeded. Please wait {wait_seconds} seconds before querying again."

		# Record this query
		self.query_times.append(now)
		return True, ""

	def reset(self) -> None:
		"""Reset rate limiter (clear all tracked queries)."""
		self.query_times.clear()


def validate_user_query(query: str) -> tuple[bool, str]:
	"""Validate user query before processing.

	Performs security validation to prevent:
	- Excessively long/short queries
	- Invalid characters (HTML, scripts, SQL)
	- SQL injection attempts

	Args:
		query: User's natural language query string

	Returns:
		Tuple of (is_valid, error_message)
		- is_valid: True if query passes validation
		- error_message: Empty if valid, descriptive message if invalid

	Examples:
		>>> validate_user_query("What did Dan ask me to do?")
		(True, "")
		>>> validate_user_query("x" * 1000)
		(False, "Query too long. Maximum 500 characters.")
	"""
	# Length validation
	if len(query) < MIN_QUERY_LENGTH:
		return False, f"Query too short. Minimum {MIN_QUERY_LENGTH} characters."

	if len(query) > MAX_QUERY_LENGTH:
		return False, f"Query too long. Maximum {MAX_QUERY_LENGTH} characters."

	# Character whitelist (prevent code injection attempts)
	if not re.match(ALLOWED_CHARS_PATTERN, query):
		return False, "Query contains invalid characters. Use only letters, numbers, and basic punctuation."

	# Reject obvious SQL injection keywords
	# These should never appear in natural language queries
	sql_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "--", "/*", "*/"]
	query_upper = query.upper()

	for keyword in sql_keywords:
		if keyword in query_upper:
			return False, "Query contains suspicious keywords. Please rephrase your question naturally."

	return True, ""
