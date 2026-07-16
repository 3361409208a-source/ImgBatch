/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        'on-primary': 'var(--color-on-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
        background: 'var(--color-background)',
        foreground: 'var(--color-foreground)',
        muted: 'var(--color-muted)',
        'muted-fg': 'var(--color-muted-fg)',
        border: 'var(--color-border)',
        surface: 'var(--color-surface)',
      },
      fontFamily: {
        sans: ['Manrope', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      borderRadius: {
        DEFAULT: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        md: 'var(--radius-md)',
        sm: 'var(--radius-sm)',
        xl: '1rem',
        '2xl': '1.25rem',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
        xl: 'var(--shadow-xl)',
      },
      animation: {
        'fade-up': 'fadeUp 0.6s ease-out forwards',
        float: 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
    },
  },
  plugins: [],
};
