# MusicMV — Audit & Fix Notes (v3)

Audited against live `master` commit `ad89245` of `sadeqnotion1/MusicMV`.

---

## #1 — Export only YouTube links NOT in the local library

**Where:** `intel.html` → `exportYouTubeLinks(btn)`

**Found:** the handler posts the entire `loadedTidalVideos` object
(`{ priority:[], standard:[], excluded:[] }`) to `/api/youtube/export_all`.
Every card carries an `isDownloaded` boolean (`true` = already in your local
library, shown as the green “✓ In Library” badge), but it was never used to
filter the export.

**Fix:** added `__filterNotInLibrary()` which strips entries with
`isDownloaded === true` from each category, and rewired the request body to
send the filtered set. Added a guard that aborts with a friendly message when
nothing remains. The full **catalog** export (`exportAsText`) is deliberately
left unchanged.

---

## #2 — Pipeline logs don't auto-scroll to the end

**Where:** `pipeline.html` → `renderLogs()` + the `console-body` scroll listener

**Found:** `renderLogs()` replaces `consoleBody.innerHTML`, which resets
`scrollTop`. That reset dispatches a `scroll` event; the listener then sees the
view is no longer near the bottom and sets `hasUserScrolledConsole = true`,
which suppresses the next auto-scroll. The result is the console getting
“stuck” and not following new lines.

**Fix:** `renderLogs()` records `window.__consoleLastRender = Date.now()` right
after it programmatically scrolls. The scroll listener ignores any scroll event
that arrives within 200 ms of a render (i.e. the programmatic one), so
`hasUserScrolledConsole` now reflects only **real** user scrolling. Default
behavior (no manual scroll) keeps the console pinned to the newest line.

---

## #3 — Tidal icons not visible

**Where:** `intel.html` — sidebar nav Tidal icon + artist-search Tidal icon

**Found:** both inline Tidal SVGs use `viewBox="0 -373 1453 1453"`. The actual
logo paths only occupy roughly `x:532–919, y:0–257`, so inside that giant
viewBox the artwork renders at ~3–4 px in a 16 px box — effectively invisible.
The working card icon (`tidalIconSvg` const) uses the correct tight crop.

**Fix:** changed both occurrences of `viewBox="0 -373 1453 1453"` to
`viewBox="532 0 387 257"`.

---

## #4 — Tidal Sourcing unharmonized colors

**Where:** `intel.html` — nav icon `text-[#00f0ff]`, nav SVG `fill:#00f0ff`,
and the `tidalIconSvg` const `fill:#00f0ff`

**Found:** the Tidal accent used neon `#00f0ff`, which is not in the palette
(`primary #8b5cf6`, `secondary #06b6d4`, `terminal-green #10b981`, …). It
clashed with the muted cyan secondary used elsewhere.

**Fix:** replaced all `#00f0ff` with the palette `secondary #06b6d4` (3
occurrences). The Tidal accent now matches the “Watch on Tidal” card styling
and the rest of the UI.

---

## Safety
* Idempotent: guards skip already-applied edits; second run is a no-op.
* One-time `.bak` backup per file.
* `--dry-run` previews; `--selftest` validates transform + idempotency offline.
