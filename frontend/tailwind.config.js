/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        parchment: {
          50: '#FDFBF7',
          100: '#F9F6F0',
          200: '#F3EFE6',
          300: '#EAE4D7',
          400: '#DDD4C3',
          500: '#CABEAE',
        },
        brass: {
          50: '#FBF8F0',
          100: '#F5EED8',
          200: '#EBDBB0',
          300: '#DFC283',
          400: '#CCA355',
          500: '#B88730', // Antique brass primary
          600: '#9C6E25',
          700: '#7D5420',
          800: '#64421E',
          900: '#4F351B',
        },
        charcoal: {
          50: '#F6F6F6',
          100: '#E7E7E7',
          200: '#D1D1D1',
          300: '#B0B0B0',
          400: '#888888',
          500: '#6D6D6D',
          600: '#575757',
          700: '#444444',
          800: '#2B2B2B',
          900: '#1A1A1A',
          950: '#111111',
        },
        gold: {
          pure: '#D4AF37',
          foil: '#E6CA65',
          alloy: '#C29B38',
          scrap: '#A88029',
        },
        status: {
          success: '#15803D',
          'success-bg': '#F0FDF4',
          'success-border': '#BBF7D0',
          warning: '#B45309',
          'warning-bg': '#FFFBEB',
          'warning-border': '#FDE68A',
          danger: '#B91C1C',
          'danger-bg': '#FEF2F2',
          'danger-border': '#FECACA',
          info: '#334155',
          'info-bg': '#F8FAFC',
          'info-border': '#E2E8F0',
        }
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        serif: ['"Cinzel"', '"Playfair Display"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', '"SFMono-Regular"', 'Consolas', '"Liberation Mono"', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(28, 25, 23, 0.05)',
        'card': '0 1px 3px 0 rgba(28, 25, 23, 0.07), 0 1px 2px -1px rgba(28, 25, 23, 0.05)',
        'brass': '0 0 0 1px rgba(184, 135, 48, 0.25), 0 2px 4px rgba(184, 135, 48, 0.1)',
      }
    },
  },
  plugins: [],
}

