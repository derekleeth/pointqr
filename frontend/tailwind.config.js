/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // .dark class on <html> — same selector PrimeVue Aura uses
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  corePlugins: {
    // Disable Tailwind's base reset to avoid conflicts with PrimeVue's own normalisation
    preflight: false,
  },
  theme: {
    extend: {},
  },
  plugins: [],
}
