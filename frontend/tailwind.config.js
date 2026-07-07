/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1B2430",
        navy: "#12263A",
        navyLight: "#1B3A56",
        steel: "#2E6F95",
        paper: "#F5F6F4",
      },
      fontFamily: {
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
