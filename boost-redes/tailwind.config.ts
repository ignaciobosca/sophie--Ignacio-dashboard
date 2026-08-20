import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0a0a0f",
        panel: "#14141f",
        brand: {
          DEFAULT: "#7c5cff",
          glow: "#a78bfa",
        },
        gold: "#f5c542",
        silver: "#cbd5e1",
        bronze: "#d08a52",
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -8px rgba(124,92,255,0.6)",
      },
      keyframes: {
        rise: {
          "0%": { transform: "translateY(8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
      animation: {
        rise: "rise 0.35s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
