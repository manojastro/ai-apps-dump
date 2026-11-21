"""Northstar Global Technologies - fictitious enterprise used for the simulated environment.

Everything here is SYNTHETIC (company, hosts, teams, IPs, users). Vulnerability data is real
public data from the bundled NVD/KEV/EPSS snapshot. The software inventory is designed so the
simulated Defender scan yields exactly 75 findings across 20 CVEs, including the demo
scenarios (see docs/DEMO.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DOMAIN = "northstar.example"  # RFC 2606 reserved domain

# key: (cpe vendor, cpe product, display name, safe version, sw_edition)
PACKAGES: dict[str, tuple[str, str, str, str, str | None]] = {
    "log4j": ("apache", "log4j", "Apache Log4j", "2.17.1", None),
    "spring": ("vmware", "spring_framework", "Spring Framework", "5.3.39", None),
    "httpd": ("apache", "http_server", "Apache HTTP Server", "2.4.62", None),
    "openssh": ("openbsd", "openssh", "OpenSSH", "9.8p1", None),
    "activemq": ("apache", "activemq", "Apache ActiveMQ", "5.18.6", None),
    "confluence": ("atlassian", "confluence_data_center", "Confluence Data Center", "8.5.4", None),
    "kernel": ("linux", "linux_kernel", "Linux kernel", "6.8.0", None),
    "polkit": ("polkit_project", "polkit", "polkit", "124", None),
    "libcurl": ("haxx", "libcurl", "libcurl", "8.10.1", None),
    "commons_text": ("apache", "commons_text", "Apache Commons Text", "1.10.0", None),
    "winrar": ("rarlab", "winrar", "WinRAR", "7.01", None),
    "7zip": ("7-zip", "7-zip", "7-Zip", "24.09", None),
    "jenkins": ("jenkins", "jenkins", "Jenkins LTS", "2.426.3", "lts"),
    "chrome": ("google", "chrome", "Google Chrome", "130.0.6723.92", None),
    "openssl": ("openssl", "openssl", "OpenSSL", "3.0.15", None),
    "teamcity": ("jetbrains", "teamcity", "JetBrains TeamCity", "2023.11.4", None),
    "zlib": ("zlib", "zlib", "zlib", "1.3.1", None),
    "libexpat": ("libexpat_project", "libexpat", "libexpat", "2.6.3", None),
    "xz": ("tukaani", "xz", "XZ Utils", "5.4.6", None),
}

LINUX_BASE = ["openssh", "openssl", "libcurl", "kernel", "polkit", "zlib", "libexpat", "xz"]
WINDOWS_SERVER_BASE = ["7zip"]
WORKSTATION_BASE = ["chrome", "7zip"]

SERVICES = {
    "pay": (
        "Payment Processing",
        "Financial Services",
        "1 - most critical",
        "Payments Platform Team",
        "Card and wallet payment authorisation",
    ),
    "ledger": (
        "Core Banking Ledger",
        "Financial Services",
        "1 - most critical",
        "Ledger Engineering",
        "General ledger and reconciliation",
    ),
    "store": ("Online Storefront", "E-commerce", "1 - most critical", "Digital Commerce Team", "Customer-facing web shop"),
    "order": ("Order Fulfillment", "E-commerce", "2 - somewhat critical", "Fulfillment Systems", "Order routing and EDI"),
    "idp": ("Customer Identity & SSO", "E-commerce", "1 - most critical", "Identity Platform Team", "Customer login and SSO"),
    "mes": (
        "Manufacturing Execution System",
        "Manufacturing",
        "2 - somewhat critical",
        "Plant Systems Team",
        "Shop-floor execution and ERP integration",
    ),
    "scm": ("Supply Chain Portal", "Manufacturing", "3 - less critical", "Supply Chain Apps", "Supplier collaboration portal"),
    "collab": (
        "Employee Collaboration",
        "Internal Applications",
        "3 - less critical",
        "Workplace Technology",
        "Wiki, chat and file services",
    ),
    "ci": (
        "CI/CD Platform",
        "Cloud Infrastructure",
        "2 - somewhat critical",
        "Developer Platform Team",
        "Build and release pipelines",
    ),
    "mq": (
        "Messaging Backbone",
        "Cloud Infrastructure",
        "2 - somewhat critical",
        "Integration Platform Team",
        "Shared message brokers used by many business services",
    ),
}
SUBDOMAIN = {
    "pay": "fin",
    "ledger": "fin",
    "store": "shop",
    "order": "shop",
    "idp": "shop",
    "mes": "mfg",
    "scm": "mfg",
    "collab": "corp",
    "ci": "cloud",
    "mq": "cloud",
    None: "corp",
}
OCTET = {
    "pay": 10,
    "ledger": 11,
    "store": 20,
    "order": 21,
    "idp": 22,
    "mes": 40,
    "scm": 41,
    "collab": 50,
    "ci": 60,
    "mq": 61,
    None: 70,
}
CRIT = {
    "critical": "1 - most critical",
    "high": "2 - somewhat critical",
    "medium": "3 - less critical",
    "low": "4 - not critical",
}


@dataclass
class Host:
    hostname: str
    service: str | None
    env: str
    criticality: str
    internet: bool | None
    platform: str  # linux | windows_server | workstation
    vulns: list[tuple[str, str]] = field(default_factory=list)
    cloud: str | None = None
    defender: bool = True
    owner: str | None = "default"
    operational: str = "1"
    fqdn_override: str | None = None
    ip_override: str | None = None


H = Host
HOSTS: list[Host] = [
    # Payment Processing
    H("pay-api-01", "pay", "production", "critical", True, "linux", [("log4j", "2.14.1"), ("openssh", "8.9p1")], cloud="aws"),
    H("pay-api-02", "pay", "production", "critical", True, "linux", [("log4j", "2.14.1")], cloud="aws"),
    H("pay-db-01", "pay", "production", "critical", False, "linux", [("kernel", "5.15.19"), ("polkit", "0.120")]),
    H("pay-gw-01", "pay", "production", "critical", True, "linux", [("httpd", "2.4.49"), ("openssl", "3.0.2")]),
    H("pay-batch-01", "pay", "production", "high", False, "linux", [("commons_text", "1.9")]),
    H("pay-api-stg-01", "pay", "staging", "medium", False, "linux", [("spring", "5.3.17")], cloud="aws"),
    H("pay-api-dev-01", "pay", "development", "low", False, "linux", cloud="aws"),
    H("pay-hsm-proxy-01", "pay", "production", "critical", False, "linux", [("openssh", "8.4p1")]),
    # Core Banking Ledger
    H("ledger-app-01", "ledger", "production", "critical", False, "linux", [("spring", "5.3.17")]),
    H("ledger-app-02", "ledger", "production", "critical", False, "linux", [("spring", "5.3.17")]),
    H("ledger-db-01", "ledger", "production", "critical", False, "linux", [("kernel", "5.15.19")]),
    H("ledger-db-02", "ledger", "production", "critical", False, "linux", [("polkit", "0.120")]),
    H("ledger-recon-01", "ledger", "production", "high", False, "linux", [("commons_text", "1.9")]),
    H("ledger-api-01", "ledger", "production", "critical", True, "linux", [("openssh", "8.9p1")]),
    H("ledger-stg-01", "ledger", "staging", "medium", False, "linux", [("libexpat", "2.5.0")]),
    H("ledger-dev-01", "ledger", "development", "low", False, "linux"),
    # Online Storefront
    H("store-web-01", "store", "production", "critical", True, "linux", [("httpd", "2.4.49")], cloud="azure"),
    H("store-web-02", "store", "production", "critical", True, "linux", [("openssl", "3.0.2")], cloud="azure"),
    H("store-app-01", "store", "production", "critical", False, "linux", [("log4j", "2.14.1")], cloud="azure"),
    H("store-app-02", "store", "production", "critical", False, "linux", [("libcurl", "8.2.1")], cloud="azure"),
    H("store-cdn-origin-01", "store", "production", "high", True, "linux", [("openssh", "8.9p1")], cloud="azure"),
    H("store-search-01", "store", "production", "high", False, "linux", [("kernel", "5.15.19")]),
    H("store-stg-01", "store", "staging", "medium", False, "linux", [("zlib", "1.2.13")], cloud="azure"),
    H("store-dev-01", "store", "development", "low", False, "linux", cloud="azure"),
    # Order Fulfillment
    H("order-svc-01", "order", "production", "high", False, "linux", [("log4j", "2.14.1")]),
    H("order-svc-02", "order", "production", "high", False, "linux", [("libcurl", "8.2.1")]),
    H("order-db-01", "order", "production", "high", False, "linux", [("polkit", "0.120")]),
    H("order-worker-01", "order", "production", "high", False, "linux", [("commons_text", "1.9")]),
    H("order-api-01", "order", "production", "high", True, "linux", [("openssh", "8.9p1")]),
    H("order-stg-01", "order", "staging", "medium", False, "linux"),
    H("order-dev-01", "order", "development", "low", False, "linux"),
    H("order-edi-01", "order", "production", "high", True, "linux", [("openssl", "3.0.2")]),
    # Customer Identity & SSO
    H("idp-01", "idp", "production", "critical", True, "linux"),
    H("idp-02", "idp", "production", "critical", True, "linux", [("libcurl", "8.2.1")]),
    H("idp-db-01", "idp", "production", "critical", False, "linux", [("kernel", "5.15.19")]),
    H("idp-stg-01", "idp", "staging", "medium", False, "linux", [("libexpat", "2.5.0")]),
    H("idp-dev-01", "idp", "development", "low", False, "linux", defender=False),
    H("idp-ldap-01", "idp", "production", "critical", False, "linux", [("openssh", "8.4p1")]),
    # Manufacturing Execution System
    H("mes-app-01", "mes", "production", "high", False, "linux", [("log4j", "2.14.1")]),
    H("mes-app-02", "mes", "production", "high", False, "linux", [("spring", "5.3.17")]),
    H("mes-db-01", "mes", "production", "high", False, "linux", [("polkit", "0.120")]),
    H("mes-hmi-01", "mes", "production", "high", False, "windows_server", [("7zip", "23.01")]),
    # Two CMDB records share the hostname legacy-erp-01 (ambiguous-match scenario). The Defender
    # device for this host is created separately with a short name and an unrelated IP.
    H(
        "legacy-erp-01",
        "mes",
        "production",
        "high",
        False,
        "linux",
        defender=False,
        fqdn_override=f"legacy-erp-01.mfg.{DOMAIN}",
        ip_override="10.40.2.21",
    ),
    H(
        "legacy-erp-01",
        "mes",
        "test",
        "low",
        False,
        "linux",
        defender=False,
        operational="2",
        fqdn_override=f"legacy-erp-01.qa.{DOMAIN}",
        ip_override="10.90.2.21",
    ),
    H("mes-stg-01", "mes", "staging", "medium", False, "linux"),
    H("mes-historian-01", "mes", "production", "medium", False, "windows_server", [("winrar", "6.22")]),
    # Supply Chain Portal
    H("scm-portal-01", "scm", "production", "medium", True, "linux", [("openssh", "8.9p1")]),
    H("scm-portal-02", "scm", "production", "medium", True, "linux", [("xz", "5.6.1")]),
    H("scm-api-01", "scm", "production", "medium", False, "linux", [("libexpat", "2.5.0")], owner=None),
    H("scm-db-01", "scm", "production", "medium", False, "linux", [("kernel", "5.15.19")]),
    H("scm-dev-01", "scm", "development", "low", False, "linux", [("xz", "5.6.1")]),
    H("scm-stg-01", "scm", "staging", "medium", False, "linux"),
    # Employee Collaboration
    H("collab-wiki-01", "collab", "production", "medium", True, "linux", [("confluence", "8.5.1")]),
    H("collab-wiki-stg-01", "collab", "staging", "low", False, "linux", [("confluence", "8.5.1")]),
    H("collab-chat-01", "collab", "production", "medium", False, "linux", [("zlib", "1.2.13")]),
    H("collab-files-01", "collab", "production", "medium", False, "windows_server", [("winrar", "6.22")]),
    # Endpoints (no business service)
    H("ws-fin-0142", None, "production", "medium", False, "workstation", [("winrar", "6.22"), ("chrome", "115.0.5790.170")]),
    H("ws-fin-0157", None, "production", "medium", False, "workstation", [("7zip", "23.01"), ("chrome", "115.0.5790.170")]),
    H("ws-eng-0311", None, "production", "medium", False, "workstation", [("7zip", "23.01"), ("winrar", "6.22")]),
    H("ws-eng-0318", None, "production", "medium", False, "workstation", [("chrome", "115.0.5790.170")]),
    H("ws-hr-0207", None, "production", "medium", False, "workstation", [("7zip", "23.01")]),
    H("ws-ops-0099", None, "production", "medium", False, "workstation"),
    H("ws-mfg-0420", None, "production", "medium", False, "workstation"),
    H("ws-exec-0003", None, "production", "high", False, "workstation"),
    # CI/CD Platform
    H("ci-jenkins-01", "ci", "production", "high", False, "linux", [("jenkins", "2.426.2")]),
    H("ci-jenkins-02", "ci", "production", "high", False, "linux", [("jenkins", "2.426.2")]),
    H("ci-teamcity-01", "ci", "production", "high", True, "linux", [("teamcity", "2023.11.3")]),
    H("ci-runner-01", "ci", "production", "medium", False, "linux", [("libcurl", "8.2.1")]),
    H("ci-artifact-01", "ci", "production", "high", False, "linux"),
    H("ci-runner-02", "ci", "production", "medium", False, "linux"),
    # Messaging Backbone
    H("mq-broker-01", "mq", "production", "high", False, "linux", [("activemq", "5.17.5")]),
    H("mq-broker-02", "mq", "production", "high", False, "linux", [("activemq", "5.17.5")]),
    H("mq-dev-01", "mq", "development", "low", False, "linux", [("activemq", "5.17.5")]),
    H("mq-monitor-01", "mq", "production", "medium", False, "linux", [("openssh", "8.9p1")]),
    H("kafka-01", "mq", "production", "high", False, "linux"),
    H("kafka-02", "mq", "production", "high", False, "linux"),
    # Shared infrastructure
    H("bastion-01", None, "production", "high", True, "linux", [("openssh", "8.4p1")]),
    H("dev-sandbox-02", None, "development", "low", False, "linux", [("log4j", "2.14.1")]),
    H("dev-sandbox-07", None, "development", "low", False, "linux", [("zlib", "1.2.13")]),
    H("monitoring-01", None, "production", "medium", False, "linux"),
    H("monitoring-02", None, "production", "medium", False, "linux"),
    H("log-collector-01", None, "production", "medium", False, "linux"),
    H("backup-01", None, "production", "high", False, "linux"),
    H("dns-01", None, "production", "high", False, "linux", defender=False),
    H("dns-02", None, "production", "high", False, "linux", defender=False),
    H("ntp-01", None, "production", "low", False, "linux", defender=False),
    H("jump-02", None, "production", "medium", False, "linux"),
    H("vault-01", None, "production", "critical", False, "linux"),
    H("proxy-01", None, "production", "high", True, "linux"),
    H("mail-relay-01", None, "production", "medium", True, "linux"),
    H("k8s-node-01", None, "production", "high", False, "linux", cloud="aws"),
    H("k8s-node-02", None, "production", "high", False, "linux", cloud="aws"),
    H("k8s-node-03", None, "production", "high", False, "linux", cloud="aws"),
    H("win-dc-01", None, "production", "critical", False, "windows_server"),
    H("win-dc-02", None, "production", "critical", False, "windows_server"),
    H("win-file-01", None, "production", "medium", False, "windows_server"),
    H("print-01", None, "production", "low", False, "windows_server", defender=False),
    H("dev-sandbox-03", None, "development", "low", False, "linux"),
    H("qa-perf-01", None, "test", "low", False, "linux"),
    H("qa-auto-01", None, "test", "low", None, "linux", defender=False),  # exposure unknown in CMDB
]

# Devices visible to Defender but not cleanly represented in the CMDB.
EXTRA_DEVICES: list[dict[str, Any]] = [
    # Ambiguous: short hostname matches two CMDB records; IP matches neither.
    {"name": "legacy-erp-01", "platform": "linux", "ip": "10.40.9.15", "vulns": [("httpd", "2.4.49")]},
    # Unmatched: shadow-IT kiosk not registered in the CMDB.
    {"name": "kiosk-lobby-03", "platform": "workstation", "ip": "10.80.1.33", "vulns": [("chrome", "115.0.5790.170")]},
]

# (parent depends on child) - mirrored into cmdb_rel_ci
DEPENDENCIES = [
    ("pay-api-01", "mq-broker-01"),
    ("pay-api-02", "mq-broker-02"),
    ("order-svc-01", "mq-broker-01"),
    ("order-svc-02", "mq-broker-02"),
    ("store-app-01", "mq-broker-01"),
    ("store-app-02", "mq-broker-02"),
    ("ledger-recon-01", "mq-broker-01"),
    ("pay-api-01", "pay-db-01"),
    ("pay-api-02", "pay-db-01"),
    ("pay-gw-01", "pay-api-01"),
    ("pay-gw-01", "pay-api-02"),
    ("pay-api-01", "pay-hsm-proxy-01"),
    ("store-web-01", "store-app-01"),
    ("store-web-02", "store-app-02"),
    ("store-app-01", "idp-01"),
    ("store-app-02", "idp-02"),
    ("store-app-01", "store-search-01"),
    ("ledger-app-01", "ledger-db-01"),
    ("ledger-app-02", "ledger-db-02"),
    ("ledger-api-01", "ledger-app-01"),
    ("order-svc-01", "order-db-01"),
    ("order-api-01", "order-svc-01"),
    ("order-edi-01", "order-svc-02"),
    ("idp-01", "idp-db-01"),
    ("idp-02", "idp-db-01"),
    ("idp-01", "idp-ldap-01"),
    ("idp-02", "idp-ldap-01"),
    ("mes-app-01", "mes-db-01"),
    ("mes-app-02", "mes-db-01"),
    ("scm-portal-01", "scm-api-01"),
    ("scm-api-01", "scm-db-01"),
    ("ci-jenkins-01", "ci-artifact-01"),
    ("ci-jenkins-02", "ci-artifact-01"),
    ("collab-wiki-01", "idp-01"),
    ("order-worker-01", "mq-broker-02"),
    ("mes-app-01", "mq-broker-01"),
]

DEMO_USERS = [
    ("admin@northstar.example", "Morgan Reyes", "admin"),
    ("analyst@northstar.example", "Sam Patel", "analyst"),
    ("analyst2@northstar.example", "Taylor Brooks", "analyst"),
    ("approver@northstar.example", "Jordan Kim", "approver"),
    ("approver2@northstar.example", "Casey Nguyen", "approver"),
    ("viewer@northstar.example", "Drew Walsh", "viewer"),
]
DEV_ONLY_PASSWORD = "AegisDemo!2026"  # development-only; seeding refuses to use it in production
