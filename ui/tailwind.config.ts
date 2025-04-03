import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  darkMode: "class", // Enable dark mode using class strategy
  content: [
    "./pages/**/*.{ts,tsx}", // Include pages directory if you use it
    "./components/**/*.{ts,tsx}", // Include components directory
    "./app/**/*.{ts,tsx}", // Include app directory (Next.js 13+ App Router)
    "./src/**/*.{ts,tsx}", // Include src directory
  ],
  prefix: "", // No prefix for utility classes
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      fontFamily: {
        // Example: If using a custom font like Inter
        sans: ["var(--font-sans)", "sans-serif"],
      },
    },
  },
  plugins: [
    typography, // Only typography plugin remains
  ],
};

export default config;
