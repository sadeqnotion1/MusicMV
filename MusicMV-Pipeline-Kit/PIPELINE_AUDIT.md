# MusicMV — Pipeline (Control Panel) Audit

Scope: `src/templates/pipeline.html`. Three areas requested — (1) diagnose /
functionality, (2) log-viewer quality, (3) UI. Findings below reflect the
**post-fix** state of the file (after `apply_ui_fixes.py` was run multiple times).

---

## 0. Regression introduced by repeated fix runs (CRITICAL)

`apply_ui_fixes.py` was applied more than once and its icon/title inserts were
not idempotent, so they **stacked**:

- **Process Guests Only** button → **3 identical “users” `<svg>` icons** (expected 1).
- **Fetch Avatars Only** button → **3 identical “image” `<svg>` icons** (expected 1).
- **Notifications** header button → `<title>Notifications</title>` **×3** (expected 1).
- **Connection** header button → `<title>Connection</title>` **×3** (expected 1).

Only the first `<title>` in an SVG is honored; the extras are invalid. The
tripled icons are a visible layout bug. Fixed by edits #1 and #2 in
`apply_pipeline_fixes.py` (and the new script is idempotent).

---

## 1. Pipeline diagnose — does it work correctly?

The control flow is structurally sound:
`loadStatus() → updatePipelineStatus() → startPolling()`, and
`run*() → saveConfig() → POST /api/archive/run → pollLogs()`. Run/idle button and
input disabling is correct, and polling speeds up (1s) while running, slows (4s)
when idle.

**Gaps:**

- **Polling never recovers from an initial failure.** `startPolling()` is only
  called inside `updatePipelineStatus()`, which only runs when
  `/api/archive/status` returns `status === 'success'`. On load it does a
  one-shot `loadStatus().then(pollLogs)`. If that first call fails (backend down,
  bad root path), no interval is ever set — stats stay `-`, the console stays
  stuck on **“Loading logs…”**, and nothing retries. Failures only hit
  `console.error`. → Fixed by edit #6 (fallback `startPolling` + visible ERROR).
- **Empty-token clobber after the env-var change.** `#tidal-token` now loads
  blank, but `saveConfig()` runs on every input blur/change (and before each
  run) and POSTs `tidalToken: ''`. If the backend persists that config, the UI
  silently overwrites the token with an empty string. → Fixed by edit #7 (omit
  the key when blank).
- **Minor:** `runMasterPipeline` sends `historyDays: 7`; the guests/avatars runs
  omit it. Likely fine via backend default, but inconsistent.

---

## 2. Log viewer / log quality

**Strengths:** color-coded levels (SUCCESS/OK green, WARNING amber, ERROR red,
INFO cyan, DEBUG muted), timestamps, monospace terminal chrome (traffic lights +
`system_orchestrator.log`), auto-scroll with manual-scroll detection, blink
cursor, idle state.

**Issues & fixes:**

- **Full `innerHTML` rebuild every poll** (every 1s while running) wiped any text
  selection — you couldn’t reliably select/copy a log line during a run — and
  caused flicker. → Edit #5 skips re-render when the log set is unchanged.
- **No log cap / virtualization.** Re-rendering the entire array each poll grows
  memory/CPU on long runs. → Edit #4 caps to the last 500 lines.
- **Inconsistent escaping.** Only `log.message` went through `escapeHTML()`;
  `log.time` and `log.level` were injected raw. → Edit #3 escapes all three.
- **Mixed time sources.** Entries use server `log.time`; the trailing blink line
  uses client `new Date().toLocaleTimeString()` — possible format/timezone
  mismatch in the same view. (Left as-is; cosmetic.)
- **No log controls** (clear / copy-all / download / pause-autoscroll / jump to
  bottom). Recommended enhancement, not included here.
- **DEBUG/muted contrast** (`#475569` on black) is low and hard to read.

---

## 3. Other UI issues

- Tripled icons/titles — see section 0 (the headline bug).
- DEBUG/muted log text contrast on the pure-black console.
- **Tailwind via CDN** — dev-only, emits a console warning; fine locally, not for
  production.
- Layout itself (fixed 260px sidebar + `ml-[260px]` main, 1/3 config + 2/3
  console split, ambient glow) is clean and consistent — no issues.

---

## Fix coverage map

| Finding | Status |
|---------|--------|
| Tripled button icons | Fixed (edit #1) |
| Tripled `<title>` tags | Fixed (edit #2) |
| Unescaped log.time / log.level | Fixed (edit #3) |
| Unbounded log DOM | Fixed (edit #4) |
| Selection wiped on poll | Fixed (edit #5) |
| Polling frozen on first failure | Fixed (edit #6) |
| Empty token clobber | Fixed (edit #7) |
| Hardcoded token in app.py | Scan + warn (manual rotate) |
| DEBUG contrast / Tailwind CDN / log controls | Documented (manual) |
