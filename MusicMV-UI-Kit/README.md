# MusicMV — UI Fix Kit

This kit corrects the UI/UX issues found in the **MusicMV** media‑sourcing
terminal (the Flask app with the **Intel Search**, **Local Library**, and
**Control Panel** views). It contains:

| File | What it is |
|------|------------|
| `apply_ui_fixes.py` | One‑shot, idempotent fixer that edits the real templates in place |
| `UI_AUDIT.md` | Full audit — every issue, where it lives, and the fix |
| `fixes/tailwind_config.snippet.js` | The corrected Tailwind `theme.extend` block (reference) |
| `fixes/icons.md` | The SVG icon set used for the export / download / action buttons |

---

## What MusicMV is

MusicMV is a local Flask control terminal for sourcing and organizing music
videos. Three routes render three templates:

- `/` → `src/templates/intel.html` — **Media Sourcing** (TIDAL search, Billboard
  chart explorer, artist chart history, downloads drawer).
- `/library` → `src/templates/library.html` — **Local Library Explorer**
  (sorted artists, missing‑track auditor).
- `/pipeline` → `src/templates/pipeline.html` — **Control Panel** (pipeline
  config + live log console).

Styling is Tailwind via the play CDN, with a shared dark glass/violet+cyan theme.

---

## How to apply the fixes

From the repo root (the folder that contains `src/templates/`):

```bash
python3 apply_ui_fixes.py
```

Or point it at the repo explicitly:

```bash
python3 apply_ui_fixes.py /path/to/MusicMV
```

- The script prints an **APPLIED / SKIPPED** report for every change.
- It is **idempotent** — running it twice does nothing the second time.
- The first time a file changes, a `*.bak` backup is written next to it. To roll
  back: `mv src/templates/intel.html.bak src/templates/intel.html` (etc.).

Verify the edit logic without touching your files:

```bash
python3 apply_ui_fixes.py --selftest
```

---

## What gets fixed

1. **Missing icons** on the text‑only **Export Links / Export Catalog / Export
   Chart / Export History** buttons (intel), **Clear Finished** (intel), and
   **Process Guests Only / Fetch Avatars Only** (pipeline) — a consistent
   download / action icon is added and the buttons become aligned flex rows.
2. **Color harmony** — the off‑palette `emerald-400/500` accent in the *Artist
   Chart History* column is unified to a single defined `terminal-green` token
   that already exists on the Control Panel, and that token is added to the
   Intel palette so both pages use the exact same green.
3. **Fonts actually load** — `font-display-lg` and `font-label-sm` were used on
   every heading but never defined, so the page silently fell back to the
   default sans stack. They are now wired into the Tailwind config (Outfit for
   display, Inter for body, Fira Code for the console).
4. **Accessibility** — the icon‑only bell and globe buttons in the Control Panel
   header get accessible names / tooltips.
5. **Consistency** — the sidebar label for the library page is normalized to
   *Local Library* across all pages (was *Library Explorer* on the pipeline).
6. **Security** — the hardcoded TIDAL token is removed from the page source.

---

## Action still required from you (not auto‑changed)

- **Rotate the TIDAL token** and move it out of the backend. The fixer removes
  it from the HTML and *warns* if it is still hardcoded in any `.py` file, but
  it will not edit your Python. Recommended:

  ```python
  import os
  TIDAL_TOKEN = os.environ.get("TIDAL_TOKEN", "")
  ```

  then run with `TIDAL_TOKEN=... python app.py`.

- **Tailwind CDN** (`cdn.tailwindcss.com`) is a dev‑only build. For production,
  compile Tailwind to a static CSS file. This is a build‑pipeline change and is
  intentionally left to you.

See `UI_AUDIT.md` for the complete, location‑by‑location breakdown.
