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
          50: '#F0F4FF',
          100: '#DFE8FF',
          200: '#C2D2FF',
          300: '#9DB7FF',
          400: '#6F96FF',
          500: '#4C8EFF',
          600: '#2D6BFF',
          700: '#224FCF',
          800: '#1B3FA5',
          900: '#14307A',
        },
        secondary: {
          50: '#F3F2FF',
          100: '#E6E4FF',
          200: '#CECBFF',
          300: '#ABA7FF',
          400: '#8682F5',
          500: '#6D6AF2',
          600: '#5250C8',
          700: '#403EA7',
          800: '#302F80',
          900: '#1F1D58',
        },
        surface: {
          50: '#FAFAFD',
          100: '#F4F1FF',
          200: '#EDEAFF',
          300: '#DCD4FF',
          400: '#C3BBFF',
          500: '#ADA5FF',
        },
        neutral: {
          fog: '#FAFAFD',
          graphite: '#505869',
          slate: '#1F2330',
          silver: '#D6D9E6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
