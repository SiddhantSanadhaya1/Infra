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
        insureco: {
          red: "#D0021B",
          "red-dark": "#A80116",
          "red-light": "#FF1F38",
          navy: "#1A1A2E",
          "navy-light": "#16213E",
          "navy-mid": "#0F3460",
          gray: "#F5F5F5",
          "gray-mid": "#9CA3AF",
          "gray-dark": "#374151",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
