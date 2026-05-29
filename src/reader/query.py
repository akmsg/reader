"""Build Gmail search queries from structured filter parameters."""

from __future__ import annotations


def build_query(
    labels: list[str] | None = None,
    sender: str | None = None,
    before: str | None = None,
    after: str | None = None,
    subject: str | None = None,
    query: str | None = None,
    unread_only: bool = True,
) -> str:
    """Build a Gmail search query string from filter parameters.

    Examples:
        >>> build_query(labels=["promotions"], unread_only=True)
        'is:unread label:promotions'
        >>> build_query(sender="noreply@github.com", after="2024/01/01")
        'is:unread from:noreply@github.com after:2024/01/01'
    """
    parts: list[str] = []

    if unread_only:
        parts.append("is:unread")

    if labels:
        for label in labels:
            parts.append(f"label:{label}")

    if sender:
        parts.append(f"from:{sender}")

    if after:
        parts.append(f"after:{after}")

    if before:
        parts.append(f"before:{before}")

    if subject:
        parts.append(f"subject:({subject})")

    if query:
        parts.append(query)

    return " ".join(parts)
