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
          50: "#f0f4ff",
          100: "#e0e9ff",
          500: "#4f72f5",
          600: "#3b5bdb",
          900: "#1a1f36",
          950: "#0f1224",
        },
      },
    },
  },
  plugins: [],
};

export default config;
