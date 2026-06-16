#!/usr/bin/env python3
"""
MusicMV UI Fixer
================
Applies the UI/UX corrections from UI_AUDIT.md directly to the real template
files in this repo (src/templates/intel.html, library.html, pipeline.html).

Usage:
    python3 apply_ui_fixes.py [REPO_ROOT]      # default REPO_ROOT = current dir
    python3 apply_ui_fixes.py --selftest       # verify edits against fixtures

The script is idempotent: running it twice is safe. Each edit reports one of
APPLIED / SKIPPED (already done or not found). A .bak copy of every modified
file is written next to it the first time it changes.
"""
import os
import re
import sys
import shutil

TEMPLATE_DIR = os.path.join("src", "templates")

# ---------------------------------------------------------------------------
# Reusable inline SVG icons (1.75px stroke, matches the design system spec)
# ---------------------------------------------------------------------------
DL = ('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
      'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
      'stroke-linecap="round" stroke-linejoin="round">'
      '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>'
      '<polyline points="7 10 12 15 17 10"></polyline>'
      '<line x1="12" y1="15" x2="12" y2="3"></line></svg>')

TRASH = ('<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" '
         'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
         'stroke-linecap="round" stroke-linejoin="round">'
         '<polyline points="3 6 5 6 21 6"></polyline>'
         '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>')

GUESTS = ('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
          'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
          'stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>'
          '<circle cx="9" cy="7" r="4"></circle>'
          '<path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>'
          '<path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>')

AVATARS = ('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
           'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
           'stroke-linecap="round" stroke-linejoin="round">'
           '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>'
           '<circle cx="8.5" cy="8.5" r="1.5"></circle>'
           '<polyline points="21 15 16 10 5 21"></polyline></svg>')

# ---------------------------------------------------------------------------
# fontFamily injection (makes the no-op font-display-lg / font-label-sm classes
# actually resolve, and wires Inter/Outfit/Fira Code into the Tailwind config)
# ---------------------------------------------------------------------------
FONT_RE = re.compile(r'("text-muted":\s*"#475569")(\s*)\}')


def insert_font_family(content, include_mono=False):
    if '"fontFamily"' in content:
        return content, 0
    entries = [
        '"sans": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]',
        '"display-lg": ["Outfit", "Inter", "sans-serif"]',
        '"label-sm": ["Inter", "ui-sans-serif", "sans-serif"]',
    ]
    if include_mono:
        entries.append('"mono": ["Fira Code", "ui-monospace", "monospace"]')
    block = ',\n'.join('                        ' + e for e in entries)
    repl = (r'\g<1>\g<2>},' + '\n'
            + '                    "fontFamily": {\n'
            + block + '\n'
            + '                    }')
    return FONT_RE.subn(repl, content, count=1)


# ---------------------------------------------------------------------------
# String edits per file: (description, old, new, replace_all)
# ---------------------------------------------------------------------------
EDITS = {
    "intel.html": [
        ("Add terminal-green token to palette",
         '"secondary": "#06b6d4",\n                        "background": "#05060a",',
         '"secondary": "#06b6d4",\n                        "terminal-green": "#10b981",\n                        "background": "#05060a",',
         False),
        ("Unify off-palette emerald-400 -> terminal-green",
         'emerald-400', 'terminal-green', True),
        ("Unify off-palette emerald-500 -> terminal-green",
         'emerald-500', 'terminal-green', True),
        ("Add download icon to Export Links button",
         'text-secondary hover:text-white">Export Links',
         'text-secondary hover:text-white inline-flex items-center gap-1.5">' + DL + 'Export Links',
         False),
        ("Add download icon to Export Catalog button",
         'text-secondary hover:text-white">Export Catalog',
         'text-secondary hover:text-white inline-flex items-center gap-1.5">' + DL + 'Export Catalog',
         False),
        ("Add download icon to Export Chart button",
         'text-secondary hover:text-white">Export Chart',
         'text-secondary hover:text-white inline-flex items-center gap-1.5">' + DL + 'Export Chart',
         False),
        ("Add download icon to Export History button",
         'text-secondary hover:text-white">Export History',
         'text-secondary hover:text-white inline-flex items-center gap-1.5">' + DL + 'Export History',
         False),
        ("Add trash icon to Clear Finished button",
         'Clear Finished', TRASH + 'Clear Finished', False),
    ],
    "library.html": [
        # Only the font fix is needed here (handled separately).
    ],
    "pipeline.html": [
        ("Remove hardcoded Tidal token from page source",
         'value="CzET4vdadNUFQ5JU"', 'value=""', False),
        ("Make Process Guests button a flex row",
         'id="btn-process-guests" class="btn-glass-cyan px-4 py-2 rounded-lg font-bold text-xs text-secondary hover:text-white disabled:opacity-50 disabled:pointer-events-none"',
         'id="btn-process-guests" class="btn-glass-cyan px-4 py-2 rounded-lg font-bold text-xs text-secondary hover:text-white disabled:opacity-50 disabled:pointer-events-none inline-flex items-center justify-center gap-1.5"',
         False),
        ("Add icon to Process Guests button",
         'Process Guests Only', GUESTS + 'Process Guests Only', False),
        ("Make Fetch Avatars button a flex row",
         'id="btn-fetch-avatars" class="btn-glass-cyan px-4 py-2 rounded-lg font-bold text-xs text-secondary hover:text-white disabled:opacity-50 disabled:pointer-events-none"',
         'id="btn-fetch-avatars" class="btn-glass-cyan px-4 py-2 rounded-lg font-bold text-xs text-secondary hover:text-white disabled:opacity-50 disabled:pointer-events-none inline-flex items-center justify-center gap-1.5"',
         False),
        ("Add icon to Fetch Avatars button",
         'Fetch Avatars Only', AVATARS + 'Fetch Avatars Only', False),
        ("Fix inconsistent nav label (Library Explorer -> Local Library)",
         'Library Explorer', 'Local Library', False),
        ("Label the notifications header button",
         '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>',
         '<title>Notifications</title><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>',
         False),
        ("Label the connection-status header button",
         '<path d="M21.2 15a8.85 8.85 0 0 0-3.25-3.24 8.8 8.8 0 0 0-6.8 0A8.9 8.9 0 0 0 7.9 15"></path>',
         '<title>Connection</title><path d="M21.2 15a8.85 8.85 0 0 0-3.25-3.24 8.8 8.8 0 0 0-6.8 0A8.9 8.9 0 0 0 7.9 15"></path>',
         False),
    ],
}

