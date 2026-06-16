#!/usr/bin/env python3
"""
MusicMV — Fix Kit v3
====================
Addresses 4 reported issues (Tidal Sourcing page + Pipeline console):

  #1  Export YouTube Links should only export tracks NOT already in the
      local library.                                   [intel.html]
  #2  Pipeline console logs don't auto-scroll to the newest line.
                                                       [pipeline.html]
  #3  Tidal icons not visible (oversized SVG viewBox).  [intel.html]
  #4  Tidal Sourcing uses off-palette neon cyan (#00f0ff) instead of the
      palette secondary (#06b6d4).                      [intel.html]

The script is IDEMPOTENT: running it twice makes no further changes.
A one-time .bak backup is written for each modified file.

Usage:
    python3 apply_fixes_v3.py                # apply fixes in place
    python3 apply_fixes_v3.py --dry-run      # show what would change, write nothing
    python3 apply_fixes_v3.py --selftest     # run built-in tests (no repo needed)
    python3 apply_fixes_v3.py --root <path>  # repo root (default: auto-detect)
"""
import argparse
import os
import sys

# ----------------------------------------------------------------------------
# Color / palette constants
# ----------------------------------------------------------------------------
OFF_PALETTE_CYAN = "#00f0ff"        # neon cyan currently used for Tidal accent
PALETTE_SECONDARY = "#06b6d4"       # harmonized palette secondary
BAD_VIEWBOX = 'viewBox="0 -373 1453 1453"'
GOOD_VIEWBOX = 'viewBox="532 0 387 257"'


class Edit:
    """A single guarded string edit."""
    def __init__(self, name, old, new, replace_all=False, guard=None, required=True):
        self.name = name
        self.old = old
        self.new = new
        self.replace_all = replace_all
        # guard(content) -> True means "already applied, skip"
        self.guard = guard
        self.required = required

    def apply(self, content):
        """Return (new_content, count, status_msg)."""
        if self.guard and self.guard(content):
            return content, 0, "skip (already applied)"
        if self.old not in content:
            if self.required:
                return content, 0, "NOT FOUND (anchor missing)"
            return content, 0, "skip (anchor absent, optional)"
        if self.replace_all:
            count = content.count(self.old)
            content = content.replace(self.old, self.new)
        else:
            count = 1
            content = content.replace(self.old, self.new, 1)
        return content, count, "applied"


# ----------------------------------------------------------------------------
# intel.html edits
# ----------------------------------------------------------------------------

# --- #1: filter export to exclude tracks already in the local library --------
EXPORT_OLD = (
    "        async function exportYouTubeLinks(btn) {\n"
    '            if (!loadedTidalVideos) return alert("No Tidal videos loaded to export.");\n'
    "            const artist = tidalArtistName.textContent;\n"
    "            const originalHtml = btn.textContent;\n"
    "            btn.disabled = true;\n"
    "            btn.textContent = 'Exporting...';\n"
    "            try {\n"
    "                const response = await fetch('/api/youtube/export_all', {\n"
    "                    method: 'POST',\n"
    "                    headers: { 'Content-Type': 'application/json' },\n"
    "                    body: JSON.stringify({ artistName: artist, videos: loadedTidalVideos })\n"
    "                });"
)
EXPORT_NEW = (
    "        // [fix v3 #1] Returns a copy of loadedTidalVideos with tracks already in the\n"
    "        // local library (isDownloaded === true) removed, so we only export NEW YouTube links.\n"
    "        function __filterNotInLibrary(vids) {\n"
    "            if (!vids) return vids;\n"
    "            if (Array.isArray(vids)) return vids.filter(v => !(v && v.isDownloaded));\n"
    "            const out = {};\n"
    "            for (const k of Object.keys(vids)) {\n"
    "                out[k] = Array.isArray(vids[k]) ? vids[k].filter(v => !(v && v.isDownloaded)) : vids[k];\n"
    "            }\n"
    "            return out;\n"
    "        }\n"
    "\n"
    "        async function exportYouTubeLinks(btn) {\n"
    '            if (!loadedTidalVideos) return alert("No Tidal videos loaded to export.");\n'
    "            const artist = tidalArtistName.textContent;\n"
    "            const exportVideos = __filterNotInLibrary(loadedTidalVideos);\n"
    "            const __remaining = Array.isArray(exportVideos)\n"
    "                ? exportVideos.length\n"
    "                : Object.keys(exportVideos).reduce((n, k) => n + (Array.isArray(exportVideos[k]) ? exportVideos[k].length : 0), 0);\n"
    '            if (__remaining === 0) return alert("All matched tracks are already in your local library \\u2014 no new YouTube links to export.");\n'
    "            const originalHtml = btn.textContent;\n"
    "            btn.disabled = true;\n"
    "            btn.textContent = 'Exporting...';\n"
    "            try {\n"
    "                const response = await fetch('/api/youtube/export_all', {\n"
    "                    method: 'POST',\n"
    "                    headers: { 'Content-Type': 'application/json' },\n"
    "                    body: JSON.stringify({ artistName: artist, videos: exportVideos })\n"
    "                });"
)


