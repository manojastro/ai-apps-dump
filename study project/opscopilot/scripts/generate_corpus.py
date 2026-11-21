"""Generate the synthetic Acme Retail Ltd corpus: 30 KEDB + 8 SOP markdown docs.

Traps (on purpose, all synthetic):
- 2 conflicting pairs: (KB0007 vs KB0008), (KB0015 vs KB0016)
- 2 retired: KB0029, KB0030 (status: retired)
- 2 near-duplicates: KB0011 vs KB0012 (same fix, slightly reworded)

Usage: uv run python scripts/generate_corpus.py [--out data/corpus]
"""

from __future__ import annotations

import argparse
from pathlib import Path


def kedb(
    kb_id: str,
    title: str,
    service: str,
    symptoms: str,
    cause: str,
    workaround: str,
    fix: str,
    status: str = "active",
    updated: str = "2025-06-01",
    code: str = "",
) -> str:
    code_line = f"\n**Error code:** `{code}`\n" if code else ""
    return f"""---
doc_id: {kb_id}
title: "{title}"
doc_type: kedb
service: {service}
status: {status}
updated_at: "{updated}"
synthetic: true
---

# {title}
{code_line}
## Symptoms

{symptoms}

## Cause

{cause}

## Workaround

{workaround}

## Permanent fix

{fix}

---
*Synthetic data for Acme Retail Ltd. Fictional — no real customer or employee data.*
"""


def sop(
    doc_id: str,
    title: str,
    service: str,
    purpose: str,
    steps: str,
    escalation: str,
    status: str = "active",
    updated: str = "2025-05-01",
) -> str:
    return f"""---
doc_id: {doc_id}
title: "{title}"
doc_type: sop
service: {service}
status: {status}
updated_at: "{updated}"
synthetic: true
---

# {title}

## Purpose

{purpose}

## Steps

{steps}

## Escalation

{escalation}

---
*Synthetic data for Acme Retail Ltd. Fictional — no real customer or employee data.*
"""


