# 09 — Performance & Caching (make a slow dashboard instant)

Once your AI operator has a dashboard with several tabs, you hit a wall: every tab pulls live
from external APIs (GHL, Stripe, your accounting tool) **on every switch**, so each load takes
8–30 seconds. The fix is a small **snapshot cache** with a background refresher. It took our
heaviest tabs from ~9–14s to **under 0.1s** while keeping the data ~5 minutes fresh.

This doc is the pattern, copy-paste ready. It's framework-agnostic but shown with FastAPI.

---

## The problem

A tab calls an endpoint; the endpoint calls 3–5 external APIs synchronously and returns. Do that
on every tab click (and worse, on a poll timer) and the UI feels broken. Caching is the answer,
but a naive cache has two failure modes you must design around:

1. **Cold-load stampede** — when the cache is empty, ten concurrent requests all trigger the
   expensive build at once.
2. **Stale cliff** — when the entry expires, the *next* user eats the full slow rebuild.

The pattern below solves both with **stale-while-revalidate** + a **background warm loop** +
**per-key locks**.

---

## The pattern

- **Serve stale instantly, refresh in the background.** If a cached value exists but is past its
  TTL, return it *now* and kick off a rebuild in the background. Nobody waits on a stale cliff.
- **Warm in the background.** A loop refreshes registered keys every ~60s, so in practice users
  almost always hit a fresh value and never trigger a cold build themselves.
- **Coalesce concurrent builds with a per-key lock.** Only one build per key runs at a time; other
  callers wait for it instead of stampeding.
- **Keep the old value on error.** A transient API hiccup must not blow away a good snapshot.
- **Offer a force-refresh.** A `?refresh=1` query param (wired to a manual ↻ button) bypasses the
  cache for "I just changed something, show me now."
- **Invalidate on writes.** After an action that changes what a snapshot would return, drop that key.

Single-process app? A plain module-level dict is enough — no Redis. State resets on restart and
repopulates lazily.

---

## Drop-in implementation

```python
# snapshot_cache.py — in-memory stale-while-revalidate cache + background warming.
import asyncio, time, logging
log = logging.getLogger("snapshot_cache")

_store: dict[str, dict] = {}      # key -> {"value":..., "fetched_at": epoch}
_locks: dict[str, asyncio.Lock] = {}
_registry: dict[str, tuple] = {}  # key -> (builder, ttl) for the warm loop

def _lock(key):
    lk = _locks.get(key)
    if lk is None:
        lk = _locks[key] = asyncio.Lock()
    return lk

async def _build_under_lock(key, builder, skip_if_fresher_than=None):
    async with _lock(key):                       # coalesce: one build per key
        if skip_if_fresher_than is not None:
            e = _store.get(key)
            if e and (time.time() - e["fetched_at"]) < skip_if_fresher_than:
                return                            # someone built it while we waited
        try:
            _store[key] = {"value": await builder(), "fetched_at": time.time()}
        except Exception as ex:                   # keep the old value on error
            log.warning("build failed for %s: %s", key, ex)

async def cached(key, builder, ttl=300, force=False):
    _registry.setdefault(key, (builder, ttl))
    e = _store.get(key)
    if e is None:                                 # cold: build now (coalesced)
        await _build_under_lock(key, builder, skip_if_fresher_than=ttl)
        cur = _store.get(key); return cur["value"] if cur else None
    if force:                                     # manual ↻ refresh
        await _build_under_lock(key, builder)
        cur = _store.get(key); return cur["value"] if cur else None
    if (time.time() - e["fetched_at"]) >= ttl and not _lock(key).locked():
        asyncio.create_task(_build_under_lock(key, builder, skip_if_fresher_than=ttl))
    return e["value"]                             # stale-while-revalidate

def invalidate(key): _store.pop(key, None)
def register(key, builder, ttl=300): _registry[key] = (builder, ttl)

async def prime(keys=None):                       # build hot keys once at startup
    for key in (keys if keys is not None else list(_registry)):
        reg = _registry.get(key)
        if reg: await _build_under_lock(key, reg[0], skip_if_fresher_than=reg[1])

async def background_loop(interval=60):           # keep registered keys warm
    while True:
        await asyncio.sleep(interval)
        for key, (builder, ttl) in list(_registry.items()):
            e = _store.get(key)
            if e is None or (time.time() - e["fetched_at"]) >= ttl:
                await _build_under_lock(key, builder, skip_if_fresher_than=ttl)
```

---

## Wiring it into an endpoint (the refactor)

Split a slow handler into a thin **wrapper** + an inner **builder**:

```python
# Before: slow on every call
@app.get("/api/contacts")
async def contacts(limit: int = 500):
    ...  # hits the CRM live every time
    return {...}

# After: cached wrapper + inner builder
@app.get("/api/contacts")
async def contacts(limit: int = 500, refresh: bool = False):
    from snapshot_cache import cached
    return await cached(f"contacts:{limit}", lambda: _contacts_build(limit),
                        ttl=300, force=refresh)

async def _contacts_build(limit: int = 500):
    ...  # the original slow body, unchanged
    return {...}
```

Two rules that bite if you miss them:

- **The cache key must include every parameter the frontend varies** (`limit`, `role`, date range).
  Otherwise different views collide on one key.
- **Register hot keys at startup so they're pre-warmed** — and the registered key string must match
  what the wrapper computes *exactly*, or you'll warm a key nobody reads.

```python
@app.on_event("startup")
async def _start_cache():
    from snapshot_cache import register, prime, background_loop
    register("contacts:1000", lambda: _contacts_build(1000), 300)   # match the wrapper's key
    # ... register your other hot endpoints ...
    await prime()                 # build them once now
    await background_loop(60)      # refresh any key that reaches its TTL, every 60s
```

---

## Frontend: force-refresh vs. cheap poll

Wire the manual refresh button to force a live pull, but let any background poll read the cache so
it stays cheap:

```js
// manual ↻ button → live pull
refreshBtn.addEventListener("click", () => loadContacts(true));
// 10s poll → cached (no &refresh), basically free
setInterval(() => loadContacts(false), 10000);

async function loadContacts(force) {
  const r = await fetch("/api/contacts?limit=1000" + (force ? "&refresh=1" : ""));
  render(await r.json());
}
```

And invalidate on writes so a change shows immediately:

```python
@app.post("/api/issues/{id}/fix")
async def fix(id: str):
    result = do_fix(id)
    from snapshot_cache import invalidate
    invalidate("issues")    # next read rebuilds, so the fixed item clears at once
    return result
```

---

## Results & when to reach further

In practice this took our heaviest tabs from **9–14s to <0.1s** on a cache hit, with data never
more than ~5 minutes stale (and instant via the ↻ button). The startup warm loop means the *first*
user after a restart is usually the only one who ever sees a cold build.

When do you outgrow it?

- **Multiple server processes / machines** → move the dict to Redis (same logic, shared store).
- **You need true real-time freshness** (no 5-min window) → have the upstream platform **push** to
  you. GHL can fire a webhook on contact/opportunity changes; on receipt, `invalidate()` just the
  affected key so the next read rebuilds. That's the "only update when something actually changed"
  ideal — layer it *on top of* this cache, not instead of it.

← Back to [00 — Start Here](00-start-here.md) · See also [02 — Architecture](02-architecture.md)
