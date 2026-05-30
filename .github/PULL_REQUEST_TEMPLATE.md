<!--
Thanks for contributing to the Controller commons! This template helps keep the library safe
and consistent. AI assistants opening this PR: fill every section and check every box honestly.
-->

## What this adds / changes

<!-- One or two sentences. If it's a new project, name it and what it does. -->

## Why

<!-- The problem it solves or the capability it adds. -->

## How it was tested

<!-- e.g. "Ran the demo against a test GHL location, read-only." / "Built the workflow on a
sandbox account and confirmed it published." If untested, say so. -->

---

## Sanitization checklist (required — this repo is public)

- [ ] **No credentials** — no API keys, tokens (`pit-…`, `sk-…`, JWTs), passwords, or private keys.
- [ ] **No real identifiers** — no real GHL location/contact/workflow IDs or cloud resource IDs; placeholders only (`{LOC}`, `{TOKEN}`, `yourdomain.com`).
- [ ] **No customer or personal data** — no real names, emails, phone numbers, transcripts, or revenue figures.
- [ ] **Credentials read from the environment** — anything secret comes from `.env` (git-ignored), with a `.env.example` of placeholders.
- [ ] **I ran a secret scan** — e.g. `git grep -nIE "pit-[a-f0-9]|sk-[A-Za-z0-9]|eyJ[A-Za-z0-9_-]{10,}|password|secret"` came back clean.
- [ ] **Runnable code ships its deps** — a `requirements.txt` (or documented deps) so it installs and runs.

## Standards checklist

- [ ] I read [CONTRIBUTING.md](../CONTRIBUTING.md) and followed the house style.
- [ ] Any data-changing action defaults to read-only or queue-then-human-confirm (no firing writes on a live account without confirmation).
- [ ] New project? It lives under `projects/<name>/` with a README from `projects/TEMPLATE.md`, and I added it to the `projects/README.md` index.
- [ ] No em dashes in user-facing copy; claims are specific and verifiable (no hype).
