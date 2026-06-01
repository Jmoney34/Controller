# 08 — AI Social Content Engine (approval-gated)

A pattern for an AI agent that **plans, generates, and schedules on-brand social posts
into GoHighLevel's Social Planner — behind a human approval gate.** Nothing publishes
without a person approving it, twice. Built on top of the GHL pieces in
[03-ghl-knowledge-base.md](03-ghl-knowledge-base.md); pairs with the render/brand-asset
ideas in [07-cookbook.md](07-cookbook.md).

> Everything here is sanitized. `{LOC}` = your sub-account location id; `{APPROVER}` =
> the GHL user id who approves posts. No real keys, ids, or customer data. Read creds
> from the environment.

---

## The core unlock: GHL's `in_review` approval gate

Captured from the live Social Planner UI and verified on the **public API** (services
host + long-lived token — no expiring admin token needed):

```python
# POST /social-media-posting/{LOC}/posts   (services host, Bearer)
body = {
  "accountIds": account_ids,          # from GET /social-media-posting/{LOC}/accounts
  "userId": APPROVER,
  "summary": caption,
  "media": [{"url": cdn_url, "type": "image/png"}],   # multiple urls = carousel
  "scheduleDate": "2026-06-10T17:00:00.000Z",
  "status": "in_review",                              # ← the gate
  "postApprovalDetails": {"approver": APPROVER, "requesterNote": "..."},
  "type": "post",
  "instagramPostDetails": {"type": "post", "showOnFeed": True},
  "facebookPostDetails": {"type": "post"},
  "tags": [],
}
```

`status:"in_review"` + `postApprovalDetails.approver` puts the post in the approver's
**Social Planner approval queue**. It will not publish until a human approves it inside
GHL. Notes:
- The **public** body uses `accountIds` + `userId`. (The UI/backend variant uses `userIds`
  — different field. Capture-once beats guessing; see [05-beyond-ghl.md](05-beyond-ghl.md).)
- Per-platform different captions = create one post per platform (one `summary` each).
- List: `POST /posts/list` (string `limit`/`skip`). Delete: `DELETE /posts/{id}`.
- This is **URL-safe** with the media library: a file's CDN url is keyed on its storage uuid,
  not its folder, so moving/organizing assets never breaks a scheduled post.

**Two gates, by design:** (1) your own app queues the create behind a confirm step, then
(2) GHL holds it `in_review`. An AI never reaches the public feed unattended.

---

## Architecture (4 separable concerns)

```
 weekly cron ─► IDEA ENGINE ──► (human approves the plan)
                 │  Python balances the content-pillar mix + dedups recent topics;
                 │  the LLM only writes the creative hooks.
                 ▼
            ASSET RENDER ──► on-brand PNG (HTML→PNG templates; one place for brand tokens)
                 ▼
            CAPTION ENGINE ──► 2-3 variants, per platform
                 │  grounded in a curated DOMAIN-KNOWLEDGE reference + voice/clarity lint
                 ▼
            GATED POST ──► POST .../posts  status:"in_review"  (human approves in GHL)
                 ▼
            ENGAGEMENT TRIAGE ──► classify + draft replies to comments/DMs (human sends)
```

Keep these as separate modules. Each is independently testable, and the deterministic
parts (balancing, linting) stay out of the LLM so output is repeatable.

---

## 1. Idea engine — Python balances, the LLM only riffs

Don't let the model decide *what* to post; that drifts. Compute the plan deterministically,
then ask the model only for creative hooks against fixed slots.

```python
PILLAR_WEIGHTS = {"educational": 3, "community": 2, "motivation": 2, "career": 2, "fun": 2}

def plan_week(count, recent_pillars):
    rc, used, slots = Counter(recent_pillars[-8:]), Counter(), []
    for _ in range(count):
        best = max(PILLAR_WEIGHTS, key=lambda p: PILLAR_WEIGHTS[p] / (1 + rc[p] + used[p]*2))
        slots.append({"pillar": best, "template": rotate_template(best, used[best])})
        used[best] += 1
    return slots   # → feed slots + a "recent topics to avoid" list to the idea LLM
```

