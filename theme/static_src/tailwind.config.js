/** @type {import('tailwindcss').Config} */
import typography from '@tailwindcss/typography';

export default {
  content: [
    '../../**/{templates,static}/**/*.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    typography,
  ],
}; 