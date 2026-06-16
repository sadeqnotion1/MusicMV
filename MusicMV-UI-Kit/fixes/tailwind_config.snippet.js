// Corrected Tailwind theme.extend block.
// intel.html / library.html: omit the "mono" line.
// pipeline.html: keep "mono" (Fira Code) and "terminal-green" (already present).
// intel.html also needs "terminal-green" added (shown below).

tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#8b5cf6",
        secondary: "#06b6d4",
        "terminal-green": "#10b981", // add to intel.html (already in pipeline.html)
        background: "#05060a",
        "surface-glass": "rgba(20, 24, 38, 0.65)",
        "border-glow": "rgba(139, 92, 246, 0.15)",
        "text-primary": "#f8fafc",
        "text-secondary": "#94a3b8",
        "text-muted": "#475569",
      },
      // NEW — makes the previously-undefined classes resolve:
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        "display-lg": ["Outfit", "Inter", "sans-serif"],
        "label-sm": ["Inter", "ui-sans-serif", "sans-serif"],
        mono: ["Fira Code", "ui-monospace", "monospace"], // pipeline.html only
      },
    },
  },
};
