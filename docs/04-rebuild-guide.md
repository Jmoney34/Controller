# 04 — Rebuild Guide ("hand this to your AI assistant")

This is the build plan. You can follow it yourself, or paste it (plus `03-ghl-knowledge-base.md`)
to an AI coding assistant and have it scaffold the system with you.

The guide goes in stages, smallest-useful-thing first. You get value at the end of **every** stage,
so you can stop whenever it's "enough" for your business.

---

## Stage 0 — Prerequisites

- A GoHighLevel account + a **Private Integration Token** (read scopes to start) and your
  **Location ID**.
- Python 3.10+.
- An AI assistant you can call from code. Two options:
  - The **Claude CLI** (`claude`) — bills against a flat-rate subscription; what the reference system
    uses. Install it and log in once.
  - Or the Anthropic API with a key — simpler to start, billed per token.
- (Later stages) a small cloud server, a Browserbase account, a Gladia account.

> Validate Stage 0 by running the `../demo/demo.py` against your account. If it connects and lists
> your pipelines, your token + location are good.

---

## Stage 1 — Read-only API client

Build a tiny module that wraps GHL reads (contacts, pipelines, orders, conversations). The demo
(`../demo/`) already is this — start from it.

**Done when:** you can pull and print your pipelines, recent orders, and a contact list from code.

---

## Stage 2 — The AI brain (one call)

Add a function that sends a prompt to Claude and returns text. If using the CLI, the pattern is:

```python
import os, subprocess, json

def ask_claude(prompt, system=None, model="claude-sonnet-4-6"):
    # Strip ANTHROPIC_API_KEY so the CLI uses your subscription login, not metered API billing.
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", model]
    if system:
        cmd += ["--system-prompt", system]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    return json.loads(p.stdout)["result"]
```

**Done when:** you can feed a contact's data to `ask_claude` and get back a tier + summary. (See
`../starter/profile_review_example.py` for a working version.)

---

## Stage 3 — Tools the AI can call (MCP server)

Wrap your GHL functions as an **MCP server** so the AI can call them itself during a conversation,
instead of you hardcoding the sequence. Start with read tools, add writes later.

Use `../starter/mcp_server_skeleton.py` as your starting point. Register it with your AI assistant so
tools like `ghl_search_contacts`, `ghl_get_pipeline`, etc. are available in chat.

**Done when:** you can ask the AI "how many contacts have the tag X?" and it calls your tool and
answers — no hardcoded script.

---

## Stage 4 — Safe writes (the confirmation pattern)

Add write tools, but make them **queue** instead of fire:

1. A write tool inserts a row into a `pending_writes` table (operation + params + description) and
   returns a pending ID.
2. Your UI (or CLI) shows pending changes; you approve one.
3. On approval, a separate executor performs the actual GHL write.

This is what makes AI-operated writes safe. Start with one write (e.g. add a tag), prove the
round-trip, then add more (send message, move stage, update field).

**Reuse the gotchas in `03-ghl-knowledge-base.md`** — especially: tags via the additive endpoint, the
bulk pre-flight scan, and never empty trigger conditions.

**Done when:** you can say "tag this contact as VIP," approve it, and see the tag appear in GHL.

---

## Stage 5 — Building workflows from a prompt

This is the showpiece. Use the **admin token (Token B)** and the workflow endpoints + step shapes in
`03-ghl-knowledge-base.md`:

1. Create an empty workflow (`POST /workflow/{LOC}`).
2. Have the AI translate the user's request into a `templates` array (steps), using the step shapes.
3. Save it (`PUT .../auto-save`), attach triggers (`POST .../trigger` + `only-triggers` re-sync),
   publish (`change-status`).

Start with a simple 2-step flow (trigger + one SMS) and work up to branching. Mind the `parent`-field
and condition-operator gotchas — they're the two things that bite everyone.

**Done when:** "build a workflow that texts new leads instantly" produces a live, firing workflow.

---

## Stage 6 — Always-on (server + scheduled jobs)

Move it to a small cloud server and add background loops (pollers, scheduled jobs, webhooks). This is
when automations run without you. Full instructions: **[06-full-server-setup.md](06-full-server-setup.md)**.

**Done when:** a form submission triggers a flow with your laptop closed.

---

## Stage 7 — Beyond GHL (optional, powerful)

Add browser automation to reach platforms with no API. Method + worked example:
**[05-beyond-ghl.md](05-beyond-ghl.md)**.

---

## Suggested prompt to your AI assistant

> "I'm building an AI automation system for my GoHighLevel account. Here is the API knowledge base
> [paste `03-ghl-knowledge-base.md`] and the build plan [paste this file]. Start me at Stage 1: build
> a read-only Python client that pulls my pipelines, recent orders, and a contact sample. I'll give
> you my token and location ID via a .env file. Follow the gotchas in the knowledge base. Don't write
> any data — reads only — until I say so."

Then advance one stage at a time. Keep writes behind the confirmation pattern until you trust it.
