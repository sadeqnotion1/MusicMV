---
name: Cyber-Obsidian Glass (Pipeline Control Console)
colors:
  surface: '#101415'
  surface-dim: '#101415'
  surface-bright: '#363a3b'
  surface-container-lowest: '#0b0f10'
  surface-container-low: '#191c1e'
  surface-container: '#1d2022'
  surface-container-high: '#272a2c'
  surface-container-highest: '#323537'
  on-surface: '#e0e3e5'
  on-surface-variant: '#cbc3d7'
  inverse-surface: '#e0e3e5'
  inverse-on-surface: '#2d3133'
  outline: '#958ea0'
  outline-variant: '#494454'
  surface-tint: '#d0bcff'
  primary: '#8b5cf6'
  on-primary: '#ffffff'
  primary-container: '#a078ff'
  on-primary-container: '#340080'
  inverse-primary: '#6d3bd7'
  secondary: '#06b6d4'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#c5c5d2'
  on-tertiary: '#2e303a'
  tertiary-container: '#8f909c'
  on-tertiary-container: '#272933'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  background: '#05060a'
  on-background: '#e0e3e5'
  surface-variant: '#323537'
typography:
  display-xl:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg:
    fontFamily: Outfit
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar_left_width: 260px
  grid_gutter: 24px
  panel_padding: 20px
  container_margin: 32px
  stack_sm: 8px
  stack_md: 16px
  stack_lg: 32px
---

## Brand & Style
The Pipeline Control Console for the MusicMV Media Sourcing Center is built upon an **Ultra-Premium Cyber-Obsidian** administrative layout. It acts as the pipeline configuration and execution core for the Windows automated Python backend.

The aesthetic merges developer-oriented utility with visual elegance, pairing a dark theme and terminal outputs with glassmorphic cards and glowing status glows.

## Colors
- **Primary (Electric Violet #8B5CF6):** Used for primary execution run buttons and terminal action triggers.
- **Secondary (Cyber-Cyan #06B6D4):** Used for active synchronization indicators, status icons, and secondary buttons.
- **Terminal Green (#10B981):** Monospaced log success output coloring.
- **Background:** Deep dark velvet (#05060A).

## Typography
- **Headlines & Button Labels:** Outfit font family. Sleek, clean, geometric sans-serif.
- **Settings & Controls:** Inter font family. High readability.
- **Logs Console:** Fira Code or standard monospaced font family for terminal lines.

## Layout & Spacing
- **Left Navigation Sidebar:** Fixed 260px panel utilizing modern inline SVGs.
- **Center Workspace (Widescreen Split):**
  - **Left Config Column (1/3 Width):** Vertical stack of configuration cards for paths, keys, and toggles.
  - **Right Console Column (2/3 Width):** Active action buttons at the top, followed by a large terminal console window filling the remaining screen space.

## Elevation & Depth
- **Level 1 (Config Cards):** `rgba(20, 24, 38, 0.65)` glass surface with a `1px` stroke outline of `rgba(139, 92, 246, 0.15)` and `20px` backdrop filter blur.
- **Console Terminal Window:** Pitch-black background with deep inset inner shadow to simulate screen depth.

## Components
- **Text Inputs:** Dark input boxes with border transitions from slate to cyan on focus.
- **Checkbox Controls:** Custom styled checkbox toggles with violet fills.
- **Action Buttons:** Glowing mesh gradients on primary buttons, with clean click micro-animations.
- **Console Logger:** macOS-style header containing red, yellow, green titlebar window dots, a center log filename tag, and scrollable console rows.
- **Iconography:** Modern thin-line (1.5px stroke) SVGs. No emojis.
