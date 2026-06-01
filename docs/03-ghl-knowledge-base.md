# 03 — GoHighLevel API Knowledge Base

> The reference that took months and a lot of trial-and-error to compile. Endpoints, the two-token
> auth model, payload shapes, and — most valuably — the **gotchas** that silently break things.
> Hand this to your AI assistant and it can operate GHL with confidence.

**Conventions in this doc:**
- `{LOC}` = your GHL Location ID. `{TOKEN}` = your API token.
- All IDs shown as `{...}` are placeholders — look up your own (see "Looking up your IDs" at the end).
- Hosts: `services.leadconnectorhq.com` (public API) and `backend.leadconnectorhq.com` (internal
  admin API).

---

## Part 1 — Authentication: two distinct token systems

GHL has **two** separate auth paths. Using the wrong one (or wrong `Version` header) is the #1 cause
of mysterious 401/422 errors.

### Token A — Public API (OAuth / Private Integration Token)
- **Host:** `services.leadconnectorhq.com`
- **Headers:** `Authorization: Bearer {TOKEN}` + `Version: 2021-07-28`
  - Exception: call recordings/transcripts use `Version: 2023-02-21`.
- **Lifetime:** long-lived (months). Create via GHL > Settings > Private Integrations.
- **Covers:** contacts, opportunities, conversations/messages, calendars, custom fields, tags,
  email templates, payments/orders, media library, users, locations.
- **Cannot do:** edit workflow internal structure, publish/unpublish workflows, some admin reporting.

### Token B — Internal Admin API (session "token-id" JWT)
- **Host:** `backend.leadconnectorhq.com`
- **Headers:**
  ```
  token-id:  {JWT}
  channel:   APP
  source:    WEB_USER
  version:   2021-07-28        (or 2021-04-15 for some reporting/calls endpoints)
  origin:    https://client-app-automation-workflows.leadconnectorhq.com
  referer:   https://client-app-automation-workflows.leadconnectorhq.com/
  ```
- **Lifetime:** ~1 hour. A 401/403 means it expired — refresh it (captured via an automated browser
  login; see `05-beyond-ghl.md` for the browser-auth pattern).
- **Covers:** workflow CRUD (create/edit steps, triggers, publish, archive), email campaign stats,
  per-user call activity, payments/invoices admin, notifications.
- **Hybrid note:** some `/reporting/calls/*` endpoints need **both** the `token-id` AND the
  `Authorization: Bearer` header together.

> Rule of thumb: use **Token A** for everything you can; only reach for **Token B** when building or
> editing the *internals* of workflows.

---

## Part 2 — Endpoint catalog (public API unless noted)

### Contacts
```
POST /contacts/search                       # search w/ filters + pagination
GET  /contacts/{contactId}                  # single contact
PUT  /contacts/{contactId}                  # update fields (NEVER include tags here — see gotcha)
POST /contacts/{contactId}/tags             # ADD tags (additive, safe)
DELETE /contacts/{contactId}/tags           # remove tags
GET/POST/DELETE /contacts/{contactId}/notes # notes
POST /contacts/search/duplicate             # find by email/phone
```
Search body:
```json
{ "locationId": "{LOC}", "pageLimit": 100,
  "filters": [{"field": "tags", "operator": "contains", "value": "your_tag"}],
  "searchAfter": "<cursor from the LAST contact of the previous page>" }
```
Filter operators: `contains`, `equals`, `exists`, `not_contains`, `gt`, `lt`.

### Opportunities & pipelines
```
GET /opportunities/pipelines?locationId={LOC}         # pipelines + their stages
GET /opportunities/search?location_id={LOC}&pipeline_id={PID}&status=open|won|lost|abandoned&limit=100&page=1
PUT /opportunities/{opportunityId}                    # body: {"pipelineStageId": "..."} or {"status": "won"}
```

### Conversations & messages
```
POST /conversations/search/v2     # inbox search (status/category/assignedTo filters)
GET  /conversations/{conversationId}/messages?limit=50&type=Email|SMS
POST /conversations/messages      # SEND a message (see body)
```
Send body:
```json
{ "type": "SMS|Email|WhatsApp", "contactId": "...",
  "message": "...",                      // SMS/WhatsApp
  "subject": "...", "html": "<p>...</p>", // Email
  "fromNumber": "+1..." }                // optional: send from a specific number
```

### Calls & recordings  (note the special Version)
```
GET /conversations/messages/{messageId}/locations/{LOC}/recording          # Version: 2023-02-21 -> audio
GET /conversations/locations/{LOC}/messages/{messageId}/transcription       # Version: 2023-02-21 -> utterances
POST /reporting/calls/get-all-phone-calls-new   # ADMIN host + both tokens; per-user call activity
POST /reporting/calls/get-call-status-summary   # ADMIN host; missed/answered summary
```

