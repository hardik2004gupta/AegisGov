import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        aegis: {
          50:  "#f0f4ff",
          100: "#e0e9ff",
          200: "#c7d8fe",
          300: "#a5bcfc",
          400: "#7b96f8",
          500: "#4f72f5",
          600: "#3b5bdb",
          700: "#2f4ac2",
          800: "#243899",
          900: "#1a2a72",
          950: "#0f1a4a",
        },
        surface: {
          DEFAULT: "#ffffff",
          subtle: "#f7f8fa",
          muted:  "#f0f2f5",
        },
        border: {
          DEFAULT: "#e4e7ec",
          strong:  "#cdd2da",
        },
        ink: {
          DEFAULT: "#0f172a",
          muted:   "#475569",
          faint:   "#94a3b8",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Cascadia Code", "monospace"],
      },
      boxShadow: {
        card:  "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)",
        modal: "0 20px 60px rgba(0,0,0,0.12), 0 8px 24px rgba(0,0,0,0.06)",
      },
      borderRadius: {
        "2xs": "2px",
        xs:    "4px",
      },
      animation: {
        "fade-in":    "fadeIn 180ms ease-out",
        "slide-up":   "slideUp 200ms ease-out",
        "pulse-slow": "pulse 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:  { from: { opacity: "0" },               to: { opacity: "1" } },
        slideUp: { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};

export default config;
