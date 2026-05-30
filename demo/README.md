# The Live Demo (read-only)

This proves the system is real by running against **your own** GoHighLevel account — and it's
**100% read-only**, so it's completely safe. It only reads data; it never creates, edits, deletes,
tags, messages, or moves anything.

## Run it in 60 seconds

```bash
cd demo
cp .env.example .env
# open .env and paste in your GHL_TOKEN and GHL_LOCATION_ID
pip install -r requirements.txt
python3 demo.py
```

## What you'll see

1. **Connection check** — confirms the AI can securely reach your account.
2. **Pipelines & stages** — your real sales process, exactly as you set it up.
3. **Recent real sales** — actual paid orders and a revenue total from your account.
4. **Contacts at a glance** — sample size, plus your most-used tags.
5. **A sample AI Contact Review** — picks a real contact and generates a "tier + summary," the same
   kind of review the full system writes onto every contact automatically.

If you have the **Claude CLI** installed locally, step 5 generates the review live. If not, it shows
a representative example so you still see the shape.

## Getting your two credentials

**GHL_TOKEN** — In GoHighLevel: **Settings > Private Integrations > Create new token**. For the demo,
read scopes are enough: *View Contacts, View Opportunities, View Payments, View Locations*.

**GHL_LOCATION_ID** — In GoHighLevel: **Settings > Business Profile**, or read it from your dashboard
URL: `https://app.gohighlevel.com/v2/location/`**`<THIS_IS_YOUR_LOCATION_ID>`**`/dashboard`.

## "Is it really safe?"

Yes. Every call in `demo.py` is a `GET` or a `/search` read. There is not a single create/update/
delete call in the file — you can read it top to bottom in a couple minutes. The loud "READ-ONLY"
banners are there on purpose.

## What it does NOT show (but the full system does)

The demo deliberately stays read-only. The full system also **writes and builds**: it constructs
entire automation workflows from a chat prompt, sends messages, moves deals, updates contacts, and
even automates platforms outside GHL. The demo ends with a tour of all of that — and the
[`../docs/`](../docs/) folder explains how to build it.
