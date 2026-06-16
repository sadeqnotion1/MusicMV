# MusicMV Fix Kit v3

Four fixes for the **Tidal Sourcing** page (`intel.html`) and the **Pipeline** console (`pipeline.html`).

| # | Issue | File | What changes |
|---|-------|------|--------------|
| 1 | "Export YouTube Links" exported every matched track, including ones already downloaded | `intel.html` | `exportYouTubeLinks()` now filters out tracks where `isDownloaded === true`, so only links **not** in your local library are exported. If everything is already in the library it tells you instead of exporting an empty file. |
| 2 | Pipeline console didn't follow new log lines to the bottom | `pipeline.html` | The scroll listener now ignores the programmatic scroll that fires when logs re-render, so auto-scroll sticks to the newest line unless you deliberately scroll up. |
| 3 | Tidal icons not visible | `intel.html` | The sidebar + artist-search Tidal logos used an oversized `viewBox` (`0 -373 1453 1453`) that shrank the artwork to a few pixels. Corrected to the tight crop `532 0 387 257` (same as the working card icon). |
| 4 | Tidal Sourcing colors clashed | `intel.html` | The neon `#00f0ff` Tidal accent is replaced with the palette `secondary` `#06b6d4` so it harmonizes with the rest of the UI. |

## How to run

From your repo root (or anywhere inside it — the script auto-detects `src/templates`):

```bash
# 1. Preview (writes nothing)
python3 apply_fixes_v3.py --dry-run

# 2. Apply
python3 apply_fixes_v3.py

# 3. (optional) point at an explicit repo root
python3 apply_fixes_v3.py --root /path/to/MusicMV
```

A one-time `*.bak` backup is written next to each modified file the first time it changes. Re-running is safe — the script is **idempotent** and will report `skip (already applied)`.

## Verify

```bash
python3 apply_fixes_v3.py --selftest   # built-in tests, no repo needed
```

After applying:

```bash
git diff src/templates/intel.html src/templates/pipeline.html
git add -A && git commit -m "UI/UX fixes v3: export filter, log auto-scroll, Tidal icon + color harmony"
git push
```

Then hard-refresh the browser (Ctrl/Cmd+Shift+R) to clear cached templates.

## Notes
* Fix #1 is client-side: it filters the payload sent to `/api/youtube/export_all`. No backend change required — the catalog export (`Export Catalog` / `exportAsText`) is intentionally left untouched so it still includes everything.
* Reminder from earlier: rotate your Tidal token (treat the old one as compromised) and set it via the `TIDAL_TOKEN` environment variable.
