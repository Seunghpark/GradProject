import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins:[react()],
  // shortcut: retain build assets for restricted Windows writes; clean dist when packaging a release.
  build:{emptyOutDir:false},
  server:{host:'127.0.0.1',port:5173,strictPort:true,proxy:{'/api':'http://127.0.0.1:8000'}}
})
