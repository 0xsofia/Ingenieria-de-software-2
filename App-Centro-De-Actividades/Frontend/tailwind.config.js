/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e3a8a',
          900: '#172554',
        },
      },
      boxShadow: {
        frame: '0 24px 72px -40px rgba(15, 23, 42, 0.42)',
        panel: '0 20px 48px -40px rgba(15, 23, 42, 0.28)',
      },
    },
  },
  plugins: [],
}
