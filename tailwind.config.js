/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hal: {
          navy: '#003366',
          green: '#00A86B',
          gold: '#D4AF37',
          blue: '#1E90FF',
          bg: '#F4F6F8',
          panel: '#FFFFFF',
        }
      },
      fontFamily: {
        rajdhani: ['Rajdhani', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        '2xs': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}
