import { defineConfig } from 'vite'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import electron from 'vite-plugin-electron/simple'
import react from '@vitejs/plugin-react-swc'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
    plugins: [
        react(),
        electron({
            main: { entry: 'electron/main.ts' },
            preload: { input: join(__dirname, 'electron/preload.ts') },
        }),
    ],
    server: {
        host: '127.0.0.1',
        port: 5173,
    },
    optimizeDeps: {
        include: [
            'react',
            'react-dom',
            'lucide-react',
            'framer-motion',
            'zustand',
            'clsx',
            'tailwind-merge',
        ],
    },
})
