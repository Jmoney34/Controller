# 00 — Start Here

Welcome. This is the **Controller** reference library: a shared, sanitized collection of AI-automation
code, patterns, and project blueprints. The flagship is an AI "chief of staff" that operates a
GoHighLevel account (and reaches beyond it) the way a senior ops team would, running 24/7 on a small
server. Everything here is real and running; it's documented so you (and your AI assistant) could
rebuild it.

> **New here? Two-minute orientation, then pick a path below.**

---

## The fastest proof: run the demo (60 seconds)

The [`demo/`](../demo/) folder has a **read-only** script. Put your own GHL token + location ID in a
local `.env` and watch it connect to your account, list pipelines, surface real sales, and generate a
sample AI contact review. It only reads, so it's safe.

```bash
cd demo && cp .env.example .env   # add your token + location id
pip install -r requirements.txt && python3 demo.py
```

---

## Reading order

Read these in sequence for the full picture. Each ends with a "Next →" link.

| # | Doc | What you get | ~time |
|---|---|---|---|
| 01 | [What it can do](01-what-it-can-do.md) | The capability tour + real use cases (reads **and** builds) | 8 min |
| 02 | [Architecture](02-architecture.md) | How the pieces fit together (the stack) | 6 min |
| 03 | [GHL knowledge base](03-ghl-knowledge-base.md) | The API "bible": endpoints, two-token auth, step shapes, gotchas | 15 min |
| 04 | [Rebuild guide](04-rebuild-guide.md) | "Hand this to your AI assistant and build your own," stage by stage | 10 min |
| 05 | [Beyond GHL](05-beyond-ghl.md) | Automating platforms that have **no API** (the reverse-engineering method) | 8 min |
| 06 | [Full server setup](06-full-server-setup.md) | Stand up the always-on server, and why it beats a laptop app | 8 min |
| 07 | [Cookbook](07-cookbook.md) | Copy-paste recipes for the common tasks | reference |

---

## "I just want to…"

- **…see it work on my account** → [`demo/`](../demo/)
- **…understand what it can do** → [01](01-what-it-can-do.md)
- **…look up a specific GHL endpoint or gotcha** → [03](03-ghl-knowledge-base.md)
- **…have my AI assistant build this for me** → it should read [CLAUDE.md](../CLAUDE.md) first (its playbook), then [04](04-rebuild-guide.md) + [03](03-ghl-knowledge-base.md)
- **…grab a ready-made code recipe** → [07 — Cookbook](07-cookbook.md)
- **…automate a platform with no API** → [05](05-beyond-ghl.md)
- **…run it 24/7** → [06](06-full-server-setup.md)
- **…contribute a project or fix** → [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## A word on safety

Everything in this repo is sanitized: no real credentials, customer data, or account IDs. You supply
your own via a local `.env` (git-ignored). The demo is read-only. When you turn on the write/build
features, the recommended pattern routes every change through a **human confirmation step** so nothing
fires unintentionally. If you contribute, hold that same line, see [CONTRIBUTING.md](../CONTRIBUTING.md).

Next → **[01 — What it can do](01-what-it-can-do.md)**
