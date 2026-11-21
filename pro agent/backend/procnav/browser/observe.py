"""Structured page observation from the rendered DOM and accessibility semantics.

The JavaScript below is fixed tool code; it is never supplied by or exposed to a model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..core.redact import redact_text

COLLECT_JS = r"""
() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const text = (el) => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
  const main = document.querySelector('main') || document.body;
  const pairs = [];
  main.querySelectorAll('dl').forEach(dl => { const dts = dl.querySelectorAll('dt');
    dts.forEach(dt => { const dd = dt.nextElementSibling; if (dd && dd.tagName === 'DD') pairs.push([text(dt), text(dd)]); }); });
  main.querySelectorAll('tr').forEach(tr => { const th = tr.querySelector('th'); const tds = tr.querySelectorAll('td');
    if (th && tds.length === 1) pairs.push([text(th), text(tds[0])]); });
  main.querySelectorAll('.row').forEach(row => { const kids = Array.from(row.children);
    if (kids.length === 2) pairs.push([text(kids[0]), text(kids[1])]); });
  const chips = [];
  main.querySelectorAll('ul li').forEach(li => { if (li.closest('ul').getAttribute('aria-label')) chips.push(text(li)); });
  const tables = [];
  main.querySelectorAll('table').forEach(t => { const head = Array.from(t.querySelectorAll('thead th, tr:first-child th')).map(text);
    if (head.length > 1) { const rows = Array.from(t.querySelectorAll('tbody tr, tr')).filter(r => r.querySelectorAll('td').length > 1)
      .map(r => Array.from(r.querySelectorAll('td')).map(text)); tables.push({headers: head, rows}); } });
  const links = Array.from(document.querySelectorAll('a[href]')).filter(vis).map((a, i) => {
    a.setAttribute('data-pn-link', String(i));
    return { text: text(a), href: a.href, in_main: main.contains(a), nav: !!a.closest('nav') }; });
  const controls = Array.from(document.querySelectorAll('input:not([type=hidden]), select, textarea, button')).filter(vis).map((el, i) => {
    el.setAttribute('data-pn-ctl', String(i));
    let label = el.getAttribute('aria-label') || '';
    if (!label && el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if (l) label = text(l); }
    if (!label) { const l = el.closest('label'); if (l) label = text(l); }
    if (!label && el.placeholder) label = el.placeholder;
    return { tag: el.tagName.toLowerCase(), type: el.type || '', name: el.name || '', label: label || text(el),
      sensitive: el.type === 'password' }; });
  const alerts = Array.from(document.querySelectorAll('[role=alert],[role=status]')).map(el => ({
    text: text(el), code: el.getAttribute('data-error-code') || '' }));
  const headings = Array.from(main.querySelectorAll('h1,h2,h3')).map(text);
  const notes = Array.from(main.querySelectorAll('p')).map(text).filter(t => t.length < 200);
  return { title: document.title, url: location.href, headings, pairs, chips, tables, links, controls, alerts, notes,
           text: text(main).slice(0, 6000) };
}
"""


class LinkInfo(BaseModel):
    index: int
    text: str
    href: str
    in_main: bool
    nav: bool


class ControlInfo(BaseModel):
    index: int
    tag: str
    type: str
    name: str
    label: str
    sensitive: bool = False


class PageObservation(BaseModel):
    url: str
    title: str
    headings: list[str] = Field(default_factory=list)
    pairs: list[tuple[str, str]] = Field(default_factory=list)
    chips: list[str] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    links: list[LinkInfo] = Field(default_factory=list)
    controls: list[ControlInfo] = Field(default_factory=list)
    alerts: list[dict[str, str]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    text: str = ""
    http_status: int | None = None

    def pair_dict(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for k, v in self.pairs:
            out.setdefault(k, v)
        return out

    def summary(self) -> dict[str, Any]:
        """Compact form persisted with browser steps and offered to models."""
        return {
            "url": self.url,
            "title": self.title,
            "http_status": self.http_status,
            "headings": self.headings[:8],
            "alerts": self.alerts[:5],
            "pairs": self.pairs[:40],
            "links": [{"i": lk.index, "text": lk.text[:120]} for lk in self.links if lk.in_main][:30],
        }


def observe(page, secrets: list[str] | None = None, http_status: int | None = None) -> PageObservation:
    raw = page.evaluate(COLLECT_JS)
    red = lambda s: redact_text(s, secrets)  # noqa: E731
    return PageObservation(
        url=raw["url"],
        title=red(raw["title"]),
        headings=[red(h) for h in raw["headings"]],
        pairs=[(red(k), red(v)) for k, v in raw["pairs"]],
        chips=[red(c) for c in raw["chips"]],
        tables=[{"headers": t["headers"], "rows": [[red(c) for c in r] for r in t["rows"]]} for t in raw["tables"]],
        links=[
            LinkInfo(index=i, text=red(lk["text"]), href=lk["href"], in_main=lk["in_main"], nav=lk["nav"])
            for i, lk in enumerate(raw["links"])
        ],
        controls=[ControlInfo(index=i, **c) for i, c in enumerate(raw["controls"])],
        alerts=[{"text": red(a["text"]), "code": a["code"]} for a in raw["alerts"]],
        notes=[red(n) for n in raw["notes"]],
        text=red(raw["text"]),
        http_status=http_status,
    )
