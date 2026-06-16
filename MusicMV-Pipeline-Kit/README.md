# MusicMV — Pipeline Fix Kit

_A drop-in correction pass for the **Control Panel** page (`src/templates/pipeline.html`), written so your AI terminal can apply it in one step._

## Context (read me first)

The earlier UI fix pass (`apply_ui_fixes.py`) was **run more than once**, and its
icon/title inserts were not idempotent — so they **stacked**. Right now
`pipeline.html` contains:

- **3 identical icons** on the **Process Guests Only** button (should be 1)
- **3 identical icons** on the **Fetch Avatars Only** button (should be 1)
- **3 `<title>` tags** inside the **Notifications** header button (should be 1)
- **3 `<title>` tags** inside the **Connection** header button (should be 1)

This kit undoes that duplication **and** lands the diagnose/log-viewer
improvements from the audit. **Every edit is guarded, so this script is safe to
run as many times as you like** — re-running does nothing once applied.

## How to run (for the AI terminal)

From the repository root:

```bash
python3 apply_pipeline_fixes.py            # apply in place (writes pipeline.html.bak once)
python3 apply_pipeline_fixes.py --dry-run  # preview the change report, write nothing
python3 apply_pipeline_fixes.py --selftest # run the built-in tests
```

No dependencies — standard library only. On Windows, if you hit
`PermissionError [Errno 13]`, clear the hidden/read-only attribute on the
templates first: `attrib -h -r src\templates\*.html`.

## What it corrects (7 guarded edits)

| # | Fix | Area |
|---|-----|------|
| 1 | Collapse tripled action-button **icons** → one each | UI |
| 2 | Collapse tripled **`<title>`** tags → one each | UI / a11y |
| 3 | **Escape** `log.time` and `log.level` (message was already escaped) | Log quality |
| 4 | **Cap** the log viewer to the last **500** lines (no unbounded DOM) | Log quality |
| 5 | **Skip re-render when logs are unchanged** — stops the console wiping your **text selection** every poll | Log quality |
| 6 | If the first `/api/archive/status` call fails, **keep polling** and show an **ERROR** line instead of freezing on “Loading logs…” | Diagnose |
| 7 | **Never POST an empty Tidal token** — prevents `saveConfig()` from clobbering the stored/env token now that the field loads blank | Diagnose / security |

The script also **scans `app.py`** and warns (without editing) if a Tidal token
literal still appears to be hardcoded.

## Manual follow-ups (the script will NOT do these)

1. **Rotate the Tidal token.** It was previously committed in source — treat it
   as compromised, regenerate it in Tidal, and set it as an env var:
   - PowerShell (session): `$env:TIDAL_TOKEN="your-new-token"`
   - Permanent: `setx TIDAL_TOKEN "your-new-token"` (reopen the terminal)
2. If the token was ever committed, **scrub git history** (BFG / `git filter-repo`)
   and add a secrets pattern to `.gitignore`.
3. **Tailwind via CDN** is dev-only (console warning). Switch to a Tailwind CLI
   build before any production deploy.

## Verify (2-minute smoke test)

Load the Control Panel and confirm:

- [ ] **Process Guests Only** shows exactly **one** users icon; **Fetch Avatars Only** shows exactly **one** image icon.
- [ ] Bell and globe header buttons each have **one** tooltip (`Notifications` / `Connection`).
- [ ] Start a run → logs stream, colors are correct, and you can **select/copy** a log line without it being wiped.
- [ ] Stop the backend → the console shows a red **“Cannot reach backend…”** line instead of freezing on “Loading logs…”.
- [ ] Leaving the **Tidal API Token** field blank no longer wipes the stored token.

Once it looks right, delete `pipeline.html.bak`.

## Files in this kit

- `apply_pipeline_fixes.py` — the idempotent fixer (run this)
- `PIPELINE_AUDIT.md` — full findings for the three audited areas
- `README.md` — this file
