#!/usr/bin/env python3
"""
MusicMV — Pipeline Fix Kit (idempotent)
=======================================
Corrects src/templates/pipeline.html. SAFE TO RUN MULTIPLE TIMES
(every edit is guarded, so re-running is a no-op).

Fixes applied:
  1. Collapse tripled action-button icons      -> single icon
  2. Collapse tripled <title> tags             -> single title
  3. Escape log.time and log.level in log view -> consistent escaping
  4. Cap the log viewer to the last 500 lines  -> no unbounded DOM growth
  5. Skip re-render when logs are unchanged     -> preserves text selection
  6. Recover polling + show error if the first  -> diagnose never gets stuck
     /api/archive/status call fails
  7. Never POST an empty Tidal token            -> won't clobber stored token

It also SCANS app.py and warns (no edit) if a Tidal token literal is still
hardcoded.

Usage:
  python3 apply_pipeline_fixes.py            # apply in place (creates .bak)
  python3 apply_pipeline_fixes.py --dry-run  # show what would change
  python3 apply_pipeline_fixes.py --selftest # run built-in tests
"""
import re
import os
import sys
import shutil

TARGET = os.path.join("src", "templates", "pipeline.html")
APP_PY = "app.py"


def apply_fixes(content):
    """Return (new_content, report). report is a list of (label, count)."""
    report = []

    # 1. Collapse adjacent identical <svg>...</svg> runs (fixes tripled icons)
    new, n = re.subn(r'(<svg\b[^>]*>.*?</svg>)(?:\s*\1)+', r'\1', content, flags=re.S)
    content = new
    report.append(("Collapse duplicate <svg> icons", n))

    # 2. Collapse adjacent identical <title>...</title>
    new, n = re.subn(r'(<title>.*?</title>)(?:\s*\1)+', r'\1', content, flags=re.S)
    content = new
    report.append(("Collapse duplicate <title> tags", n))

    # 3a. Escape log.time in the rendered line
    if '[${log.time}]' in content:
        content = content.replace('[${log.time}]', '[${escapeHTML(log.time)}]')
        report.append(("Escape log.time", 1))
    else:
        report.append(("Escape log.time", 0))

    # 3b. Escape log.level in the rendered label
    if '>${log.level}:</span>' in content:
        content = content.replace('>${log.level}:</span>', '>${escapeHTML(log.level)}:</span>')
        report.append(("Escape log.level", 1))
    else:
        report.append(("Escape log.level", 0))

    # 4. Cap rendered logs to the last 500 entries
    cap_anchor = "let html = '';\n            logs.forEach(log => {"
    if 'logs.slice(-500)' not in content and cap_anchor in content:
        content = content.replace(
            cap_anchor,
            "let html = '';\n            if (logs.length > 500) logs = logs.slice(-500);\n            logs.forEach(log => {",
            1,
        )
        report.append(("Cap log viewer to 500 lines", 1))
    else:
        report.append(("Cap log viewer to 500 lines", 0))

    # 5. Skip re-render when the log set is unchanged (preserves selection)
    sig_anchor = "const consoleBody = document.getElementById('console-body');\n            if (!consoleBody) return;"
    if 'logSig' not in content and sig_anchor in content:
        inject = (
            sig_anchor
            + "\n\n            const __sig = (logs && logs.length) ? (logs.length + '|' + logs[logs.length - 1].message) : '0';"
            + "\n            if (consoleBody.dataset.logSig === __sig) return;"
            + "\n            consoleBody.dataset.logSig = __sig;"
        )
        content = content.replace(sig_anchor, inject, 1)
        report.append(("Skip identical re-render (keep selection)", 1))
    else:
        report.append(("Skip identical re-render (keep selection)", 0))

    # 6. Recover polling + surface an error if the first status fetch fails
    if 'Cannot reach backend' not in content:
        pat = r'\}\s*catch \(err\) \{\s*console\.error\("Error fetching status:", err\);\s*\}'
        repl = (
            '} catch (err) {\n'
            '                console.error("Error fetching status:", err);\n'
            '                if (!activeTimer) startPolling(4000);\n'
            "                renderLogs([{ time: new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}), level: 'ERROR', message: 'Cannot reach backend (/api/archive/status). Retrying\u2026' }]);\n"
            '            }'
        )
        new, n = re.subn(pat, repl, content, count=1, flags=re.S)
        content = new
        report.append(("Recover polling on status failure", n))
    else:
        report.append(("Recover polling on status failure", 0))

    # 7. Do not POST an empty Tidal token (avoid clobbering stored/env token)
    if '__p.tidalToken' not in content:
        pat = (
            r'body: JSON\.stringify\(\{\s*'
            r'path,\s*tidalToken,\s*syncDeezerAvatars,\s*generateCatalogs,\s*reconcileShortcuts\s*\}\)'
        )
        repl = (
            'body: (() => { const __p = { path, syncDeezerAvatars, generateCatalogs, reconcileShortcuts }; '
            'if (tidalToken) __p.tidalToken = tidalToken; return JSON.stringify(__p); })()'
        )
        new, n = re.subn(pat, repl, content, count=1, flags=re.S)
        content = new
        report.append(("Guard empty Tidal token save", n))
    else:
        report.append(("Guard empty Tidal token save", 0))

    return content, report


