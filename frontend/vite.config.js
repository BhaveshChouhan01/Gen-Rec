import { defineConfig } from "vite";
// import react from "@vitejs/plugin-react"; // uncomment if using React

export default defineConfig({
  clearScreen: false,
  server: {
    host: true,       // show both Local + Network URL
    port: 5173,
    strictPort: true, // avoid "choose another port?" prompt
    open: true        // auto open browser
  }
});
