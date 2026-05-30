#!/usr/bin/env python3
"""
Standalone example: AI "Contact Review" (tier + summary) for a GHL contact.

Demonstrates the core intelligence pattern:
  1. Read a contact from GHL (read-only).
  2. Ask Claude to score + summarize it.
  3. (Optional, commented out) write the result back onto the contact.

It uses the Claude CLI as a subprocess so it bills against a flat-rate subscription
rather than metered API calls. Falls back to the API if you prefer (see note).

Usage:
  export GHL_TOKEN=...   GHL_LOCATION_ID=...
  python3 profile_review_example.py <contactId>
"""
import os
import sys
import json
import shutil
import subprocess

import requests

GHL_BASE = "https://services.leadconnectorhq.com"
VERSION = "2021-07-28"


def hdrs():
    token = os.environ.get("GHL_TOKEN", "")
    if not token:
        raise SystemExit("ERROR: set GHL_TOKEN first.")
    return {"Authorization": f"Bearer {token}",
            "Version": VERSION, "Content-Type": "application/json"}


def get_contact(contact_id):
    try:
        r = requests.get(f"{GHL_BASE}/contacts/{contact_id}", headers=hdrs(), timeout=25)
        r.raise_for_status()
    except requests.RequestException as e:
        detail = getattr(getattr(e, "response", None), "text", "") or str(e)
        raise SystemExit(f"ERROR fetching contact {contact_id}: {detail[:300]}")
    return r.json().get("contact", {})


def ask_claude(prompt):
    """Call the Claude CLI. Strips ANTHROPIC_API_KEY so it uses subscription login."""
    if not shutil.which("claude"):
        return None
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    p = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        env=env, capture_output=True, text=True, timeout=120,
    )
    try:
        return json.loads(p.stdout)["result"]
    except Exception:
        return (p.stdout or "").strip() or None


def review_contact(contact):
    name = f"{contact.get('firstName','')} {contact.get('lastName','')}".strip() or "(no name)"
    signals = {k: contact.get(k) for k in ("tags", "email", "phone", "dateAdded", "source")}
    prompt = (
        "You are a sales-ops analyst. Using ONLY the data below, return:\n"
        "Line 1: 'Tier: <Champion|Strong|Solid|Pass>'\n"
        "Then 2-3 sentences: who they are + the single best next action.\n\n"
        f"CONTACT: {name}\nDATA: {json.dumps(signals, default=str)}\n"
    )
    out = ask_claude(prompt)
    if out:
        return out
    # Fallback so the example always produces something
    tier = "Strong" if contact.get("tags") else "Solid"
    return (f"Tier: {tier}\n{name} is in your database. "
            f"Recommended next action: a personalized follow-up referencing their last interaction.\n"
            f"(install the Claude CLI to generate this live)")


def write_back(contact_id, tier, summary):
    """OPTIONAL write-back. INTENTIONALLY DISABLED in this example, by design, not a bug.

    This file demonstrates the READ + score side only. The commented code below is the
    template for the 'write' side: persist the AI's review onto custom fields so your team
    sees it inside GHL. To enable it, replace the field IDs with your own (look them up via
    GET /locations/{LOC}/customFields) and route the call through a human-confirmation step
    rather than firing directly (see docs/04-rebuild-guide.md for the safe write pattern).
    Leaving it raise-guarded keeps the example safe to run as-is.
    """
    raise NotImplementedError(
        "write_back() is an intentional safety template, not a bug. "
        "Enable it deliberately via your pending-write confirmation flow (see docs/04)."
    )
    # TIER_FIELD_ID = "<your custom field id>"
    # SUMMARY_FIELD_ID = "<your custom field id>"
    # body = {"customFields": [
    #     {"id": TIER_FIELD_ID, "value": tier},
    #     {"id": SUMMARY_FIELD_ID, "value": summary},
    # ]}
    # requests.put(f"{GHL_BASE}/contacts/{contact_id}", headers=hdrs(), json=body, timeout=25)


def main():
    if len(sys.argv) < 2:
        print("usage: python3 profile_review_example.py <contactId>")
        sys.exit(1)
    if not os.environ.get("GHL_TOKEN") or not os.environ.get("GHL_LOCATION_ID"):
        print("Set GHL_TOKEN and GHL_LOCATION_ID first.")
        sys.exit(1)
    contact = get_contact(sys.argv[1])
    review = review_contact(contact)
    print("\n=== AI CONTACT REVIEW ===\n")
    print(review)
    print("\n(To persist this onto the contact, see write_back() + docs/04-rebuild-guide.md)\n")


if __name__ == "__main__":
    main()
