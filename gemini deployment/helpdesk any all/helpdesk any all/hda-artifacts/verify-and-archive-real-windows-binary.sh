#!/usr/bin/env bash
# Verify-and-archive gate for the EXACT binary manually accepted on real Windows.
#
# This script NEVER accepts a rebuilt binary. It archives one file and only one
# file: the artifact whose SHA-256 matches the manually accepted hash recorded in
# GOLDEN_WORKING_STATE.md.
#
# Usage: verify-and-archive-real-windows-binary.sh <path-to-uploaded-exe>

set -euo pipefail

EXPECTED_SHA="5ff9764663e2016b91fc46ea036939ea8c842af049bc53b8f246536d02a48a40"
EXPECTED_SIZE=65918210
REBUILT_SHA="435bbe5fc9569cb81a8738f2ac5d2c010ae86d44bb11f24e7666a42ca84a8c0c"

ARCHIVE_DIR="$HOME/hda-artifacts/real-windows-verified"
ARCHIVE_NAME="HelpdeskAnywhere-REAL-WINDOWS-VERIFIED-2026-09-06.exe"
DEST="$ARCHIVE_DIR/$ARCHIVE_NAME"

src="${1:-}"
if [[ -z "$src" || ! -f "$src" ]]; then
  echo "ARCHIVE STATUS: FAILED — no such file: ${src:-<none given>}" >&2
  exit 2
fi

actual_sha="$(sha256sum "$src" | awk '{print $1}')"
actual_size="$(stat -c %s "$src")"

echo "candidate : $src"
echo "sha-256   : $actual_sha"
echo "size      : $actual_size bytes"

if [[ "$actual_sha" == "$REBUILT_SHA" ]]; then
  echo "ARCHIVE STATUS: FAILED — this is the REBUILT golden binary (435bbe5f...)," >&2
  echo "not the binary manually accepted on real Windows. Refusing to archive." >&2
  exit 3
fi

if [[ "$actual_sha" != "$EXPECTED_SHA" ]]; then
  echo "ARCHIVE STATUS: FAILED — hash mismatch." >&2
  echo "  expected $EXPECTED_SHA" >&2
  echo "  actual   $actual_sha" >&2
  exit 4
fi

if [[ "$actual_size" != "$EXPECTED_SIZE" ]]; then
  echo "ARCHIVE STATUS: FAILED — size mismatch (expected $EXPECTED_SIZE)." >&2
  exit 5
fi

mkdir -p "$ARCHIVE_DIR"
if [[ -e "$DEST" ]]; then
  if [[ "$(sha256sum "$DEST" | awk '{print $1}')" == "$EXPECTED_SHA" ]]; then
    echo "ARCHIVE STATUS: SAFE — already archived at $DEST"
    exit 0
  fi
  echo "ARCHIVE STATUS: FAILED — $DEST exists with a different hash. Not overwriting." >&2
  exit 6
fi

install -m 0444 "$src" "$DEST"
chmod 0444 "$DEST"
sha256sum "$DEST" > "$DEST.sha256"
chmod 0444 "$DEST.sha256"

echo
echo "REAL WINDOWS VERIFIED EXE: $DEST"
echo "SHA-256: $(sha256sum "$DEST" | awk '{print $1}')"
echo "ARCHIVE STATUS: SAFE"
echo
echo "Optional, once archived — attach to the golden tag's release:"
echo "  gh release create hda-windows-privileged-control-working-2026-09-06 \\"
echo "    \"$DEST\" --title 'Golden: Windows privileged control (2026-09-06)' \\"
echo "    --notes 'Exact binary manually accepted on real Windows. Source commit 1509db7.'"
