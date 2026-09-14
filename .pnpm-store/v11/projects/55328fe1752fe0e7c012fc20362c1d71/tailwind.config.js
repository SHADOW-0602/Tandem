/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0e0e13",
        foreground: "#fffaea",
        dark: {
          bg: "#0e0e13",
          card: "#111013",
          surface: "#1f1f23",
          raised: "#000000",
          cream: "#efebdd",
          "cream-light": "#fffaea",
          mint: "#9acdbf",
          "mint-bright": "#62f6b5",
          "mint-hover": "#82f8c4",
          "mint-dark": "#0d241e",
          border: "rgba(255, 255, 255, 0.08)",
          "border-strong": "rgba(255, 255, 255, 0.15)",
          muted: "#a1a1aa",
          subtle: "#71717a",
        },
        moss: {
          50: "#dffdf5",
          100: "#bde3d8",
          400: "#62f6b5",
          500: "#37cd8f",
          600: "#23b97b",
          900: "#0d241e",
        },
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "Inter", "Segoe UI", "sans-serif"],
        mono: ["Geist Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        xs: "2px",
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        "2xl": "20px",
        "3xl": "24px",
      },
      letterSpacing: {
        tightest: "-0.04em",
        tighter: "-0.025em",
        eyebrow: "0.08em",
      },
      animation: {
        "pulse-glow": "pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "sub10-glow": "sub10Glow 2.4s ease-in-out infinite",
        "fhero-bubble": "fheroBubble 0.32s cubic-bezier(0.2, 0.8, 0.2, 1) both",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { opacity: 1, transform: "scale(1)" },
          "50%": { opacity: 0.7, transform: "scale(1.05)" },
        },
        sub10Glow: {
          "0%, 100%": { boxShadow: "0 0 12px rgba(98, 246, 181, 0.3)" },
          "50%": { boxShadow: "0 0 24px rgba(98, 246, 181, 0.7)" },
        },
        fheroBubble: {
          "0%": { opacity: 0, transform: "translateY(8px)" },
          "100%": { opacity: 1, transform: "translateY(0px)" },
        },
      },
    },
  },
  plugins: [],
};
