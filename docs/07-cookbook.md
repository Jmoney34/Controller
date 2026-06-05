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

## Recipe 8 — Media library: organize it end to end (create, move, rename)

Full CRUD over the media library is available via the API — create folders, move files into them,
rename, trash. The one non-obvious bit is the **move** endpoint: it's `/medias/move-files` with a
`targetParentId` + a `filesToBeMoved` array, **not** a `parentId` on the file. (`POST /medias/{id}`
*looks* like it should move — it accepts `parentId` — but it silently ignores it and only renames.
Use the dedicated endpoint.)

```python
def create_folder(name, parent_id=""):
    r = requests.post(f"{GHL}/medias/folder", headers=HDRS,
        json={"name": name, "parentId": parent_id, "altId": LOC, "altType": "location", "mode": "public"})
    return r.json().get("_id")                      # 201 -> new folder _id

def move_files(file_ids, target_parent_id=""):      # "" = move to root; batch-capable
    return requests.post(f"{GHL}/medias/move-files", headers=HDRS, json={
        "altId": LOC, "altType": "location", "targetParentId": target_parent_id,
        "filesToBeMoved": [{"_id": fid, "altId": LOC, "altType": "location"} for fid in file_ids]
    })                                              # 201 {"status":"Success"}; per-file {_id} is enough

def rename_media(media_id, new_name):               # files AND folders
    return requests.post(f"{GHL}/medias/{media_id}", headers=HDRS,
        json={"name": new_name, "altId": LOC, "altType": "location"})
```

So an AI *can* do a one-shot library cleanup: build the folder tree with `create_folder`, then
`move_files` everything into place. **Moves are URL-safe** — a file's CDN URL
(`assets.cdn.filesafe.space/{LOC}/media/{file-uuid}.{ext}`) is keyed on its storage uuid, not its
folder, so emails/pages/configs pointing at a moved file keep working with no reference fixups.

> Finding-the-endpoint note: the move call isn't in the public API docs. We found it by running an
> interactive browser session, doing one move by hand, and recording the network calls (the
> capture-once pattern in [05-beyond-ghl.md](05-beyond-ghl.md)). When an endpoint is undocumented,
> capture it from the real UI rather than guessing field names.

---

## Recipe 9 — Edit AND publish a landing/funnel page, 100% headlessly (no browser, no manual click)

The single highest-leverage page capability: change live page content (prices, CTA text, contract
links, copy) **and publish it** with zero browser session. The trick is `pageType: "live"` on the
autosave call — it publishes — and editing the **parsed** `pageData`, not its serialized string.

```python
# Page-builder lives on the admin host with the short-lived admin token-id JWT (not the public token).
# If your host hits Cloudflare error 1010 on Python's TLS, route these calls through a curl subprocess.
BACKEND = "https://backend.leadconnectorhq.com"
PB = {"token-id": os.environ["GHL_ADMIN_TOKEN_ID"], "channel": "APP",
      "source": "WEB_USER", "version": "2021-04-15", "Content-Type": "application/json"}

def get_page(page_id):                                  # READ also needs the page-builder origin
    r = requests.get(f"{BACKEND}/funnels/builder/page/data?pageId={page_id}",
                     headers={**PB, "origin": "https://page-builder.leadconnectorhq.com"})
    return r.json()                                     # full object: {funnelId, sections, settings, ...}

def walk_replace(node, rules):                          # edit the PARSED tree, never json.dumps(...)
    if isinstance(node, dict):  return {k: walk_replace(v, rules) for k, v in node.items()}
    if isinstance(node, list):  return [walk_replace(v, rules) for v in node]
    if isinstance(node, str):
        for r in rules:                                 # rule: {"find","replace", optional "anchor"}
            if r.get("anchor") and r["anchor"] not in node: continue
            node = node.replace(r["find"], r["replace"])
        return node
    return node

def autosave(page_id, page, funnel_id, page_type):      # page_type "draft" stages, "live" PUBLISHES
    return requests.post(f"{BACKEND}/funnels/builder/autosave/{page_id}", headers=PB,
        json={"funnelId": funnel_id, "pageData": page, "pageVersion": 1,
              "pageType": page_type, "integrations": {}})

page = get_page(PAGE)
edited = walk_replace(page, [{"find": "$799", "replace": "$699"}])
autosave(PAGE, edited, page["funnelId"], "draft")       # TWO-STEP: draft ...
autosave(PAGE, edited, page["funnelId"], "live")        # ... then live (a lone "live" sometimes won't stick)
```

Hard-won details:

- **Two-step publish.** Send `"draft"` then `"live"`. A single `"live"` autosave sometimes doesn't persist.
- **Edit the parsed structure.** Prices/links/copy live deep in `sections` (button + contract links sit
  in `faqList[].value[].text` HTML). Recursively replace string fields. Editing the `json.dumps` string
  fails — its quotes are escaped and won't match.
- **Make finds unique, or anchor them.** Dry-run count each `find` first. For a surgical link swap where
  the same contract id appears on several cards, add an `anchor` so you only rewrite the card that also
  contains a sibling marker (e.g. anchor on the CES contract id so a CPT card's identical id is spared).
- **Verify out-of-band.** The autosave response is a poor success signal — re-GET the page **and** curl the
  public URL with a cache-busting query param. The public render lags `pageData` ~10-15s (CDN), so re-check
  after a short wait rather than assuming the write failed.
- **Back up first.** Save the `get_page` result before editing; restore by autosaving it back.

This replaces browser automation for *all* page-content work. Browser sessions are now a true last
resort for pages.

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
