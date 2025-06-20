// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'

// // https://vite.dev/config/
// export default defineConfig({
//   plugins: [react()],
//   server: {
//     proxy: {
//       '/': {
//         target: 'http://localhost:5000',
//         changeOrigin: true,
//         secure: false,
//       },
//     },
//   },
// })

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    assetsDir: 'static',
  },
  server: {
    port: 3000,
    cors: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000/", 
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""),  
      },
    },
  },
});
