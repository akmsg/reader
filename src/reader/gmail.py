"""Gmail API operations: list messages and batch modify."""

from __future__ import annotations

import time
from typing import Callable

from googleapiclient.errors import HttpError

BATCH_SIZE = 1000
MAX_RETRIES = 3


def _execute_with_retry(request):
    """Execute a Gmail API request with exponential backoff on 429/5xx."""
    for attempt in range(MAX_RETRIES):
        try:
            return request.execute()
        except HttpError as e:
            if e.resp.status in (429, 500, 503) and attempt < MAX_RETRIES - 1:
                wait = 2**attempt
                time.sleep(wait)
            else:
                raise


def list_message_ids(
    service,
    query: str,
    max_results: int | None = None,
) -> list[str]:
    """Fetch all message IDs matching the query, handling pagination.

    Args:
        service: Gmail API service resource.
        query: Gmail search query string.
        max_results: Optional cap on number of IDs to return.

    Returns:
        List of message ID strings.
    """
    message_ids: list[str] = []
    page_token: str | None = None

    while True:
        page_size = 500
        if max_results:
            page_size = min(500, max_results - len(message_ids))

        kwargs = {
            "userId": "me",
            "q": query,
            "maxResults": page_size,
            "fields": "messages(id),nextPageToken",
        }
        if page_token:
            kwargs["pageToken"] = page_token

        response = _execute_with_retry(service.users().messages().list(**kwargs))

        messages = response.get("messages", [])
        message_ids.extend(msg["id"] for msg in messages)

        if max_results and len(message_ids) >= max_results:
            message_ids = message_ids[:max_results]
            break

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return message_ids


def batch_modify_messages(
    service,
    message_ids: list[str],
    remove_labels: list[str],
    add_labels: list[str] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> int:
    """Modify messages in batches of up to 1000.

    Args:
        service: Gmail API service resource.
        message_ids: List of message IDs to modify.
        remove_labels: Labels to remove (e.g., ["UNREAD", "INBOX"]).
        add_labels: Labels to add (optional).
        progress_callback: Called with (processed_count, total_count) after each batch.

    Returns:
        Total number of messages modified.
    """
    total = len(message_ids)
    processed = 0

    for i in range(0, total, BATCH_SIZE):
        chunk = message_ids[i : i + BATCH_SIZE]

        body: dict = {
            "ids": chunk,
            "removeLabelIds": remove_labels,
        }
        if add_labels:
            body["addLabelIds"] = add_labels

        _execute_with_retry(
            service.users().messages().batchModify(userId="me", body=body)
        )

        processed += len(chunk)
        if progress_callback:
            progress_callback(processed, total)

    return processed
