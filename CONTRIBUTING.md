# Contributing to Controller

This is a **shared, open reference library** of AI-automation code, patterns, and project blueprints,
built so people (and their AI assistants) can learn from real working systems and add their own. This
guide is the standard every contribution follows. Keep the bar high; you're setting the example for
the next contributor.

---

## The one rule that matters most: never commit anything sensitive

This repo is public. Treat every file as if a stranger will read it tomorrow, because they will.

**Sanitization checklist, run it before every commit:**

- [ ] **No credentials.** No API keys, tokens (e.g. `pit-...`, `sk-...`, JWTs starting `eyJ...`),
      passwords, or private keys. Read them from environment variables / a local `.env` instead.
- [ ] **No real account identifiers.** No real GoHighLevel location/contact/workflow/funnel IDs, no
      DigitalOcean or cloud resource IDs. Use placeholders: `{LOC}`, `{TOKEN}`, `yourdomain.com`,
      `<your-contact-id>`.
- [ ] **No customer or personal data.** No real names, emails, phone numbers, addresses, call
      transcripts, or revenue figures. Invent neutral examples ("a coaching business", "a contractor").
- [ ] **No internal hostnames or IPs** beyond obvious placeholders (`127.0.0.1` for localhost is fine).
- [ ] **Provide a `.env.example`** with empty placeholder keys for anything your code reads from the
      environment, and make sure `.env` (and any `*auth*.json` / session-state files) is git-ignored.
- [ ] **Grep before you push:**
      ```bash
      git grep -nIE "pit-[a-f0-9]|sk-[A-Za-z0-9]|eyJ[A-Za-z0-9_-]{10,}|password|secret" 
      git grep -nI -iE "<your-name>|<your-company>|<a-real-client>"
      ```

The root [`.gitignore`](.gitignore) already blocks `.env`, `*auth*.json`, `*storage_state*.json`,
`.ghl_*`, and databases. Don't weaken it. If you find a leak in existing content, open an issue (or
flag it) rather than quietly force-pushing over history.

---

## House style

- **Code reads creds from the environment**, never hardcoded. Mirror the patterns in
  [`demo/demo.py`](demo/demo.py) and [`starter/`](starter/) (env vars + a small `.env` loader).
- **Read before write; confirm before firing.** Anything that changes data should default to a
  read-only or "queue then human-confirm" path, not fire directly. See the safe write pattern in
  [`docs/04-rebuild-guide.md`](docs/04-rebuild-guide.md) and the queue example in
  [`starter/mcp_server_skeleton.py`](starter/mcp_server_skeleton.py).
- **Fail loud, not silent.** Validate required env vars on startup; return a clear error on a bad HTTP
  response instead of crashing or silently no-op-ing.
- **No em dashes in user-facing copy** (docs, messages, generated content). Use commas, periods, or
  parentheses. This keeps generated copy from reading as obviously AI-written.
- **Be specific and cite evidence.** "Tested against a live location on 2026-05-30, got 422 without
  `triggersChanged:true`" beats "I think this works." No hedging.
- **Keep runnable code runnable.** If a file has imports, ship a `requirements.txt` (or list deps in
  its README) so a newcomer's `pip install -r requirements.txt` just works.

---

## The contribution workflow (fork → PR)

This is an open commons. Anyone (and any AI assistant) can contribute, and you don't need write
access. The flow is the standard open-source one, and a maintainer reviews every PR before it merges,
which is what keeps the library safe and consistent.

1. **Fork** this repo to your own GitHub account.
2. **Clone your fork** and create a branch: `git checkout -b add-my-thing`.
3. **Make your change** (a fix, or a new project under `projects/`, or a knowledge/endpoint addition).
4. **Run the sanitization checklist below** — this repo is public; a leaked key is forever.
5. **Commit and push to your fork**, then **open a Pull Request** against `Jmoney34/Controller`.
6. A maintainer reviews it against the sanitization + standards checklist (the PR template fills these
   in automatically) and merges. Then the next person, and the next person's Claude, builds on it.

> Working with an AI assistant? Point it at this file and the PR template. Both are written so it can
> self-certify the change is clean before a human ever looks at it.

## How to contribute

### Fix or improve existing content
Follow the fork → PR flow above. For docs, keep the voice and structure consistent with the
surrounding files. For code, include the dependency list and a one-line note on how you tested it.

### Add a new project
The flagship system lives in [`docs/`](docs/). Additional contributed projects live under
[`projects/`](projects/), one folder each. To add one:

1. Copy [`projects/TEMPLATE.md`](projects/TEMPLATE.md) to `projects/<your-project>/README.md` and fill
   it in.
2. Put any sanitized code alongside it in that folder, with a `.env.example` and a `requirements.txt`.
3. Add a one-line entry to [`projects/README.md`](projects/README.md).
4. Run the sanitization checklist above.

See [`projects/README.md`](projects/README.md) for the full structure.

### Extend the GHL API knowledge
The endpoint/gotcha reference in [`docs/03-ghl-knowledge-base.md`](docs/03-ghl-knowledge-base.md) is a
living document. There is also a companion knowledge base, **[`ghl-claude-knowledge`](https://github.com/Jmoney34/ghl-claude-knowledge)**,
where multiple AI agents contribute verified endpoints and gotchas in a structured way. Add new
endpoints/gotchas there (or via PR here), with evidence, following the same "be specific, cite
evidence, no hedging" tone.

---

## Anti-patterns

- ❌ Committing a real `.env`, token, ID, or customer record (run the checklist!)
- ❌ Code that fires writes to a live account without a confirmation step
- ❌ A runnable script with undeclared dependencies
- ❌ Marketing hype or unverifiable claims in docs, keep it credible and specific
- ❌ Overwriting someone else's work without discussion

By contributing you agree to keep this a welcoming, honest, secure space, see
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Thanks for helping this grow. Build the way you'd want the next person (or the next Claude) to build.
