"""Small shared helpers for the service classes."""


def same_text(first, second) -> bool:
    """Case-insensitive, whitespace-tolerant string comparison."""
    return str(first).strip().lower() == str(second).strip().lower()