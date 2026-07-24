import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cosmic: {
          black: '#0A0A0F',
          soft: '#0D0D14',
          surface: '#111118',
          border: '#16161F',
          cyan: '#00FFFF',
          'cyan-dim': '#00CCCC',
          purple: '#6C63FF',
          'purple-dim': '#5A52E0',
          white: '#FFFFFF',
          muted: '#A0A0B8',
          dim: '#6A6A88',
        },
      },
      fontFamily: {
        sans: ['var(--font-syne)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      boxShadow: {
        'cyan-glow': '0 0 30px rgba(0, 255, 255, 0.25)',
        'purple-glow': '0 0 30px rgba(108, 99, 255, 0.30)',
      },
      keyframes: {
        'aurora-drift': {
          '0%': { opacity: '1', transform: 'scale(1) translateY(0px)' },
          '50%': { transform: 'scale(1.03) translateY(-12px) translateX(8px)' },
          '100%': { opacity: '0.85', transform: 'scale(1.02) translateY(-6px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
      animation: {
        aurora: 'aurora-drift 24s ease-in-out infinite alternate',
        shimmer: 'shimmer 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

export default config