### Payments
```
GET /payments/orders/?altId={LOC}&altType=location&limit=20        # real sales (status=completed, paymentStatus=paid)
GET /payments/transactions/?altId={LOC}&altType=location           # granular events (may be partial/installment)
GET /invoices/dashboard?altId={LOC}&altType=location&currency=USD  # invoice totals
```

### Custom fields, values, tags
```
GET /locations/{LOC}/customFields                  # resolve field id <-> name
PUT /locations/{LOC}/customFields/{fieldId}        # body: {"options": [...]}  (NOT "picklistOptions")
GET /locations/{LOC}/customValues/                 # location-level variables
GET /locations/{LOC}/tags/search                   # tag catalog
```

### Media library
```
GET    /medias/files?altType=location&altId={LOC}&type=file   # list; type=file (NOT type=image — see gotcha)
GET    /medias/files?...&parentId={folderId}                  # list inside a folder (type=folder lists subfolders)
POST   /medias/upload-file?altType=location&altId={LOC}       # multipart; optional parentId form field to file it
POST   /medias/folder        {name, altType, altId, parentId?}   # create folder -> returns the folder incl. _id
POST   /medias/{id}          {name, altType, altId}              # RENAME a file/folder (see move gotcha below)
DELETE /medias/{id}?altType=location&altId={LOC}                 # delete a file or folder
```
You can **create, rename, upload, and delete** via the API — but you **cannot move/reparent an
existing file** through it (see gotcha 7). CDN URLs look like
`assets.cdn.filesafe.space/{LOC}/media/{file-uuid}.{ext}` and are keyed on the file's storage uuid
(not its catalog `_id`, not its folder), so a move never changes a file's URL.

### Calendars
```
GET    /calendars/events?locationId={LOC}&startTime={ms}&endTime={ms}
GET    /calendars/configuration/location/{LOC}
POST   /calendars/events/appointments
PUT    /calendars/events/appointments/{eventId}
DELETE /calendars/events/appointments/{eventId}
```

### Users
```
GET /users/search?locationId={LOC}
GET /users/{userId}        # a user's phone is in lcPhone[{LOC}]
```

### Email (admin host, Token B)
```
GET /emails/stats/location/{LOC}?startDate=...&endDate=...&timeZone=America/Chicago&topPerformingType=opened&fetchParams[]=hasCampaignStats&fetchParams[]=hasDailyStats&fetchParams[]=hasTopCampaigns
GET /emails/builder?locationId={LOC}&limit=20     # templates (public host)
```

### Workflows (admin host, Token B)
```
GET  /workflow/{LOC}/list?limit=50&offset=0
GET  /workflow/{LOC}/{workflowId}?includeScheduledPauseInfo=true
POST /workflow/{LOC}                              # create empty {name, parentId, type:"workflow"}
PUT  /workflow/{LOC}/{workflowId}/auto-save       # THE mutation endpoint (full workflow object)
PUT  /workflow/{LOC}/change-status/{workflowId}   # {status:"draft"|"published", updatedBy:"{userId}"}
PUT  /workflow/{LOC}/move-directory/{workflowId}  # archive: {parentId:"{folderId}"}
GET    /workflow/{LOC}/trigger?workflowId={wfId}
POST   /workflow/{LOC}/trigger
PUT    /workflow/{LOC}/trigger/{trigId}
DELETE /workflow/{LOC}/trigger/{trigId}?userId={userId}
PUT  /workflow/{LOC}/only-triggers/{wfId}         # re-sync triggers for "bucket-migrated" workflows
```

### Funnels / website pages
```
GET  /funnels/funnel/list?locationId={LOC}                          # Version 2021-07-28
GET  /funnels/builder/page/data?locationId={LOC}&pageId={PAGE}      # Version 2021-04-15 (read full page)
POST /funnels/builder/autosave/{PAGE}                               # Version 2021-04-15 (save DRAFT)
POST /funnels/funnel/create                                         # {locationId,name,type:"funnel"|"website"}
POST /funnels/funnel/{FUNNEL}/step                                  # add a page
```
> Page autosave writes the **draft** only; there is no confirmed public "publish page" API — publish
> still happens with a click in the GHL builder (or via browser automation).

---

## Part 3 — Workflow step shapes (for `auto-save`)

When editing a workflow via `auto-save`, `workflowData.templates` is the source of truth. Editable
`attributes` by step type:

| Step type | Key attributes |
|---|---|
| `sms` | `body`, `attachments` |
| `email` | `subject`, `preHeader`, `html`, `from_name`, `from_email` |
| `chatgpt` | `promptText`, `instructions`, `model`, `temperature` (string, e.g. `"0.7"`) |
| `update_contact_field` | `fields[].{field, value, title, type, date}` (`field` = custom-field ID) |
| `add_contact_tag` | `tags` (array) |
| `create_opportunity` | `pipeline_id`, `pipeline_stage_id`, `opportunity_name`, `monetary_value` |
| `assign_user` | `user_list`, `traffic_weightage` (round-robin) |
| `wait` | `startAfter.{type, value, when}` |
| `if_else` | `branches[].{name, segments[].conditions[]}` (parent `next` is an ARRAY) |
| `remove_from_workflow` | `workflow_id` (array of UUIDs) |
| `internal_notification` | `notification.{title, body, userType, redirectPage}` |
| `webhook` | `method`, `url`, `customData[]`, `headers[]` |