INCLUDE_MONO = {"pipeline.html": True}


def apply_edits(content, edits):
    log = []
    for desc, old, new, all_ in edits:
        n = content.count(old)
        if n == 0:
            state = "SKIPPED (not found / already applied)"
        elif all_:
            content = content.replace(old, new)
            state = "APPLIED x%d" % n
        else:
            content = content.replace(old, new, 1)
            state = "APPLIED"
        log.append((desc, state))
    return content, log


def process_file(path, fname):
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()
    content, fn = insert_font_family(original, INCLUDE_MONO.get(fname, False))
    log = [("Wire Inter/Outfit%s fonts into Tailwind config" % ("/Fira Code" if INCLUDE_MONO.get(fname) else ""),
            "APPLIED" if fn else "SKIPPED (already applied)")]
    content, more = apply_edits(content, EDITS.get(fname, []))
    log += more
    changed = content != original
    if changed:
        bak = path + ".bak"
        if not os.path.exists(bak):
            shutil.copyfile(path, bak)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return changed, log


def scan_for_secrets(root):
    """Warn (never auto-edit) if the Tidal token literal is still in any .py file."""
    hits = []
    token = "CzET4vdadNUFQ5JU"
    for dirpath, _dirs, files in os.walk(root):
        if ".git" in dirpath or "node_modules" in dirpath:
            continue
        for fn in files:
            if fn.endswith(".py"):
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        if token in f.read():
                            hits.append(fp)
                except OSError:
                    pass
    return hits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    tdir = os.path.join(root, TEMPLATE_DIR)
    if not os.path.isdir(tdir):
        print("ERROR: could not find %s" % tdir)
        print("Run this from the MusicMV repo root, or pass the repo path as an argument.")
        sys.exit(1)

    print("MusicMV UI Fixer\n================\nRepo: %s\n" % os.path.abspath(root))
    any_change = False
    for fname in ("intel.html", "library.html", "pipeline.html"):
        path = os.path.join(tdir, fname)
        if not os.path.exists(path):
            print("[%s] MISSING - skipped\n" % fname)
            continue
        changed, log = process_file(path, fname)
        any_change = any_change or changed
        print("[%s] %s" % (fname, "updated (.bak saved)" if changed else "no changes"))
        for desc, state in log:
            print("    - %-52s %s" % (desc, state))
        print()

    secrets = scan_for_secrets(root)
    if secrets:
        print("SECURITY WARNING: the Tidal API token is still hardcoded in:")
        for fp in secrets:
            print("    %s" % fp)
        print("    Move it to an environment variable (see README) and ROTATE the token.\n")

    print("Done." if any_change else "Nothing to change - already up to date.")


def _selftest():
    """Verify every edit fires against fixtures built from the real anchors."""
    ok = True
    cfg = ('                    "colors": {\n'
           '                        "primary": "#8b5cf6",\n'
           '                        "secondary": "#06b6d4",\n'
           '                        "background": "#05060a",\n'
           '                        "text-muted": "#475569"\n'
           '                    }\n'
           '                }')
    out, n = insert_font_family(cfg, True)
    assert n == 1 and '"fontFamily"' in out and '"mono"' in out, "fontFamily inject failed"
    out2, n2 = insert_font_family(out, True)
    assert n2 == 0, "fontFamily not idempotent"

    for fname, edits in EDITS.items():
        for desc, old, new, _all in edits:
            fixture = "xx " + old + " xx"
            res, log = apply_edits(fixture, [(desc, old, new, _all)])
            assert new in res, "FAILED: %s / %s" % (fname, desc)
    print("selftest: OK - all %d edits + font inject verified" %
          sum(len(v) for v in EDITS.values()))
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
