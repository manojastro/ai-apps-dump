# Migration Manifest — generated 2026-09-22T03:15:21Z

## Source VM
- OS: Ubuntu 24.04.4 LTS
- Kernel: 6.17.0-1020-oracle
- Hostname: helpdesk-anywhere-vm
- Project directory: /home/ubuntu/Helpdesk Anywhere

## Git
- Repository: https://github.com/manojastro/helpdesk-anywhere-claude-Linux.git
- Branch: main
- Commit SHA: 2ac28ed81bf19327c479622163a217f53c5f4f9c
- Working tree: clean

## Docker
- Docker: Docker version 29.1.3, build 29.1.3-0ubuntu3~24.04.2
- Compose: Docker Compose version 2.40.3+ds1-0ubuntu1~24.04.1
- Compose project: helpdeskanywhere
- Active profile observed at backup time: app,cloudflared

## Containers (expected)
- app        — server/Dockerfile, port 8080 internal only (expose, not published)
- caddy      — profile: tls   — publishes 80/443 (permanent DuckDNS path, PLAN 7.3)
- ngrok      — profile: ngrok — publishes 127.0.0.1:4040 only (temporary)
- cloudflared— profile: cloudflared — publishes 127.0.0.1:2000 only (temporary, no account/DNS)
Exactly one of caddy/ngrok/cloudflared should run at a time (one PUBLIC_HOST, one /ws Origin).

## Persistent volumes
- helpdeskanywhere_caddy_data, helpdeskanywhere_caddy_config — Let's Encrypt cert cache
  (tls profile only; safe to recreate empty on the new VM, Caddy re-issues automatically)
- ./audit (bind mount) — the only real persistent state; back this up, do not skip it

## Firewall / ports required
- 22/tcp  — SSH (administration)
- 80/tcp  — only for the tls profile (ACME HTTP-01 challenge + HSTS redirect)
- 443/tcp — only for the tls profile (HTTPS/WSS)
No inbound ports are required for the ngrok/cloudflared profiles — both dial out.

## Required environment variables (names only — see config/.env, restore manually)
- PUBLIC_HOST
- AGENT_NAME
- CONSOLE_USER
- CONSOLE_PASSWORD
- NGROK_AUTHTOKEN

## Secrets present in .env (FOUND / NOT FOUND only)
- CONSOLE_PASSWORD: FOUND
- NGROK_AUTHTOKEN:  FOUND
- PUBLIC_HOST set:  FOUND

## Domain / tunnel in use at backup time
See config/.env (PUBLIC_HOST) — not reproduced here as it identifies the live endpoint.
Cross-check against MIGRATION_DNS.md in the repo root for the cutover plan.

## systemd services required
None beyond docker.service itself. No DuckDNS renewal cron exists on this host
(Caddy's built-in ACME client handles renewal automatically when the tls profile
 is used — nothing to schedule separately).

## Required directories on the new VM
- <repo_root>/audit           (bind-mounted, must be writable by HOST_UID:HOST_GID)
- <repo_root>/server/public/download (applet .exe served from here)

## Application startup command
  cd <repo_root>
  export HOST_UID=$(id -u) HOST_GID=$(id -g)
  docker compose --profile <tls|ngrok|cloudflared> up -d --build

## Verification commands
  docker compose ps
  curl -fsS https://<host>/healthz
  ./scripts/verify-deployment.sh https://<host>
  ./scripts/cloud-migration/verify-migration.sh https://<host> 2ac28ed81bf19327c479622163a217f53c5f4f9c
