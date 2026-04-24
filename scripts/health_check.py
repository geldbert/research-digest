#!/usr/bin/env python3
"""Quick health check for research-digest. Run during Phase 1 reconnect cycles."""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from research_digest.cli import default_config  # type: ignore

OLLAMA_HOST = "http://localhost:11434"


def run(cmd, cwd=None, timeout=30):
    try:
        result = subprocess.run(
            cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as exc:
        return False, "", str(exc)


def check_python():
    ok = sys.version_info >= (3, 10)
    return ok, f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_tests():
    ok, out, err = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=REPO_ROOT, timeout=60)
    if ok:
        for line in (out + err).splitlines():
            if "Ran" in line and "tests" in line:
                return True, line.strip()
        return True, "tests passed"
    return False, (err or out)[:200]


def check_arxiv():
    url = "https://export.arxiv.org/api/query?search_query=all:test&max_results=1"
    req = urllib.request.Request(url, headers={"User-Agent": "research-digest/health-check"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return exc.code == 429, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)[:100]


def check_feeds(cfg):
    results = {}
    all_ok = True
    for feed in cfg.get("feeds", []):
        url = feed.get("url", "")
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-digest/health-check"}, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                results[url] = (True, resp.status)
        except Exception as exc:
            results[url] = (False, str(exc)[:60])
            all_ok = False
    return all_ok, results


def check_ollama():
    url = f"{OLLAMA_HOST}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "research-digest/health-check"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            models = [m["name"] for m in data.get("models", [])]
            return True, f"{len(models)} models available"
    except Exception as exc:
        return False, str(exc)[:80]


def check_cli():
    ok, out, err = run([sys.executable, "-m", "research_digest.cli", "--version"], cwd=REPO_ROOT)
    if ok:
        return True, (out or err).strip()
    return False, (err or out)[:100]


def check_git():
    ok, out, _ = run(["git", "status", "--short"], cwd=REPO_ROOT)
    if ok:
        clean = not out.strip()
        return clean, ("clean" if clean else f"{len(out.strip().splitlines())} uncommitted changes")
    return False, "git failed"


def main():
    start = time.time()
    cfg = default_config()
    print("⚡ research-digest health check")
    print("=" * 50)

    py_ok, py_ver = check_python()
    print(f"Python >=3.10: {'✅' if py_ok else '❌'} {py_ver}")

    cli_ok, cli_ver = check_cli()
    print(f"CLI:           {'✅' if cli_ok else '❌'} {cli_ver}")

    test_ok, test_msg = check_tests()
    print(f"Tests:         {'✅' if test_ok else '❌'} {test_msg}")

    arxiv_ok, arxiv_msg = check_arxiv()
    print(f"arXiv API:     {'✅' if arxiv_ok else '❌'} {arxiv_msg}")

    feeds_ok, feeds_detail = check_feeds(cfg)
    total = len(feeds_detail)
    print(f"Default feeds: {'✅' if feeds_ok else '⚠️'} ({total} checked)")
    for url, (ok, status) in feeds_detail.items():
        short = url.replace("https://", "").replace("http://", "")
        print(f"   {'✅' if ok else '❌'} {short} — {status}")

    ollama_ok, ollama_msg = check_ollama()
    print(f"Ollama:        {'✅' if ollama_ok else '⚠️'} {ollama_msg}")

    git_ok, git_msg = check_git()
    print(f"Git working tree: {'✅' if git_ok else '⚠️'} {git_msg}")

    checks = [py_ok, cli_ok, test_ok, arxiv_ok, feeds_ok, ollama_ok, git_ok]
    score = sum(checks) / len(checks)
    grade = (
        "A" if score >= 0.9 else
        "B" if score >= 0.8 else
        "C" if score >= 0.7 else
        "D"
    )
    duration = round(time.time() - start, 2)

    print("=" * 50)
    print(f"Health Score: {score:.0%} | Grade: {grade} | Time: {duration}s")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python": {"ok": py_ok, "version": py_ver},
        "cli": {"ok": cli_ok, "version": cli_ver},
        "tests": {"ok": test_ok, "summary": test_msg},
        "arxiv": {"ok": arxiv_ok, "status": arxiv_msg},
        "feeds": {
            "ok": feeds_ok,
            "details": {url: {"ok": ok, "status": s} for url, (ok, s) in feeds_detail.items()},
        },
        "ollama": {"ok": ollama_ok, "status": ollama_msg},
        "git": {"ok": git_ok, "status": git_msg},
        "score": round(score, 2),
        "grade": grade,
        "duration_sec": duration,
    }
    out_path = REPO_ROOT / "health_report.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Report saved: {out_path}")
    return 0 if score >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
