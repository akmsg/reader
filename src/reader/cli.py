"""CLI entry point for the Gmail bulk reader."""

import sys
from pathlib import Path

import click
from googleapiclient.errors import HttpError

from reader import __version__
from reader.auth import (
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_TOKEN_PATH,
    build_gmail_service,
    get_credentials,
)
from reader.gmail import batch_modify_messages, list_message_ids
from reader.query import build_query


@click.command()
@click.option(
    "--label", "-l", multiple=True, help="Gmail label to filter by (repeatable)."
)
@click.option("--from", "-f", "sender", help="Filter by sender email or name.")
@click.option("--after", "-a", help="Only messages after this date (YYYY/MM/DD).")
@click.option("--before", "-b", help="Only messages before this date (YYYY/MM/DD).")
@click.option("--subject", "-s", help="Filter by subject keyword.")
@click.option(
    "--query", "-q", help="Raw Gmail search query (appended to other filters)."
)
@click.option(
    "--max-results", "-m", type=int, default=None, help="Max messages to process."
)
@click.option(
    "--archive/--no-archive", default=True, help="Remove from INBOX. Default: yes."
)
@click.option(
    "--mark-read/--no-mark-read", default=True, help="Mark as read. Default: yes."
)
@click.option(
    "--include-read", is_flag=True, default=False, help="Include already-read messages."
)
@click.option(
    "--dry-run", "-n", is_flag=True, default=False, help="Show what would be done."
)
@click.option(
    "--credentials",
    type=click.Path(exists=True),
    default=None,
    help="Path to credentials.json.",
)
@click.option("--token", type=click.Path(), default=None, help="Path to token.json.")
@click.version_option(version=__version__)
def main(
    label,
    sender,
    after,
    before,
    subject,
    query,
    max_results,
    archive,
    mark_read,
    include_read,
    dry_run,
    credentials,
    token,
):
    """Gmail Bulk Reader - Mark emails as read and archive them in bulk.

    Authenticates with Gmail via OAuth2 and processes messages matching
    your filters. Requires a credentials.json from Google Cloud Console.

    \b
    Examples:
      reader --label promotions
      reader --from notifications@github.com --before 2024/01/01 --no-archive
      reader --label social --after 2024/06/01 --dry-run
      reader --query "from:noreply@medium.com has:attachment"
    """
    if not archive and not mark_read:
        click.echo(
            "Error: Both --no-archive and --no-mark-read specified. Nothing to do.",
            err=True,
        )
        sys.exit(1)

    # Build search query
    gmail_query = build_query(
        labels=list(label) if label else None,
        sender=sender,
        before=before,
        after=after,
        subject=subject,
        query=query,
        unread_only=not include_read,
    )
    click.echo(f"Search query: {gmail_query}")

    # Authenticate
    try:
        click.echo("Authenticating...")
        creds = get_credentials(
            credentials_path=Path(credentials) if credentials else DEFAULT_CREDENTIALS_PATH,
            token_path=Path(token) if token else DEFAULT_TOKEN_PATH,
        )
        service = build_gmail_service(creds)
        click.echo("Authenticated successfully.")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # List matching messages
    try:
        click.echo("Fetching matching messages...")
        message_ids = list_message_ids(service, gmail_query, max_results=max_results)
    except HttpError as e:
        if e.resp.status == 400:
            click.echo(f"Invalid query: {gmail_query}", err=True)
            click.echo(f"API error: {e}", err=True)
        else:
            click.echo(f"Gmail API error: {e}", err=True)
        sys.exit(1)

    if not message_ids:
        click.echo("No messages matched your filters. Nothing to do.")
        sys.exit(0)

    click.echo(f"Found {len(message_ids)} message(s) matching filters.")

    # Dry run
    if dry_run:
        click.echo("[DRY RUN] Would process these messages. Exiting without changes.")
        sys.exit(0)

    # Determine labels to modify
    remove_labels = []
    if mark_read:
        remove_labels.append("UNREAD")
    if archive:
        remove_labels.append("INBOX")

    actions = []
    if mark_read:
        actions.append("marking as read")
    if archive:
        actions.append("archiving")
    click.echo(f"Processing: {' and '.join(actions)}...")

    # Execute
    try:

        def progress(processed, total):
            click.echo(f"  Processed {processed}/{total} messages...")

        count = batch_modify_messages(
            service, message_ids, remove_labels=remove_labels, progress_callback=progress
        )
        click.echo(f"Done. Successfully processed {count} message(s).")
    except HttpError as e:
        if e.resp.status == 429:
            click.echo(
                "Rate limited by Gmail API. Please wait and try again.", err=True
            )
        elif e.resp.status == 403:
            click.echo(
                "Insufficient permissions. Delete token.json and re-authenticate.",
                err=True,
            )
        else:
            click.echo(f"Gmail API error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user.", err=True)
        sys.exit(130)