def intel_edits():
    return [
        Edit(
            "#1 export filter (skip in-library tracks)",
            EXPORT_OLD, EXPORT_NEW,
            guard=lambda c: "__filterNotInLibrary" in c,
        ),
        Edit(
            "#3 Tidal icon viewBox (sidebar + artist search)",
            BAD_VIEWBOX, GOOD_VIEWBOX, replace_all=True,
            guard=lambda c: BAD_VIEWBOX not in c,
        ),
        Edit(
            "#4 harmonize Tidal accent color (#00f0ff -> #06b6d4)",
            OFF_PALETTE_CYAN, PALETTE_SECONDARY, replace_all=True,
            guard=lambda c: OFF_PALETTE_CYAN not in c,
        ),
    ]


# ----------------------------------------------------------------------------
# pipeline.html edits  (#2 auto-scroll)
# ----------------------------------------------------------------------------
SCROLL_TAIL_OLD = (
    "            if (isScrolledToBottom || !window.hasUserScrolledConsole) {\n"
    "                consoleBody.scrollTop = consoleBody.scrollHeight;\n"
    "            }\n"
    "        }\n"
    "\n"
    "        // Track if user scrolled the console manually"
)
SCROLL_TAIL_NEW = (
    "            if (isScrolledToBottom || window.hasUserScrolledConsole !== true) {\n"
    "                consoleBody.scrollTop = consoleBody.scrollHeight;\n"
    "            }\n"
    "            // [fix v3 #2] mark render time so the scroll listener can ignore the\n"
    "            // programmatic scroll event caused by replacing innerHTML above.\n"
    "            window.__consoleLastRender = Date.now();\n"
    "        }\n"
    "\n"
    "        // Track if user scrolled the console manually"
)

LISTENER_OLD = (
    "        document.getElementById('console-body').addEventListener('scroll', function(e) {\n"
    "            const el = e.target;\n"
    "            // User is near the bottom\n"
    "            if (el.scrollHeight - el.clientHeight <= el.scrollTop + 30) {\n"
    "                window.hasUserScrolledConsole = false;\n"
    "            } else {\n"
    "                window.hasUserScrolledConsole = true;\n"
    "            }\n"
    "        });"
)
LISTENER_NEW = (
    "        document.getElementById('console-body').addEventListener('scroll', function(e) {\n"
    "            // [fix v3 #2] ignore scroll events fired by the programmatic innerHTML\n"
    "            // re-render so genuine user intent isn't overwritten.\n"
    "            if (window.__consoleLastRender && (Date.now() - window.__consoleLastRender) < 200) return;\n"
    "            const el = e.target;\n"
    "            // User is near the bottom\n"
    "            if (el.scrollHeight - el.clientHeight <= el.scrollTop + 30) {\n"
    "                window.hasUserScrolledConsole = false;\n"
    "            } else {\n"
    "                window.hasUserScrolledConsole = true;\n"
    "            }\n"
    "        });"
)


def pipeline_edits():
    return [
        Edit(
            "#2 auto-scroll render timestamp",
            SCROLL_TAIL_OLD, SCROLL_TAIL_NEW,
            guard=lambda c: "__consoleLastRender = Date.now()" in c,
        ),
        Edit(
            "#2 scroll listener ignores programmatic scrolls",
            LISTENER_OLD, LISTENER_NEW,
            guard=lambda c: "ignore scroll events fired by the programmatic" in c,
        ),
    ]


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------
FILES = {
    "intel.html": intel_edits,
    "pipeline.html": pipeline_edits,
}


