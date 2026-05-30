# Starter Code

Sanitized, minimal building blocks to grow into the full system. No secrets — you supply your own
via environment variables or a local `.env` (git-ignored).

## Files

### `profile_review_example.py`
The core AI-intelligence pattern, standalone: read a GHL contact, ask Claude for a tier + summary,
print it. Write-back is included but intentionally disabled (wire it through the confirmation flow in
`../docs/04-rebuild-guide.md`).

```bash
export GHL_TOKEN=...  GHL_LOCATION_ID=...
python3 profile_review_example.py <contactId>
```
Uses the Claude CLI if installed (flat-rate billing); otherwise prints a representative example.

### `mcp_server_skeleton.py`
A minimal MCP tool server: a few read tools + one **write tool that queues for confirmation** instead
of firing. This is the safe foundation for letting an AI operate your CRM. Extend it with more tools
using the endpoints in `../docs/03-ghl-knowledge-base.md`.

```bash
pip install mcp requests
GHL_TOKEN=... GHL_LOCATION_ID=... python3 mcp_server_skeleton.py
```
Then register it with your AI assistant / MCP client.

## Where to go next

Follow `../docs/04-rebuild-guide.md` stage by stage. These two files cover Stage 2 (the AI brain) and
Stage 3-4 (tools + safe writes). The knowledge base (`../docs/03-ghl-knowledge-base.md`) has every
endpoint and gotcha you'll need to add the rest.