def build_kedb() -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    A = "active"
    docs.append(("KB0001.md", kedb("KB0001", "Outlook repeatedly prompts for password after MFA reset",
        "outlook", "After an MFA reset, Outlook for Windows keeps asking for the password every few minutes. Webmail works fine.",
        "Stale cached credentials in Windows Credential Manager still reference the old MFA claim.",
        "Open Credential Manager > Windows Credentials, remove all `Outlook` and `MicrosoftOffice` entries, restart Outlook and sign in again.",
        "Push the Acme identity baseline that forces Modern Authentication and blocks legacy basic auth for Exchange Online.",
        A, "2025-07-10", "0x80070005")))
    docs.append(("KB0002.md", kedb("KB0002", "VPN client fails with error ERR_VPN_809 on home broadband",
        "vpn", "The Acme VPN client fails immediately with `ERR_VPN_809`. The user is on home broadband behind NAT.",
        "UDP ports 500/4500 for IPsec NAT traversal are blocked or NAT-T is disabled on the home router.",
        "Enable NAT-T in the VPN client settings, allow UDP 500 and 4500 on the router, then reconnect.",
        "Roll out the Always-On VPN profile v3 which falls back to SSTP when IPsec is blocked.",
        A, "2025-06-20", "ERR_VPN_809")))
    docs.append(("KB0003.md", kedb("KB0003", "Shop-floor handhelds drop WiFi near freezers",
        "wifi", "Handheld scanners disconnect every few minutes in the freezer aisle of Acme stores.",
        "2.4 GHz interference plus aggressive roaming on old handheld firmware.",
        "Set handhelds to prefer 5 GHz, update to firmware 4.2.1, and raise roam threshold to -70 dBm.",
        "Replace freezer-aisle APs with directional antennas per the store refresh plan.", A, "2025-04-11")))
    docs.append(("KB0004.md", kedb("KB0004", "Till receipt printer shows spooler error 0x0000011b",
        "printer", "Windows till prints fail with spooler error `0x0000011b` after the monthly patch.",
        "Hardened UNC print behaviour from the security patch blocks the shared till printer path.",
        "On the till, add the print server DWORD `RpcAuthnLevelPrivacyEnabled=0`, restart spooler, re-add the printer.",
        "Migrate till printers to the Type-4 driver queue which does not need the registry workaround.",
        A, "2025-08-02", "0x0000011b")))
    docs.append(("KB0005.md", kedb("KB0005", "AD account locks after three bad logins at POS",
        "iam", "Cashiers get locked out after exactly three wrong PIN attempts at the POS login.",
        "The Acme POS account lockout policy is set to 3 attempts with a 15-minute reset window.",
        "Unlock in AD Users and Computers, confirm the cashier uses the current 6-digit PIN, wait 15 minutes if it relocks.",
        "Move POS logins to the self-service PIN reset kiosk to cut service-desk unlock tickets.", A, "2025-03-15")))
    docs.append(("KB0006.md", kedb("KB0006", "Laptop asks for BitLocker recovery key after BIOS update",
        "laptop", "After an overnight BIOS update, the laptop boots to a blue BitLocker recovery screen.",
        "The BIOS update changed the measured boot values so the TPM no longer unseals the key.",
        "Fetch the 48-digit recovery key from the Acme device portal, enter it once, then suspend and resume BitLocker.",
        "Enable the BIOS-update BitLocker suspend task in the patch baseline before firmware pushes.",
        A, "2025-05-22", "BITLK-48")))
    # Conflicting pair 1: shared mailbox cached mode
    docs.append(("KB0007.md", kedb("KB0007", "Shared mailbox sync is slow in Outlook ( guidance A )",
        "outlook", "A shared info@ mailbox with 50k items syncs very slowly and search misses recent mail.",
        "Cached Exchange Mode downloads the whole shared mailbox to a small OST.",
        "Disable Cached Exchange Mode for shared mailboxes: File > Account Settings > More Settings > Advanced > uncheck Download shared folders.",
        "Apply the Acme Outlook GPO 'SharedMail-NoCache' to all tills-office PCs.",
        A, "2025-02-10")))
    docs.append(("KB0008.md", kedb("KB0008", "Shared mailbox sync is slow in Outlook ( guidance B )",
        "outlook", "A shared info@ mailbox with 50k items syncs very slowly and search misses recent mail.",
        "Online mode for a large shared mailbox hammers the server on every search.",
        "Keep Cached Exchange Mode ON and set cache to 3 months: File > Account Settings > More Settings > keep Download shared folders checked. Do NOT disable cached mode.",
        "Apply the Acme Outlook GPO 'SharedMail-Cache3Months' instead of disabling cache.",
        A, "2025-06-30")))
    docs.append(("KB0009.md", kedb("KB0009", "SharePoint sync stuck on 'Processing changes' for 2 hours",
        "sharepoint", "OneDrive/SharePoint client is stuck on 'Processing changes' with 0 bytes synced.",
        "A file with a `#` character plus a 260+ char path blocks the sync queue.",
        "Pause sync, rename the file to remove `#`, shorten the path under 200 chars, resume sync.",
        "Enable the long-paths GPO and the illegal-character guard in the Acme 365 baseline.", A, "2025-07-01")))
    docs.append(("KB0010.md", kedb("KB0010", "Teams microphone not working on till-office headset",
        "laptop", "Teams shows no input level on the Jabra headset, but Windows Sound Recorder works.",
        "Teams is using the laptop mic while the headset is set as default only in Windows, not in Teams.",
        "In Teams > Settings > Devices set the Jabra as Microphone and Speaker, then rejoin the call.",
        "Pin the headset device ID via the Acme Teams device policy.", A, "2025-01-20")))
    # Near-dup pair: POS paper jam
    docs.append(("KB0011.md", kedb("KB0011", "POS receipt printer paper jam E-POS-03 (variant 1)",
        "pos", "The Epson receipt printer flashes red and shows jam E-POS-03 mid-receipt.",
        "Receipt roll is misaligned and a torn fragment covers the feed sensor.",
        "Power off the printer, open the cover, remove the roll, clear fragments with tweezers, reload with the glossy side out, feed 10 cm.",
        "Replace worn feed rollers quarterly on high-volume tills.",
        A, "2025-04-02", "E-POS-03")))
    docs.append(("KB0012.md", kedb("KB0012", "POS receipt printer paper jam E-POS-03 (variant 2)",
        "pos", "The Epson receipt printer blinks red and reports jam code E-POS-03 while printing a receipt.",
        "The receipt roll sits crooked and a small torn piece blocks the paper sensor.",
        "Switch the printer off, lift the cover, take out the roll, pick out fragments using tweezers, refit with glossy side outward, advance 10 cm.",
        "Swap feed rollers every quarter on busy tills.",
        A, "2025-04-03", "E-POS-03")))
    docs.append(("KB0013.md", kedb("KB0013", "SAP retail login loops back to the logon screen",
        "iam", "Entering correct SAP credentials just returns to the logon screen with no error.",
        "An expired temporary password plus a locked SAP user flag combine into a silent loop.",
        "Unlock the SAP user in SU01, issue a one-time password, and clear the browser SSO cache.",
        "Connect SAP IDM to the joiner-mover-leaver feed so passwords never go stale.", A, "2025-03-28")))
    docs.append(("KB0014.md", kedb("KB0014", "Badge reader denies entry with green blink pattern 3-1",
        "iam", "The stockroom badge reader blinks green 3-1 and denies entry for a valid badge.",
        "The badge lost its stockroom access group after a department transfer.",
        "Re-add the stockroom group in the badge portal and ask the user to tap twice after 5 minutes.",
        "Automate group updates from the HR transfer feed.", A, "2025-02-14", "BDG-31")))
    # Conflicting pair 2: VPN split-tunnel DNS
    docs.append(("KB0015.md", kedb("KB0015", "VPN split-tunnel DNS for store systems (guidance A)",
        "vpn", "Over VPN, store intranet names fail but internet works.",
        "Split-tunnel DNS sends only `*.acme.internal` to the corporate resolver.",
        "Force ALL DNS over VPN: set the client DNS mode to tunnel-all so every lookup uses 10.20.0.53.",
        "Push profile v4 with tunnel-all DNS as the default.", A, "2025-01-30")))
    docs.append(("KB0016.md", kedb("KB0016", "VPN split-tunnel DNS for store systems (guidance B)",
        "vpn", "Over VPN, store intranet names fail but internet works.",
        "Tunnel-all DNS overloads the corporate resolver and breaks guest WiFi captive portals.",
        "Keep split-tunnel DNS and add `*.acme.internal` plus `till.acme.internal` to the allow list. Do NOT force tunnel-all DNS.",
        "Push profile v5 with the extended split-DNS allow list.", A, "2025-08-10")))
    docs.append(("KB0017.md", kedb("KB0017", "Outlook search returns no results for last week",
        "outlook", "Outlook search shows nothing newer than 7 days although new mail arrives.",
        "The search index is corrupt after a forced shutdown.",
        "Rebuild the index: File > Options > Search > Indexing Options > Advanced > Rebuild, then wait 30 minutes.",
        "Enable the weekly index-health scheduled task.", A, "2025-05-05")))
    docs.append(("KB0018.md", kedb("KB0018", "WiFi captive portal loops on customer tablets",
        "wifi", "Customer tablets loop on the guest portal accept page without getting online.",
        "The portal cookie domain does not match the new guest gateway hostname.",
        "Clear the tablet browser cache, open `http://portal.acme.local`, accept, and re-authenticate.",
        "Fix the portal certificate SAN to include the new gateway name.", A, "2025-06-15")))
    docs.append(("KB0019.md", kedb("KB0019", "Laptop fan at 100 percent after VPN connect",
        "laptop", "CPU fan spins at full speed within a minute of connecting the VPN.",
        "The old VPN client 5.1 polls the firewall every 200 ms when DPD is on.",
        "Upgrade to VPN client 5.4 and set dead-peer-detection to 10 seconds.",
        "Block client versions below 5.4 at the gateway.", A, "2025-07-22")))
    docs.append(("KB0020.md", kedb("KB0020", "POS card reader declines contactless over 100",
        "pos", "Contactless payments over 100 are declined; chip and PIN works.",
        "The terminal contactless limit is still set to the old 45 default.",
        "In the terminal menu set contactless CVM limit to 100, reboot, run a 1.00 test transaction.",
        "Push the limit centrally from the payment estate manager.", A, "2025-03-10", "POS-CLESS-100")))
    docs.append(("KB0021.md", kedb("KB0021", "Email quarantine releases go to junk again",
        "outlook", "A released quarantine message arrives but jumps straight to Junk.",
        "The sender is on the user's blocked-senders list from an earlier phishing report.",
        "Remove the sender from Blocked Senders in Outlook > Junk > Junk Email Options, then release again.",
        "Tune the quarantine allow workflow to auto-remove one-time blocks.", A, "2025-08-15")))
    docs.append(("KB0022.md", kedb("KB0022", "Till screen freezes at 'Register closed' overnight",
        "pos", "The till app freezes on 'Register closed' and needs a hard reboot each morning.",
        "The overnight AV scan locks the till SQLite journal at 02:00.",
        "Exclude `C:\\AcmeTill\\data\\*.db-journal` from AV, restart the till service.",
        "Move the AV window to 04:00 outside the close-of-day job.", A, "2025-02-28")))
    docs.append(("KB0023.md", kedb("KB0023", "OneDrive 'signed out' loop after password change",
        "sharepoint", "After a password change, OneDrive signs out every 10 minutes.",
        "The old refresh token is cached in the Windows Web Account Manager.",
        "Remove the Work account in Settings > Accounts > Access work or school, re-add, then sign in to OneDrive.",
        "Enable Seamless SSO so password changes do not orphan tokens.", A, "2025-06-05")))
    docs.append(("KB0024.md", kedb("KB0024", "VPN drops every 60 minutes on the dot",
        "vpn", "The VPN disconnects exactly every 60 minutes and reconnects cleanly.",
        "The gateway SA lifetime is 60 minutes and rekey fails on double-NAT home routers.",
        "Set the client rekey margin to 5 minutes and enable keepalives every 30 seconds.",
        "Raise the gateway SA lifetime to 8 hours in the next change window.", A, "2025-04-25")))
    docs.append(("KB0025.md", kedb("KB0025", "New starter has no SAP access on day one",
        "iam", "A new starter can log into Windows but SAP shows 'no authorisation'.",
        "The HR feed created the AD account but the SAP role mapping job runs only at night.",
        "Assign the SAP base role manually in SU01 for day one; the nightly job reconciles after.",
        "Move SAP provisioning to the hourly JML micro-batch.", A, "2025-07-30")))
    docs.append(("KB0026.md", kedb("KB0026", " till barcode scanner types wrong characters",
        "pos", "The USB scanner types `é` instead of `/` in the till search box.",
        "The scanner is in French AZERTY layout while Windows uses UK English.",
        "Scan the 'Set UK layout' barcode from the scanner manual, then test in Notepad.",
        "Stock only pre-flashed UK-layout scanners in the spares cage.", A, "2025-05-18")))
    docs.append(("KB0027.md", kedb("KB0027", "Outlook out-of-office replies twice to the same sender",
        "outlook", "External senders get two out-of-office replies for one message.",
        "Both a server-side OOF and a client-side inbox rule reply at once.",
        "Turn off the client rule 'Reply with OOF template' and keep only the server automatic replies.",
        "Audit OOF rules with the monthly mailbox hygiene script.", A, "2025-01-12")))
    docs.append(("KB0028.md", kedb("KB0028", "Store printer prints blank pages from the back-office PC",
        "printer", "The back-office laser printer feeds pages but they come out blank.",
        "The toner cartridge seal tape was never removed during install.",
        "Reseat the toner, pull the orange seal tape fully out, print a test page.",
        "Add 'remove seal tape' photo step to the printer install SOP.", A, "2025-03-05")))
    # Retired pair
    docs.append(("KB0029.md", kedb("KB0029", "Windows 7 till cannot join the new WiFi (RETIRED)",
        "wifi", "Windows 7 tills cannot see the new WPA3 store SSID.",
        "Windows 7 does not support WPA3-SAE.",
        "RETIRED: keep a WPA2 legacy SSID per store (removed March 2024). Do not use for new builds.",
        "RETIRED: replaced by the Windows 11 till refresh; see KB0003 for current WiFi guidance.",
        "retired", "2023-11-01")))
    docs.append(("KB0030.md", kedb("KB0030", "Lotus Notes archive access for old payslips (RETIRED)",
        "iam", "Staff ask for payslips from the retired Lotus Notes archive.",
        "Lotus Notes was decommissioned in 2023; archives moved to SharePoint vault.",
        "RETIRED: open the Notes client on ARCHIVE-PC-01 (decommissioned). Do not follow this path.",
        "RETIRED: use the SharePoint vault; see SOP-SHR-01 for access requests.",
        "retired", "2023-12-15")))
    return docs


