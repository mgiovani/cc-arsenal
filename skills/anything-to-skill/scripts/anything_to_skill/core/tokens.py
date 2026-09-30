def count(text: str) -> int:
    """Token estimate (chars/4): cheap, consistent, and good enough for budgeting."""
    return (len(text) + 3) // 4
