/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        'dolarize-dark': '#0B132B',
        'dolarize-card': '#111C3A',
        'dolarize-gold': '#C5A059',
        'dolarize-blue-glow': '#1E40AF',
      },
      fontFamily: {
        'sans': ['Inter', 'Montserrat', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
