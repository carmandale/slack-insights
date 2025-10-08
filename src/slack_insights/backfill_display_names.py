"""
Backfill script to update existing conversations with display names.

Run this after adding the display_name column to resolve user IDs.
"""

import os
import sys

from slack_insights.database import init_database
from slack_insights.user_lookup import load_user_map, resolve_user_id


def backfill_display_names(db_path: str = "slack_insights.db", users_file: str = "users-T1YNKSBL5.txt"):
	"""
	Backfill display_name column for all existing conversations.

	Args:
		db_path: Path to database file
		users_file: Path to users mapping file

	Returns:
		Tuple of (updated_count, total_count)
	"""
	# Load user map
	if not os.path.exists(users_file):
		raise FileNotFoundError(f"Users file not found: {users_file}")

	print(f"Loading user map from {users_file}...")
	user_map = load_user_map(users_file)
	print(f"Loaded {len(user_map)} users")

	# Connect to database
	conn = init_database(db_path)

	# Get all conversations
	cursor = conn.execute("SELECT id, user_id, display_name FROM conversations")
	conversations = cursor.fetchall()

	total_count = len(conversations)
	print(f"\nFound {total_count} conversations to process")

	# Update conversations with display names
	updated_count = 0
	skipped_count = 0

	for conv in conversations:
		conv_id = conv[0]
		user_id = conv[1]
		current_display_name = conv[2]

		# Skip if display_name already set
		if current_display_name:
			skipped_count += 1
			continue

		# Resolve user ID to display name
		display_name = resolve_user_id(user_id, user_map)

		# Only update if we found a mapping (not just returning user_id)
		if display_name != user_id:
			conn.execute(
				"UPDATE conversations SET display_name = ? WHERE id = ?",
				(display_name, conv_id),
			)
			updated_count += 1

	conn.commit()
	conn.close()

	print(f"\nBackfill complete:")
	print(f"  Updated: {updated_count}")
	print(f"  Skipped (already set): {skipped_count}")
	print(f"  Unmapped: {total_count - updated_count - skipped_count}")
	print(f"  Total: {total_count}")

	return updated_count, total_count


def main():
	"""CLI entry point for backfill script."""
	db_path = os.getenv("SLACK_INSIGHTS_DB", "slack_insights.db")
	users_file = os.getenv("SLACK_USERS_FILE", "users-T1YNKSBL5.txt")

	print("=" * 60)
	print("Backfill Display Names")
	print("=" * 60)
	print(f"Database: {db_path}")
	print(f"Users file: {users_file}")
	print()

	try:
		updated, total = backfill_display_names(db_path, users_file)

		# Calculate success rate
		success_rate = (updated / total * 100) if total > 0 else 0
		print(f"\nSuccess rate: {success_rate:.1f}%")

		if success_rate < 90:
			print("\n⚠️  Warning: Less than 90% of users were resolved")
			print("   Check that users file is up to date")
			sys.exit(1)
		else:
			print("\n✓ Backfill successful!")
			sys.exit(0)

	except Exception as e:
		print(f"\n✗ Error: {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