def build_sops() -> list[tuple[str, str]]:
    sops: list[tuple[str, str]] = []
    sops.append(("SOP-VPN-01.md", sop("SOP-VPN-01", "VPN access provisioning for new starters",
        "vpn", "Grant a new starter corporate VPN access on day one.",
        "1. Confirm the AD account is active.\n2. Add the user to group `SG-VPN-Users`.\n3. Assign the Always-On profile v3.\n4. Ask the user to connect once on-site before working from home.",
        "If the gateway rejects the login with `ERR_VPN_809`, follow KB0002 then re-raise to NetOps.")))
    sops.append(("SOP-IAM-01.md", sop("SOP-IAM-01", "Joiner-mover-leaver account provisioning",
        "iam", "Process HR joiner, mover, and leaver events within one business day.",
        "1. Pull the daily HR feed at 07:00.\n2. Create AD + mailbox for joiners.\n3. Adjust groups for movers the same day.\n4. Disable leavers within 1 hour of exit time.",
        "If SAP roles are missing on day one, apply the KB0025 manual step, then inform IAM Ops.")))
    sops.append(("SOP-PRT-01.md", sop("SOP-PRT-01", "Replace till-area printer toner safely",
        "printer", "Replace toner without dirtying stock or triggering the fire alarm.",
        "1. Put the printer in maintenance mode.\n2. Remove the old cartridge into the bag.\n3. Shake the new cartridge 5 times, remove the seal tape.\n4. Insert, print a test page, log the swap.",
        "If pages print blank after a swap, follow KB0028 before logging a hardware call.")))
    sops.append(("SOP-POS-01.md", sop("SOP-POS-01", "POS end-of-day reconciliation",
        "pos", "Close each till and reconcile card totals before midnight.",
        "1. Run 'Close register' on every till.\n2. Compare the Z-report card total to the estate manager.\n3. If they differ by more than 1.00, recount cash and reprint.\n4. File the Z-report in the safe log.",
        "If the till freezes at 'Register closed', follow KB0022, then escalate to Store Systems.")))
    sops.append(("SOP-OUT-01.md", sop("SOP-OUT-01", "Outlook mailbox delegation for assistants",
        "outlook", "Let an assistant manage a manager mailbox with audit trail.",
        "1. Manager approves in the access portal.\n2. Grant FullAccess + SendAs via Exchange Admin.\n3. Assistant restarts Outlook and opens the extra mailbox.\n4. Log the grant in the access register.",
        "If the shared mailbox sync is slow, compare KB0007 and KB0008 — they conflict; raise to Messaging.")))
    sops.append(("SOP-WIFI-01.md", sop("SOP-WIFI-01", "Issue guest WiFi vouchers at the till",
        "wifi", "Give shoppers a 2-hour guest WiFi voucher on request.",
        "1. Open the voucher portal on the till.\n2. Generate a 2-hour code.\n3. Print the slip and hand it over.\n4. Log the issue count at close.",
        "If the portal loops, follow KB0018, then call NetOps if still broken.")))
    sops.append(("SOP-LAP-01.md", sop("SOP-LAP-01", "Reimage a store laptop from USB",
        "laptop", "Rebuild a faulty store laptop to the gold image.",
        "1. Back up `C:\\Users` to the NAS.\n2. Boot the gold USB and run the Acme image.\n3. Join the domain, install the VPN client 5.4.\n4. Return BitLocker key in the device portal (see KB0006).",
        "If BitLocker recovery appears, fetch the key per KB0006; escalate to EUC if the TPM fails.")))
    sops.append(("SOP-SHR-01.md", sop("SOP-SHR-01", "SharePoint leaver-vault access requests",
        "sharepoint", "Handle requests for archived payslips and leaver files.",
        "1. Verify the requester identity with two factors.\n2. Check the vault index for the file.\n3. Grant time-boxed read access for 7 days.\n4. Revoke and log the grant.",
        "Do NOT use the retired Notes path in KB0030; the SharePoint vault is the only source.")))
    return sops


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/corpus")
    args = parser.parse_args()
    out = Path(args.out)
    (out / "kedb").mkdir(parents=True, exist_ok=True)
    (out / "sop").mkdir(parents=True, exist_ok=True)
    for name, body in build_kedb():
        (out / "kedb" / name).write_text(body, encoding="utf-8")
    for name, body in build_sops():
        (out / "sop" / name).write_text(body, encoding="utf-8")
    n_kb = len(build_kedb())
    n_sop = len(build_sops())
    print(f"Wrote {n_kb} KEDB + {n_sop} SOP docs to {out}")


if __name__ == "__main__":
    main()