**Content pillars** are the backbone: a small set of post types (educational / community /
motivation / career / entertainment for an education brand) each mapped to a render template,
a copy framework, and a curated hashtag set. The mix is what builds a *brand*, not random posts.

## 2. Asset render — brand tokens in ONE place

Render PNGs from HTML templates (see cookbook Recipe). A shared `_doc()` wrapper injects the
palette/fonts/logo so every template is on-brand by construction; individual templates only
supply their content. A color or font change is then a one-line edit, not N copies.
(Gotcha: headless Chromium has no color-emoji font — use vector shapes/glyphs, not emoji, in renders.)

## 3. Caption engine — grounded, linted, multi-variant

Three things make AI captions not sound like AI:

**a) Domain-knowledge grounding.** For any content that teaches or makes claims, inject a
*curated reference file* into the prompt and instruct: "teach ONLY from this; if it's not here,
don't claim it." This keeps an education brand's posts accurate to its actual curriculum.
Generalizes to any niche: ground the model in your real domain canon, don't trust its training.

**b) Deterministic voice + clarity lint** (a hard backstop, not just prompt rules):

```python
def voice_lint(text):
    issues = []
    if "—" in text: issues.append("em dash (banned by brand voice)")
    for p in FLATTERY + HYPE:
        if p in text.lower(): issues.append(f"off-voice: {p}")
    rd = readability(text)                      # Flesch-Kincaid + sentence length
    if rd["avg_sentence_words"] > 18: issues.append("sentences too long; simplify")
    return {"ok": not issues, "issues": issues, "readability": rd}
```

Judge clarity on **sentence length**, not word length — domain terms are long but expected.
Aim for a ~5th-grade reading level on the prose (short sentences, plain words), keep the
technical term, then explain it simply. Simple is respect for the reader, not dumbing down.

**c) 2-3 variants per platform.** The model returns an array of `{caption, hashtags, alt_text,
first_comment}` per variant, tailored per channel. A human picks the best in the review UI
instead of rewriting from scratch. (GHL has no "variants" feature — this is yours; you just
send GHL the chosen one.)

## 4. Endpoints surface (drive it from your app)

```
GET  /api/social/accounts     list connected channels
POST /api/social/plan         balanced week of ideas (optionally saved to your calendar)
POST /api/social/captions     2-3 voice-linted caption variants for a pillar/topic
POST /api/social/render       render a template + upload to the media library → cdn url
POST /api/social/post         create the in_review post (the gated create)
GET  /api/social/queue        current planner posts (incl. awaiting approval)
POST /api/social/batch        fill a week end-to-end (sequential; LLM spawns are lock-serialized)
POST /api/social/triage       classify a comment/DM + draft a reply (human sends)
```

Persist each post as a row in your own planning/calendar store (status: idea → asset_ready →
in_review → published), so the calendar — not GHL — is your system of record + audit trail.

## 5. Engagement triage (comments + DMs)

GHL surfaces comments on Social-Planner-published posts (`POST
/social-media-posting/comments/{platform}/list`) and syncs DMs into Conversations. Route an
incoming message to the LLM to classify **sentiment + urgency + intent** and draft a reply in
brand voice — then **queue the reply for human approval** (never auto-send). Critical rule:
if a real fact is needed (a price, a deadline, eligibility) and the model doesn't have it,
it must escalate and ask, not invent. A time-sensitive question is exactly the contact you
can't afford to miss, so triage earns its keep on community-feel alone.

---

## Guardrails (non-negotiable for an outward-facing AI)

- **Never auto-publish.** Two gates: your app's confirm + GHL `in_review`. No code path sets
  `scheduled`/`published` directly.
- **Never invent facts.** Ground claims in a curated reference; pillars needing real data
  (a real winner, a real deadline) refuse to render without it.
- **Deterministic voice/clarity lint** on every caption, plus prompt rules.
- **One post per item.** Track a posted-id so nothing double-posts; the cron only *drafts*, never posts.
- **Capture undocumented endpoints from the real UI** rather than guessing field names.

---

Next → back to **[00-start-here.md](00-start-here.md)**, or the render/recipe patterns in
**[07-cookbook.md](07-cookbook.md)**.
