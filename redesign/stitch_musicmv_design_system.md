# 🎨 Google Stitch Design System Prompt: Desktop Web App Overhaul

This design system and master prompt are explicitly optimized for a **Desktop Web Dashboard (optimized for 1920x1080 and larger desktop displays)**, replacing basic emojis with custom high-fidelity SVG icon assets and premium desktop-grade GUI components.

---

## 🖥️ Desktop Dashboard Overhaul Prompt for Google Stitch

Copy and paste this prompt directly into **[stitch.withgoogle.com](https://stitch.withgoogle.com/)** to generate the desktop-first interface:

```text
Design a responsive Desktop Web Dashboard for a Windows desktop application named 'MusicMV Media Sourcing Center'.
Viewport: Designed for a 16:9 widescreen desktop layout (1920px width minimum), NOT mobile.

Aesthetic: Ultra-premium dark cyber-obsidian dashboard.
Color Palette:
- Primary background: Deep dark slate-black (#07080C)
- Side navigation & Header panels: Translucent glass-slate (rgba(15, 17, 26, 0.8)) with a subtle glowing edge (1px solid rgba(139, 92, 246, 0.15))
- Active state highlight: Bright cyber-cyan (#06B6D4) and electric violet (#8B5CF6) gradients.

Desktop Layout Grid (Left-to-Right):
1. Left Widescreen Sidebar (Fixed 260px):
   - Expanded state showing brand title 'MusicMV' and subtitle 'Pipeline Sorter'.
   - Collapsible to a 72px icon-only bar with smooth hover expansions.
   - REPLACE all emojis with clean, thin-line desktop-style inline SVGs.
   - Navigation links: 'Intel Search' (Radar/Wave SVG), 'Local Library' (Folder Stack SVG), and 'Control Console' (Monospaced Terminal Chip SVG).

2. Main Sourcing Area (Flexible Center Panel):
   - Horizontal filter bar stretching across the screen, containing three large inputs side-by-side:
     * Tidal lookup field (with search glass SVG icon)
     * Playlist scraper URL field (with external link SVG icon)
     * Billboard Charts select dropdown
   - Desktop Media Grid below: 4-column responsive grid (for 1080p widescreen) containing 16:9 wide video thumbnail cards.
   - Hover states for video cards: Dynamic blur transition, showing an overlay with:
     * A translucent play circle SVG.
     * Metadata tags (duration, 1080p resolution tag, exact file size in MB).
     * Quick download arrow-tray SVG icon.

3. Desktop Downloads Sidebar Drawer (Fixed Right 350px):
   - A persistent or togglable side panel showing concurrent active downloads.
   - Sleek linear progress bars with neon violet-to-cyan glows (#8B5CF6 to #06B6D4).
   - Display file speed stats (e.g. '4.2 MB/s') and time counters (e.g. 'ETA 1m 12s') side-by-side.

General Widescreen Constraints:
- No elements should look like cards stacked vertically for phone screens.
- Keep columns wide and make use of horizontal space with clean tabular alignments.
- All icons must be modern, lightweight inline SVGs. Font weights should be light/medium (Outfit font family for headers, Inter for standard controls).
```

---

## 📐 SVG Icons Asset Library (Desktop Optimized)

Use these pixel-perfect, clean SVG code blocks in Stitch to replace the emojis:

### 1. Radar Sourcing Icon (Intel Search)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"></circle>
  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
  <path d="M2 12h20"></path>
</svg>
```

### 2. Stacked Catalog Folders Icon (Local Library)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
  <path d="M2 10h20"></path>
</svg>
```

### 3. Chip Processor/Terminal Icon (Control Console)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
  <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
  <rect x="9" y="9" width="6" height="6"></rect>
  <line x1="9" y1="1" x2="9" y2="4"></line>
  <line x1="15" y1="1" x2="15" y2="4"></line>
  <line x1="9" y1="20" x2="9" y2="23"></line>
  <line x1="15" y1="20" x2="15" y2="23"></line>
  <line x1="20" y1="9" x2="23" y2="9"></line>
  <line x1="20" y1="15" x2="23" y2="15"></line>
  <line x1="1" y1="9" x2="4" y2="9"></line>
  <line x1="1" y1="15" x2="4" y2="15"></line>
</svg>
```

### 4. Downward Tray Icon (Download Button)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
  <polyline points="7 10 12 15 17 10"></polyline>
  <line x1="12" y1="15" x2="12" y2="3"></line>
</svg>
```

---

## 💎 Desktop Dashboard Best Practices

* **Grid Columns**: Always lock content grids to 3 or 4 columns wide on desktop viewports. Stacking them into 1 column ruins the widescreen interface design.
* **Ambient Lighting Effects**: Emphasize desktop card borders by adding a faint inner shadow `box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.05)`.
* **Sidebar Hover Collapsing**: When the sidebar is collapsed to 72px, hover tooltips should show floating bubble labels.
