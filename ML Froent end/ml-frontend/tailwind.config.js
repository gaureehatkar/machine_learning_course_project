/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'page-bg': {
          DEFAULT: '#F6F8FA',
          alt: '#F4F8FB',
        },
        'surface-card': '#FFFFFF',
        'border-subtle': {
          DEFAULT: '#D9E2EC',
          alt: '#E2E8F0',
        },
        'text-primary': {
          DEFAULT: '#0F2137',
          alt: '#102A43',
        },
        'text-secondary': {
          DEFAULT: '#486581',
          alt: '#5B6B7B',
        },
        'text-muted': '#627D98',
        'action-primary': {
          DEFAULT: '#0E7C7E',
          alt: '#159A9C',
          hover: '#0b6567',
        },
        'domain-risk': {
          DEFAULT: '#2E5EAA',
          tint: '#F0F4FA',
          border: '#BCD0EE',
        },
        'domain-evidence': {
          DEFAULT: '#B9770E',
          tint: '#FDF8F0',
          border: '#F4DCB1',
        },
        'domain-policy': {
          DEFAULT: '#6B4C9A',
          tint: '#F6F3FA',
          border: '#DACFE7',
        },
        'status-approve': {
          DEFAULT: '#1B7F37',
          alt: '#1E8A3E',
          bright: '#3FB950',
          surface: '#EAF5EC',
          dark: '#0A3615',
        },
        'status-review': {
          DEFAULT: '#946200',
          alt: '#E3B341',
          bright: '#F0C000',
          surface: '#FDF8E8',
          dark: '#412900',
        },
        'status-decline': {
          DEFAULT: '#CF222E',
          alt: '#F85149',
          surface: '#FDF0EF',
          dark: '#5C0B11',
        },
        'notice-bar': {
          bg: '#1E293B',
          text: '#E2E8F0',
        },
        'notice-banner': {
          bg: '#FFF8E6',
          border: '#F0C000',
          text: '#533F03',
        },
        'code-bg': '#0B1A28',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        full: '9999px',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