def find_file(root, name):
    candidates = [
        os.path.join(root, "src", "templates", name),
        os.path.join(root, "templates", name),
        os.path.join(root, name),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    # last resort: walk
    for dirpath, _dirs, files in os.walk(root):
        if name in files:
            return os.path.join(dirpath, name)
    return None


def process_file(path, edits, dry_run):
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()
    content = original
    results = []
    for e in edits:
        content, count, status = e.apply(content)
        results.append((e.name, count, status))

    changed = content != original
    if changed and not dry_run:
        bak = path + ".bak"
        if not os.path.exists(bak):
            with open(bak, "w", encoding="utf-8") as f:
                f.write(original)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return changed, results


def run(root, dry_run):
    print(f"MusicMV Fix Kit v3  (root: {root}, dry-run: {dry_run})")
    print("=" * 64)
    any_missing = False
    for name, edit_fn in FILES.items():
        path = find_file(root, name)
        print(f"\n>> {name}")
        if not path:
            print(f"   !! could not locate {name} under {root}")
            any_missing = True
            continue
        print(f"   {path}")
        changed, results = process_file(path, edit_fn(), dry_run)
        for ename, count, status in results:
            mark = "NOT FOUND" in status
            if mark:
                any_missing = True
            print(f"     - {ename}: {status}" + (f" (x{count})" if count else ""))
        if changed:
            print("   => " + ("WOULD CHANGE" if dry_run else "UPDATED (.bak written)"))
        else:
            print("   => no change")
    print("\n" + "=" * 64)
    if any_missing:
        print("WARNING: some anchors were not found. Inspect the files above.")
        return 1
    print("Done.")
    return 0


# ----------------------------------------------------------------------------
# Self test
# ----------------------------------------------------------------------------
INTEL_SAMPLE = (
    '<span class="inline-flex items-center justify-center text-[#00f0ff]">'
    '<svg viewBox="0 -373 1453 1453" style="width:16px;height:16px;fill:#00f0ff !important;"></svg></span>\n'
    'const tidalIconSvg = `<svg viewBox="0 -373 1453 1453" style="fill:#00f0ff !important;"></svg>`;\n'
    + EXPORT_OLD + "\n"
)

PIPELINE_SAMPLE = (
    SCROLL_TAIL_OLD + "\n"
    + "        " + LISTENER_OLD.lstrip() + "\n"
)


def selftest():
    print("Running self-test...")
    ok = True

    # intel
    c = INTEL_SAMPLE
    for e in intel_edits():
        c, count, status = e.apply(c)
    assert "__filterNotInLibrary" in c, "#1 not applied"
    assert "videos: exportVideos" in c, "#1 body not rewired"
    assert BAD_VIEWBOX not in c, "#3 viewBox remains"
    assert GOOD_VIEWBOX in c, "#3 good viewBox missing"
    assert OFF_PALETTE_CYAN not in c, "#4 neon cyan remains"
    assert c.count(PALETTE_SECONDARY) >= 3, "#4 not all recolored"
    print("  intel.html edits: OK")

    # idempotency intel
    c2 = c
    total = 0
    for e in intel_edits():
        c2, count, status = e.apply(c2)
        total += count
    assert c2 == c and total == 0, "intel edits not idempotent"
    print("  intel.html idempotent: OK")

    # pipeline
    p = PIPELINE_SAMPLE
    for e in pipeline_edits():
        p, count, status = e.apply(p)
    assert "__consoleLastRender = Date.now()" in p, "#2 timestamp missing"
    assert "ignore scroll events fired by the programmatic" in p, "#2 listener guard missing"
    assert "window.hasUserScrolledConsole !== true" in p, "#2 condition not updated"
    print("  pipeline.html edits: OK")

    # idempotency pipeline
    p2 = p
    total = 0
    for e in pipeline_edits():
        p2, count, status = e.apply(p2)
        total += count
    assert p2 == p and total == 0, "pipeline edits not idempotent"
    print("  pipeline.html idempotent: OK")

    print("\nAll self-tests passed.")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="MusicMV Fix Kit v3")
    ap.add_argument("--root", default=None, help="Repo root (default: auto-detect)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    root = args.root
    if not root:
        # auto-detect: prefer a dir that contains src/templates
        here = os.getcwd()
        root = here
        for cand in (here, os.path.dirname(here)):
            if os.path.isdir(os.path.join(cand, "src", "templates")):
                root = cand
                break
    return run(root, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
