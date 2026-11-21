<!-- allowed_roles: employee, it, support -->
# Runbook: VPN Stale Token After Password Change

## Symptom
VPN fails to connect right after a password change while identity and
MFA stay healthy. The secure-access client holds a stale cached token.

## Evidence
Entra shows a successful password reset plus healthy sign-in and MFA.
Zscaler reports VPN down with a stale-token error while network path,
DNS, and proxy stay healthy.

## Remediation
Reconnect the VPN client with the new password to refresh the token
(approved reconnect action). Verify VPN up plus healthy sign-in after.
