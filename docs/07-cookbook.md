# 07 — Cookbook (copy-paste recipes)

Quick, practical patterns for the things you'll do most. This is the fast-lookup companion to
**[03-ghl-knowledge-base.md](03-ghl-knowledge-base.md)** (the full endpoint reference) and
**[04-rebuild-guide.md](04-rebuild-guide.md)** (the staged build). Every snippet is sanitized: it
reads credentials from the environment and uses placeholders. Adapt, don't paste blindly.

```python
# Assumed setup for the snippets below
import os, asyncio, aiohttp, requests
GHL = "https://services.leadconnectorhq.com"
HDRS = {"Authorization": f"Bearer {os.environ['GHL_TOKEN']}",
        "Version": "2021-07-28", "Content-Type": "application/json"}
LOC = os.environ["GHL_LOCATION_ID"]
```

---

## Hard rules (memorize — these are production-burnt)

1. **Never `PUT /contacts/{id}` with a `tags` field** — it wipes all tags. Use `POST /contacts/{id}/tags` (additive).
2. **Auth split:** contacts / tags / pipelines / messaging / payments / calendars → public token. Workflows / funnels → admin token.
3. **Version header:** workflows + funnels = `2021-04-15`; everything else = `2021-07-28`.
4. **Workflow `triggersChanged: true` is mandatory** on the trigger call — it fails silently without it.
5. **Re-fetch a workflow after unpublishing** — the version bumps; a stale object gets a 422.
6. **Rate limits ~100 req/min per location** — batch with a small delay.
7. **Probe before you render** — never guess a custom-field name; pull a sample first.
8. **Route every write through human confirmation** on a live account.

---

## Recipe 1 — AI-personalized email per contact (batch)

Score/draft per contact in parallel, then send through the one sanctioned send path.

```python
async def send_personalized_batch(contact_ids, prompt_template):
    async with aiohttp.ClientSession(headers=HDRS) as s:
        async def one(cid):
            async with s.get(f"{GHL}/contacts/{cid}") as r:
                contact = (await r.json()).get("contact", {})
            draft = await claude_p(prompt_template.format(contact=contact))   # see CLI wrapper below
            await s.post(f"{GHL}/conversations/messages", json={
                "type": "Email", "contactId": cid,
                "fromName": "Your Rep", "fromEmail": "rep@yourdomain.com",
                "subject": parse_subject(draft), "html": parse_body(draft)})
        await asyncio.gather(*(one(c) for c in contact_ids))
```

`/conversations/messages` is the only sanctioned send path. `fromName` + `fromEmail` are required. A
200/201 means it sent. Guard against double-sends before calling this.

## Recipe 2 — Profile review (tier + summary, written back)

Ask Claude for a strict-format verdict, parse it, write it onto custom fields. Tiers used in this
library: **Champion / Strong / Solid / Pass**. (Full standalone version:
[`../starter/profile_review_example.py`](../starter/profile_review_example.py).)

```python
prompt = ("Using ONLY this data, reply EXACTLY:\n"
          "tier:: <Champion|Strong|Solid|Pass>\n"
          "summary:: <2 sentences + the single best next action>\n\n"
          f"CONTACT: {contact}")
out = await claude_p(prompt)
tier   = re.search(r"^\s*tier\s*::\s*(.+)$",    out, re.M | re.I).group(1).strip()
summary= re.search(r"^\s*summary\s*::\s*(.+)$", out, re.M | re.I).group(1).strip()
# Write back to custom fields (NEVER include `tags` in this body):
requests.put(f"{GHL}/contacts/{cid}", headers=HDRS, json={"customFields": [
    {"id": TIER_FIELD_ID, "value": tier}, {"id": SUMMARY_FIELD_ID, "value": summary}]})
# Mark it reviewed (additive, separate call):
requests.post(f"{GHL}/contacts/{cid}/tags", headers=HDRS, json={"tags": ["profile_reviewed"]})
```

## Recipe 3 — Bulk pipeline audit (find stuck deals)

```python
def audit_open_opps(pipeline_id):
    flags, page = [], 1
    while True:
        # NOTE: /opportunities/search is the one endpoint that uses snake_case params
        r = requests.get(f"{GHL}/opportunities/search", headers=HDRS, params={
            "location_id": LOC, "pipeline_id": pipeline_id, "status": "open",
            "limit": 100, "page": page}).json()
        for opp in r.get("opportunities", []):
            # flag: stale stage age, missing fields, no recent activity, etc.
            flags.append(opp)
        if not r.get("opportunities"):   # or follow meta.nextPageUrl
            break
        page += 1
    return flags   # surface in your UI; don't auto-act
```

## Recipe 4 — Tag-based audience segmentation

```python
def contacts_with_tag(tag, limit=100):
    body = {"locationId": LOC, "pageLimit": limit,
            "filters": [{"field": "tags", "operator": "contains", "value": tag}]}
    return requests.post(f"{GHL}/contacts/search", headers=HDRS, json=body).json()
    # paginate via the cursor in the response meta
```

## Recipe 5 — Build a workflow from a prompt (the 5-call chain)

This is the showpiece, and it uses the **admin token** (`docs/03`, Token B) on the backend host.
The order is exact:

```
1. POST /workflow/{LOC}                       create the shell        -> wfId
2. GET  /workflow/{LOC}/{wfId}                 re-fetch (get version)
3. PUT  /workflow/{LOC}/{wfId}/auto-save       save the steps (draft only)
4. POST /workflow/{LOC}/trigger                register trigger  (triggersChanged: true !!)
5. PUT  /workflow/{LOC}/change-status/{wfId}   publish
```

Skip or reorder a step, or reuse a stale object, and you get a cryptic 422. To build *many* at once,
run independent chains concurrently and track which succeeded so you can resume failures without
creating duplicates. Full step shapes are in `docs/03`.

## Recipe 6 — Let GHL itself call AI mid-workflow

Inject a `chatgpt` step into a workflow: its `promptText` is the prompt, its `outputField` is the
custom-field ID where the result lands. A downstream `if/else` step can then branch on that field's
value. Useful when the personalization should happen inside GHL's own automation rather than your
server.

## Recipe 7 — Cross-workflow audit before adding a step

Before adding a nurture/message step to workflow A, scan every *other* workflow's steps for the same
audience or topic so you don't double-message people. List the workflows, iterate their steps, grep
the message bodies. Cheap insurance against the most common automation embarrassment.

---

## The Claude CLI wrapper (flat-rate, not metered)

Spawn the Claude CLI as a subprocess so it bills against a flat-rate subscription. Strip
`ANTHROPIC_API_KEY` first so it uses the subscription login, not metered API billing.

```python
async def claude_p(prompt, model="claude-sonnet-4-6", timeout=120):
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    for attempt in range(1, 5):                      # retry transient CLI hiccups
        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt, "--model", model,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env)
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        text = out.decode("utf-8", "replace").strip()
        if text:
            return text
        await asyncio.sleep(3 * attempt)
    return None
```

Tips: parse strict outputs with anchored regex (`re.search(r"^\s*subject\s*::\s*(.+)$", text, re.M)`);
parallelize with an `asyncio.Semaphore(10)` to stay under CLI limits; for high-stakes outbound, run a
second `claude_p` call as a QA grader before sending.

---

Next → back to **[00-start-here.md](00-start-here.md)**, or build with **[04-rebuild-guide.md](04-rebuild-guide.md)**.
