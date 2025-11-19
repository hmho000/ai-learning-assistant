/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: "#2563eb",
        },
      },
      boxShadow: {
        subtle: "0 10px 25px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

