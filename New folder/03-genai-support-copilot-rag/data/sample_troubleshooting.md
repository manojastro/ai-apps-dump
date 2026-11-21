# Troubleshooting Sync Failures and Login Errors

Use this runbook to diagnose sync failures, login errors, and connectivity
problems in the desktop and mobile clients.

## Error AUTH-401: Session expired

**Symptom:** The app logs you out unexpectedly or shows "Session expired".

1. Log back in. Sessions expire after **7 days** of inactivity by design.
2. If logouts repeat daily, disable VPN or proxy tools that rotate IP addresses
   mid-session, then log in again.
3. Update the client to the latest version — versions older than 4.2 had a
   token-refresh bug fixed in release 4.2.1.

## Error SYNC-500: Sync failed

**Symptom:** Files stop syncing and the status bar shows SYNC-500.

1. Check the system status page; server-side incidents are posted there first.
2. Verify free disk space: syncing pauses automatically below **500 MB** free.
3. Sign out, restart the device, and sign back in to rebuild the local sync
   queue.
4. Clear the cache: **Settings → Advanced → Clear local cache**. Cached files
   are re-downloaded; unsynced drafts are not affected because they live in
   local storage until synced.

## Error NET-1008: Connection timeout

**Symptom:** Requests hang ~30 seconds, then fail with NET-1008.

- Confirm the device can reach `api.example.com` on port **443**.
- Corporate networks must allowlist `*.example.com` and WebSocket upgrade
  requests; ask IT to unblock them.
- On mobile, switch between Wi-Fi and cellular to isolate the network path.

## Conflicts and duplicate files

When two devices edit the same file offline, the newer edit wins and the older
version is preserved as `<filename> (conflict copy)`. Conflict copies are kept
for **30 days** before automatic cleanup. Merge content manually if needed.

## Reinstall guidance

A clean reinstall resolves persistent client-side corruption:

1. Sign out and quit the app.
2. Uninstall, delete `%LOCALAPPDATA%/ExampleApp` (Windows) or
   `~/Library/Application Support/ExampleApp` (macOS), and reinstall.
3. Log back in — settings sync down from the server automatically.

## When to escalate to a human agent

Escalate to support when any of the following is true:

- The same error persists after a clean reinstall on two different networks.
- A file shows SYNC-500 for more than **24 hours**.
- You suspect data loss involving conflict copies created more than 30 days ago.

Include the diagnostic bundle (**Settings → Advanced → Export diagnostics**)
with your ticket; it shortens investigation time significantly.
