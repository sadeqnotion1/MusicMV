---
name: Cyber-Obsidian Glass
colors:
  surface: '#121318'
  surface-dim: '#121318'
  surface-bright: '#38393e'
  surface-container-lowest: '#0d0e13'
  surface-container-low: '#1a1b20'
  surface-container: '#1e1f25'
  surface-container-high: '#292a2f'
  surface-container-highest: '#33343a'
  on-surface: '#e3e2e9'
  on-surface-variant: '#cbc3d7'
  inverse-surface: '#e3e2e9'
  inverse-on-surface: '#2f3036'
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
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00a572'
  on-tertiary-container: '#00311f'
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
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#121318'
  on-background: '#e3e2e9'
  surface-variant: '#33343a'
  surface-glass: rgba(20, 24, 38, 0.65)
  outline-glow: rgba(139, 92, 246, 0.15)
  accent-cyan-glow: rgba(6, 182, 212, 0.5)
  terminal-black: '#000000'
  text-primary: '#F3F4F6'
  text-secondary: '#A1A1AA'
  text-muted: '#71717A'
  error-neon: '#EF4444'
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
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: '0'
  headline-sm:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
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
  console-log:
    fontFamily: Fira Code
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  sidebar-width: 260px
  drawer-width: 350px
  gutter: 24px
  panel-padding: 20px
  margin-page: 32px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is an ultra-premium administrative workspace tailored for power users and media professionals. It embodies a **Cyber-Obsidian** aesthetic, merging developer-centric utility with cinematic elegance. The interface is characterized by high-fidelity glassmorphism, floating translucent panels, and a "Deep Velvet" atmospheric void.

The visual narrative is one of precision engineering and real-time execution. It uses glowing neon accents—specifically Electric Violet and Cyber-Cyan—to guide focus against a pitch-black, low-strain background. The style is a sophisticated blend of **Minimalism** and **Glassmorphism**, emphasizing structural clarity, thin-line geometry, and technical transparency. It should evoke a sense of absolute control, futuristic reliability, and high-performance throughput.

## Colors

The palette is rooted in high-contrast cinematic environments. The core foundation is **Velvet Void** (`#05060A`), which serves as the infinite canvas to maximize the luminance of overlay panels.

- **Primary (Electric Violet):** Reserved for high-priority task executions and active navigational focus.
- **Secondary (Cyber-Cyan):** Indicates active synchronization, hover states, and secondary toggles.
- **Tertiary (Terminal Green):** Exclusively for success states within monospaced console logs.
- **Neutral:** Deep obsidian blacks and translucent slates form the structural surfaces.

Interactive elements should utilize a **Neon Glow Gradient** (Electric Violet to Cyber-Cyan at 135°) for progress bars and featured borders. Use `rgba(139, 92, 246, 0.15)` for the characteristic violet refraction stroke on all glass surfaces.

## Typography

The system employs a tri-font framework to balance editorial geometry with technical utility.

- **Outfit:** Used for headlines and branding. Display sizes (XL, LG) require a `-0.02em` letter-spacing to create "display tension" for a premium feel.
- **Inter:** The primary workhorse for UI controls, inputs, and metadata. It provides neutral, high-readability support for dense information.
- **Fira Code:** Dedicated to the **Console Logger**. It must be used for all system logs, file paths, and execution data to provide a developer-oriented diagnostic feel.

`label-sm` should be treated with `text-transform: uppercase` when used for technical tags or category indicators to simulate command-center instrumentation.

## Layout & Spacing

This system utilizes a **Fixed-Shell Fluid-Content** model optimized for 16:9 widescreen displays.

### Structure
- **Left Navigation Sidebar:** Fixed at 260px. Translucent glass-slate backing with a glowing violet vertical divider.
- **Right Drawer:** Fixed at 350px for secondary utilities like download queues or missing track auditors.
- **Center Workspace:** A fluid area housing the main media grids and console.

### Grids
- **Media Grid:** 4-column layout for 16:9 video cards.
- **Artist Grid:** 6-column layout for circular profiles.

The spacing rhythm follows an 8px baseline. Panel interiors must strictly use `20px` padding to maintain consistent internal "breathability" within glass containers.

## Elevation & Depth

Hierarchy is established through **Glassmorphism** and **Ambient Glows** rather than traditional shadows.

- **Level 1 (Panels):** Surfaces use `rgba(20, 24, 38, 0.65)` with a `20px` backdrop filter blur. Each panel features a `1px` stroke of `rgba(139, 92, 246, 0.15)` and an internal top-highlight: `inset 0 1px 0 0 rgba(255, 255, 255, 0.05)`.
- **Level 2 (Active Elements):** Active cards or buttons utilize an external glow. Artist avatars use a `rgba(6, 182, 212, 0.5)` Cyber-Cyan ring on hover.
- **The Console:** Unlike other panels, the terminal console is "inset" into the layout, featuring a pitch-black background with a deep inner shadow to simulate physical depth and screen-within-a-screen focus.

## Shapes

The shape language is refined and professional, utilizing **Rounded** corners to soften the technical aesthetic.

- **Standard Containers:** Use `rounded-md` (0.5rem) for a balanced appearance.
- **Media Thumbnails:** Use `rounded-lg` (1rem) for a more cinematic feel.
- **Artist Avatars:** Strictly circular (full rounding) to contrast against the geometric grid.
- **Status Pills:** Use pill-shaped (full) rounding for categorical tags and folder counts.

## Components

### Buttons
- **Primary Execution:** Glowing mesh gradient (Violet to Cyan) with white Outfit text. On hover, apply a 1.02x scale and a soft Electric Violet outer glow.
- **Glass Action:** Translucent surface with a Cyber-Cyan border. On hover, the border opacity increases to 100%.

### Console Logger
A specialized component featuring a macOS-style header strip with three window dots (Red, Yellow, Green) and a centered log filename. The body is a pitch-black inset area with Fira Code text. Success logs are colored in Terminal Green (`#10B981`).

### Inputs & Forms
- **Text Fields:** 44px height, pitch-black background (`rgba(0, 0, 0, 0.4)`). Borders transition from slate to Electric Violet on focus with a soft ambient glow.
- **Toggles:** Custom checkbox toggles with solid Electric Violet fills when active.

### Cards
- **Media Cards:** 16:9 aspect ratio. On hover, the thumbnail scales 1.05x, and a glass play overlay slides into view.
- **Artist Cards:** 80x80px circular avatars with an inner shadow ring that activates a Cyan glow on hover.

### Iconography
Use **Thin-line SVGs** (1.5px stroke weight). Avoid filled icons or emojis. Icons should remain unboxed unless they are the primary action trigger.