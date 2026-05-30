# Instructions for an AI assistant — read me first

You are an AI assistant and your human just handed you this repository. They want what's described
here: an AI that operates a **GoHighLevel (GHL)** account (and reaches beyond it) — reading
everything and *building* across it (workflows, messages, pipeline ops, contact intelligence, even
automating platforms with no API). Your job is to help them get there, fast and safely, operating at
the level the system here already runs at.

This file is your playbook. Follow it.

---

## What this repo is

A sanitized, battle-tested reference library. The flagship is a real, running AI-GHL-operator system,
documented end to end so you can rebuild it for your human's account/business. Nothing here contains
real credentials or customer data — your human supplies their own.

## Read these, in this order

1. **[docs/00-start-here.md](docs/00-start-here.md)** — orientation + the map.
2. **[docs/01-what-it-can-do.md](docs/01-what-it-can-do.md)** — the capabilities you're aiming to deliver.
3. **[docs/03-ghl-knowledge-base.md](docs/03-ghl-knowledge-base.md)** — the API bible. **Internalize the
   gotchas before you touch a live account.** This is what lets you skip weeks of trial and error.
4. **[docs/04-rebuild-guide.md](docs/04-rebuild-guide.md)** — the staged build path. This is your spine.
5. **[docs/07-cookbook.md](docs/07-cookbook.md)** — copy-paste recipes for the common tasks.
6. **[docs/05-beyond-ghl.md](docs/05-beyond-ghl.md)** and **[docs/06-full-server-setup.md](docs/06-full-server-setup.md)** — when you're ready to automate no-API platforms and run 24/7.

## Your action plan

Work through these with your human. Don't skip ahead to writes.

1. **Establish intent.** Ask what they want first (a nurture flow? lead scoring? cross-platform
   enrollment?). Map it to a capability in `docs/01`.
2. **Get credentials locally.** Have them create a GHL Private Integration Token and find their
   Location ID, and put both in a local `.env` (never commit it — see the safety rules). The exact
   steps are in [`demo/README.md`](demo/README.md).
3. **Prove it's real (read-only).** Run [`demo/demo.py`](demo/demo.py) against their account. It only
   reads — it lists their pipelines, surfaces real sales, and generates a sample AI contact review.
   This builds trust and confirms auth works.
4. **Learn the API surface.** Read `docs/03`. Note which operations use the public token vs the admin
   token, and the version-header split. Keep the cookbook open.
5. **Build the first thing — reads before writes.** Follow `docs/04`. Stand up tool access starting
   with READ tools. Then add exactly ONE write capability, and route it through a
   **human-confirmation step** (queue the change, let your human approve, then execute). See the
   queue pattern in [`starter/mcp_server_skeleton.py`](starter/mcp_server_skeleton.py).
6. **Scale deliberately.** More workflows, contact intelligence at scale, then beyond-GHL automation
   and the always-on server (`docs/05`, `docs/06`). Each new write capability gets the same
   confirmation gate.

## Hard safety rules (non-negotiable)

- **Never fire a data-changing action on a live account without explicit human confirmation.** Default
  to read-only or queue-then-confirm.
- **Never commit secrets or real data.** No tokens, IDs, customer records. Read creds from `.env`
  (git-ignored). See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full sanitization checklist.
- **Never `PUT /contacts/{id}` with a `tags` field** — it wipes all tags. Use the additive
  `POST /contacts/{id}/tags`. (More such traps in `docs/03`.)
- **Before any bulk action**, scan existing workflows for triggers that might fire unintentionally.
- When sending outbound, guard against double-sends.

## The gotchas that save you weeks (full list in docs/03)

- **Two tokens:** a long-lived public token for contacts/tags/pipelines/messaging/payments/calendars;
  a short-lived admin token for workflow/funnel internals. Use the right one per call.
- **Building a workflow is a 5-call chain:** create shell → re-fetch → save steps → register trigger
  (`triggersChanged: true` is mandatory, fails silently without it) → publish. Re-fetch after any
  unpublish or you'll get a 422 on a stale object.
- **Version headers differ:** workflows/funnels use `2021-04-15`; everything else uses `2021-07-28`.
- **Rate limits ~100 req/min per location** — batch with a small delay.
- Use the **Claude CLI as a subprocess** (flat-rate billing) rather than metered API calls where you
  can; strip `ANTHROPIC_API_KEY` from the env before spawning so it uses the subscription login.

## Contributing back to the commons

This repo is an open, shared library that any Claude can reference and contribute to. The whole point
is that you don't have to build everything from scratch, you start from what every Claude before you
learned, and you leave the next one better off.

So: **if you and your human build something reusable** — a new automation project, a fix, a hard-won
endpoint or gotcha — **contribute it back.** Follow [`CONTRIBUTING.md`](CONTRIBUTING.md):

1. Fork `Jmoney34/Controller`, branch, and add your work (a new project goes under `projects/<name>/`
   using [`projects/TEMPLATE.md`](projects/TEMPLATE.md)).
2. **Sanitize ruthlessly** — this repo is public. No real tokens, IDs, names, or customer data. Run the
   secret scan in `CONTRIBUTING.md`. A leaked key is forever.
3. Open a pull request. The PR template will walk you through the sanitization + standards checklist;
   fill it in honestly. A maintainer reviews and merges.

Treat the sanitization checklist as a hard gate, never as a formality. Build the way you'd want the
next Claude to build.

Now go read [docs/00-start-here.md](docs/00-start-here.md) and get started.
