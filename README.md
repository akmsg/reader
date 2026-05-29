# Reader - Gmail Bulk Reader CLI

Mark emails as read and archive them in bulk using the Gmail API.

## Setup

### 1. Create Google Cloud OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**: APIs & Services → Library → search "Gmail API" → Enable
4. Create credentials: APIs & Services → Credentials → Create Credentials → OAuth client ID
5. Configure consent screen if prompted:
   - User Type: External
   - Add scope: `https://www.googleapis.com/auth/gmail.modify`
   - Add your email as a test user
6. Application type: **Desktop app**
7. Download the JSON file

### 2. Place Credentials

```bash
mkdir -p ~/.config/reader
mv ~/Downloads/client_secret_*.json ~/.config/reader/credentials.json
```

### 3. Install

Clone the repository and install:

```bash
git clone https://github.com/akmsg/reader.git
cd reader
pip install -e .
```

### 4. First Run

```bash
reader --label promotions --dry-run
```

First run opens your browser for OAuth consent. Token is stored at `~/.config/reader/token.json` for subsequent runs.

## Usage

```
reader [OPTIONS]

Options:
  -l, --label TEXT           Gmail label to filter by (repeatable)
  -f, --from TEXT            Filter by sender email or name
  -a, --after TEXT           Only messages after date (YYYY/MM/DD)
  -b, --before TEXT          Only messages before date (YYYY/MM/DD)
  -s, --subject TEXT         Filter by subject keyword
  -q, --query TEXT           Raw Gmail search query
  -m, --max-results INT      Max messages to process
  --archive / --no-archive   Archive messages (default: yes)
  --mark-read / --no-mark-read  Mark as read (default: yes)
  --include-read             Include already-read messages
  -n, --dry-run              Preview without making changes
  --credentials PATH         Custom credentials.json path
  --token PATH               Custom token.json path
  --version                  Show version
  --help                     Show help
```

## Examples

```bash
# Archive all unread promotional emails
reader --label promotions

# Mark as read only (keep in inbox) emails from GitHub
reader --from notifications@github.com --no-archive

# Dry run to preview what matches
reader --label social --after 2024/06/01 --dry-run

# Process max 100 messages
reader --label updates --max-results 100

# Use raw Gmail search syntax
reader --query "from:noreply@medium.com older_than:30d"

# Process all emails (including read ones) in a label
reader --label newsletters --include-read
```

## License

This project is licensed under the [MIT License](LICENSE).
