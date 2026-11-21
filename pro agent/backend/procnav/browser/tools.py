"""Typed browser tools over an isolated, egress-guarded Playwright context.

Rules enforced here, independent of any model:
* navigation and network access are limited to the supplier's configured origins;
* every action is checked against the current page before execution and verified after;
* purchase-submission controls can only be operated by submit_approved_order, which itself
  refuses unless the order ledger says this exact intent is in the 'submitting' state;
* results are structured, timestamped, persisted as browser steps, and reference evidence.
"""

from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.crypto import decrypt, encrypt
from ..core.redact import redact, redact_text
from ..core.tracing import span
from ..quotes.schemas import ExtractedCheckout, ExtractedProduct
from ..suppliers.secrets import SupplierCredential
from .guard import EgressGuard, origin_of
from .observe import PageObservation, observe

PROTECTED_CONTROL = re.compile(r"place order|confirm purchase|submit purchase order|buy now|pay now", re.IGNORECASE)
SEARCH_LABEL = re.compile(r"search|find|keyword|what do you need", re.IGNORECASE)
QTY_LABEL = re.compile(r"^(quantity|qty|order quantity|how many\??)", re.IGNORECASE)
ADD_BUTTON = re.compile(r"add to (cart|basket|quote cart)|add items", re.IGNORECASE)
CHECKOUT_LINK = re.compile(r"checkout|proceed to purchase", re.IGNORECASE)
CONTINUE_BUTTON = re.compile(r"^(continue|next)", re.IGNORECASE)
ADDRESS_LABEL = re.compile(r"address|ship to|consignee", re.IGNORECASE)
PO_LABEL = re.compile(r"po number|order reference|po reference", re.IGNORECASE)
CART_LINK = re.compile(r"^(basket|cart|quote cart)$", re.IGNORECASE)
ORDERS_LINK = re.compile(r"^(my orders|orders|purchase history)$", re.IGNORECASE)
ORDER_REF = re.compile(r"\b[A-Z]O-[0-9A-F]{8}\b")


class ToolError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, data: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.data = data or {}


