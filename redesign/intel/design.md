---
name: Cyber-Obsidian Glass
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
  primary: '#d0bcff'
  on-primary: '#3c0091'
  primary-container: '#a078ff'
  on-primary-container: '#340080'
  inverse-primary: '#6d3bd7'
  secondary: '#4cd7f6'
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
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#d0bcff'
  on-primary-fixed: '#23005c'
  on-primary-fixed-variant: '#5516be'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#e1e1ef'
  tertiary-fixed-dim: '#c5c5d2'
  on-tertiary-fixed: '#191b24'
  on-tertiary-fixed-variant: '#454651'
  background: '#101415'
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
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
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
The design system for the MusicMV Media Sourcing Center is built upon an **Ultra-Premium Cyber-Obsidian** aesthetic. It targets high-end media professionals and curators who require a high-performance, immersive workspace. The brand personality is technical, futuristic, and exclusive.

The design style is a sophisticated blend of **Minimalism** and **Glassmorphism**. It utilizes deep, near-black backgrounds to provide infinite depth, while UI elements appear as suspended "glass" planes. High-precision glowing edges and vibrant neon accents serve as functional indicators within a dark, cinematic environment. The interface should feel like a high-end digital cockpit—precise, responsive, and luxurious.

## Colors
The palette is rooted in a deep obsidian base (`#07080C`), providing maximum contrast for the translucent layers. 

- **Primary (Electric Violet):** Used for primary actions and active states. It represents the energy of the media.
- **Secondary (Cyber-Cyan):** Used for success states, data visualization, and secondary highlights.
- **Surface Panels:** Constructed from translucent slate-glass. Every panel must feature a subtle `1px` inner stroke of `border_glow` to simulate a light-refracting edge.
- **Gradients:** Use the Electric Violet to Cyber-Cyan gradient sparingly for high-impact areas like progress bars, primary buttons, or featured media hover states.

## Typography
The typography strategy contrasts the geometric, wide apertures of **Outfit** for editorial impact with the systematic clarity of **Inter** for utility.

- **Headlines:** Use Outfit for all titles and large display text. It should feel airy and modern. Use a slight negative letter-spacing on Display sizes to maintain tension.
- **UI & Controls:** Use Inter for all labels, inputs, and body text. Inter’s high x-height ensures legibility against dark, blurred backgrounds.
- **Labels:** Small labels (`label-sm`) should be uppercase with increased tracking to evoke a technical, "data-tag" feel.

## Layout & Spacing
This design system utilizes a **Fixed-Shell Fluid-Content** model. The interface is anchored by two persistent architectural elements:
- **Left Sidebar (260px):** Navigation and library management.
- **Right Drawer (350px):** Active downloads and metadata inspection.

The central stage is a fluid workspace.
- **Filter Bar:** A 3-column structured horizontal bar for rapid media sorting.
- **Media Grid:** A 4-column responsive grid specifically optimized for 16:9 media thumbnails.
- **Rhythm:** An 8px base grid governs all internal component spacing. Use larger `stack_lg` (32px) gaps between distinct functional sections to maintain the minimalist breathability.

## Elevation & Depth
Depth is not communicated through traditional drop shadows, but through **Backdrop Blurs** and **Luminance**.

1.  **Level 0 (Base):** `#07080C` Solid black.
2.  **Level 1 (Panels):** `rgba(15, 17, 26, 0.8)` with a `20px` backdrop-filter blur. These surfaces feature a `1px` border of `rgba(139, 92, 246, 0.15)`.
3.  **Level 2 (Floating/Popovers):** Higher transparency, `40px` backdrop blur, and a more pronounced violet outer glow (`0px 0px 15px rgba(139, 92, 246, 0.1)`).
4.  **Active State:** When a card or element is focused, the border opacity increases, and a subtle "inner light" appears from the bottom-left corner using a cyan-to-transparent gradient.

## Shapes
The shape language is "Soft-Tech." While the overall layout is rigid and structured, individual components use a precise **0.25rem (4px)** corner radius (`roundedness: 1`). 

- **Media Thumbnails:** Use `rounded-lg` (8px) to soften the density of the 4-column grid.
- **Buttons:** Small buttons are slightly more rounded, while large layout containers (sidebar/drawer) remain sharp or use minimal 4px radii to emphasize structural integrity.
- **Iconography:** Use 1.5px thin-line SVG icons. Icons should be unboxed or placed within a subtle circular glass treatment.

## Components

- **Primary Buttons:** Filled with the `accent_gradient`. Text is high-contrast white. No shadow, but a `2px` outer glow on hover.
- **Glass Chips:** `rgba(255, 255, 255, 0.05)` background with `label-sm` text. Used for media tags (e.g., "4K", "ProRes").
- **Media Cards:** 16:9 aspect ratio. On hover, the image scales slightly (1.05x) within its clipped container, and the `1px` violet edge brightens to `0.4` opacity.
- **Filter Bar:** Three distinct glass segments. Each segment has a dropdown chevron. Active filters are highlighted with a cyan underline.
- **Input Fields:** Darker than the panels (`rgba(0, 0, 0, 0.4)`). Borders are only visible on focus, transitioning from slate to electric violet.
- **Download Drawer:** Contains a vertical list of "Media Strips." Each strip shows a mini-thumbnail, a progress bar (using the cyan-violet gradient), and a thin-line "X" to cancel.
- **Iconography:** Thin-line (1.5px stroke) icons. Inactive icons are `rgba(255, 255, 255, 0.4)`; active icons use the primary violet color with a tiny glow point.