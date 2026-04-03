/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:    ['DM Sans', 'system-ui', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
      },
      colors: {
        'pp-base':    'var(--bg-base)',
        'pp-surface': 'var(--bg-surface)',
        'pp-raised':  'var(--bg-elevated)',
        'pp-border':  'var(--border-soft)',
        'pp-accent':  'var(--accent)',
        'pp-cyan':    'var(--accent-cyan)',
        'pp-warm':    'var(--accent-warm)',
        'pp-text':    'var(--text-primary)',
        'pp-muted':   'var(--text-secondary)',
      },
      boxShadow: {
        'glow':    'var(--shadow-glow)',
        'glow-sm': 'var(--shadow-sm)',
        'glow-md': 'var(--shadow-md)',
      },
    },
  },
  plugins: [],
}
