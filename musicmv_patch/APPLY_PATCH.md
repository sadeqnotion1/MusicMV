# MusicMV — Animated Dashboard PATCH (apply exactly, do not improvise)

You are a code-applying agent. Follow these steps literally. Do not redesign anything.
This patch is ADDITIVE: it adds a new page at `/dashboard` and read-only APIs. It must NOT
change any existing route, template, or pipeline behavior.

## STEP 1 — BACK UP THE REPO FIRST (mandatory)
Run from the repo root BEFORE doing anything else:
```bash
zip -r "../musicmv-backup-$(date +%Y%m%d-%H%M%S).zip" . -x "*.git/*" -x "*__pycache__/*"
```
Windows PowerShell:
```powershell
Compress-Archive -Path * -DestinationPath "..\musicmv-backup-$(Get-Date -Format yyyyMMdd-HHmmss).zip"
```
Verify the .zip exists and is non-empty. If STEP 5 fails, delete the new files and restore from this zip.

## STEP 2 — COPY THESE FILES IN (no edits to existing files yet)
Copy the files from this patch into the repo, keeping the same paths:
```
src/dashboard_api.py          (NEW)
src/templates/dashboard.html  (NEW)
src/static/dashboard.css      (NEW)
src/static/dashboard.js       (NEW)
```
These are all new files. They cannot break existing functionality.

## STEP 3 — MAKE EXACTLY ONE EDIT TO `src/app.py`
Open `src/app.py`. Find this line near the bottom:
```python
if __name__ == '__main__':
```
(It may use double quotes: `if __name__ == "__main__":` — either is fine.)

Insert these TWO lines on the lines IMMEDIATELY ABOVE it, at column 0 (no indentation):
```python
from dashboard_api import register_dashboard
register_dashboard(app, lambda: PIPELINE_PATH)
```

Result should look like:
```python
from dashboard_api import register_dashboard
register_dashboard(app, lambda: PIPELINE_PATH)

if __name__ == '__main__':
    ...existing code unchanged...
```

### IMPORTANT notes for this edit
- Do NOT put these two lines INSIDE the `if __name__` block, and do NOT put them AFTER
  `app.run(...)`. They must run at import time, above the `if __name__` guard.
- `PIPELINE_PATH` is an existing global in app.py (it is the archive root path). The `lambda`
  reads its live value at request time — do not change how `PIPELINE_PATH` is defined.
- If `PIPELINE_PATH` is defined LOWER in the file than where you inserted the two lines, that is
  fine: the lambda is only evaluated later when a request hits the dashboard.
- Change nothing else in app.py.

## STEP 4 — RUN AND OPEN
Start the app the normal way (e.g. `python app.py` from `src/`, or the usual launcher), then open:
```
http://127.0.0.1:<the port the app prints>/dashboard
```
The existing pages (`/`, `/library`, `/pipeline`) must still work exactly as before.

## STEP 5 — QUALITY GATE (keep only if ALL pass; else restore the STEP 1 zip)
- [ ] App still starts; `/`, `/library`, `/pipeline` work unchanged.
- [ ] `/dashboard` loads with no console errors.
- [ ] Stat cards count up: Artists / Music Videos / Collaborations / Missing.
- [ ] Artist grid shows real folders with their `avatar.jpg`; clicking an artist filters videos.
- [ ] Video cards show real titles + real file sizes (MB); clicking a card opens the file in the
      default player (via `/api/dashboard/reveal`).
- [ ] Missing drawer lists tracks from `music_videos.txt` with a working Deezer link button
      (or a clean "run the pipeline" empty state if no data).
- [ ] Animations are smooth and stop when the OS "reduce motion" setting is on.

---

## What this patch reads from YOUR real backend (so nothing is faked)
- Scans `PIPELINE_PATH` for artist subfolders.
- Primary videos = real video files in each folder (extensions from
  `manage_music_videos.video_extensions`, with a safe fallback list) + real byte sizes.
- Collaborations = the `.lnk` Windows shortcuts your dual-pass reconciliation creates.
- Avatars = the `avatar.jpg` your Deezer step downloads (served via `/api/dashboard/avatar/...`).
- Missing tracks = best-effort parse of the "Missing" section in each `music_videos.txt`
  (title + album + Deezer link). No data → friendly empty state, never fake rows.
- "Open" actions call `os.startfile` (Windows) on paths INSIDE `PIPELINE_PATH` only.

## Endpoints added (all additive, read-only except the safe open action)
- `GET  /dashboard`                      -> the page
- `GET  /api/dashboard`                  -> JSON: artists, per-artist videos/collabs/missing, totals
- `GET  /api/dashboard/avatar/<artist>`  -> serves that artist's avatar image
- `POST /api/dashboard/reveal`           -> opens a file/folder in Explorer (path must be inside PIPELINE_PATH)

No new Python dependencies. Pure stdlib + the Flask you already use.
