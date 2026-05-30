#!/usr/bin/env python3
"""
GHL AI Automation — LIVE READ-ONLY DEMO
=======================================

Proves the system is real by running against YOUR OWN GoHighLevel account.

  *** THIS SCRIPT IS 100% READ-ONLY. ***
  It only performs GET / search reads. It never creates, updates, deletes,
  tags, messages, or moves anything. Safe to run on a live production account.

What it shows you (against your real data):
  1. Connection + which account you're on
  2. Your pipelines and their stages
  3. Recent REAL sales / orders (revenue signal)
  4. Your contacts at a glance (counts + tag distribution)
  5. A sample AI "Contact Review" (tier + summary) — the kind the full system
     writes back onto every contact automatically

Then it shows you everything the FULL system does once write actions are on
(workflow buildouts, messaging, cross-platform automation, and more).

Setup:
  cp .env.example .env      # add your GHL token + location id
  pip install -r requirements.txt
  python3 demo.py

Get your credentials:
  - GHL_TOKEN: GHL > Settings > Private Integrations > create token with read
    scopes (contacts, opportunities, payments, locations).
  - GHL_LOCATION_ID: GHL > Settings > Business Profile (or your dashboard URL:
    .../v2/location/<THIS_IS_YOUR_LOCATION_ID>/...).
"""

import os
import sys
import json
import textwrap
from datetime import datetime

try:
    import requests
except ImportError:
    print("Missing dependency. Run:  pip install -r requirements.txt")
    sys.exit(1)

# ----------------------------------------------------------------------------- config
GHL_BASE = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"


# ----------------------------------------------------------------------------- pretty
class C:
    """Terminal colors (degrade gracefully if not a TTY)."""
    _on = sys.stdout.isatty()
    H = "\033[95m" if _on else ""     # header magenta
    B = "\033[94m" if _on else ""     # blue
    G = "\033[92m" if _on else ""     # green
    Y = "\033[93m" if _on else ""     # yellow
    R = "\033[91m" if _on else ""     # red
    BOLD = "\033[1m" if _on else ""
    DIM = "\033[2m" if _on else ""
    X = "\033[0m" if _on else ""      # reset


def banner(text):
    line = "=" * 74
    print(f"\n{C.H}{C.BOLD}{line}\n{text}\n{line}{C.X}")


def section(n, title, proves):
    print(f"\n{C.B}{C.BOLD}[{n}] {title}{C.X}")
    print(f"{C.DIM}    why this matters: {proves}{C.X}")


def ok(msg):
    print(f"    {C.G}+{C.X} {msg}")


def info(msg):
    print(f"      {msg}")


def warn(msg):
    print(f"    {C.Y}!{C.X} {msg}")


def err(msg):
    print(f"    {C.R}x{C.X} {msg}")


