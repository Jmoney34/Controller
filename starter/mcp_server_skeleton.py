#!/usr/bin/env python3
"""
MCP server SKELETON for GoHighLevel.

An MCP ("Model Context Protocol") server exposes "tools" your AI assistant can call
during a conversation. This skeleton shows the pattern with a few READ tools and ONE
write tool that uses the safe "queue then confirm" pattern (it does not fire directly).

Extend it by adding more tools following the same shape. Pair with:
  - docs/03-ghl-knowledge-base.md  (every endpoint + gotcha)
  - docs/04-rebuild-guide.md       (build stages)

Run (after `pip install mcp requests`):
  GHL_TOKEN=... GHL_LOCATION_ID=... python3 mcp_server_skeleton.py

Then register it with your AI assistant / MCP client.
"""
import os
import json
import sqlite3
import uuid

import requests

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    raise SystemExit("Install the MCP SDK first:  pip install mcp")

GHL_BASE = "https://services.leadconnectorhq.com"
VERSION = "2021-07-28"
LOC = os.environ.get("GHL_LOCATION_ID", "")
DB = os.environ.get("PENDING_DB", "pending_writes.db")


# --------------------------------------------------------------------------- helpers
def hdrs():
    return {"Authorization": f"Bearer {os.environ.get('GHL_TOKEN','')}",
            "Version": VERSION, "Content-Type": "application/json"}


def api(method, path, **kw):
    """HTTP with status checking. A network error or 4xx/5xx returns a clean error
    object instead of raising, so a single bad call can never crash the tool server."""
    try:
        r = requests.request(method, f"{GHL_BASE}{path}", headers=hdrs(), timeout=25, **kw)
    except requests.RequestException as e:
        return {"error": "network_error", "detail": str(e)}
    if r.status_code >= 300:
        return {"error": f"http_{r.status_code}", "detail": r.text[:300]}
    try:
        return r.json()
    except ValueError:
        return {"error": "non_json_response", "detail": r.text[:300]}


def ok(obj):
    return [TextContent(type="text", text=json.dumps(obj, default=str))]


def init_pending_db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS pending_writes (
        id TEXT PRIMARY KEY, operation TEXT, params TEXT, description TEXT,
        status TEXT DEFAULT 'pending', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.commit(); c.close()


def queue_write(operation, params, description):
    """The SAFE write pattern: record the intended change, return an id for human approval.
    A separate executor (not shown) performs the real GHL call after approval."""
    pid = str(uuid.uuid4())
    c = sqlite3.connect(DB)
    c.execute("INSERT INTO pending_writes (id, operation, params, description) VALUES (?,?,?,?)",
              (pid, operation, json.dumps(params), description))
    c.commit(); c.close()
    return pid


# --------------------------------------------------------------------------- server
app = Server("ghl-starter")


@app.list_tools()
async def list_tools():
    return [
        Tool(name="ghl_list_pipelines",
             description="List the location's pipelines and their stages.",
             inputSchema={"type": "object", "properties": {}}),
        Tool(name="ghl_search_contacts",
             description="Search contacts. Optional query string (name/email/phone).",
             inputSchema={"type": "object", "properties": {
                 "query": {"type": "string"}, "limit": {"type": "integer", "default": 20}}}),
        Tool(name="ghl_get_contact",
             description="Get a single contact by id.",
             inputSchema={"type": "object", "properties": {"contact_id": {"type": "string"}},
                          "required": ["contact_id"]}),
        Tool(name="ghl_recent_orders",
             description="List recent payment orders (real sales signal).",
             inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 10}}}),
        # ---- one WRITE tool, demonstrating the queue-then-confirm safety pattern ----
        Tool(name="ghl_add_tag",
             description="QUEUE adding a tag to a contact (requires human confirmation before it runs).",
             inputSchema={"type": "object", "properties": {
                 "contact_id": {"type": "string"}, "tag": {"type": "string"}},
                 "required": ["contact_id", "tag"]}),
    ]


@app.call_tool()
async def call_tool(name, arguments):
    # ---- reads (execute live) ----
    if name == "ghl_list_pipelines":
        return ok(api("GET", "/opportunities/pipelines", params={"locationId": LOC}))

    if name == "ghl_search_contacts":
        body = {"locationId": LOC, "pageLimit": arguments.get("limit", 20)}
        if arguments.get("query"):
            body["query"] = arguments["query"]
        return ok(api("POST", "/contacts/search", json=body))

    if name == "ghl_get_contact":
        return ok(api("GET", f"/contacts/{arguments['contact_id']}"))

    if name == "ghl_recent_orders":
        return ok(api("GET", "/payments/orders/",
                      params={"altId": LOC, "altType": "location",
                              "limit": arguments.get("limit", 10)}))

    # ---- write (QUEUES, does not fire) ----
    if name == "ghl_add_tag":
        # NOTE: real execution uses POST /contacts/{id}/tags (additive). Here we only QUEUE it.
        pid = queue_write("add_tag",
                          {"contact_id": arguments["contact_id"], "tag": arguments["tag"]},
                          f"Add tag '{arguments['tag']}' to contact {arguments['contact_id']}")
        return ok({"queued": True, "pending_id": pid,
                   "note": "Approve this in your cockpit to execute. Nothing changed yet."})

    return ok({"error": f"unknown tool {name}"})


def _check_env():
    """Fail fast with a clear message instead of silently calling GHL with an empty
    token / location id (which would return confusing 401/404s from every tool)."""
    missing = [v for v in ("GHL_TOKEN", "GHL_LOCATION_ID") if not os.environ.get(v)]
    if missing:
        raise SystemExit(f"ERROR: set these environment variables first: {', '.join(missing)}")


async def _main():
    _check_env()
    init_pending_db()
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(_main())
