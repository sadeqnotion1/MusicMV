---
name: Cyber-Obsidian Glass (Library Explorer)
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
  drawer_right_width: 350px
  grid_gutter: 24px
  panel_padding: 20px
  container_margin: 32px
  stack_sm: 8px
  stack_md: 16px
  stack_lg: 32px
---

## Brand & Style
The Library Explorer for the MusicMV Media Sourcing Center is built upon an **Ultra-Premium Cyber-Obsidian** desktop theme. It complements the Sourcing Center, creating a unified workspace for managing locally archived artist directories.

The visual system is designed for high-density, rich-metadata navigation, combining glassmorphic surfaces with glowing cyber accents.

## Colors
- **Primary (Electric Violet #8B5CF6):** Used for navigation highlights, active stats, and main interactive buttons.
- **Secondary (Cyber-Cyan #06B6D4):** Used for success badges, local file count tags, and download triggers.
- **Background:** Deep dark velvet (#05060A).

## Typography
- **Titles & Stats Numbers:** Outfit font family. It should feel geometric, lightweight, and modern.
- **Grids & Data Sheets:** Inter font family. High legibility at smaller sizes.

## Layout & Spacing
- **Left Navigation Sidebar:** Fixed 260px widescreen layout. Uses clean inline SVGs for navigation.
- **Right Audit Drawer (350px):** 'Missing Tracks Auditor' displaying Deezer chart mismatches.
- **Center Main Stage:** Fluid 16:9 widescreen layout with:
  - A top horizontal row of 3 Statistics Cards.
  - A 6-column grid of circular artist profile cards.

## Elevation & Depth
- **Level 1 (Panels/Cards):** `rgba(20, 24, 38, 0.65)` glass surface with a `1px` stroke outline of `rgba(139, 92, 246, 0.15)` and `20px` backdrop filter blur.
- **Circular Avatars:** Ring outline glows cyan (`rgba(6, 182, 212, 0.5)`) on card hover.

## Components
- **Stats Card:** Glass cards with cyber outline accents. Title is in `label-sm` tracking uppercase, value in bold Outfit display, footer in cyan/violet.
- **Circular Artist Cards:** Circular avatar container (80x80px) with absolute inner-shadow ring, clean text label, and a cyan count pill showing local folder items (e.g. '12 Videos').
- **Missing Tracks List:** Clean row format displaying track name, album, and a download action button with inline down-arrow SVG.
- **Iconography:** Modern thin-line (1.5px stroke) SVGs. No emojis allowed.
