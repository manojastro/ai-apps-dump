"""Evidence pack: one JSON document per decision with everything an auditor needs to see
why it was made. Bank numbers are masked; the pack's SHA-256 is recorded in the audit log."""

import hashlib
import json
from pathlib import Path
from typing import Any

from invoiceflow.observability.masking import mask


def write_evidence_pack(directory: Path, case_id: str, pack: dict[str, Any]) -> tuple[Path, str]:
    directory.mkdir(parents=True, exist_ok=True)
    body = json.dumps(mask(pack), indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    path = directory / f"{case_id}.json"
    path.write_text(body, encoding="utf-8", newline="\n")
    return path, hashlib.sha256(body.encode("utf-8")).hexdigest()
