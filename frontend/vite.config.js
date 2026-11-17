import { defineConfig } from 'vite';

// Dev proxies chat/health to the FastAPI deliverable so the frontend
// uses relative URLs everywhere (no CORS surface, easy to reverse-proxy later).
// Lit needs no build plugin — plain Vite handles its template literals.
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/chat': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
