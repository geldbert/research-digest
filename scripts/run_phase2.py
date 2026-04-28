#!/usr/bin/env python3
"""Phase 2 Fast-Forward runner for research-digest"""
import json, os, re, subprocess, sys
from pathlib import Path

PROJ = Path.home() / "workspace/research-digest"
OUT  = Path.home() / ".hermes/cron/output"
PY   = str(PROJ / ".venv/bin/python")
ZERO_FAILURES = True
SUMMARIES = []

# 1. Tests
try:
    proc = subprocess.run(
        [PY, "-m", "pytest", "tests/", "-q"],
        capture_output=True, text=True, cwd=str(PROJ), timeout=60
    )
    ok = proc.returncode == 0
    combined = proc.stdout + proc.stderr
    m = re.search(r'Ran \d+ tests? in ([\d.]+)s', combined)
    if not m:
        m = re.search(r'\d+\s+passed\s+in\s+([\d.]+)s', combined)
    dur = float(m.group(1)) if m else None
    SUMMARIES.append(f"Tests: {'OK' if ok else 'FAIL'} (duration={dur}s)")
    if not ok or dur is None or dur > 5.0:
        ZERO_FAILURES = False
except Exception as e:
    SUMMARIES.append(f"Tests: error {e}")
    ZERO_FAILURES = False

# 2. Git cleanness (tracked changes only; untracked files OK)
try:
    proc = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True, cwd=str(PROJ), timeout=10
    )
    tracked_dirty = False
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            status = line[:2]
            if status.strip() and status != '??':   # untracked files OK
                tracked_dirty = True
                break
    clean = proc.returncode == 0 and not tracked_dirty
    SUMMARIES.append(f"Git clean: {clean}")
    if not clean:
        ZERO_FAILURES = False
except Exception as e:
    SUMMARIES.append(f"Git clean: error {e}")
    ZERO_FAILURES = False

# 3. Report error scan
report_errs = 0
try:
    for p in sorted(OUT.glob("cycle_report_*.txt"), key=lambda p: p.stat().st_mtime)[-10:]:
        txt = p.read_text(errors="ignore")
        for line in txt.splitlines():
            if re.search(r'\b(error|exception|traceback|failed|failure)\b', line, re.I):
                lower = line.lower()
                if any(s in lower for s in [
                    "error-free","zero error","no error","no failures",
                    "without error","failure investigation","failure investigate","next phase:","phase 2",
                    "not a failure","non-failure","not failure","no new failures","no new error",
                    "before it becomes a failure","failure check","report-error snapshots",
                    "genuine error mentions"
                ]):
                    continue
                report_errs += 1
    SUMMARIES.append(f"Report errors: {report_errs}")
    if report_errs:
        ZERO_FAILURES = False
except Exception as e:
    SUMMARIES.append(f"Report errors: error {e}")

# 4. Digest size
try:
    latest = max(
        (p for p in (PROJ / "digests").glob("digest_*.md")),
        key=lambda p: p.stat().st_mtime
    )
    size = latest.stat().st_size
    SUMMARIES.append(f"Digest size: {size} bytes ({latest.name})")
    if size < 1000:
        ZERO_FAILURES = False
except Exception as e:
    SUMMARIES.append(f"Digest size: error {e}")
    ZERO_FAILURES = False

# 5. Health score
try:
    hp = PROJ / "health_report.json"
    health = json.loads(hp.read_text()).get("score", 0)
    SUMMARIES.append(f"Health score: {health}")
    if float(health) < 0.80:
        ZERO_FAILURES = False
except Exception:
    pass

action = "FAST-FORWARD" if ZERO_FAILURES else "INVESTIGATE"
print(f"Phase 2 {action}")
for s in SUMMARIES:
    print(f"  {s}")
