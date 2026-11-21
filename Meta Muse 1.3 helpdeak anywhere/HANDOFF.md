# Helpdesk Anywhere — Session Handoff (OpenCode)

> Read this file first in any new session, then `PLAN_UPDATED_WINDOWS_OPENCODE.md`
> (build plan, phase gates), then `CLAUDE2_UPDATED_WINDOWS_OPENCODE.md`
> (architecture + constraints). Then run `git log --oneline -8` and
> `git status --short` before touching anything.

## 1. What this is

LogMeIn Rescue-style **attended** remote support POC. A support agent opens a
browser console, generates a 6-digit session code, shares a link. The end user
runs a Windows applet, types the code, clicks Accept. The agent then views and
controls the machine — **including UAC / Secure Desktop prompts** — over
WSS/443 through a relay server. No stealth, no persistence: the elevated helper
service uninstalls at session end.

## 2. Hard environment boundary (do not violate)

- **Local Windows workstation = the ONLY dev/build/test environment.**
  PowerShell 7, Node.js **22 LTS** (v22.17.1 verified), .NET SDK **8.x**
  (8.0.424 verified), Git 2.52. All C#, TypeScript, WinForms, service, UAC work
  happens here.
- **Ubuntu VM = deployment-only host** (Docker + Caddy + Node). It does not
  exist yet in practice; nothing has been deployed anywhere. Never develop on it.
- Repo root: `D:\ai apps dump\Meta Muse 1.3 helpdeak anywhere`
  (note the `helpdeak` spelling — that is the real folder name).

## 3. Non-negotiable constraints (from CLAUDE2 doc)

1. Explicit modal consent naming the agent before every session; nothing streams before Accept.
2. Always-visible, non-hideable session indicator; one-click End.
3. No stealth/persistence: service installed at session start, uninstalled at end; nothing survives reboot.
4. Server-side audit log of start/stop/consent/elevation/exec.
5. Credentials never logged/retained; zeroed after use; refused without TLS; elevation shown in the indicator.
6. Never evade AV. Defender + **Bitdefender** are installed on the dev box and
   WILL flag/fight this project (see §9). Add exclusions; never work around detections.

## 4. Architecture (as built)

```
Agent browser (portal.html/js) ──WSS──▶ Ubuntu: Caddy :443 ──▶ Node app:8080
Windows Applet.exe (user) ──────WSS──▶   (sessions + relay + audit + download)
   │ installs/starts (elevated, per session)
   ▼
SecureDesktopService.exe (SYSTEM, session 0): 200ms input-desktop poll,
spawns DesktopHelper into the console session on non-Default desktops,
60s pipe watchdog with self-uninstall.
   ▼
DesktopHelper.exe (SYSTEM, user session, --desktop Winlogon): GDI capture +
SendInput over the applet's named pipe (per-session GUID, ACL = LocalSystem +
current user ONLY).
```

- Single WSS endpoint `/ws`. JSON control; binary video `[0x01][jpeg]` full,
  `[0x02][x:u16be][y:u16be][w:u16be][h:u16be][jpeg]` dirty rect (128px tiles,
  keyframe every 5s). Full catalog: `shared/protocol.md` (source of truth) =
  `server/src/protocol.ts` = `windows/Shared/Protocol.cs`. Change all three.
- Server relays verbatim when `state === active`, drops before that. No DB
  (in-memory Map). Audit = append-only JSONL (`AUDIT_PATH`, default
  `server/data/audit.jsonl`; `/data/audit.jsonl` in Docker).
- Session codes: 6-digit `crypto.randomInt`, 10-min expiry, single-use burn,
  5 `host.join`/min/IP, 5 `agent.requestElevation`/session (server AND applet),
  60s sweep, 20s WS heartbeat.

## 5. Repo map (what lives where)

```
docker-compose.yml, Caddyfile, .env.example, .gitignore
shared/protocol.md
scripts/build-windows.ps1      # publishes svc+helper, embeds into applet, single exe (SEE §9: helper Release blocked)
scripts/dev-server.ps1         # local dev server (Node directly)
scripts/deploy.sh              # Ubuntu-only deploy stub
scripts/mock-host.js           # tiny WS mock host (global WebSocket, no deps)
scripts/verify-phase{N}.mjs    # automated acceptance per phase (1-5)
scripts/test-phase5-elevated.ps1 + verify-phase5-uac.mjs  # ELEVATED UAC cycle (see §7)
server/src/{index,config,protocol,sessions,signaling,audit}.ts
server/src/routes/{portal,download}.ts
server/public/{portal.html,portal.js,portal.css,join.html,download/}
server/Dockerfile, package.json (express, ws, tsx, typescript), tsconfig (strict, ES2022/NodeNext, ESM)
windows/HelpdeskAnywhere.sln
windows/Shared/                # Capture/, Imaging/, Input/ (injector, KeyMap, InputHandler),
                               # Interop/ (Service, Logon, Desktop/Session), PipeChannel (PipeServer/PipeClient),
                               # ElevationErrors, ServiceManager, Protocol
windows/Applet/                # WinForms (code entry, consent, indicator), SessionClient,
                               # Streaming/ (Frame + DirtyRect), Elevation/ (Installer, ElevationSession,
                               # PipeHost, SecureBridge), Resources/ (gitignored payload staging)
windows/SecureDesktopService/  # watcher service (+ --console mode)
windows/DesktopHelper/         # secure-desktop worker
e2e/{package.json,portal-stream.mjs,portal-input.mjs}  # Playwright + Chromium (already downloaded)
```

