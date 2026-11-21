# Helpdesk Anywhere — Wire Protocol (Phase 1)

Single WSS endpoint `/ws`. First message declares role. JSON for control;
binary frames for video (first byte = frame type, remainder = JPEG payload).

Mirrors: `server/src/protocol.ts` + `windows/Shared/Protocol.cs`.
Change all three together.

## Agent → server

```json
{ "t": "agent.create" }
{ "t": "agent.input", "kind": "mouse-move", "x": 960, "y": 540 }
{ "t": "agent.input", "kind": "mouse-down", "button": "left", "x": 960, "y": 540 }
{ "t": "agent.input", "kind": "mouse-up", "button": "left", "x": 960, "y": 540 }
{ "t": "agent.input", "kind": "wheel", "dx": 0, "dy": -120, "x": 960, "y": 540 }
{ "t": "agent.input", "kind": "key-down", "code": "KeyA" }
{ "t": "agent.input", "kind": "key-up", "code": "KeyA" }
{ "t": "agent.exec", "shell": "powershell", "script": "...", "asSystem": false }
{ "t": "agent.requestElevation", "mode": "interactive" }
{ "t": "agent.requestElevation", "mode": "credential", "domain": "...", "username": "...", "password": "..." }
{ "t": "agent.sas" }
{ "t": "agent.end" }
```

`agent.create` → `{ "t": "session.created", "code": "482913" }`

`agent.input` coords are remote backing-store pixels (canvas maps via the
backing-store ratio, never CSS size). `button` is `left`|`middle`|`right`.
`code` is the DOM `event.code` (physical key, layout-independent). Wheel
`dx`/`dy` are DOM pixel deltas as-is (down/right positive); the host converts
sign for `SendInput`. Special keys
the browser swallows (Win, Alt+Tab, Ctrl+Esc, PrintScreen) are sent as plain
`key-down`/`key-up` pairs from console buttons. Ctrl+Alt+Del is never sent over
this message — it is a Secure Attention Sequence, wired in Phase 5 only.

Credential-mode elevation is **refused on non-TLS** and **never logged**
(password is redacted at the relay; only fact/result + username are audited).

`agent.sas` requests a software Secure Attention Sequence from the elevated
helper (Phase 5). The portal enables its Ctrl+Alt+Del button only after
`host.elevated { ok:true }`; the relay audits the fact and forwards it only
while the session is active. The applet forwards it to the helper pipe only
while the secure desktop is active.

## Host (applet) → server

```json
{ "t": "host.join", "code": "482913", "machine": "...", "user": "...", "os": "..." }
{ "t": "host.consent", "accepted": true }
{ "t": "host.desktopChanged", "desktop": "Default" }
{ "t": "host.elevated", "ok": true }
{ "t": "host.elevated", "ok": false, "error": "declined" }
{ "t": "host.execResult", "id": "...", "exitCode": 0, "stdout": "...", "stderr": "..." }
```

Binary:

- `[0x01][jpeg bytes]` — full frame
- `[0x02][x:u16be][y:u16be][w:u16be][h:u16be][jpeg bytes]` — dirty rect (Phase 3.3):
  128×128 tiles (edge tiles smaller), coords relative to the virtual-desktop
  origin, integers big-endian. Full keyframe every 5s and on start.

## Server → both

- `{ "t": "peer.joined", "...": "..." }`
- `{ "t": "peer.left", "...": "..." }`
- `{ "t": "error", "error": "..." }`
- To host only: `{ "t": "host.connectRequest", "agentName": "..." }`
- To agent only: `{ "t": "consent.result", "accepted": true }`

## Rules (Phase 1)

- 6-digit numeric codes from `crypto.randomInt`. Collision → retry.
- `state`: `waiting_for_host` → `waiting_for_consent` → `active` → `ended`.
- Codes expire after 10 minutes unused; single-use — burn on host join.
- Rate-limit `host.join` to 5 attempts per IP per minute.
- Sweep expired/ended sessions on a 60s timer.
- Drop any frame arriving before `state === "active"` (except create/join/consent/end).
- Heartbeat ping every 20s, drop dead peers.
- Close both sides when either drops.
- Elevation (Phase 5): at most 5 `agent.requestElevation` per session, then
  `host.elevated { ok:false, error:"rate_limited" }`. Failure errors:
  `declined`, `tls_required`, `timeout`, `launch_failed`, `install_failed`,
  `logon failure: wrong username or password`, `blank passwords are not
  allowed for this account`, `account disabled`,
  `account is not allowed interactive logon`, `account locked out`.
