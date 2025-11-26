import { fontFamily } from "tailwindcss/defaultTheme";
import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#f5f5f7",
        surfaceMuted: "#ffffff",
        sidebar: "#ffffff",
        bubbleUser: "#0f766e",
        bubbleAssistant: "#f3f4f6",
        borderDark: "#e5e7eb",
        textPrimary: "#000000",
        textSecondary: "#000000",
        accent: "#0f766e",
      },
      fontFamily: {
        sans: ["Inter", ...fontFamily.sans],
      },
      boxShadow: {},
      animation: {
        "pulse-slow": "pulse 2.5s ease-in-out infinite",
      },
    },
  },
  plugins: [typography],
};

