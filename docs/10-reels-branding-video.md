# 10 — Reels / branding video pipeline

The branding agent doesn't just render static social images (doc 08) — it produces **genuine
short-form vertical video (Reels/Shorts/TikTok)** with real footage, AI voiceover, and word-synced
captions, end to end and approval-gated. This is the video lane of the social system.

## What it produces
A 1080×1920 MP4 with: real b-roll matched to the script, an AI voiceover track, burned-in
word-synced captions, brand colors/handle, and a subtle scrim for legibility on bright footage —
then queued (not auto-posted) to the social planner for human approval.

## Pipeline (modular)
1. **Script / voiceover** — a short on-brand script (voice-linted: no em-dashes, no flattery/hype,
   length-checked) → text-to-speech (e.g. ElevenLabs) returns audio **plus per-character timing**,
   which is what makes word-synced captions possible.
2. **Content-aware b-roll director** — the script is split into ~cut windows using the TTS word
   timings; one vision call describes each clip in your media library (cached), and one planning call
   assigns the best real clip per window. When the library doesn't truly cover a concept it flags a
   concrete stock-search query.
3. **Real-first footage waterfall** — real library clip → free stock video → stock image (Ken-Burns
   zoompan) → AI-generated clip **only for non-human concepts** (the brand never fabricates people;
   "needs a person" windows fall back to the closest real clip). AI clips are face-checked and
   rejected if a person appears.
4. **Face-aware framing** — local face detection (OpenCV Haar cascades; no GPU/API/cost) auto-centers
   talking heads and moves captions to a safe band so a low subject isn't covered. Falls back to
   center/bottom on any doubt, so it can never make output worse.
5. **Assembly (ffmpeg)** — vertical bed (center-crop or Ken-Burns), looped to fill each window, audio
   muxed, captions burned via timed subtitles, concat timebase pinned. Output validated (dims +
   audio + caption sync) before it leaves the box.
6. **Upload + approval** — pushed to the media library and queued to the social planner as
   `in_review` with a per-segment footage rundown (X real / Y stock / Z AI) so the approver isn't
   blind. Nothing posts without a human approve.

## Hard rules (the expensive lessons)
- **Fail loud, not silent.** Render is the expensive step (TTS minutes + ffmpeg) — if the upload
  fails, keep the local render, retry with backoff, and surface a real error + `warnings[]`; never
  swallow it and return null.
- **Validate cached b-roll.** A partial/corrupt download must be re-fetched (length check) and
  deleted so the cache self-heals — a silently-zero-duration clip drops from the reel forever.
- **Guard caption alignment.** Empty TTS alignment = hard error; a length mismatch warns + truncates
  to the common length — never let captions silently drift.
- **AI footage face-guard fails CLOSED.** If you can't inspect the generated frames, reject the clip;
  a mislabeled concept must not ship a fake human.
- **Verify renders.** The agent can hallucinate success on a tool failure — check the returned
  `cdn_url`/`warnings[]`, don't assume.

## Deps
ffmpeg; a TTS provider with character-level timings; a vision-capable model for clip cataloging +
planning; OpenCV (headless) + Pillow + numpy for face-aware framing; optional free stock-media keys
(the waterfall just skips the stock tier until a key is present).

> Same approval-gate philosophy as the rest of the system (docs/01, docs/08): the AI assembles and
> queues; a human approves before anything goes live.
