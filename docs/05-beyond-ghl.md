# 05 — Beyond GoHighLevel: Automating Platforms With No API

The system isn't limited to GHL. The same AI + browser automation can drive almost **any** web
platform your business depends on — even ones with no API, or ones hidden behind bot protection like
Cloudflare. This is one of the most powerful (and rare) capabilities.

This doc explains the **method**, using a real worked example: auto-enrolling customers in a
third-party course/certification platform that has only a login form.

---

## The core idea

If a human can do it in a browser, the system can do it in a browser — programmatically. A headless
real Chrome session (via **Browserbase**) logs in, navigates, and submits forms exactly like a
person, so it sails past protections that block plain scripts.

Two modes:
1. **Discovery** — a human drives once while the system records every network call, so we learn the
   platform's internal endpoints.
2. **Automation** — the system replays those calls (with fresh tokens) from inside an authenticated
   browser session, hands-off.

---

## Step 1 — Discover the endpoints (capture once)

Open an interactive Browserbase session and have a person do the task once (e.g. create a user, enroll
them) while a network listener records every request: method, URL, headers, request body, response.

```js
// pseudo-pattern
context.on("response", async (resp) => {
  const req = resp.request();
  if (["xhr", "fetch"].includes(req.resourceType())) {
    record({ method: req.method(), url: req.url(),
             reqHeaders: req.headers(), reqBody: req.postData(),
             status: resp.status(), respBody: await resp.text() });
  }
});
```

From the recording you extract: the login call, the action calls (create/enroll/etc.), where the
**CSRF token** lives, and what a success vs failure response looks like. (Filter out analytics noise —
the real calls are usually on the platform's own domain.)

---

## Step 2 — Understand the auth model

Most non-API platforms use **session cookies + per-form CSRF tokens** (classic server-rendered apps).
There's no bearer token to grab — instead:

- Logging in sets a session cookie.
- Each form page embeds a fresh `csrfToken` you must scrape before submitting.

If the site is behind **Cloudflare**, plain HTTP requests get a `403` even with perfect headers —
which is exactly why you must run inside a **real browser** session. Real Chrome passes the challenge.

---

## Step 3 — Automate (replay from inside the browser)

The reliable pattern: do everything via same-origin `fetch()` **from within the authenticated page**,
so it inherits the session cookie and Cloudflare clearance:

```js
// inside page.evaluate, on the logged-in site:
const token = document.querySelector('input[name="csrfToken"]').value;
const res = await fetch("/some/action/endpoint", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ ...fields, csrfToken: token })
});
```

Log in by driving the real login form (seed a saved session if you have one), then run your action
calls.

---

## Worked example: cross-platform auto-enrollment

A business gives customers a free course on a separate platform (NASM/ClubConnect-style: a
Cloudflare-protected, server-rendered site). The goal: when someone signs up in GHL, get them into
the course automatically.

The catch: the platform **emails the user an activation link**, and you can't enroll them until they
activate. So the flow has an unavoidable wait — handled by polling.

**The pipeline:**
1. **GHL form submit** → trigger.
2. **Create the user** on the course platform (`POST /administrator/manage-users/create`, which sends
   the activation email).
3. **Text the customer** (via GHL): "check your email to finish setup; we'll add the course once
   you're set up."
4. **Track them** as "awaiting activation" in a small database table.
5. **Poll** the platform's user list on a schedule. Its status column reads `Pending` until they
   activate, then flips to `Active`.
6. **When Active** → look the user up, enroll them in the course, and **text the confirmation**.
   (The platform's "already enrolled" response gives you free idempotency — you can never
   double-enroll.)

Two platforms, two different auth models, an activation gate, and an async confirmation — fully
hands-off. That's the level of automation the browser layer unlocks.

---

## Critical lessons (browser automation)

- **Throttle logins.** Many platforms flood-protect login. In testing, ~13 rapid automated logins
  triggered a temporary lockout. In production, log in **once per poll cycle** (and reuse the session
  within the cycle), not once per action.
- **Cloudflare blocks raw HTTP** even with perfect headers — you must use a real browser.
- **CSRF tokens are per-page** — scrape a fresh one before each POST.
- **Verify by re-reading**, and prefer responses that are naturally idempotent ("already done") so
  retries are safe.
- **Release browser sessions** in a `finally` block so you don't leak them.
- For GHL's own admin token, the same browser-login technique is used to capture/refresh the
  short-lived session JWT on a schedule.

---

The technique generalizes: any platform your business logs into can, in principle, be automated this
way. Next: **[06-full-server-setup.md](06-full-server-setup.md)**.