## 6. Phase status and evidence

| Phase | Status | Commit | Evidence |
|---|---|---|---|
| 0 scaffold/toolchain | ✅ DONE | `bb4ec8b` | Versions verified |
| 1 sessions/pairing/portal/audit | ✅ DONE | `941c8bd` | `verify-phase1.mjs` 10/10 |
| 2 applet connect/consent/indicator | ✅ DONE (+human GUI confirmed) | `4d7be68` | `verify-phase2.mjs` real-binary accept+decline |
| 3 capture + streaming | ✅ DONE (+browser e2e) | `70106dd`, `d1c42f0` | `verify-phase3.mjs` (6.6 FPS full; dirty: 3 keyframes + 297 deltas, 663 kbps); `e2e/portal-stream.mjs` renders in Chromium, counter 12–83/s |
| 4 input injection | ✅ DONE (auto; human residue below) | `3ce1717` | `verify-phase4.mjs` 25 checks (sub-2px cursor, live modifiers, drop→release); `e2e/portal-input.mjs` 10/10 wire-exactness |
| 5 UAC / Secure Desktop | 🟡 CODE DONE, acceptance open | `45ded02` | `verify-phase5.mjs` 14/14 unelevated (see §7). Elevated cycle NOT yet run |
| 6 script execution | ⬜ NOT STARTED | — | Phase gate: starts after Phase 5 closes |
| 7 deploy + internet test | ⬜ NOT STARTED | — | No cloud/DNS/Docker work begun |

## 7. Phase 5 — exactly what is proven vs pending

PROVEN unelevated (all in `verify-phase5.mjs`, rerun green):
`agent.sas` relay verbatim + audit; helper standalone on Default desktop
(ready, ≥5 video frames, JPEG SOI, real cursor move, survives SAS, exits);
pipe ACL exactly `SYSTEM`+current-user (`--pipe-acl-test`, in-process);
credential elevation refused without TLS ×5 then server `rate_limited` on 6th;
bad logon maps to friendly text (`--test-logon` + `HDA_TEST_*` env);
server audit keeps username, zero password hits anywhere.

PENDING (cannot be done unelevated):
1. **Elevated UAC cycle** — run once from an elevated PowerShell:
   `powershell -ExecutionPolicy Bypass -File scripts\test-phase5-elevated.ps1`
   (Debug payloads are already staged next to the exe by a previous session.)
   It installs the real service, raises a genuine UAC prompt via
   `runas /trustlevel`, proves `desktopChanged Winlogon` + secure frames reach
   the agent (samples saved to `server/data/uac-samples/`), dismisses remotely
   with Escape, proves return to Default, uninstalls everything. Screen flashes
   to secure desktop ~30s — expected. Exit 0 pass / 1 fail / 2 pending-human
   (prompt left for one manual No-click, benign).
2. **Credential mode with a correct password** — needs real admin creds + TLS
   (post-Phase-7 URL). Wrong-password path is proven.
3. **Interactive-mode click path** — needs one human Yes on a real UAC prompt
   during GUI use.
4. **Single-exe embedding** — implemented but unpublishable until the AV
   exclusion below (see §9).

## 8. How to build / run / verify (copy-paste)

```powershell
# SERVER (run each npm command with workdir = server/; `npm --prefix` is broken on this box)
npm install; npm run build
$env:PORT="8080"; node dist/index.js        # or: ./scripts/dev-server.ps1
# DOTNET (workdir = repo root)
dotnet build windows/HelpdeskAnywhere.sln   # must be 0 warnings, 0 errors
# SINGLE EXE (currently: helper Release step fails — see §9)
./scripts/build-windows.ps1                 # -> server/public/download/HelpdeskAnywhere.exe
# Applet-only publish (works today, no payloads):
dotnet publish windows/Applet/Applet.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o "$env:TEMP/hda-publish"
# VERIFY (each on its OWN fresh server port — suites share the 5/min join budget)
node scripts/verify-phase1.mjs --url ws://127.0.0.1:18080/ws --http http://127.0.0.1:18080
node scripts/verify-phase2.mjs --url ... --server ...
node scripts/verify-phase3.mjs --url ... --server ... --window 12 --min-fps 8
node scripts/verify-phase4.mjs --url ... --server ...
node scripts/verify-phase5.mjs --url ... --server ... --helper windows/DesktopHelper/bin/Debug/net8.0-windows/DesktopHelper.exe
node e2e/portal-stream.mjs --http ... --url ...     # needs server + cursor jiggle for deltas
node e2e/portal-input.mjs --http ... --url ...
```

