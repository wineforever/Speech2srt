/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0f766e",
        secondary: "#c96a45",
        accent: "#d6ad60",
        ink: "#1f2933",
        sand: "#f4efe7",
        slate: "#334155",
        mint: "#2a9d8f",
        danger: "#d64545",
      },
      fontFamily: {
        display: ['"Sora"', "sans-serif"],
        body: ['"IBM Plex Sans"', "sans-serif"],
      },
      boxShadow: {
        panel: "0 18px 50px -30px rgba(15, 23, 42, 0.4)",
      },
    },
  },
  plugins: [],
}
