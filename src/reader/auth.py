"""OAuth2 authentication for Gmail API."""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
DEFAULT_TOKEN_PATH = Path.home() / ".config" / "reader" / "token.json"
DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "reader" / "credentials.json"


def get_credentials(
    credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> Credentials:
    """Load or create OAuth2 credentials.

    On first run, opens a browser for the OAuth consent flow.
    Subsequent runs use the stored token, refreshing if expired.
    """
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found at {credentials_path}\n"
                "Download it from Google Cloud Console → APIs & Services → Credentials.\n"
                "See README.md for setup instructions."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

    # Save token for next run
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())

    return creds


def build_gmail_service(credentials: Credentials):
    """Build and return the Gmail API service resource."""
    return build("gmail", "v1", credentials=credentials)
