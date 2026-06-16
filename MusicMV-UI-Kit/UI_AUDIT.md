# MusicMV — UI Audit

Scope: the three live templates rendered by the Flask app —
`src/templates/intel.html`, `library.html`, `pipeline.html`. Findings are based
on the actual template source on the `master` branch. Design‑spec markdown under
`redesign/` was used only for intent, not treated as implementation.

Severity: 🔴 high · 🟡 medium · 🟢 low/polish

---

## 1. Missing icons on export / download / action buttons

🟡 **intel.html — export buttons are text‑only.** The four action buttons in the
artist banner have no icon, while their sibling triggers (*Load Billboard Chart*,
*Query Billboard History*) do have SVGs — so the toolbar looks half‑finished.

- `#btn-export-links` (*Export Links*)
- `#btn-export-text` (*Export Catalog*)
- `#btn-export-chart` (*Export Chart*)
- `#btn-export-history` (*Export History*)

🟡 **intel.html — `Clear Finished`** in the downloads drawer is text‑only.

🟡 **pipeline.html — `#btn-process-guests` (*Process Guests Only*)** and
`#btn-fetch-avatars` (*Fetch Avatars Only*)** are text‑only, while the primary
*Run Master Pipeline* button has a play icon.

**Fix:** add a consistent 1.75px‑stroke download/action icon and make each button
an `inline-flex items-center gap-1.5` row so icon + label align. (The design
system spec calls for a downward‑tray download icon at 1.75px stroke.)

> Note: the per‑card play/download buttons (intel video cards, library missing‑
> track rows) are injected by JavaScript and use the existing `.btn-play-outline`
> style plus a `↓` affordance; they already carry an icon/affordance and were not
> part of this pass.

---

## 2. Color / harmony issues

🟡 **Off‑palette accent (intel.html).** The *Artist Chart History* column uses
`text-emerald-400`, `bg-emerald-500/10`, `border-emerald-500/30`,
`hover:bg-emerald-500/20`. Emerald is a third accent that is **not** in the
design system (which defines violet `#8b5cf6` primary + cyan `#06b6d4`
secondary), and it is a *different* green from the Control Panel.

🟡 **Two different greens.** `pipeline.html` defines a real token
`terminal-green: #10b981` and uses it for log success lines, while `intel.html`
uses Tailwind's stock `emerald-*` (`#34d399 / #10b981`) ad‑hoc.

**Fix:** add the existing `terminal-green` token to the Intel palette and rewrite
the emerald classes to `terminal-green`, so both pages share one defined green.

🟢 **Ambient glow colors are swapped between pages** (intel: violet top‑left;
library: cyan top‑left). Harmless, intentional‑looking variation — left as is.

---

## 3. Typography — heading fonts never apply

🔴 **`font-display-lg` and `font-label-sm` are undefined.** Every page applies
these classes to its logo, headers and section titles, and `intel`/`library`
load **Outfit + Inter** while `pipeline` loads **Outfit + Inter + Fira Code**
from Google Fonts — but neither class is defined anywhere (not in the Tailwind
config, not in `<style>`). Result: all that type silently falls back to the
default `font-sans` system stack and the loaded fonts are wasted.

**Fix:** wire the families into each page's Tailwind `theme.extend.fontFamily`
so `font-display-lg` → Outfit, `font-label-sm` → Inter, `font-sans` → Inter, and
(on pipeline) `font-mono` → Fira Code.

---

## 4. Accessibility

🟡 **Unlabeled icon‑only buttons (pipeline.html header).** The bell and globe
buttons have no text, `aria-label`, or `title`, so they are unreadable to screen
readers and have no tooltip.

**Fix:** add an SVG `<title>` (accessible name + tooltip) to each.

---

## 5. Consistency

🟢 **Inconsistent nav label.** The sidebar entry for the library page reads
*Local Library* on intel/library but *Library Explorer* on pipeline.

**Fix:** normalize to *Local Library* everywhere.

🟢 **Inconsistent sidebar markup (structural, not auto‑changed).** intel/library
use an in‑flow flex `<ul><li>` sidebar (`flex-shrink-0`); pipeline uses a
`position: fixed` `<nav>` with `ml-[260px]` on the main column. Visually similar
but a different layout model — worth unifying in a future refactor.

---

## 6. Security (high)

🔴 **Hardcoded TIDAL token.** `pipeline.html` ships the token as a literal
`value="…"` on the `#tidal-token` input (it is `type=password`, but the value is
still in the page source), and it is also hardcoded in `app.py`.

**Fix:** the fixer blanks the value in the template and warns if the literal is
still present in any `.py` file. **You must rotate the token** and load it from
an environment variable (see README).

---

## 7. Build / tooling (note only)

🟢 **Tailwind via `cdn.tailwindcss.com`** is a development build and prints a
console warning in production. Compile Tailwind to static CSS before shipping.
Left to you — it is a build‑pipeline decision.

---

### Summary of automated fixes

| # | Issue | Severity | Auto‑fixed |
|---|-------|----------|-----------|
| 1 | Missing button icons | 🟡 | ✅ |
| 2 | Off‑palette / mismatched green | 🟡 | ✅ |
| 3 | Undefined heading fonts | 🔴 | ✅ |
| 4 | Unlabeled icon buttons | 🟡 | ✅ |
| 5 | Nav label inconsistency | 🟢 | ✅ |
| 6 | Token in page source | 🔴 | ✅ (template) — rotate + move backend token yourself |
| 5b | Sidebar layout model | 🟢 | ✖ manual refactor |
| 7 | Tailwind CDN in prod | 🟢 | ✖ build step |