def scan_app_py():
    if not os.path.exists(APP_PY):
        return
    try:
        with open(APP_PY, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception:
        return
    # Heuristic: a long-ish token-looking literal assigned to a tidal var
    suspicious = re.search(r'(?i)tidal[_a-z0-9]*\s*=\s*[\"\'][A-Za-z0-9_\-]{12,}[\"\']', src)
    env_based = 'os.environ' in src and 'TIDAL_TOKEN' in src
    if suspicious and not env_based:
        print("  \u26a0  app.py may still contain a hardcoded Tidal token. Move it to")
        print("     os.environ.get('TIDAL_TOKEN', '') and ROTATE the exposed token.")
    elif env_based:
        print("  \u2713  app.py reads TIDAL_TOKEN from the environment. Good.")


def print_report(report):
    applied = 0
    for label, count in report:
        mark = "APPLIED" if count else "skip   "
        extra = (" x%d" % count) if count > 1 else ""
        print("  [%s] %s%s" % (mark, label, extra))
        applied += count
    return applied


def run(dry_run=False):
    if not os.path.exists(TARGET):
        print("ERROR: %s not found. Run this from the repository root." % TARGET)
        return 1
    with open(TARGET, "r", encoding="utf-8") as f:
        original = f.read()

    updated, report = apply_fixes(original)
    print("Pipeline fixes for %s:" % TARGET)
    applied = print_report(report)

    if dry_run:
        print("\nDry run — no files written. %d change(s) would be made." % applied)
        scan_app_py()
        return 0

    if updated != original:
        bak = TARGET + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(TARGET, bak)
            print("\nBackup written: %s" % bak)
        with open(TARGET, "w", encoding="utf-8") as f:
            f.write(updated)
        print("Saved: %s (%d change groups applied)" % (TARGET, applied))
    else:
        print("\nNothing to change — file already corrected. ✓")

    scan_app_py()
    return 0


# --------------------------------------------------------------------------
# Self test
# --------------------------------------------------------------------------
FIXTURE = '''
<button id="btn-process-guests" class="inline-flex items-center justify-center gap-1.5"><svg x="1"><path d="a"></path></svg><svg x="1"><path d="a"></path></svg><svg x="1"><path d="a"></path></svg>Process Guests Only</button>
<button id="btn-fetch-avatars" class="inline-flex items-center justify-center gap-1.5"><svg y="2"><rect/></svg><svg y="2"><rect/></svg><svg y="2"><rect/></svg>Fetch Avatars Only</button>
<button class="bell"><svg w="20"><title>Notifications</title><title>Notifications</title><title>Notifications</title><path d="m"></path></svg></button>
<script>
        function escapeHTML(str) { return str; }
        async function loadStatus() {
            try {
                const r = await fetch('/api/archive/status');
            } catch (err) {
                console.error("Error fetching status:", err);
            }
        }
        async function saveConfig() {
            const tidalToken = document.getElementById('tidal-token').value.trim();
            try {
                await fetch('/api/archive/status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        path,
                        tidalToken,
                        syncDeezerAvatars,
                        generateCatalogs,
                        reconcileShortcuts
                    })
                });
            } catch (err) { console.error(err); }
        }
        function renderLogs(logs) {
            const consoleBody = document.getElementById('console-body');
            if (!consoleBody) return;
            
            if (!logs || logs.length === 0) { return; }
            let html = '';
            logs.forEach(log => {
                html += `<div><span class="text-text-muted">[${log.time}]</span> <span class="${levelClass}">${log.level}:</span> ${escapeHTML(log.message)}</div>`;
            });
            consoleBody.innerHTML = html;
        }
</script>
'''


def selftest():
    out, report = apply_fixes(FIXTURE)
    counts = dict(report)
    checks = []

    checks.append(("icons collapsed", out.count('<svg x="1">') == 1 and out.count('<svg y="2">') == 1))
    checks.append(("titles collapsed", out.count('<title>Notifications</title>') == 1))
    checks.append(("time escaped", '[${escapeHTML(log.time)}]' in out))
    checks.append(("level escaped", '>${escapeHTML(log.level)}:</span>' in out))
    checks.append(("log cap", 'logs.slice(-500)' in out))
    checks.append(("sig guard", 'dataset.logSig' in out))
    checks.append(("polling recovery", 'Cannot reach backend' in out and 'if (!activeTimer) startPolling(4000);' in out))
    checks.append(("token guard", '__p.tidalToken' in out and out.count('tidalToken,\n') == 0))

    # idempotency: second pass makes no changes
    out2, report2 = apply_fixes(out)
    idempotent = (out2 == out) and all(c == 0 for _, c in report2)
    checks.append(("idempotent second run", idempotent))

    ok = True
    for label, passed in checks:
        print("  [%s] %s" % ("PASS" if passed else "FAIL", label))
        ok = ok and passed
    print("selftest: %s" % ("OK - all checks passed" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(run(dry_run=("--dry-run" in sys.argv)))
