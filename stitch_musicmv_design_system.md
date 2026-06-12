# 🎨 Google Stitch Design System Prompt: MusicMV Premium Overhaul

This document contains a master prompt and assets designed to completely replace the basic UI/emoji icons and upgrade the entire design of your **TIDAL & Billboard Media Intel Center** to a state-of-the-art, high-fidelity premium experience.

---

## 🚀 The Premium UI Overhaul Prompt for Google Stitch

Copy and paste this prompt into **[stitch.withgoogle.com](https://stitch.withgoogle.com/)** to generate the redesigned user interface:

```text
Design a ultra-premium, modern, responsive music media center dashboard named 'MusicMV Intel Center'.
Aesthetic: Dark cyber-obsidian mode with a glassmorphic styling system. 
Color Palette: 
- Base background: Deepest velvet blue-black (#05060A)
- Card backgrounds: Translucent slate-glass (rgba(13, 17, 28, 0.7)) with border (1px solid rgba(139, 92, 246, 0.15))
- Accents: Electric violet (#8B5CF6), cyber-cyan (#06B6D4), and warm rose gold (#F43F5E) for warning or critical status indicators.

Layout Architecture:
1. Left Navigation Sidebar:
   - Make it collapsed/expandable with smooth CSS transitions.
   - REPLACE all generic emojis/icons with beautiful, modern, minimalist inline SVGs.
   - Sidebar items: 'Intel Center' (represented by a search/radar SVG), 'Local Library' (represented by a stack of catalog folders SVG), and 'Control Console' (represented by a terminal/chip SVG).
   - Sidebar footer features an active "Downloads Monitor" badge that pulses with a cyan glow.

2. Main Sourcing Panel:
   - Search row: 3 glassmorphic search input cards with embedded search icons: 'TIDAL lookup', 'Playlist crawler', and 'Billboard charts dropdown'.
   - Content Grid: High-fidelity 16:9 aspect-ratio video cards. Card hover effect must scale the image slightly and show an elegant gradient overlay (violet-to-cyan) containing:
     * A translucent play button icon.
     * Quick download icon.
     * Metadata tags: Resolution (1080p/4K), duration, and file size.
   - Replace standard ugly icons with custom SVGs: use a clean downward arrow with a curved tray for 'download', and a music note icon for 'track'.

3. Integrated Downloads Drawer (Right Side):
   - Sliding translucent drawer displaying download queue.
   - Progress bars styled as glowing neon trails (gradient of #8B5CF6 to #06B6D4) with speed labels (e.g. '5.4 MB/s') and time remaining.

General Rules:
- No emojis anywhere. All icons must be high-quality inline SVGs.
- Use the 'Outfit' geometric font for headings and 'Inter' for body/meta texts.
- Include custom CSS styles for all interactive buttons, giving them subtle hover scale (1.02) and glowing box-shadow transitions.
```

---

## 📐 SVG Icons Asset Library

Stitch allows you to edit and paste custom code. Replace the emojis in the sidebar and cards with these custom, pixel-perfect SVG icon blocks:

### 1. Intel Center / Radar Icon
```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-radar">
  <circle cx="12" cy="12" r="10"></circle>
  <circle cx="12" cy="12" r="6"></circle>
  <circle cx="12" cy="12" r="2"></circle>
  <line x1="12" y1="2" x2="12" y2="22"></line>
  <line x1="2" y1="12" x2="22" y2="12"></line>
</svg>
```

### 2. Local Library / Stacked Folders Icon
```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-library">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
  <path d="M2 10h20"></path>
</svg>
```

### 3. Pipeline / Terminal Chip Icon
```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-pipeline">
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

### 4. Custom Download Icon (Curved Tray)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-download">
  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
  <polyline points="7 10 12 15 17 10"></polyline>
  <line x1="12" y1="15" x2="12" y2="3"></line>
</svg>
```

### 5. Billboard Chart / Analytics Icon
```html
<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-charts">
  <line x1="18" y1="20" x2="18" y2="10"></line>
  <line x1="12" y1="20" x2="12" y2="4"></line>
  <line x1="6" y1="20" x2="6" y2="14"></line>
</svg>
```

---

## 💎 Suggested Additions for Premium Look & Feel

To make the app stand out and feel like a native desktop product:
* **Audio Waveform Preview Overlay**: Add a mini-canvas waveform in the video card hover state that pulses to simulate audio playback.
* **Glow-on-Border CSS**: Apply this effect to input boxes when focused:
  ```css
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.25);
  border-color: rgba(6, 182, 212, 0.8);
  ```
* **Mesh Gradients backgrounds**: Apply dynamic gradients to background elements using CSS backgrounds like `radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)`.
