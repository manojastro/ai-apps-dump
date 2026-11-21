from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


SERVICES: list[dict[str, Any]] = [
    {"id": "storefront", "kind": "service", "team": "web-platform", "port": 9101},
    {"id": "checkout-api", "kind": "service", "team": "checkout", "port": 9102},
    {"id": "payment-api", "kind": "service", "team": "payments", "port": 9103},
    {"id": "auth-service", "kind": "service", "team": "identity", "port": 9104},
    {"id": "orders-db", "kind": "database", "team": "data-platform", "port": 9105},
]

DEPENDENCIES: list[dict[str, str]] = [
    {"source": "storefront", "target": "checkout-api", "type": "calls"},
    {"source": "storefront", "target": "auth-service", "type": "calls"},
    {"source": "checkout-api", "target": "payment-api", "type": "calls"},
    {"source": "checkout-api", "target": "auth-service", "type": "calls"},
    {"source": "checkout-api", "target": "orders-db", "type": "queries"},
]


SCENARIOS: dict[str, dict[str, Any]] = {
    "bad-deployment": {
        "title": "Checkout errors after v2.4.0 deployment",
        "service": "checkout-api",
        "category": "deployment",
        "component": "checkout-api",
        "impact": "Checkout requests returned HTTP 500 for a subset of customers.",
        "observations": {
            "metrics": [
                ("checkout-api", "http_5xx_rate rose from 0.3% to 18.7%", True, "error_rate"),
                ("payment-api", "p95 latency remained within its 210 ms baseline", False, "latency"),
            ],
            "logs": [
                ("checkout-api", "NullPointerException in DiscountMapper for POST /checkout", True, "error"),
                ("checkout-api", "rollback completed; HTTP 5xx returned to 0.4%", True, "recovery"),
            ],
            "changes": [
                ("checkout-api", "deployed checkout-api v2.4.0 with DiscountMapper refactor", True, "deploy"),
            ],
            "tickets": [
                ("payment-api", "INC-771: prior checkout errors were caused by payment timeouts", False, "history"),
            ],
        },
    },
    "dependency-latency": {
        "title": "Checkout latency caused by payment provider slowdown",
        "service": "checkout-api",
        "category": "dependency",
        "component": "payment-api",
        "impact": "Checkout completion was delayed and some requests timed out.",
        "observations": {
            "metrics": [
                ("checkout-api", "p95 latency increased from 320 ms to 4.8 s", True, "latency"),
                ("payment-api", "upstream provider p95 latency increased to 4.4 s", True, "latency"),
            ],
            "logs": [
                ("checkout-api", "payment-api request exceeded 3000 ms timeout", True, "timeout"),
                ("auth-service", "token validation p95 remained at 38 ms", False, "latency"),
            ],
            "changes": [
                ("storefront", "deployed static CSS bundle v8.1.2", False, "deploy"),
            ],
            "tickets": [
                ("payment-api", "PROV-19: provider status reported regional latency", True, "provider"),
            ],
        },
    },
    "db-connection-exhaustion": {
        "title": "Orders database connection pool exhausted",
        "service": "checkout-api",
        "category": "database",
        "component": "orders-db",
        "impact": "Order creation timed out while read-only storefront traffic remained healthy.",
        "observations": {
            "metrics": [
                ("orders-db", "active_connections reached max_connections=100", True, "connections"),
                ("checkout-api", "database wait time rose to 8.2 s", True, "latency"),
            ],
            "logs": [
                ("checkout-api", "sql pool acquisition timeout after 5000 ms", True, "pool"),
                ("orders-db", "remaining connection slots are reserved", True, "pool"),
            ],
            "changes": [
                ("checkout-api", "worker concurrency increased from 20 to 80", True, "config"),
            ],
            "tickets": [
                ("orders-db", "INC-601: connection leak fixed in checkout worker", True, "history"),
            ],
        },
    },
    "cpu-saturation": {
        "title": "Inventory workload saturated checkout CPU",
        "service": "checkout-api",
        "category": "resource",
        "component": "checkout-api",
        "impact": "Checkout API responses slowed during a sustained inventory reconciliation job.",
        "observations": {
            "metrics": [
                ("checkout-api", "CPU utilization sustained at 97% for 14 minutes", True, "cpu"),
                ("checkout-api", "memory utilization stayed at 61%", False, "memory"),
            ],
            "logs": [
                ("checkout-api", "inventory reconciliation batch consumed all four worker cores", True, "workload"),
                ("checkout-api", "no out-of-memory or database timeout events observed", False, "negative"),
            ],
            "changes": [
                ("checkout-api", "inventory reconciliation interval changed from hourly to every minute", True, "config"),
            ],
            "tickets": [
                ("checkout-api", "CHG-88 requested high-frequency inventory reconciliation for launch", True, "change"),
            ],
        },
    },
    "auth-config": {
        "title": "OIDC configuration change caused authentication failures",
        "service": "auth-service",
        "category": "configuration",
        "component": "auth-service",
        "impact": "Users with newly issued tokens could not sign in or begin checkout.",
        "observations": {
            "metrics": [
                ("auth-service", "authentication failure rate increased from 0.8% to 43%", True, "auth"),
                ("auth-service", "CPU and memory remained below 45%", False, "resource"),
            ],
            "logs": [
                ("auth-service", "JWT issuer mismatch: expected login.internal, received login.example", True, "issuer"),
                ("storefront", "auth-service returned 401 for valid session renewal", True, "auth"),
            ],
            "changes": [
                ("auth-service", "OIDC_ISSUER changed from login.example to login.internal", True, "config"),
            ],
            "tickets": [
                ("auth-service", "IAM-42 documents the production issuer as login.example", True, "knowledge"),
            ],
        },
    },
    "misleading-signal": {
        "title": "Payment TLS failures hidden behind storefront CPU spike",
        "service": "storefront",
        "category": "dependency",
        "component": "payment-api",
        "impact": "Payment attempts failed although browsing and authentication remained available.",
        "force_initial_wrong": True,
        "observations": {
            "metrics": [
                ("storefront", "CPU utilization briefly peaked at 96%", False, "cpu"),
                ("payment-api", "TLS handshake failure rate reached 31% while latency stayed normal", True, "tls"),
            ],
            "logs": [
                ("storefront", "image optimization completed and CPU returned to 40% while failures continued", False, "recovery"),
                ("payment-api", "x509 certificate signed by unknown authority after trust bundle reload", True, "tls"),
            ],
            "changes": [
                ("payment-api", "rotated outbound provider CA trust bundle to bundle-2026-02", True, "config"),
            ],
            "tickets": [
                ("storefront", "INC-820 blamed high CPU but payment failures continued after scale-out", False, "history"),
                ("payment-api", "PKI-17 notes provider chain missing from bundle-2026-02", True, "knowledge"),
            ],
        },
    },
}


def scenario_observations(scenario: str, variant: int = 0) -> dict[str, list[dict[str, Any]]]:
    config = SCENARIOS[scenario]
    base = datetime(2026, 1, 15, 10, 0, tzinfo=UTC) + timedelta(days=variant, minutes=variant)
    result: dict[str, list[dict[str, Any]]] = {}
    offset = 0
    for source, rows in config["observations"].items():
        result[source] = []
        for service, summary, relevant, signal in rows:
            result[source].append(
                {
                    "service": service,
                    "summary": summary,
                    "relevant": relevant,
                    "signal": signal,
                    "observed_at": base + timedelta(seconds=offset * 45),
                    "source_ref": f"{source}://{scenario}/{variant}/{offset}",
                    "root_category": config["category"] if relevant else None,
                    "root_component": config["component"] if relevant else None,
                }
            )
            offset += 1
    return result


def default_incidents() -> list[dict[str, str]]:
    return [
        {
            "title": config["title"],
            "service": config["service"],
            "scenario": scenario,
            "severity": "SEV-2" if scenario != "auth-config" else "SEV-1",
            "alert_summary": config["impact"],
        }
        for scenario, config in SCENARIOS.items()
    ]