# ----------------------------------------------------------------------------- env
def load_env():
    """Load GHL_TOKEN + GHL_LOCATION_ID from .env (simple parser) or environment."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        for raw in open(env_path):
            raw = raw.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            k, v = raw.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    token = os.environ.get("GHL_TOKEN", "").strip()
    loc = os.environ.get("GHL_LOCATION_ID", "").strip()
    if not token or not loc:
        err("Missing credentials.")
        info("Copy .env.example to .env and fill in GHL_TOKEN and GHL_LOCATION_ID.")
        sys.exit(1)
    return token, loc


def hdrs(token):
    return {"Authorization": f"Bearer {token}", "Version": API_VERSION,
            "Content-Type": "application/json"}


def get(path, token, params=None):
    """Read-only GET with friendly error handling. Returns (ok, json_or_none)."""
    try:
        r = requests.get(f"{GHL_BASE}{path}", headers=hdrs(token), params=params, timeout=25)
    except Exception as e:
        return False, {"_error": f"network error: {e}"}
    if r.status_code == 401:
        return False, {"_error": "401 Unauthorized — check GHL_TOKEN and that it has read scopes."}
    if r.status_code == 404:
        return False, {"_error": "404 Not Found — check GHL_LOCATION_ID."}
    if r.status_code >= 300:
        return False, {"_error": f"HTTP {r.status_code}: {r.text[:160]}"}
    try:
        return True, r.json()
    except Exception:
        return False, {"_error": "non-JSON response"}


def post(path, token, body):
    """Read-only POST (used only for /search endpoints, which are reads)."""
    try:
        r = requests.post(f"{GHL_BASE}{path}", headers=hdrs(token), json=body, timeout=25)
    except Exception as e:
        return False, {"_error": f"network error: {e}"}
    if r.status_code >= 300:
        return False, {"_error": f"HTTP {r.status_code}: {r.text[:160]}"}
    try:
        return True, r.json()
    except Exception:
        return False, {"_error": "non-JSON response"}


# ----------------------------------------------------------------------------- demo steps
def step_connection(token, loc):
    section(1, "Connection check", "the AI can securely reach your GHL the moment you give it a key")
    good, data = get(f"/locations/{loc}", token)
    if not good:
        err(data.get("_error", "could not reach location"))
        info("Fix the credential issue above, then re-run. (The rest of the demo needs a connection.)")
        return None
    location = data.get("location", data) or {}
    name = location.get("name") or "(unnamed location)"
    ok(f"Connected to: {C.BOLD}{name}{C.X}")
    for label, key in [("Business", "business.name"), ("Timezone", "timezone"),
                       ("Country", "country")]:
        val = location
        for part in key.split("."):
            val = (val or {}).get(part) if isinstance(val, dict) else None
        if val:
            info(f"{label}: {val}")
    return name


def step_pipelines(token, loc):
    section(2, "Pipelines & stages", "the AI understands your exact sales process, not a generic template")
    good, data = get("/opportunities/pipelines", token, {"locationId": loc})
    if not good:
        warn(data.get("_error", "could not read pipelines"))
        return
    pipelines = data.get("pipelines", []) or []
    if not pipelines:
        info("No pipelines found on this location.")
        return
    ok(f"Found {len(pipelines)} pipeline(s):")
    for p in pipelines[:8]:
        stages = p.get("stages", []) or []
        stage_names = ", ".join(s.get("name", "?") for s in stages[:6])
        more = f" (+{len(stages) - 6} more)" if len(stages) > 6 else ""
        info(f"- {C.BOLD}{p.get('name','?')}{C.X}: {stage_names}{more}")
    info("")
    info(f"{C.DIM}The full system moves deals between these stages automatically based on"
         f" calls, replies, payments, and form fills.{C.X}")


def step_sales(token, loc):
    section(3, "Recent real sales", "the AI reports actual revenue automatically — no manual exporting")
    good, data = get("/payments/orders/", token,
                     {"altId": loc, "altType": "location", "limit": 10})
    if not good:
        warn(data.get("_error", "could not read orders"))
        info(f"{C.DIM}(Orders need the payments read scope. In the full build the AI reconciles"
             f" orders, invoices, and transactions.){C.X}")
        return
    orders = data.get("data", data.get("orders", [])) or []
    if not orders:
        info("No recent orders found (or none in scope).")
        return
    paid = [o for o in orders if str(o.get("paymentStatus", o.get("status", ""))).lower()
            in ("paid", "completed", "succeeded")]
    total = 0.0
    for o in paid:
        try:
            total += float(o.get("amount", 0) or 0)
        except Exception:
            pass
    ok(f"Pulled {len(orders)} recent order(s); {len(paid)} paid.")
    if total:
        info(f"Paid total in this sample: {C.G}{C.BOLD}${total:,.2f}{C.X}")
    for o in orders[:5]:
        nm = o.get("contactName") or (o.get("contact", {}) or {}).get("name") or "?"
        amt = o.get("amount", "?")
        st = o.get("paymentStatus", o.get("status", "?"))
        info(f"- {nm}: ${amt} [{st}]")


def step_contacts(token, loc):
    section(4, "Contacts at a glance", "the AI segments and understands your whole database instantly")
    good, data = post("/contacts/search", token,
                      {"locationId": loc, "pageLimit": 100})
    if not good:
        warn(data.get("_error", "could not search contacts"))
        return None
    contacts = data.get("contacts", []) or []
    total = data.get("total", len(contacts))
    ok(f"Sampled {len(contacts)} contact(s) (account total ~{total}).")
    # tag distribution
    tagcount = {}
    for c in contacts:
        for t in (c.get("tags") or []):
            tagcount[t] = tagcount.get(t, 0) + 1
    if tagcount:
        top = sorted(tagcount.items(), key=lambda x: -x[1])[:8]
        info("Top tags in this sample:")
        for t, n in top:
            bar = "#" * min(n, 30)
            info(f"  {t:<28} {C.B}{bar}{C.X} {n}")
    return contacts


def step_ai_review(token, loc, contacts):
    section(5, "Sample AI 'Contact Review'",
            "the AI reads a contact and writes a tier + summary — for EVERY contact, automatically")
    if not contacts:
        info("No contacts available to review.")
        return
    # pick the most data-rich contact in the sample
    contacts_sorted = sorted(
        contacts,
        key=lambda c: len((c.get("tags") or [])) + (1 if c.get("email") else 0)
        + (1 if c.get("phone") else 0),
        reverse=True,
    )
    c = contacts_sorted[0]
    cid = c.get("id")
    name = f"{c.get('firstName','')} {c.get('lastName','')}".strip() or "(no name)"
    info(f"Reviewing: {C.BOLD}{name}{C.X}")
    # pull richer detail (read-only)
    good, detail = get(f"/contacts/{cid}", token)
    contact = (detail.get("contact") if good else None) or c
    facts = []
    if contact.get("email"):
        facts.append(f"email: {contact['email']}")
    if contact.get("phone"):
        facts.append("has phone")
    if contact.get("tags"):
        facts.append(f"tags: {', '.join(contact['tags'][:6])}")
    if contact.get("dateAdded"):
        facts.append(f"added: {str(contact['dateAdded'])[:10]}")
    info(f"{C.DIM}Signals: {'; '.join(facts) or 'sparse profile'}{C.X}")

    review = generate_ai_review(name, contact)
    print()
    for line in review.splitlines():
        print(f"      {C.G}|{C.X} {line}")
    print()
    info(f"{C.DIM}In the full system this tier + summary is written back onto the contact's"
         f" custom fields, so your team sees it right inside GHL.{C.X}")


def generate_ai_review(name, contact):
    """Use the local `claude` CLI if present; otherwise show a representative example."""
    import shutil
    import subprocess
    prompt = (
        "You are a sales-ops analyst. Based ONLY on the contact data below, output a SHORT review:\n"
        "Line 1: 'Tier: <Hot|Warm|Cold|Champion>'\n"
        "Line 2-4: a 2-3 sentence summary of who they are and the recommended next action.\n"
        "Be concise and concrete.\n\n"
        f"CONTACT: {name}\n"
        f"DATA: {json.dumps({k: contact.get(k) for k in ('tags','email','phone','dateAdded','source')}, default=str)}\n"
    )
    if shutil.which("claude"):
        try:
            env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
            p = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text"],
                env=env, capture_output=True, text=True, timeout=90,
            )
            out = (p.stdout or "").strip()
            if out:
                return out + "\n\n(generated live by your local Claude CLI)"
        except Exception:
            pass
    # Fallback: representative example so the demo always shows the shape
    tags = contact.get("tags") or []
    tier = "Warm" if tags else "Cold"
    return textwrap.dedent(f"""\
        Tier: {tier}
        {name} is in your database{' with tags ' + ', '.join(tags[:3]) if tags else ' with a sparse profile'}.
        {'They show engagement signals worth a personal follow-up.' if tags else 'Enrich the profile and run a re-engagement touch.'}
        Recommended next action: a personalized message referencing their last interaction.

        (example output — install the Claude CLI to generate this live for real contacts)""")


def closing():
    banner("THAT WAS READ-ONLY. HERE'S WHAT IT DOES WHEN WRITES ARE ON.")
    items = [
        ("Builds entire GHL workflows from a chat prompt",
         "Say 'build a 5-step new-lead nurture with SMS + email + a wait + a tag' and it constructs "
         "the triggers, if/else branches, messages, waits, and publishes it live."),
        ("Spins up MULTIPLE automations in one session",
         "A nurture sequence, a post-purchase onboarding flow, and a win-back campaign — built in "
         "parallel, each with the correct triggers and safety conditions."),
        ("Sends messages for you (safely)",
         "SMS / email to contacts, from the right team member's number, with built-in duplicate "
         "protection so nobody ever gets double-texted."),
        ("Moves deals + updates contacts automatically",
         "Advances pipeline stages, updates custom fields, adds/removes tags — driven by calls, "
         "replies, payments, and form fills."),
        ("AI contact intelligence at scale",
         "Scores and summarizes every contact (the review you just saw), written back into GHL, plus "
         "call-recording sentiment analysis for coaching your sales reps."),
        ("Reaches OUTSIDE GHL",
         "Automates other platforms that have NO API at all (e.g. a course system behind Cloudflare): "
         "creates the user, waits for activation, enrolls them, and texts the confirmation — fully "
         "hands-off across two systems."),
        ("Runs 24/7 on a small server",
         "Always-on pollers, scheduled jobs, webhooks, and a chat 'cockpit' your whole team uses. "
         "Costs less than a typical SaaS subscription."),
    ]
    for title, body in items:
        print(f"\n  {C.G}{C.BOLD}* {title}{C.X}")
        for line in textwrap.wrap(body, 70):
            print(f"      {line}")
    print(f"\n{C.BOLD}  Next steps:{C.X}")
    print("   - docs/01-what-it-can-do.md   full capability tour + business use cases")
    print("   - docs/04-rebuild-guide.md    hand it to your AI assistant and build your own")
    print("   - docs/06-full-server-setup.md stand up the always-on server we run")
    print(f"\n{C.DIM}  Everything above is real and running today on a startup budget.{C.X}\n")


# ----------------------------------------------------------------------------- main
def main():
    banner("GHL AI AUTOMATION  -  LIVE READ-ONLY DEMO\n"
           "Running against YOUR account. Reads only. Nothing is changed.")
    token, loc = load_env()
    print(f"{C.DIM}Started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
          f"location {loc[:6]}... | READ-ONLY mode{C.X}")

    name = step_connection(token, loc)
    if name is None:
        return
    step_pipelines(token, loc)
    step_sales(token, loc)
    contacts = step_contacts(token, loc)
    step_ai_review(token, loc, contacts)
    closing()


if __name__ == "__main__":
    main()
