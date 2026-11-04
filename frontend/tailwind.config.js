/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        trade: {
          bg: "#0B0E14",
          card: "#121824",
          border: "#1E293B",
          accent: "#2563EB",
          bullish: "#10B981",
          bearish: "#EF4444",
          neutral: "#F59E0B",
          text: "#F8FAFC",
          muted: "#94A3B8"
        }
      }
    },
  },
  plugins: [],
}
