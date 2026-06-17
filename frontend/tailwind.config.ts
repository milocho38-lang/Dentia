import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        dentia: {
          primary: "#16A34A",
          secondary: "#22C55E",
          soft: "#BBF7D0",
          background: "#F8FAFC",
          text: "#1F2937",
          info: "#0EA5E9",
          warning: "#F59E0B",
          error: "#EF4444",
        },
      },
      boxShadow: {
        soft: "0 14px 40px rgba(31, 41, 55, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
