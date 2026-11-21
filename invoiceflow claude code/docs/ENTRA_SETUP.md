# Microsoft Entra ID setup for the approval service (prepared, not executed)

Nothing in this repository creates Entra ID objects. These are the steps for whoever owns
the tenant; creating them is an external action that needs Manoj's approval (CLAUDE.md
rule 5).

## 1. Register the API

1. Microsoft Entra admin center → App registrations → New registration.
   Name: `invoiceflow-approvals-api`; single tenant.
2. Expose an API → set the Application ID URI, for example `api://invoiceflow-approvals`.
   This is `OIDC_AUDIENCE`.
3. App roles → create these roles (allowed member types: Users/Groups):

| Display name | Value | Maps to |
|---|---|---|
| AP Clerk | `AP.Clerk` | AP_CLERK |
| AP Manager | `AP.Manager` | AP_MANAGER |
| Finance Controller | `Finance.Controller` | FINANCE_CONTROLLER |
| AP Auditor | `AP.Auditor` | AUDITOR (read-only) |
| Platform Admin | `Platform.Admin` | PLATFORM_ADMIN (cannot decide cases) |

## 2. Assign users

Enterprise applications → `invoiceflow-approvals-api` → Users and groups → assign each
synthetic test user one role. Use test accounts only.

## 3. Register the client (the inbox)

Register a second app (SPA or web) that requests the API scope. Users sign in there; the
inbox sends the access token as `Authorization: Bearer …`.

## 4. Configure InvoiceFlow

```bash
APPROVALS_AUTH=oidc
OIDC_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0
OIDC_AUDIENCE=api://invoiceflow-approvals
OIDC_JWKS_URL=https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys
```

`OidcAuth` validates the RS256 signature against the JWKS, the issuer, the audience and the
expiry. It reads `roles` for the app role and `oid` for the user id.

## What is tested without a tenant

`tests/unit/services/test_approvals_service.py` signs tokens with a locally generated RSA
key and checks five things: valid tokens map to roles; and a wrong audience, an expired
token, a token with no app role, or one signed by the wrong key are all rejected.

Verify the claim names against current Microsoft documentation before going live (rule 11).
