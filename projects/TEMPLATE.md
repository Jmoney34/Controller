# <Project Name>

> One-sentence description of what this project does and who it's for.

## What it does

A short paragraph. What problem does it solve? What does it read, build, or automate? What's the
"jaw-drop" capability, if any?

## How it works

The approach in plain terms. Which platforms/APIs it touches, the key pattern (e.g. "polls a webhook,
enriches the contact, queues a write for human approval"), and anything non-obvious.

## Run it

```bash
cp .env.example .env        # fill in your own credentials
pip install -r requirements.txt
python3 main.py             # or whatever the entry point is
```

**Requirements:** (accounts/tokens needed, language/runtime versions, any external services.)

## Configuration

| Env var | What it is | Required |
|---|---|---|
| `GHL_TOKEN` | GoHighLevel Private Integration token | yes |
| `GHL_LOCATION_ID` | Your location ID | yes |
| ... | ... | ... |

## Safety notes

Is it read-only? If it writes, how is that gated (confirmation step, dry-run flag)? Call out anything
a user should know before pointing it at a live account.

## Status

`experimental` | `working` | `battle-tested`. Last updated: <date>. Contributed by: <name/handle>.
