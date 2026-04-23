/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      colors: {
        ink: "#1a1a1a",
        muted: "#6b6b6b",
        accent: "#1b4965",
        "accent-light": "#62b6cb",
        paper: "#fafaf7",
        border: "#e5e5e0",
        ok: "#3a7d44",
        warn: "#d98e00",
        danger: "#c4463e",
      },
    },
  },
  plugins: [],
};
