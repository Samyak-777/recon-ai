/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        rzpNavyDark: '#02042b',
        rzpNavy: '#081326',
        rzpCard: '#0b192e',
        rzpCardBorder: 'rgba(51, 149, 255, 0.12)',
        rzpBlue: '#0c6cf2',
        rzpBlueLight: '#3395ff',
        rzpBlueHover: '#0b60d6',
        rzpGreen: '#00d09c',
        rzpGreenLight: '#13c296',
        rzpCyan: '#00baf2',
        rzpAmber: '#ffb400',
        rzpRose: '#f43f5e',
        rzpPurple: '#8b5cf6',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'rzp-glow': '0 0 35px -5px rgba(12, 108, 242, 0.25)',
        'rzp-green-glow': '0 0 30px -5px rgba(0, 208, 156, 0.25)',
        'rzp-purple-glow': '0 0 30px -5px rgba(139, 92, 246, 0.25)',
        'rzp-card': '0 10px 30px -10px rgba(2, 4, 43, 0.7)',
      }
    },
  },
  plugins: [],
}
