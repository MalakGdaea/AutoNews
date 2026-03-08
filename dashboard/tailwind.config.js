/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
    "./lib/**/*.{js,jsx}"
  ],
  theme: {
    extend: {
      colors: {
        surface: "#0E1116",
        panel: "#161B22",
        accent: "#1CC88A",
        warning: "#FFB020",
        danger: "#EF4444",
        text: "#E6EDF3",
        muted: "#8B949E"
      },
      boxShadow: {
        panel: "0 20px 45px rgba(0, 0, 0, 0.35)"
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        rise: "rise 400ms ease-out both"
      }
    }
  },
  plugins: []
};
