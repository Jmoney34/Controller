# 02 — Architecture

How the whole thing fits together, in plain terms first, then the technical detail.

---

## The plain-terms version

Picture five parts working together:

1. **A small always-on cloud server** — the home base. It never sleeps, so automations run 24/7.
2. **A web app (the "cockpit")** — what you and your team open in a browser to chat with the AI and
   see dashboards.
3. **The AI brain** — Claude, invoked to understand requests, make decisions, and write content.
4. **Tool servers** — small programs that give the AI safe, specific abilities (read a contact, build
   a workflow, send a text, drive a browser). The AI calls these like a person uses apps.
5. **External services** — GoHighLevel (the CRM), a headless browser service (for things with no
   API), and a call-transcription service. Plus a local database that remembers everything.

You talk to the cockpit → the AI brain figures out what to do → it uses the tool servers → they call
GoHighLevel (or other platforms) → results come back and stream to your screen. Anything that changes
data waits for your confirmation first.

---

## Diagram

```
                         YOU / YOUR TEAM
                               |
                      (browser: the cockpit)
                               |
                         HTTPS via Caddy
                               |
          +--------------------------------------------+
          |   CLOUD SERVER (always on, small/cheap)    |
          |                                            |
          |   Web app (FastAPI)  --- SQLite database   |
          |        |                                   |
          |   AI brain (Claude, via CLI subprocess)    |
          |        |                                   |
          |   Tool servers (MCP):                      |
          |    - GHL tools (read/write CRM)            |
          |    - Browser bridge (headless Chrome)      |
          |    - Knowledge / accounting tools          |
          +--------------------------------------------+
              |              |                 |
        GoHighLevel    Browserbase         Gladia
        (CRM API)   (headless browser)  (call transcribe)
                          |
                  platforms with NO API
                  (e.g. course system)
```

---

## The stack (technical)

| Layer | Technology | Role |
|---|---|---|
| HTTP gateway | **Caddy** (auto HTTPS via Let's Encrypt) | Public entry point, TLS, reverse proxy |
| Web backend | **FastAPI + uvicorn** (Python 3.12) | The cockpit API + endpoints + background jobs |
| AI brain | **Claude**, invoked via the `claude` **CLI** as a subprocess | Reasoning, decisions, content generation |
| Tool layer | **MCP servers** (Model Context Protocol) | Give the AI concrete abilities (CRM, browser, etc.) |
| Browser automation | **Browserbase** + Playwright/Stagehand | Drive web UIs that have no API |
| Call intelligence | **Gladia** | Transcription, diarization, sentiment |
| Storage | **SQLite** | Chat history, queued writes, run logs, analyses |
| Process mgmt | **systemd** | Keeps the app running, restarts on failure |

---

## Key design choices (and why they matter)

### The AI runs as a CLI subprocess, not a raw API client
The brain is invoked by spawning the `claude` command-line tool, not by calling a billed API
directly. This lets the whole system run against a **flat-rate subscription** instead of metered
per-token API billing — a major cost difference at scale. The tool-use loop happens *inside* the CLI,
so the AI can chain many tool calls per request. (Details + the exact pattern in
`04-rebuild-guide.md`.)

### Tools are MCP servers, not hardcoded functions
Each capability area is a small "MCP server" exposing tools the AI can call. This keeps abilities
modular (add a new integration without touching the brain), and means the same tools work whether the
AI is reading a contact or building a workflow.

### Writes are queued, not fired blindly
Tools that change data don't execute immediately — they write a "pending change" to the database and
return an ID. A human approves it in the cockpit, then it runs. This is what makes letting an AI
operate your CRM safe.

### Browser automation for the "impossible" integrations
When a platform has no API (or hides behind Cloudflare), a headless real Chrome session driven by
Browserbase does what a person would: log in, click, fill forms — but programmatically. This is how
the system reaches outside GHL. (Full method in `05-beyond-ghl.md`.)

### Two token types for GHL
GHL exposes a stable **public API** (a long-lived token) for most operations, plus an **internal
admin API** (a short-lived session token) for deep workflow-structure editing. The system uses the
stable one by default and only reaches for the admin one when building/editing workflow internals.
(Both explained in `03-ghl-knowledge-base.md`.)

---

## What the server actually runs around the clock

- The **cockpit API** (answers the browser, streams AI responses).
- **Background pollers** (e.g. "check who activated and enroll them" every few minutes).
- **Scheduled jobs** (nightly database backup, periodic token refresh).
- **The database**, backed up automatically off-server.

This "always-on" property is the whole reason it's on a server and not a laptop app — see
`06-full-server-setup.md` for the full comparison and setup.

---

Next: **[03-ghl-knowledge-base.md](03-ghl-knowledge-base.md)** — the GHL API reference that took
months to compile.
