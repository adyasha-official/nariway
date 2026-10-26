/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        lavender: { DEFAULT: "#E9D5FF", soft: "#F6EEFF", mist: "#FBF7FF" },
        plum: { DEFAULT: "#6B21AB", deep: "#4A1580", ink: "#2E0D52" },
        coral: { DEFAULT: "#FF7F6E", soft: "#FFE9E4" },
        teal: { DEFAULT: "#14B8A6", soft: "#DDF6F2" },
      },
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", "serif"],
        sans: ['"Inter Variable"', '"Inter"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 10px 30px -12px rgba(107,33,171,0.25)",
        phone: "0 30px 60px -20px rgba(46,13,82,0.45)",
      },
    },
  },
  plugins: [],
};
