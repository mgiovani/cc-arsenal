"""Tunables shared by more than one module. A check-specific ceiling lives next
to the check that uses it instead; see that module for its thresholds."""

MAX_BYTES_PER_FILE = 50 * 1024 * 1024
MAX_SKILL_FILES = 400
MEMORY_TOTAL_TOKENS_MED = 5_000
MEMORY_TOTAL_TOKENS_HIGH = 10_000
UNUSED_MIN_SESSIONS = 5
