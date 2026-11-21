import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import html as html_module
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
MAX_WORKERS = 3
REQUEST_TIMEOUT = 30
DIGEST_COUNT = 25
MAX_CANDIDATES = 180
SEED = "https://nishantkhurana.me/digests/x-ai-2026"
HERE = Path(__file__).parent
COLLECTED_PATH = HERE / "collected_posts.json"
REPORT_PATH = HERE / "collection_report.json"
STATUS_URL_RE = re.compile(r"^https://(x|twitter)\.com/[^/]+/status/\d+$")
MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
TOPIC_TERMS = ("agent", "agentic", "mcp", "model context protocol", "llm", "coding",
               "eval", "harness", "memory", "context", "prompt", "tool", "workflow",
               "rag", "skill", "cursor", "claude", "copilot", "codex", "openai",
               "anthropic", "gemini", "sdk", "inference", "code", "developer",
               "engineering", "benchmark", "retrieval", "guardrail", "orchestration",
               "tracing", "observability", "browser", "automation", "loop", "planner")
EXCLUDE_TERMS = ("exploit", "sandbox escape", "0-day", "cve-", "ransomware",
                 "botnet", "credential theft", "phishing kit", "rootkit", "payload")


def fetch(url, timeout=REQUEST_TIMEOUT):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "ignore"), resp.status
    except urllib.error.HTTPError as exc:
        return None, exc.code
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


class DigestParser(HTMLParser):
    def __init__(self, digest_url):
        super().__init__(convert_charrefs=True)
        self.digest_url = digest_url
        self.href = None
        self.text = []
        self.records = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        d = dict(attrs)
        href = d.get("href")
        if not href:
            return
        if self.href is not None:
            self.flush()
        self.href = href

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.flush()

    def flush(self):
        raw = (self.href or "").strip()
        text = " ".join("".join(self.text).split())
        self.href = None
        self.text = []
        absolute = urllib.parse.urljoin(self.digest_url, raw)
        if not STATUS_URL_RE.match(absolute):
            return
        summary = re.sub(r":?\s*https?://\S*$", "", text).strip()
        if not summary:
            summary = absolute
        self.records.append({
            "url": absolute,
            "discovery_source": self.digest_url,
            "discovery_summary": summary,
        })


def digest_posts(digest_url, digest_html):
    parser = DigestParser(digest_url)
    parser.feed(digest_html)
    parser.close()
    return parser.records


