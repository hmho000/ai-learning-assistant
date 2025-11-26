import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 说明：
// - build 输出目录保持为默认的 "dist"，与后端约定一致（backend/app.py 使用 frontend/dist）
// - 开发模式下通过 proxy 将 /api/* 请求转发到 FastAPI 后端（http://localhost:8000）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});

