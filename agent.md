# Project Guidelines for Coding Agents

This project has strict UI design guidelines regarding branding icons. Please adhere to the following rules when developing or modifying user interfaces:

## SVG Icons Rule

> [!IMPORTANT]
> **DO NOT** write the text names **"yt"**, **"youtube"**, **"billboard"**, or **"tidal"** in UI button labels, tabs, or badges where icons are intended. You **must** use the corresponding SVG logo icons instead.

The official SVG assets are located in:
* `G:\Music\MusicMV\src\svg\`

### Available SVGs and Locations:
1. **YouTube Logo**: Use [YouTube_full-color_icon_(2017).svg](file:///G:/Music/MusicMV/src/svg/YouTube_full-color_icon_(2017).svg)
2. **Tidal Logo**: Use [tidal-logo-svgrepo-com.svg](file:///G:/Music/MusicMV/src/svg/tidal-logo-svgrepo-com.svg)
3. **Billboard Logo**: Use [billboard.svg](file:///G:/Music/MusicMV/src/svg/billboard.svg)

---

## Code Examples

### 1. Inlining SVG Constants in Javascript
When generating controls dynamically, define variables for the SVGs:
```javascript
const ytIconSvg = `<svg viewBox="0 0 28.57 20" style="width:16px; height:12px; display:inline-block; vertical-align:middle;"><g><path d="..." fill="#FF0000"></path><path d="..." fill="white"></path></g></svg>`;
const tidalIconSvg = `<svg viewBox="532 0 387 257" style="width:14px; height:14px; fill:#00f0ff !important; display:inline-block; vertical-align:middle;"><path d="..."/></svg>`;
```

### 2. Button Labels
* **Incorrect**: `button.innerHTML = "Find on YouTube";`
* **Correct**: `button.innerHTML = ytIconSvg;`

* **Incorrect**: `button.innerHTML = "Watch on Tidal";`
* **Correct**: `button.innerHTML = `Watch on ${tidalIconSvg}`;` (Or just the logo itself)

---

## Styling Guidelines
* Ensure inline fills for Tidal and Billboard logos are styled with `!important` to prevent global CSS overrides:
  * e.g., `fill:#00f0ff !important;` (Tidal Cyan) or `fill:currentColor !important;` (Billboard/Dynamic theme colors).
* Select dropdown chevrons/arrows should use double chevron paths (`path d="M7 15l5 5 5-5M7 9l5-5 5 5"`) instead of single down arrows.
