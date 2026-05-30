# Controller — GHL AI Automation Reference Library

> A shared, open reference library of genuinely useful automation code, patterns, and project
> blueprints. The flagship reference: an **enterprise-grade AI automation system for
> GoHighLevel (GHL)** — built and running on a startup budget.

This repo is meant to grow into an **open library that Claude instances can reference and contribute
to**, so each one builds on the last instead of starting from scratch. It begins with one
battle-tested system (documented end to end so you could rebuild it) and is structured so anyone, and
any AI assistant, can add their own working projects, patterns, and hard-won knowledge over time.
Read it freely; contribute back via a pull request (see [CONTRIBUTING.md](CONTRIBUTING.md)).

> 👉 **New here? Start with [docs/00-start-here.md](docs/00-start-here.md)** for a 2-minute orientation
> and a reading path. Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md).
>
> 🤖 **Are you an AI assistant** reading this for someone? Read **[CLAUDE.md](CLAUDE.md)** first — it's
> your playbook for using this repo to build the system for your human, safely and at full capability.

---

## What's the flagship system?

An AI "chief of staff" that operates a GoHighLevel account (and beyond) the way a senior ops team
would — except it runs 24/7 on a small cloud server and you talk to it in plain English.

It can **read** everything in your GHL (contacts, pipelines, conversations, calls, payments,
calendars) **and write/build** across it: it constructs entire automation workflows from a single
chat prompt, sends messages, moves deals, scores and summarizes contacts with AI, analyzes call
recordings for sentiment, and even reaches **outside** GHL to automate other platforms that have no
API at all.

See **[docs/01-what-it-can-do.md](docs/01-what-it-can-do.md)** for the full capability tour with
real business use cases, and **[GHL-AI-Automation-Capabilities.pdf](GHL-AI-Automation-Capabilities.pdf)** for the
shareable overview.

---

## Quick start (60 seconds) — see it work on YOUR GHL

The `demo/` folder has a **read-only** script that proves this is real by running against your own
GoHighLevel account. It only *reads* — it never changes anything — so it's 100% safe to run.

```bash
cd demo
cp .env.example .env        # then put your GHL token + location ID in .env
pip install -r requirements.txt
python3 demo.py
```

You'll watch it connect to your account, list your pipelines, surface recent real sales, profile your
contacts, and generate a sample AI "contact review." Full instructions: **[demo/README.md](demo/README.md)**.

> The demo is read-only on purpose. The real system also **writes and builds** — see the capability
> docs for everything it does once write actions are turned on (workflow buildouts, messaging,
> cross-platform enrollment, and more).

---

## What's inside

| Path | What it is |
|---|---|
| **[CLAUDE.md](CLAUDE.md)** | Playbook for an AI assistant handed this repo — **AIs start here** |
| **[docs/00-start-here.md](docs/00-start-here.md)** | Orientation + reading path — **humans start here** |
| **[docs/01-what-it-can-do.md](docs/01-what-it-can-do.md)** | The full capability tour + business use cases (reads **and** writes/builds) |
| **[docs/02-architecture.md](docs/02-architecture.md)** | How the whole thing fits together (the stack) |
| **[docs/03-ghl-knowledge-base.md](docs/03-ghl-knowledge-base.md)** | The GHL API "bible": endpoints, auth, gotchas, step shapes |
| **[docs/04-rebuild-guide.md](docs/04-rebuild-guide.md)** | "Hand this to your AI assistant and build your own" |
| **[docs/05-beyond-ghl.md](docs/05-beyond-ghl.md)** | Automating platforms with **no API** (reverse-engineering method) |
| **[docs/06-full-server-setup.md](docs/06-full-server-setup.md)** | Stand up the always-on server stack we run, and why it beats a laptop app |
| **[docs/07-cookbook.md](docs/07-cookbook.md)** | Copy-paste recipes for the most common tasks |
| **[demo/](demo/)** | The read-only "see it on your account" demo |
| **[starter/](starter/)** | Sanitized starter code (MCP tool server skeleton, AI contact-review example) |
| **[projects/](projects/)** | Community-grown shelf of additional contributed projects |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | How to add a project or fix, and the sanitization standard everyone follows |

---

## Requirements to actually use it

- A **GoHighLevel** account + an API token (Private Integration Token) and your Location ID.
- Python 3.10+ for the demo and starter code.
- For the full system: a small cloud server, plus accounts for the AI model and (optionally)
  browser-automation and call-transcription services. All covered in the docs.

---

## A note on safety & secrets

Everything here is sanitized — no real credentials, customer data, or account IDs. You supply your
own via a local `.env` file (which is git-ignored). The demo is read-only. When you build the
write/build features, the recommended pattern (documented inside) routes every write through a
**human confirmation step** so nothing fires unintentionally. Contributing? Hold the same line — the
sanitization checklist is in **[CONTRIBUTING.md](CONTRIBUTING.md)**.

---

## License

MIT — use it, learn from it, build on it. See [LICENSE](LICENSE).
