# 06 — Full Server Setup (and Why a Server Beats a Laptop App)

The system can run on your laptop for development, but its real power — running automations 24/7 —
needs an always-on server. This doc covers **why**, then **how**.

---

## Why a server, not the desktop app

A desktop AI app is single-session and tied to your machine being open. The whole value here is work
that happens **while you're not watching**. Concrete differences:

| Capability | Laptop / desktop app | Always-on server |
|---|---|---|
| Automations run when you're asleep / closed | No | **Yes** |
| Background pollers ("check every 10 min and enroll") | No | **Yes** |
| Webhooks (form submit instantly triggers a flow) | No | **Yes** |
| Long tasks survive you closing the tab | No | **Yes** |
| Scheduled jobs (nightly backup, token refresh) | No | **Yes** |
| Whole team uses the same cockpit | No (single user) | **Yes** |
| Persistent browser sessions for automation | No | **Yes** |

**Concrete example:** a customer signs up at 2am. The server creates their account on the course
platform, texts them, and — hours later, when they activate — enrolls them and confirms. A laptop app
was asleep for all of it.

**Cost framing:** the whole thing runs comfortably on a small cloud server (a 2 vCPU / ~4 GB VM is
roughly **$12–24/month**) plus a flat-rate Claude subscription for the AI brain (instead of metered
per-token API billing). The optional services are usage-based and have free tiers to start
(Browserbase for browser automation; Gladia for call transcription, ~10 free hours/month). For most
small operations the all-in cost lands in the low tens of dollars a month, which is the "enterprise
capability on a startup budget" part. Your numbers will vary with volume.

---

## The deployment topology

```
Internet
   |
[Caddy]  -- automatic HTTPS (Let's Encrypt), reverse proxy
   |
[FastAPI + uvicorn]  -- the cockpit app, port 3001 (localhost only)
   |
   +-- SQLite database (chat history, pending writes, run logs)
   +-- claude CLI subprocesses (the AI brain)
   +-- MCP tool servers (GHL, browser bridge, etc.)
   |
[systemd]  -- keeps it all running, restarts on failure

Scheduled (cron):  nightly DB backup -> off-server object storage
                   periodic admin-token refresh
```

---

## Setup, step by step

### 1. Provision a server
Any small Linux cloud VM works (e.g. a 2 vCPU / ~4 GB droplet on DigitalOcean, or equivalent on any
provider). Ubuntu LTS is a good default.

### 2. Install the runtime
```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nodejs npm caddy
# install the Claude CLI per its docs, and log in once
```

### 3. Lay down the app
Put your code in `/opt/yourapp` (or `/root/yourapp`), create a virtualenv, install deps:
```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```

### 4. Store secrets in an env file (root-only)
```bash
sudo tee /etc/yourapp.env >/dev/null <<'EOF'
GHL_TOKEN=...
GHL_LOCATION_ID=...
BROWSERBASE_API_KEY=...
GLADIA_API_KEY=...
EOF
sudo chmod 600 /etc/yourapp.env
```

### 5. Run it under systemd
```ini
# /etc/systemd/system/yourapp.service
[Unit]
Description=GHL AI Automation
After=network.target

[Service]
Type=simple
EnvironmentFile=/etc/yourapp.env
ExecStart=/opt/yourapp/venv/bin/uvicorn main:app --host 127.0.0.1 --port 3001 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now yourapp
```

### 6. Put Caddy in front (HTTPS for free)
```
# /etc/caddy/Caddyfile
yourdomain.com {
    reverse_proxy 127.0.0.1:3001
    request_body { max_size 500MB }   # for audio/file uploads
    reverse_proxy {
        flush_interval -1             # don't buffer streamed AI responses
    }
}
```
```bash
sudo systemctl reload caddy
```
Point your domain's DNS A record at the server's IP and Caddy auto-issues the TLS cert.

### 7. Background jobs (the always-on magic)
- **In-process loops:** start `asyncio` tasks on app startup for pollers (e.g. the cross-platform
  enrollment poller from `05-beyond-ghl.md`).
- **Cron jobs:** nightly database backup to object storage; periodic admin-token refresh.

### 8. Backups & safety
- Nightly: snapshot the SQLite DB (use the SQLite backup API so it's consistent with live writers),
  gzip, upload to object storage; prune old copies.
- Lock down the firewall: SSH from your IP only; 80/443 open for the web app.
- Add basic uptime + resource alerts.

---

## Operating it

```bash
systemctl status yourapp           # is it running?
systemctl restart yourapp          # after code changes (briefly interrupts active chats)
journalctl -u yourapp -n 50 -f     # logs
curl https://yourdomain.com/api/health
```

> Tip: static front-end files (HTML/JS) are read from disk per request — you only need to restart
> after changing Python code, not after tweaking the UI.

---

## External services checklist

| Service | For | Notes |
|---|---|---|
| GoHighLevel | the CRM | public token + (optional) admin token |
| Claude (CLI or API) | the AI brain | CLI = flat-rate subscription billing |
| Browserbase | browser automation | only if you automate non-API platforms / GHL UI |
| Gladia | call transcription + sentiment | only if you do call intelligence |
| Object storage (e.g. Spaces/S3) | off-server backups | cheap, flat-rate |

That's the full stack. With this running, the capabilities in `01-what-it-can-do.md` operate around
the clock — which is the entire point.