class HumanHandoff(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class BudgetExhausted(Exception):
    def __init__(self, budget: str, detail: str):
        super().__init__(detail)
        self.budget = budget


class RunCanceled(Exception):
    pass


class ToolResult(BaseModel):
    tool: str
    ok: bool
    status: str  # ok | error | blocked | handoff
    data: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    message: str | None = None
    url: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    at: datetime
    duration_ms: int
    step_seq: int | None = None


@dataclass(frozen=True)
class SupplierHandle:
    id: uuid.UUID
    key: str
    name: str
    base_url: str
    allowed_origins: tuple[str, ...]
    credential_ref: str
    is_simulated: bool


class StepSink:
    """Persistence and budget hooks provided by the worker (DB-backed) or tests (in-memory)."""

    def before_action(self, tool: str, side_effect: bool) -> None: ...

    def record(
        self,
        result: ToolResult,
        *,
        supplier_key: str,
        tool_input: dict[str, Any],
        side_effect: bool,
        explanation: str | None,
        decided_by: str,
        observation: dict[str, Any],
    ) -> int:
        return 0

    def save_evidence(self, kind: str, label: str, data: bytes, content_type: str, ext: str) -> str:
        return ""

    def load_state(self, supplier: SupplierHandle) -> bytes | None:
        return None

    def store_state(self, supplier: SupplierHandle, encrypted: bytes, ttl_seconds: int) -> None: ...

    def note_recovery(self, kind: str) -> None: ...


@dataclass
class InMemorySink(StepSink):
    steps: list[dict[str, Any]] = field(default_factory=list)
    evidence: dict[str, bytes] = field(default_factory=dict)
    states: dict[str, bytes] = field(default_factory=dict)
    recoveries: list[str] = field(default_factory=list)
    max_actions: int = 80
    actions: int = 0

    def before_action(self, tool: str, side_effect: bool) -> None:
        self.actions += 1
        if self.actions > self.max_actions:
            raise BudgetExhausted("browser_actions", f"exceeded {self.max_actions} browser actions")

    def record(self, result, *, supplier_key, tool_input, side_effect, explanation, decided_by, observation):
        self.steps.append(
            {
                "tool": result.tool,
                "status": result.status,
                "supplier": supplier_key,
                "input": tool_input,
                "data": result.data,
                "error": result.error_code,
            }
        )
        return len(self.steps)

    def save_evidence(self, kind, label, data, content_type, ext):
        key = f"{kind}-{len(self.evidence)}"
        self.evidence[key] = data
        return key

    def load_state(self, supplier):
        return self.states.get(supplier.key)

    def store_state(self, supplier, encrypted, ttl_seconds):
        self.states[supplier.key] = encrypted

    def note_recovery(self, kind: str) -> None:
        self.recoveries.append(kind)


def _now() -> datetime:
    return datetime.now(UTC)


class SupplierBrowser:
    """One isolated browser context for one tenant and supplier. Use as a context manager."""

    def __init__(
        self,
        browser,
        supplier: SupplierHandle,
        credential: SupplierCredential,
        sink: StepSink,
        *,
        decided_by: str = "code",
    ):
        self.browser = browser
        self.supplier = supplier
        self.credential = credential
        self.sink = sink
        self.decided_by = decided_by
        self.settings = get_settings()
        allowed = {o.rstrip("/") for o in supplier.allowed_origins} & set(self.settings.allowed_origins)
        self.guard = EgressGuard(allowed_origins=allowed)
        self.context = None
        self.page = None
        self.last_obs: PageObservation | None = None
        self.secrets = [credential.password]
        self.visited_pages: set[str] = set()
        self.visited_links: set[str] = set()

    # ------------------------------------------------------------------ lifecycle
    def __enter__(self) -> SupplierBrowser:
        state = None
        raw = self.sink.load_state(self.supplier)
        if raw:
            try:
                import json

                state = json.loads(decrypt(raw))
            except Exception:  # noqa: BLE001 - corrupt or rotated key: start clean
                state = None
        self.context = self.browser.new_context(
            storage_state=state,
            accept_downloads=True,
            java_script_enabled=True,
            service_workers="block",
            viewport={"width": 1280, "height": 900},
        )
        self.context.set_default_timeout(self.settings.browser_action_timeout_ms)
        self.context.set_default_navigation_timeout(self.settings.browser_navigation_timeout_ms)
        self.guard.install(self.context)
        self.page = self.context.new_page()
        self.context._procnav_primary = self.page  # noqa: SLF001
        return self

    def __exit__(self, *exc) -> None:
        try:
            if self.context is not None:
                import json

                state = self.context.storage_state()
                self.sink.store_state(self.supplier, encrypt(json.dumps(state).encode()), 3600)
        finally:
            if self.context is not None:
                self.context.close()

    # ------------------------------------------------------------------ recording wrapper
    def _run(
        self,
        tool: str,
        tool_input: dict[str, Any],
        fn: Callable[[], dict[str, Any]],
        *,
        side_effect: bool = False,
        explanation: str | None = None,
        screenshot: str | None = None,
    ) -> ToolResult:
        self.sink.before_action(tool, side_effect)
        started = time.monotonic()
        at = _now()
        evidence: list[str] = []
        handoff: HumanHandoff | None = None
        try:
            with span(f"tool.{tool}", supplier=self.supplier.key, side_effect=side_effect):
                data = fn()
            status, ok, code, message = "ok", True, None, None
        except HumanHandoff as h:
            handoff = h
            data, status, ok, code, message = {"reason": h.reason}, "handoff", False, "HUMAN_HANDOFF", h.detail
        except ToolError as err:
            data, status, ok, code, message = (
                err.data,
                ("blocked" if err.code.startswith("BLOCKED") else "error"),
                False,
                err.code,
                err.message,
            )
        except Exception as err:  # noqa: BLE001 - surface Playwright failures as typed tool errors
            name = type(err).__name__
            code = "TIMEOUT" if "Timeout" in name else "BROWSER_ERROR"
            data, status, ok, message = {}, "error", False, redact_text(str(err).splitlines()[0][:300], self.secrets)
        if screenshot and self.page is not None and ok:
            evidence.append(self.capture(screenshot))
        result = ToolResult(
            tool=tool,
            ok=ok,
            status=status,
            data=redact(data, self.secrets),
            error_code=code,
            message=message,
            url=self.page.url if self.page else None,
            evidence_ids=evidence,
            at=at,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        obs = self.last_obs.summary() if self.last_obs else {}
        result.step_seq = self.sink.record(
            result,
            supplier_key=self.supplier.key,
            tool_input=redact(tool_input, self.secrets),
            side_effect=side_effect,
            explanation=explanation,
            decided_by=self.decided_by,
            observation=obs,
        )
        if handoff is not None:
            raise handoff
        return result

    def capture(self, label: str) -> str:
        """Redacted screenshot: masks password fields and lines containing postal codes."""
        masks = [self.page.locator("input[type=password]"), self.page.get_by_text(re.compile(r"\b\d{6}\b"))]
        png = self.page.screenshot(full_page=True, type="jpeg", quality=55, mask=masks, mask_color="#222")
        return self.sink.save_evidence("screenshot", f"{self.supplier.key}: {label}", png, "image/jpeg", "jpg")

    # ------------------------------------------------------------------ low-level, guarded helpers
    def _observe(self, status: int | None = None) -> PageObservation:
        self.last_obs = observe(self.page, self.secrets, status)
        self.visited_pages.add(self.last_obs.url)
        self.visited_links.update(lk.href for lk in self.last_obs.links)
        return self.last_obs

    def _check_url(self, url: str) -> None:
        ok, reason = self.guard.check(url)
        if not ok:
            self.guard.record(url, reason, "navigation")
            raise ToolError(
                "BLOCKED_NAVIGATION",
                f"Navigation to {origin_of(url) or url[:60]} is not permitted ({reason})",
                data={"url": url[:200], "reason": reason},
            )

    def _goto(self, url: str) -> PageObservation:
        self._check_url(url)
        last_status = None
        for attempt in range(self.settings.max_navigation_retries + 1):
            try:
                resp = self.page.goto(url, wait_until="domcontentloaded")
                last_status = resp.status if resp else None
            except Exception as err:  # noqa: BLE001
                if "Timeout" not in type(err).__name__ or attempt == self.settings.max_navigation_retries:
                    raise
                self.sink.note_recovery("navigation_timeout")
                continue
            if last_status in (502, 503, 504) and attempt < self.settings.max_navigation_retries:
                self.sink.note_recovery(f"http_{last_status}")
                time.sleep(min(0.5 * (2**attempt), 3))
                continue
            break
        self._after_navigation_checks()
        obs = self._observe(last_status)
        if last_status == 503:
            raise ToolError(
                "SUPPLIER_UNAVAILABLE", "Supplier portal unavailable (HTTP 503) after retries", data={"status": 503}
            )
        if last_status and last_status >= 500:
            raise ToolError("SUPPLIER_ERROR", f"Supplier returned HTTP {last_status} after retries", retryable=True)
        return obs

    def _after_navigation_checks(self) -> None:
        url = self.page.url
        ok, reason = self.guard.check(url)
        if not ok:  # e.g. a redirect that escaped the allowlist
            self.guard.record(url, reason, "redirect")
            self.page.goto("about:blank")
            raise ToolError("BLOCKED_REDIRECT", f"Redirect to a non-allowed origin was blocked ({reason})")

    def _settle(self) -> None:
        """After a click-driven navigation, retry transient 5xx pages with bounded backoff."""
        for attempt in range(self.settings.max_navigation_retries):
            status = self._status_from_page()
            if status not in (502, 503, 504):
                return
            self.sink.note_recovery(f"http_{status}")
            time.sleep(min(0.5 * (2**attempt), 3))
            self.page.goto(self.page.url, wait_until="domcontentloaded")

    def _is_login_page(self) -> bool:
        return self.page.locator("input[type=password]").count() > 0

    def _is_mfa_page(self) -> bool:
        return (
            bool(
                re.search(
                    r"one-time|verification code|passcode|otp|two-step|security check",
                    self.page.content()[:20000],
                    re.IGNORECASE,
                )
            )
            and not self._is_login_page()
        )

    def _login(self) -> None:
        user = self.page.get_by_label(re.compile(r"user|account id|username", re.IGNORECASE)).first
        user.fill(self.credential.username)
        self.page.locator("input[type=password]").first.fill(self.credential.password)
        self._click_safe(
            self.page.get_by_role("button", name=re.compile(r"sign in|log in|login", re.IGNORECASE)), "sign in"
        )
        self.page.wait_for_load_state("domcontentloaded")
        self._settle()
        if self._is_mfa_page():
            raise HumanHandoff(
                "mfa_required",
                f"{self.supplier.name} requires an interactive one-time code. "
                "An authorized person must complete sign-in; the agent never bypasses MFA.",
            )
        if self._is_login_page():
            raise ToolError("LOGIN_FAILED", "Supplier rejected the stored credentials")

    def _ensure_session(self, return_to: str | None = None) -> bool:
        """Re-authenticate if the portal shows a login page. Returns True if a login happened."""
        if self._is_mfa_page():
            raise HumanHandoff("mfa_required", f"{self.supplier.name} requires an interactive one-time code.")
        if not self._is_login_page():
            return False
        expired = "expired" in self.page.url or "expired" in self.page.content().lower()
        self._login()
        if expired:
            self.sink.note_recovery("session_expired_relogin")
        if return_to:
            self._goto(return_to)
        return True

    def _click_safe(self, locator, purpose: str, *, allow_protected: bool = False) -> None:
        if locator.count() == 0:
            raise ToolError("ELEMENT_NOT_FOUND", f"No control found for: {purpose}", retryable=True)
        el = locator.first
        name = (el.get_attribute("aria-label") or el.inner_text() or el.get_attribute("value") or "").strip()
        if PROTECTED_CONTROL.search(name) and not allow_protected:
            raise ToolError(
                "BLOCKED_PROTECTED_ACTION",
                f"'{name}' is a purchase control; only the protected submission tool may use it",
            )
        href = el.get_attribute("href")
        if href:
            self._check_url(self.page.url if href.startswith("#") else _abs(self.page.url, href))
        el.click()

    def _nav_to(self, link_rx: re.Pattern[str], purpose: str) -> PageObservation:
        link = self.page.get_by_role("link", name=link_rx)
        if link.count() == 0:
            raise ToolError("ELEMENT_NOT_FOUND", f"No navigation link for {purpose}", retryable=True)
        href = link.first.get_attribute("href") or ""
        return self._goto_checked(_abs(self.page.url, href))

    def _goto_checked(self, url: str) -> PageObservation:
        obs = self._goto(url)
        if self._ensure_session(return_to=url):
            obs = self.last_obs or self._observe()
        return obs

    # ------------------------------------------------------------------ public tools
    def open_supplier(self) -> ToolResult:
        def run():
            obs = self._goto(self.supplier.base_url + "/")
            logged_in = self._ensure_session()
            obs = self._observe()
            return {"title": obs.title, "logged_in_now": logged_in, "headings": obs.headings[:3]}

        return self._run(
            "open_supplier",
            {"supplier": self.supplier.key},
            run,
            explanation=f"Open {self.supplier.name} in an isolated session",
        )

    def observe_page(self) -> ToolResult:
        return self._run("observe_page", {}, lambda: self._observe().summary())

    def find_product(self, query: str, *, explanation: str | None = None) -> ToolResult:
        def run():
            if not query or len(query) > 120:
                raise ToolError("INVALID_INPUT", "Search query must be 1-120 characters")
            self._settle()
            box = self.page.get_by_role("search").get_by_role("textbox")
            if box.count() == 0:
                box = self.page.get_by_label(SEARCH_LABEL)
            if box.count() == 0:
                box = self.page.get_by_placeholder(SEARCH_LABEL)
            if box.count() == 0:
                raise ToolError("ELEMENT_NOT_FOUND", "No search box found on the current page", retryable=True)
            box.first.fill(query)
            with self.page.expect_navigation(wait_until="domcontentloaded"):
                box.first.press("Enter")
            self._settle()
            self._ensure_session(return_to=self.page.url)
            obs = self._observe()
            here = origin_of(obs.url)
            candidates = [
                {"index": lk.index, "text": lk.text, "href": lk.href}
                for lk in obs.links
                if lk.in_main
                and not lk.nav
                and lk.text
                and origin_of(lk.href) == here
                and not re.search(r"basket|cart|order|checkout|logout|sign ?out", lk.text, re.IGNORECASE)
            ]
            return {"query": query, "candidates": candidates[:20], "count": len(candidates)}

        return self._run("find_product", {"query": query}, run, explanation=explanation)

    def _status_from_page(self) -> int | None:
        title = self.page.title()
        m = re.match(r"^(5\d\d)$", title.strip())
        return int(m.group(1)) if m else None

    def inspect_product(self, href: str, *, explanation: str | None = None) -> ToolResult:
        def run():
            if href not in self.visited_links:
                raise ToolError("INVALID_ACTION", "Product link was not offered by a page observed in this session")
            return {"product": self._product_from(self._goto_checked(href)).model_dump()}

        return self._run("inspect_product", {"href": href}, run, explanation=explanation, screenshot="product page")

    def revisit(self, url: str, purpose: str) -> ToolResult:
        """Return to a page already observed in this session (e.g. search results)."""

        def run():
            if url not in self.visited_pages:
                raise ToolError("INVALID_ACTION", "Only pages already observed in this session can be revisited")
            obs = self._goto_checked(url)
            return {"url": obs.url, "title": obs.title}

        return self._run("observe_page", {"url": url, "purpose": purpose}, run, explanation=purpose)

    def add_to_cart(self, quantity: int) -> ToolResult:
        def run():
            if not (1 <= quantity <= 1000):
                raise ToolError("INVALID_INPUT", "Quantity must be between 1 and 1000")
            qty = self.page.get_by_label(QTY_LABEL)
            if qty.count() == 0:
                qty = self.page.get_by_role("spinbutton")
            if qty.count() == 0:
                raise ToolError("ELEMENT_NOT_FOUND", "No quantity field on this page", retryable=True)
            qty.first.fill(str(quantity))
            with self.page.expect_navigation(wait_until="domcontentloaded"):
                self._click_safe(self.page.get_by_role("button", name=ADD_BUTTON), "add to cart")
            self._settle()
            self._ensure_session()
            obs = self._observe()
            return {"landed_on": obs.headings[:1], "url": obs.url}

        return self._run(
            "add_to_cart",
            {"quantity": quantity},
            run,
            side_effect=False,
            explanation="Add the inspected item to the supplier cart (reversible, no purchase)",
        )

    def inspect_cart(self, expected_sku: str, expected_qty: int) -> ToolResult:
        def run():
            obs = self._nav_to(CART_LINK, "cart")
            removed = []
            # Remove lines for other SKUs so checkout reflects exactly one approved line.
            for _ in range(10):
                buttons = self.page.get_by_role(
                    "button", name=re.compile(r"^Remove (?!" + re.escape(expected_sku) + r"$)", re.IGNORECASE)
                )
                if buttons.count() == 0:
                    break
                label = buttons.first.get_attribute("aria-label") or ""
                with self.page.expect_navigation(wait_until="domcontentloaded"):
                    buttons.first.click()
                removed.append(label.replace("Remove ", ""))
            obs = self._observe()
            text = obs.text
            present = expected_sku in text
            lines = [row for t in obs.tables for row in t["rows"]]
            qty_ok = bool(re.search(rf"(Qty|Quantity)\s*{expected_qty}\b", text)) or any(
                expected_sku in " ".join(r) and str(expected_qty) in r for r in lines
            )
            if not present or not qty_ok:
                raise ToolError(
                    "CART_MISMATCH", f"Cart does not show {expected_qty} x {expected_sku}", data={"removed": removed}
                )
            return {"sku": expected_sku, "quantity": expected_qty, "removed_other_lines": removed}

        return self._run("inspect_cart", {"expected_sku": expected_sku, "expected_qty": expected_qty}, run)

    def _open_confirmation(self, address_ref: str) -> PageObservation:
        """Cart -> checkout preview -> select destination -> confirmation summary (no submission)."""
        link = self.page.get_by_role("link", name=CHECKOUT_LINK)
        if link.count() == 0:
            self._nav_to(CART_LINK, "cart")
            link = self.page.get_by_role("link", name=CHECKOUT_LINK)
        self._goto_checked(_abs(self.page.url, link.first.get_attribute("href") or ""))
        select = self.page.get_by_label(ADDRESS_LABEL)
        if select.count() == 0:
            raise ToolError("ELEMENT_NOT_FOUND", "No delivery address selector on checkout", retryable=True)
        options = select.first.locator("option").all_inner_texts()
        match = [o for o in options if f"({address_ref})" in o]
        if not match:
            raise ToolError(
                "DESTINATION_UNAVAILABLE",
                f"Destination {address_ref} is not offered by this supplier",
                data={"options": [re.sub(r"\(.*", "", o).strip() for o in options]},
            )
        select.first.select_option(label=match[0])
        with self.page.expect_navigation(wait_until="domcontentloaded"):
            self._click_safe(self.page.get_by_role("button", name=CONTINUE_BUTTON), "continue to confirmation")
        self._settle()
        self._ensure_session()
        return self._observe()

    def _checkout_extract(self, obs: PageObservation, address_ref: str) -> ExtractedCheckout:
        deliver = re.search(r"\((ADDR-[A-Z0-9-]+)\)", " ".join(obs.notes))
        return ExtractedCheckout(
            fields=obs.pair_dict(),
            notes=[n for n in obs.notes if re.search(r"gst|price|rate", n, re.IGNORECASE)],
            address_ref=deliver.group(1) if deliver else None,
            source_url=obs.url,
        )

    def extract_quote(self, address_ref: str, *, explanation: str | None = None) -> ToolResult:
        def run():
            obs = self._open_confirmation(address_ref)
            if any(a.get("code") for a in obs.alerts):
                raise ToolError("CHECKOUT_ERROR", obs.alerts[0]["text"])
            ext = self._checkout_extract(obs, address_ref)
            return {"checkout": ext.model_dump()}

        return self._run(
            "extract_quote", {"address_ref": address_ref}, run, explanation=explanation, screenshot="checkout summary"
        )

    def refresh_quote(self, sku_href: str, quantity: int, expected_sku: str, address_ref: str) -> list[ToolResult]:
        """Revalidation: reload the product page and checkout, returning fresh observations."""
        results = []
        results.append(
            self._run(
                "refresh_quote",
                {"href": sku_href},
                lambda: {"product": self._product_from(self._goto_checked(sku_href)).model_dump()},
                screenshot="refreshed product",
            )
        )
        if not results[-1].ok:
            return results
        results.append(self.add_to_cart(quantity))
        if results[-1].ok:
            results.append(self.inspect_cart(expected_sku, quantity))
        if results[-1].ok:
            results.append(self.extract_quote(address_ref, explanation="Reload checkout for revalidation"))
        return results

    def _product_from(self, obs: PageObservation) -> ExtractedProduct:
        self.last_obs = obs
        name = obs.headings[0] if obs.headings else obs.title
        ext = ExtractedProduct(product_name=name, fields=obs.pair_dict(), flags=obs.chips, source_url=obs.url)
        m = re.search(r"SKU:?\s*([A-Z0-9-]{4,})", obs.text)
        if not any(re.search(r"sku|item code|part number|reference", k, re.IGNORECASE) for k in ext.fields) and m:
            ext.fields["SKU"] = m.group(1)
        for note in obs.notes:
            low = note.lower()
            if "per unit price" in low and ":" in note:
                k, v = note.split(":", 1)
                ext.fields.setdefault(k.strip(), v.strip())
            elif re.search(r"stock level|arrives in", low):
                for part in note.split("·"):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        ext.fields.setdefault(k.strip(), v.strip())
                    elif re.match(r"\s*arrives in", part, re.IGNORECASE):
                        ext.fields.setdefault("Arrives in", part.strip()[len("arrives in") :].strip())
            elif re.search(r"gst .*added at checkout|delivery charge", low):
                ext.fields.setdefault("GST", note)
                m2 = re.search(r"delivery charge (INR [\d,\.]+ per \w+)", note, re.IGNORECASE)
                if m2:
                    ext.fields.setdefault("Delivery charge", m2.group(1))
        return ext

    def submit_approved_order(
        self,
        *,
        intent_key: str,
        address_ref: str,
        approved_cart: dict[str, str],
        ledger_allows: Callable[[], bool],
        current_matches: Callable[[ExtractedCheckout], list[dict[str, str]]],
    ) -> ToolResult:
        """Protected side effect. Fails closed unless the ledger and the live page both agree."""

        def run():
            if not self.supplier.is_simulated and self.settings.dry_run:
                raise ToolError("DRY_RUN", "Real supplier submission is disabled in dry-run mode")
            obs = self._open_confirmation(address_ref)
            changes = current_matches(self._checkout_extract(obs, address_ref))
            if changes:
                raise ToolError(
                    "TERMS_CHANGED", "Live checkout differs from the approved purchase", data={"changes": changes}
                )
            if not ledger_allows():
                raise ToolError("LEDGER_REFUSED", "Order ledger does not permit submission for this intent")
            po = self.page.get_by_label(PO_LABEL)
            if po.count() == 0:
                raise ToolError("ELEMENT_NOT_FOUND", "No purchase-order reference field", retryable=False)
            po.first.fill(intent_key)
            button = self.page.get_by_role("button", name=PROTECTED_CONTROL)
            try:
                with self.page.expect_navigation(
                    wait_until="domcontentloaded", timeout=self.settings.browser_navigation_timeout_ms
                ):
                    self._click_safe(button, "submit approved order", allow_protected=True)
            except Exception as err:  # noqa: BLE001
                if "Timeout" in type(err).__name__:
                    raise ToolError(
                        "SUBMISSION_OUTCOME_UNKNOWN",
                        "No response before timeout; the order may or may not exist. Reconcile before any retry.",
                        data={"intent_key": intent_key},
                    ) from err
                raise
            obs = self._observe()
            codes = [a.get("code") for a in obs.alerts if a.get("code")]
            if codes:
                raise ToolError(f"SUPPLIER_REJECTED_{codes[0]}", obs.alerts[0]["text"], data={"code": codes[0]})
            m = ORDER_REF.search(obs.text)
            if not m:
                raise ToolError("SUBMISSION_OUTCOME_UNKNOWN", "Confirmation page did not show an order reference")
            return {"order_ref": m.group(0), "intent_key": intent_key, "replayed": "replay" in obs.text.lower()}

        return self._run(
            "submit_approved_order",
            {"intent_key": intent_key},
            run,
            side_effect=True,
            explanation="Submit the approved order with its idempotency token",
            screenshot="order confirmation",
        )

    def inspect_order_history(self, intent_key: str) -> ToolResult:
        def run():
            self._goto_checked(self.supplier.base_url + "/")
            obs = self._nav_to(ORDERS_LINK, "order history")
            hits = set()
            for t in obs.tables:
                for row in t["rows"]:
                    if any(intent_key == c.strip() for c in row):
                        hits.update(ORDER_REF.findall(" ".join(row)))
            if not obs.tables:
                for block in re.split(r"(?=Order number )", obs.text):
                    if intent_key in block:
                        hits.update(ORDER_REF.findall(block))
            refs = sorted(hits)
            return {
                "intent_key": intent_key,
                "found": len(refs) == 1,
                "ambiguous": len(refs) > 1,
                "order_refs": refs,
                "orders_listed": obs.text.count("O-"),
            }

        return self._run("inspect_order_history", {"intent_key": intent_key}, run, screenshot="order history")

    def verify_receipt(self, order_ref: str, wait_seconds: int = 30) -> ToolResult:
        def run():
            if not ORDER_REF.fullmatch(order_ref):
                raise ToolError("INVALID_INPUT", "Malformed order reference")
            self._goto_checked(self.supplier.base_url + "/")
            self._nav_to(ORDERS_LINK, "order history")
            link = self.page.get_by_role("link", name=re.compile(re.escape(order_ref)))
            if link.count() == 0:
                raise ToolError("ORDER_NOT_FOUND", f"Order {order_ref} is not in the account order history")
            detail_url = _abs(self.page.url, link.first.get_attribute("href") or "")
            deadline = time.monotonic() + wait_seconds
            while True:
                obs = self._goto_checked(detail_url)
                receipt_link = self.page.get_by_role("link", name=re.compile(r"download receipt", re.IGNORECASE))
                if receipt_link.count() > 0 or time.monotonic() > deadline:
                    break
                self.sink.note_recovery("receipt_pending_wait")
                time.sleep(2)
            if receipt_link.count() == 0:
                raise ToolError(
                    "RECEIPT_PENDING",
                    "Supplier has not issued a receipt yet",
                    retryable=True,
                    data={"status_text": [a["text"] for a in obs.alerts]},
                )
            self._check_url(_abs(self.page.url, receipt_link.first.get_attribute("href") or ""))
            with self.page.expect_download() as dl_info:
                receipt_link.first.click()
            dl = dl_info.value
            self._check_url(dl.url)
            raw = open(dl.path(), "rb").read().decode("utf-8", errors="replace")  # noqa: SIM115
            fields = {}
            for line in raw.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fields[k.strip()] = v.strip()
            safe_text = re.sub(r"(?m)^(Ship to: \S+).*$", r"\1 [ADDRESS REDACTED]", raw)
            ev = self.sink.save_evidence(
                "receipt", f"{self.supplier.key}: receipt {order_ref}", safe_text.encode(), "text/plain", "txt"
            )
            fields["Ship to"] = fields.get("Ship to", "").split(" ")[0]
            return {
                "order_ref": order_ref,
                "receipt": fields,
                "receipt_evidence_id": ev,
                "page_pairs": dict(obs.pair_dict()),
            }

        return self._run("verify_receipt", {"order_ref": order_ref}, run, screenshot="order detail")

    def perform_page_action(self, action: dict[str, Any], *, explanation: str | None = None) -> ToolResult:
        """Model-proposed generic action, validated against the current observation before execution."""

        def run():
            obs = self.last_obs or self._observe()
            kind = action.get("type")
            idx = action.get("index")
            if kind == "click_link":
                links = {lk.index: lk for lk in obs.links}
                if idx not in links:
                    raise ToolError("INVALID_ACTION", "Link index not present on the current page")
                target = links[idx]
                if PROTECTED_CONTROL.search(target.text):
                    raise ToolError("BLOCKED_PROTECTED_ACTION", "Purchase controls are not available to browsing")
                self._goto_checked(target.href)
                return {"navigated_to": self.page.url}
            if kind == "fill_search":
                controls = {c.index: c for c in obs.controls}
                c = controls.get(idx)
                if c is None or c.tag != "input" or c.sensitive or c.type not in ("text", "search", ""):
                    raise ToolError("INVALID_ACTION", "Only visible, non-sensitive text inputs may be filled")
                text = str(action.get("text", ""))[:120]
                loc = self.page.locator(f'[data-pn-ctl="{int(idx)}"]')
                loc.fill(text)
                with self.page.expect_navigation(wait_until="domcontentloaded"):
                    loc.press("Enter")
                return {"filled": text, "url": self.page.url}
            raise ToolError("INVALID_ACTION", f"Unsupported action type {kind!r}")

        return self._run("perform_page_action", {"action": action}, run, explanation=explanation)


def _abs(base: str, href: str) -> str:
    from urllib.parse import urljoin

    return urljoin(base, href)


def launch_browser(playwright):
    s = get_settings()
    # The Chromium sandbox stays enabled; containers use the Playwright image's supported seccomp setup.
    return playwright.chromium.launch(headless=s.browser_headless)


def session_expiry(ttl_seconds: int) -> datetime:
    return _now() + timedelta(seconds=ttl_seconds)
