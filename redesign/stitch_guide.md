# Google Stitch Redesign & Project Creation Guide

This guide provides a comprehensive workflow and boilerplate templates for designing web interfaces with [Google Stitch](https://stitch.withgoogle.com/) and integrating them into functional applications (e.g. Flask, Node.js, React).

---

## Table of Contents
1. [Stitch Design Phase (Getting Widescreen Layouts)](#1-stitch-design-phase-getting-widescreen-layouts)
2. [Code Export Phase](#2-code-export-phase)
3. [Fixing Common Stitch Layout Bugs](#3-fixing-common-stitch-layout-bugs)
4. [Setting Up a Boilerplate Project Architecture](#4-setting-up-a-boilerplate-project-architecture)
5. [Reusable Widescreen Dashboard Boilerplate](#5-reusable-widescreen-dashboard-boilerplate)
6. [Backend Integration Pattern (Flask example)](#6-backend-integration-pattern-flask-example)

---

## 1. Stitch Design Phase (Getting Widescreen Layouts)

Google Stitch defaults to mobile-first app styling when creating a new canvas. To design a premium widescreen desktop application, follow these steps first:

### Step 1: Switch View Mode
- Upon launching a canvas in Stitch, locate the canvas size viewport at the top control bar.
- Toggle the viewport setting from **`[App]`** (Mobile layout) to **`[Web]`** (Desktop layout).
- Select **1080p widescreen resolution** (1920x1080).

### Step 2: Establish the Three-Section Layout
Most premium admin dashboards feature:
1. **Left Sidebar** (Navigation & Brand): Width `260px`, `fixed h-full`, backdrop blur, gradient border.
2. **Top Header** (Breadcrumbs, Page Title, User Actions): Height `64px` (h-16), `fixed left-[260px] right-0`.
3. **Main Workspace**: Margins `ml-[260px] mt-16`, flexbox-driven grid layout.

---

## 2. Code Export Phase

When you finish your layout:
1. Select the top-level parent container of your design.
2. Click **Export Code** (or generate markdown/html).
3. Google Stitch will provide two main assets:
   - `DESIGN.md`: Explaining layout components and variables.
   - `index.html` / `.png`: HTML markup built on Tailwind CSS, along with a visual preview.

---

## 3. Fixing Common Stitch Layout Bugs

Stitch-generated layouts frequently contain specific HTML/CSS bugs when rendered in a standard web browser. You must manually correct these:

### Bug A: Header Right-Side Overflow
* **The Bug:** Stitch sidebars and headers often use `w-full ml-[260px] mr-[350px]`. In standard CSS, `w-full` renders the width as `100vw`, and the left margin shifts it rightwards, overflowing off the screen.
* **The Fix:** Change the header positioning styling to use absolute edges rather than fixed widths.
  ```diff
  - <header class="fixed w-full ml-[260px] mr-[350px] ...">
  + <header class="fixed top-0 left-[260px] right-0 w-auto ...">
  ```

### Bug B: Viewport Heights and Unwanted Scrollbars
* **The Bug:** Pages designed with ambient background glows and overflow layers sometimes introduce double scrollbars (body scrollbar + main content scrollbar).
* **The Fix:** Constrain the parent `body` element and use inner flex columns for vertical scrolling.
  ```html
  <body class="bg-[#05060a] text-white min-h-screen overflow-hidden flex flex-row font-sans">
      <!-- Sidebar remains fixed -->
      <!-- Main view handles scrollable content -->
      <main class="ml-[260px] flex-1 mt-16 p-8 overflow-y-auto h-[calc(100vh-64px)] flex flex-col">
          ...
      </main>
  </body>
  ```

---

## 4. Setting Up a Boilerplate Project Architecture

To build a project from scratch or refactor an existing one using your Stitch HTML mockups, arrange the project repository structure as follows:

```text
my-dashboard-project/
│
├── src/
│   ├── app.py                     # Flask server router
│   ├── requirements.txt           # Backend dependencies
│   │
│   ├── templates/                 # Server-rendered pages
│   │   ├── layout.html            # Base Jinja2 layout (optional)
│   │   ├── index.html             # Screen 1: Sourcing (Intel)
│   │   ├── library.html           # Screen 2: Directories & Data
│   │   └── pipeline.html          # Screen 3: Settings & Logs Console
│   │
│   └── static/                    # Frontend assets
│       ├── css/
│       │   └── custom.css         # Custom animations or scrollbars
│       └── js/
│           └── dashboard.js       # Client-side API wiring
│
└── redesign/                      # Design archive directory
    ├── design_spec.md             # Design rules & colors
    └── mockups/                   # Exported mockup designs
```

---

## 5. Reusable Widescreen Dashboard Boilerplate

Here is a ready-to-use boilerplate HTML template optimized for Google Stitch widescreen designs. Copy and save it as your starting template (e.g. `index.html`):

```html
<!DOCTYPE html>
<html class="dark" lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>Stitch Boilerplate Dashboard</title>
    <!-- Premium Fonts -->
    <link href="https://fonts.googleapis.com" rel="preconnect"/>
    <link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@400;500;600&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet"/>
    <!-- Tailwind CSS (Play CDN for rapid prototyping) -->
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#8b5cf6",      /* Violet glow */
                        "secondary": "#06b6d4",    /* Cyan accent */
                        "terminal-green": "#10b981",
                        "background": "#05060a",   /* Sleek OLED dark */
                        "surface-glass": "rgba(20, 24, 38, 0.65)",
                        "border-glow": "rgba(139, 92, 246, 0.15)"
                    }
                }
            }
        }
    </script>
    <style>
        /* Custom scrollbar adjustments for a clean look */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(139, 92, 246, 0.5); }
        .glass-panel { background-color: var(--bg-surface-glass); backdrop-filter: blur(20px); border: 1px solid var(--border-glow); }
    </style>
</head>
<body class="bg-[#05060a] text-[#f8fafc] min-h-screen overflow-hidden flex font-sans antialiased">

    <!-- 1. Side Navigation (Fixed width 260px) -->
    <nav class="fixed left-0 top-0 h-full w-[260px] bg-[#141826]/65 border-r border-border-glow backdrop-blur-xl flex flex-col py-8 z-50">
        <!-- Logo -->
        <div class="px-6 mb-8 flex items-center gap-3">
            <div class="w-9 h-9 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center font-bold text-white shadow-lg">B</div>
            <div>
                <h1 class="text-[18px] font-bold text-white tracking-tighter leading-none">Boilerplate</h1>
                <p class="text-[11px] text-[#94a3b8] uppercase tracking-wider mt-0.5">Control Center</p>
            </div>
        </div>
        <!-- Links -->
        <div class="flex-1 flex flex-col gap-2">
            <a class="flex items-center gap-4 px-6 py-3 text-white font-bold border-l-2 border-primary bg-primary/10 transition-all duration-300" href="#">
                <span>Dashboard</span>
            </a>
            <a class="flex items-center gap-4 px-6 py-3 text-[#94a3b8] hover:text-white transition-all border-l-2 border-transparent" href="/settings">
                <span>Settings</span>
            </a>
        </div>
    </nav>

    <!-- 2. Header (Fixed top, offset by sidebar 260px) -->
    <header class="fixed top-0 left-[260px] right-0 h-16 bg-[#141826]/30 border-b border-border-glow/30 flex justify-between items-center px-8 z-40">
        <h2 class="text-[18px] font-semibold text-white">System Dashboard</h2>
        <div class="flex items-center gap-4">
            <div id="status-badge" class="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                System Online
            </div>
        </div>
    </header>

    <!-- 3. Scrollable Content Area -->
    <main class="ml-[260px] flex-1 mt-16 p-8 overflow-y-auto h-[calc(100vh-64px)] flex flex-col relative">
        <!-- Ambient background gradients -->
        <div class="absolute inset-0 pointer-events-none opacity-10">
            <div class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary blur-[120px]"></div>
            <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-secondary blur-[100px]"></div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 z-10 relative">
            <!-- Metric Card 1 -->
            <div class="bg-[#141826]/65 border border-border-glow rounded-2xl p-6 flex flex-col justify-between">
                <span class="text-xs text-[#94a3b8] font-bold uppercase tracking-wider">Metrics Managed</span>
                <span class="text-3xl font-bold text-white mt-2">1,840</span>
            </div>
            <!-- Metric Card 2 -->
            <div class="bg-[#141826]/65 border border-border-glow rounded-2xl p-6 flex flex-col justify-between">
                <span class="text-xs text-[#94a3b8] font-bold uppercase tracking-wider">Storage Capacity</span>
                <span class="text-3xl font-bold text-secondary mt-2">84.2 GB</span>
            </div>
            <!-- Metric Card 3 -->
            <div class="bg-[#141826]/65 border border-border-glow rounded-2xl p-6 flex flex-col justify-between">
                <span class="text-xs text-[#94a3b8] font-bold uppercase tracking-wider">Active Tasks</span>
                <span class="text-3xl font-bold text-primary mt-2">Running</span>
            </div>
        </div>

        <!-- Terminal Console -->
        <div class="flex-1 rounded-2xl overflow-hidden border border-border-glow flex flex-col bg-black/90 shadow-[inset_0_0_20px_rgba(0,0,0,0.8)] min-h-[300px] z-10 relative">
            <div class="h-8 bg-[#15171d] border-b border-border-glow flex items-center px-4 justify-between">
                <div class="flex gap-2">
                    <div class="w-3 h-3 rounded-full bg-[#FF5F56]"></div>
                    <div class="w-3 h-3 rounded-full bg-[#FFBD2E]"></div>
                    <div class="w-3 h-3 rounded-full bg-[#27C93F]"></div>
                </div>
                <span class="font-mono text-[11px] text-[#94a3b8]">console_output.log</span>
            </div>
            <div id="console-body" class="flex-1 p-6 overflow-y-auto font-mono text-[13px] leading-relaxed text-[#f8fafc] flex flex-col gap-1.5">
                <div>[12:00:00] INFO: Dashboard loaded successfully. Ready for operations.</div>
                <div class="animate-pulse">_</div>
            </div>
        </div>
    </main>

    <script>
        // Place JS integrations here to update the metrics and console body via backend polling APIs.
    </script>
</body>
</html>
```

---

## 6. Backend Integration Pattern (Flask example)

To map multiple Stitch exported pages to dedicated URLs and templates inside a Python Flask backend:

```python
import os
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Route: Main Dashboard (Screen 1)
@app.route('/')
def home():
    return render_template('index.html')

# Route: Analytics/Library (Screen 2)
@app.route('/library')
def library():
    return render_template('library.html')

# Route: Operations / Control Panel (Screen 3)
@app.route('/pipeline')
def pipeline():
    return render_template('pipeline.html')

# API Route: Fetch status
@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'status': 'success',
        'metrics': {
            'count': 1840,
            'storage': '84.2 GB'
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

By keeping pages split into discrete HTML templates and using JSON APIs for data delivery, you can maintain a responsive design without reloading page headers and sidebar components.
