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
        navy: {
          950: '#070A11',
          900: '#0B0F19',
          850: '#0F1626',
          800: '#141D32',
          750: '#1A243D',
          700: '#1E293B',
          600: '#334155'
        },
        indigo: {
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          900: '#312E81'
        }
      }
    },
  },
  plugins: [],
}