Key applet flags: `--headless --server <ws|wss>/ws --code <6-digit>
--accept|--decline --duration <s> [--video] [--full-frames] [--log-input]`;
`--check-key A,B,C`; `--pipe-acl-test`; `--test-logon` (with `HDA_TEST_DOMAIN/
HDA_TEST_USER/HDA_TEST_PASSWORD`); `--install-service|--uninstall-service --pipe <name>`.
Helper: `--desktop <name> --pipe <name>`. Service: `--pipe <name>` (+ `--console`).

## 9. Known environment fights (do NOT "fix" by evasion)

- **Bitdefender holds the helper's Release outputs** (proven via Restart
  Manager: `bdservicehost`). Release publish of DesktopHelper fails; Debug
  builds are fine. Fix = repo-folder exclusion in Bitdefender (+ Defender),
  done by the human in AV UIs. Never disable protection or obfuscate code.
- **Defender AMSI blocks scripted window-focus** (SetForegroundWindow
  one-liners). Typing visible text into Notepad is therefore a HUMAN matrix
  item, not automated. Never obfuscate to dodge it.
- Live `Get-Acl \\.\pipe\<name>` races the single pipe instance (error 231);
  the in-process `--pipe-acl-test` is the authoritative ACL check.
- `npm --prefix` is broken on this box — always set the tool workdir instead.
- WinExe binaries don't propagate `$LASTEXITCODE` via `&`; use
  `Start-Process -Wait -PassThru`.
- `execFileSync`/spawns mid-session stall the Node event loop and can look
  like network faults; keep verify scripts spawn-free while sessions are live.
- Run each verify suite against a FRESH server (rate limits are per-IP).

## 10. Hard-won code lessons (don't regress)

- `LibraryImport` does NO A/W name mangling: `CreateDC`→`CreateDCW`,
  `MapVirtualKey`→`MapVirtualKeyW`; but `DrawIconEx`/`BitBlt`/etc. have single
  exact exports. A wrong name throws `EntryPointNotFoundException` at first call.
- Struct-bearing P/Invokes (`STARTUPINFO`) must be classic `DllImport`;
  source-gen can't marshal them (SYSLIB1051). All P/Invoke stays in `*/Interop/`.
- `ws` delivers TEXT frames as Buffer server-side: branch on the `isBinary`
  flag, never on type (Phase 1 infile bug, caught by its own test).
- Applet send loop must wait on control AND binary queues (starvation bug).
- `NamedPipeServerStreamAcl.Create` is the ACL-capable constructor on .NET
  (not a ctor overload). Pipe accept loop: faulted listen must
  Disconnect+continue (never break — a break wedges the pipe busy forever);
  10s first-frame handshake gate drops silent squatters.
- `SessionClient.ReceiveLoopAsync` wraps dispatch in try/catch (a handler bug
  must never kill reception — learned from the MapVirtualKey incident).
- Server heartbeat: `isAlive` resets on pong AND any inbound message; kills are
  audited (`heartbeat.terminated`); drops audited with role+state.
- Current user is UNELEVATED admin (Microsoft account). No standard-user test
  account exists. Service install/start, SCM writes, and the UAC cycle require
  elevation — that is what `test-phase5-elevated.ps1` is for.

## 11. Resume checklist for the next session

1. Read §2–§4 here + the two spec docs. `git log --oneline -8`, `git status`.
2. Re-run: `verify-phase1` (fresh port), `verify-phase5` (fresh port). Both green = tree healthy.
3. If the human pasted elevated-test output: triage it, fix, re-verify, then open Phase 6.
4. If the AV exclusion is done: run `build-windows.ps1` fully, confirm the
   single exe contains payloads, delete stray `server/public/download/*.exe`
   copies of Debug payloads if present (gitignored, but keep the folder clean).
5. Human gates use the `question` tool (passed/failed/skip). Phase gate rule:
   never start N+1 until N's acceptance passes on real hardware.
6. Commit after each verified phase. Never commit `.env`, `*_audit.jsonl`
   under `server/data/`, or anything under `windows/Applet/Resources/`.
