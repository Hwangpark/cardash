import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // '/cars'는 API 경로(axios)이자 SPA 라우트(/cars/:id)이기도 하다.
      // 브라우저가 직접 페이지를 요청(Accept: text/html)하면 SPA index.html을
      // 서빙하고, 그 외(axios fetch 등)만 백엔드로 프록시한다.
      '/cars': {
        target: 'http://localhost:8000',
        bypass: (req) => {
          if (req.headers.accept?.includes('text/html')) {
            return '/index.html'
          }
        },
      },
      '/admin': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
