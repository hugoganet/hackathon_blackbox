/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#F3F8FF',
          100: '#E8F2FF', 
          200: '#D1E5FF',
          300: '#A3CCFF',
          400: '#66A3FF',
          500: '#0066FF',
          600: '#0052CC',
          700: '#003D99',
          800: '#002966',
          900: '#001533',
        },
        dark: {
          900: '#1A1A1A',
        },
        success: '#00C851',
        warning: '#FF9500',
        error: '#FF3737',
        info: '#2196F3',
        gray: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#EEEEEE',
          300: '#E0E0E0',
          400: '#BDBDBD',
          500: '#9E9E9E',
          600: '#757575',
          700: '#424242',
          800: '#212121',
          900: '#0A0A0A',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      spacing: {
        'xs': '4px',
        'sm': '8px', 
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        '2xl': '48px',
        '3xl': '64px',
        '4xl': '96px',
      },
      boxShadow: {
        'elevation-1': '0 1px 3px rgba(0,0,0,0.1)',
        'elevation-2': '0 4px 6px rgba(0,0,0,0.1)', 
        'elevation-3': '0 10px 25px rgba(0,0,0,0.15)',
        'elevation-4': '0 20px 40px rgba(0,0,0,0.2)',
        'elevation-5': '0 30px 60px rgba(0,0,0,0.25)',
      },
      screens: {
        'mobile': {'max': '767px'},
        'tablet': {'min': '768px', 'max': '1023px'},
        'desktop': {'min': '1024px', 'max': '1439px'},
        'large-desktop': {'min': '1440px'},
      }
    },
  },
  plugins: [],
}