**Condition operators by field type:** single-select / radio fields use `==` with the exact value
string. Multi-select / checkbox fields use `index-of-true` / `add-index-of-true` with glob values
like `*(OPTION)*`. Mixing these up means the branch never matches (a real bug we hit — see gotchas).

**Critical `parent` field:** when inserting a step *inside* an if/else branch, set the step's
top-level `parent` to the branch-wrapper UUID. Miss it and downstream merge tokens
(`{{chatgpt.N...}}`, `{{custom_code.N...}}`) silently resolve to empty and the later email/SMS fails.

---

## Part 4 — Gotchas (the expensive lessons)

1. **Never put `tags` in a `PUT /contacts/{id}` body.** It REPLACES all tags, wiping pipeline tags.
   Use the dedicated `POST`/`DELETE .../tags` endpoints. (Shipped to production twice before learned.)

2. **Never create a workflow trigger with empty `conditions: []`.** Empty = wildcard, fires on ALL
   events of that type. One empty-condition trigger enrolled 170+ contacts unintentionally. Always
   set explicit conditions.

3. **Pre-flight before any bulk contact operation.** Before bulk-tagging/updating, scan all published
   workflow triggers for ones that would fire on your change. A mass tag can silently trigger mass
   emails.

4. **Single-select vs multi-select condition operators** (see Part 3). Using `index-of-true` + globs
   on a single-select radio field means the branch never matches and the contact silently falls
   through.

5. **Don't restructure a LIVE workflow's entry/root or add a rejoin/merge node.** It can stop the
   whole workflow from firing even though it validates. Drive dynamic behavior with a merge field +
   contact field instead, or build fresh and cut over.

6. **Verify trigger-fired workflows with a REAL UI action.** Setting a contact field via API PUT does
   NOT reliably fire `contact_changed` triggers the way clicking + saving in the UI does. Test with a
   genuine UI save.

7. **Media library: use `type=file`, not `type=image`.** Uploads are stored as `type=file`; querying
   `type=image` returns count 0 even in a folder full of PNGs. **And you cannot MOVE a file between
   folders via the API — it's UI-only.** The media library is Firestore-backed; reparenting is a
   Firestore write with no working REST endpoint. `POST /medias/{id}` renames fine but silently
   ignores `parentId` (returns `{"updated":true}`, nothing moves); the undocumented `POST /medias/move`
   returns `{"status":"Success"}` and no-ops; `bulk-update` 400s. None of the dest-field names, API
   versions, or hosts change this, and headless-browser automation can't move either (the app needs a
   Firebase token that cookie auth doesn't supply → `permission-denied`). Workaround: create folders
   via API, but have a human do the file moves in the UI (drag, or right-click → Move to folder).
   It's URL-safe — a move never changes a file's CDN URL (URLs are keyed on the file's storage uuid,
   not its folder), so any links pointing at moved files keep working.

8. **Email stats params are strict:** `timeZone` (camelCase), a valid `topPerformingType` enum, and
   all three `fetchParams[]` — or you get a misleading 422 "must be a string."

9. **`searchAfter` pagination cursor** lives on the LAST contact of the previous page, not the
   response root.

10. **Custom field options:** update with `options`, not `picklistOptions` (422 otherwise).

11. **Bucket-migrated workflows:** a `GET .../trigger` may return `[]` even when triggers exist, and a
    `POST` trigger may not "stick" until you also `PUT .../only-triggers/{wfId}` with the full
    workflow object. Also: `triggersChanged: true` is required in the trigger POST body, and the field
    is `workflowId` (camelCase) — `workflow_id` is silently ignored.

12. **Email HTML merge-token escaping:** GHL escapes HTML inside interpolated merge tokens. Have AI
    steps output plain-text paragraphs and wrap them in STATIC `<p>` tags in the email step's HTML.

13. **Call recording endpoint needs `Version: 2023-02-21`**, not `2021-07-28`.

---

## Part 5 — Looking up your own IDs

Everything tenant-specific is discoverable from the API:

| You need | How to get it |
|---|---|
| Location ID | GHL Settings > Business Profile, or your dashboard URL |
| Pipeline + stage IDs | `GET /opportunities/pipelines?locationId={LOC}` |
| Custom field IDs | `GET /locations/{LOC}/customFields` |
| User IDs (+ phone) | `GET /users/search?locationId={LOC}` then `GET /users/{id}` |
| Tag names | `GET /locations/{LOC}/tags/search` |
| Workflow IDs + folders | `GET /workflow/{LOC}/list` (admin) or `GET /workflows/?locationId={LOC}` |

Next: **[04-rebuild-guide.md](04-rebuild-guide.md)** — turn this knowledge into a working system.
