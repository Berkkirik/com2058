/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Apple's typeface stack. SF Pro is Apple-only — web falls back to the closest
        // commonly-available alternative, Inter, which is designed with similar metrics.
        display: [
          'SF Pro Display', '-apple-system', 'BlinkMacSystemFont',
          'Inter', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif',
        ],
        text: [
          'SF Pro Text', '-apple-system', 'BlinkMacSystemFont',
          'Inter', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif',
        ],
      },
      colors: {
        // Apple design system palette
        black: '#000000',
        'ink': '#1d1d1f',           // near-black, primary text on light
        'off-white': '#f5f5f7',     // light gray, alt section bg (not pure white)
        accent: '#0071e3',          // Apple Blue — ONLY chromatic color
        'link-dark': '#0066cc',     // slightly darker link on light bg
        'link-bright': '#2997ff',   // brighter link on dark bg
        // Dark surfaces (for cards on black sections)
        'surface-1': '#272729',
        'surface-2': '#262628',
        'surface-3': '#28282a',
        'surface-4': '#2a2a2d',
        'surface-5': '#242426',
        // Button neutrals
        'btn-active': '#ededf2',
        'btn-default': '#fafafc',
      },
      fontSize: {
        // Apple type scale (px and rem)
        'hero': ['56px', { lineHeight: '1.07', letterSpacing: '-0.28px', fontWeight: '600' }],
        'section': ['40px', { lineHeight: '1.10', letterSpacing: '-0.4px', fontWeight: '600' }],
        'tile': ['28px', { lineHeight: '1.14', letterSpacing: '0.196px', fontWeight: '400' }],
        'card-title': ['21px', { lineHeight: '1.19', letterSpacing: '0.231px', fontWeight: '700' }],
        'sub': ['21px', { lineHeight: '1.19', letterSpacing: '0.231px', fontWeight: '400' }],
        'nav-heading': ['34px', { lineHeight: '1.47', letterSpacing: '-0.374px', fontWeight: '600' }],
        'body-l': ['18px', { lineHeight: '1.47', letterSpacing: '-0.374px' }],
        'body': ['17px', { lineHeight: '1.47', letterSpacing: '-0.374px' }],
        'emphasis': ['17px', { lineHeight: '1.24', letterSpacing: '-0.374px', fontWeight: '600' }],
        'link': ['14px', { lineHeight: '1.43', letterSpacing: '-0.224px' }],
        'caption': ['14px', { lineHeight: '1.29', letterSpacing: '-0.224px' }],
        'micro': ['12px', { lineHeight: '1.33', letterSpacing: '-0.12px' }],
        'nano': ['10px', { lineHeight: '1.47', letterSpacing: '-0.08px' }],
      },
      borderRadius: {
        'pill': '980px',
        'xl-apple': '12px',
      },
      boxShadow: {
        'card-apple': 'rgba(0, 0, 0, 0.22) 3px 5px 30px 0px',
        'glow-accent': '0 0 0 4px rgba(0, 113, 227, 0.25)',
        'glow-strong': '0 8px 40px rgba(0, 113, 227, 0.35)',
      },
      backdropBlur: {
        'glass': '20px',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(0, 113, 227, 0.5)' },
          '50%': { boxShadow: '0 0 0 12px rgba(0, 113, 227, 0)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s cubic-bezier(0.22, 1, 0.36, 1) both',
        'fade-in': 'fade-in 0.4s ease-out both',
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-glow': 'pulse-glow 2.2s ease-out infinite',
        'float': 'float 4s ease-in-out infinite',
      },
      transitionTimingFunction: {
        'apple': 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
};
