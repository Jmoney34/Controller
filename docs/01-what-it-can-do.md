# 01 — What It Can Do

> An AI "chief of staff" that runs your GoHighLevel account in plain English, 24/7 — reading
> everything, and **building and writing** across your whole stack. This is the capability tour.

The demo you can run (`../demo/`) is intentionally read-only. This document covers the **full**
system, including everything it does once write/build actions are turned on. That write side is the
part that makes people's jaws drop, so it's called out clearly throughout.

---

## The one-sentence version

You talk to it like a teammate ("build me a new-lead nurture sequence," "who in my pipeline went
cold this week," "enroll everyone who bought the course"), and it actually does the work inside GHL
and beyond — safely, with a confirmation step before anything changes.

---

## 1. Conversational control center ("the cockpit")

A chat interface backed by a real AI brain with your business context loaded in. You can:

- Ask questions about your data in plain English and get answers pulled live from GHL.
- Give instructions ("text everyone who didn't show up", "move the won deals to onboarding") and it
  executes them — routing every change through a confirmation step first.
- Talk to it by **voice** (mic to transcription to spoken reply) and **paste/drag images** for it to
  read.
- Run it as a team: different team members get role-appropriate views and permissions.

**Use case (any business):** Your closer opens the cockpit Monday morning and asks "what needs my
attention today?" It returns the unworked leads, the deals that stalled, the unread conversations,
and the callbacks due — pulled live, ranked, with one-click actions.

---

## 2. Builds entire automations from a chat prompt  ⭐ (write power)

This is the headline. You describe an automation in words; it builds the whole thing in GHL —
triggers, branching logic, messages, waits, tags, opportunity steps — and publishes it live.

- **Multi-step workflow buildouts:** "Build a 5-touch new-lead nurture: instant SMS, then an email
  after 1 hour, wait a day, branch on whether they replied, tag the engaged ones, and notify the rep
  on hot leads." It assembles every step with the correct structure.
- **Multiple automations in one session:** spin up a nurture sequence, a post-purchase onboarding
  flow, and a win-back campaign in parallel — each with the right trigger and safety conditions.
- **Edits existing workflows:** add a step, change copy, rewrite an AI prompt step, fix a broken
  branch — without rebuilding from scratch.
- **Publishes / unpublishes / archives** workflows on command.

**Use case:** A coaching business wants a "missed discovery call" recovery flow. Instead of an hour
of clicking in the builder, they describe it once and it's live in minutes — with a wait timer, two
follow-up messages, and a branch that stops if the lead reschedules.

> Why this is rare: most "AI for GHL" tools can only *read* or *suggest*. This actually constructs
> and ships working automations through the same API the GHL UI uses.

---

## 3. Messaging that sends itself (safely)  ⭐ (write power)

- Sends **SMS, email, and WhatsApp** to contacts through your own GHL numbers/senders.
- Sends **from the right team member** (e.g. a specific rep's number), not a generic line.
- **Built-in duplicate protection:** before sending, it checks whether the same message already went
  out recently and refuses to double-send. Nobody ever gets texted twice by accident.
- Drafts in your voice and (optionally) shows you the draft before it goes.

**Use case:** A new lead fills out a form at 11pm. Within seconds they get a personal-sounding text
from the assigned rep's number — and if a workflow would have also texted them, the system won't
stack a second message on top.

---

## 4. Pipeline & contact operations on autopilot  ⭐ (write power)

- **Moves opportunities** between stages based on real signals (calls, replies, payments, form fills).
- **Updates custom fields** and **adds/removes tags** — using the safe, additive methods so it never
  wipes existing tags.
- **Creates opportunities** and contacts.
- **Bulk operations with a safety pre-flight:** before any bulk tag/update, it scans your live
  workflows for triggers that might fire unintentionally, so a mass update doesn't accidentally blast
  hundreds of people.

**Use case:** When a payment lands, the buyer is auto-moved to "Customer," tagged for onboarding, and
dropped into the onboarding sequence — no manual stage-dragging.

---

## 5. AI contact intelligence at scale  ⭐ (write power)

- **Profile review:** reads a contact's full history and writes back a **tier** (Hot / Warm / Cold /
  Champion) and a short **summary + recommended next action** — directly onto the contact's custom
  fields so your team sees it inside GHL. (You saw a sample of this in the demo.)
- **Runs across your whole database**, not one at a time.
- **Call-recording analysis:** pulls call audio + transcripts, runs speaker diarization and
  **sentiment/emotion analysis**, and turns it into coaching notes and deal-health scores.

**Use case:** Every lead that comes in is auto-scored and summarized, so reps instantly know who's
worth calling first and why — and managers get objective call coaching without listening to hours of
recordings.

---

## 6. Reaches OUTSIDE GoHighLevel  ⭐ (write power)

The system isn't limited to GHL. It can drive other platforms — even ones with **no API at all**.

- Worked example: a course/certification platform sitting behind Cloudflare with only a login form.
  The system creates the student account, waits (polling) until they activate it, enrolls them in the
  course, and texts them the confirmation — a fully hands-off flow spanning **two** platforms with
  different logins and timing.
- The same technique (covered in `05-beyond-ghl.md`) generalizes to almost any web platform your
  business depends on.

**Use case:** A customer buys a bundle that includes access to a third-party tool. The moment they
pay in GHL, they're provisioned in the other tool and notified — without a human touching either
system.

---

## 7. Always-on automation & scheduled work

- **Background pollers and scheduled jobs:** recurring tasks run on their own (e.g. "every 10
  minutes, check who activated their account and enroll them").
- **Webhooks:** form submissions and events kick off flows instantly.
- **Resilient:** long tasks keep running even if you close your laptop — it's on a server, not your
  desktop. (See `02-architecture.md` and `06-full-server-setup.md`.)

---

## 8. Reporting & answers, live

- Revenue and orders (the demo shows this), email/SMS campaign stats, call stats per rep, pipeline
  health, "what's stuck," and more — answered on demand, pulled live, no exporting to spreadsheets.

---

## How "safe" works

Every action that changes something is designed to pass through a **pending-write confirmation**
step: the AI proposes the change, you approve it, then it executes. Bulk actions get an automatic
pre-flight scan for unintended workflow triggers. Reads (like the demo) need no confirmation because
they can't break anything. You decide how much autonomy to grant.

---

## The bottom line

It reads everything, and — this is the part most tools can't do — it **builds and writes**: whole
automations from a sentence, messages that send themselves safely, contacts scored and summarized by
AI, and automation that reaches beyond GHL entirely. All running 24/7 on a small server for less than
a typical SaaS subscription.

Next: **[02-architecture.md](02-architecture.md)** for how it's built, or
**[04-rebuild-guide.md](04-rebuild-guide.md)** to build your own.
