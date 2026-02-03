import { IpcMain, dialog, BrowserWindow, app } from 'electron'
import { join, dirname } from 'node:path'

/**
 * Get the app's root directory (where the exe is located)
 * In dev mode: uses cwd
 * In production: uses the directory containing the exe
 */
function getAppDir(): string {
    if (app.isPackaged) {
        // Production: use the exe's directory
        return dirname(app.getPath('exe'))
    }
    // Development: use current working directory
    return process.cwd()
}

/**
 * Get the .bin directory path for storing dependencies
 */
export function getBinDir(): string {
    return join(getAppDir(), '.bin')
}

export function registerHandlers(ipcMain: IpcMain) {
    // Window controls
    ipcMain.on('toMain', (event, data) => {
        const win = BrowserWindow.fromWebContents(event.sender)
        if (!win) return

        switch (data.type) {
            case 'setZoom':
                win.webContents.setZoomFactor(data.scale)
                break
            case 'minimize':
                win.minimize()
                break
            case 'maximize':
                if (win.isMaximized()) {
                    win.unmaximize()
                } else {
                    win.maximize()
                }
                break
            case 'close':
                win.close()
                break
            case 'openFile':
                if (data.path) {
                    import('electron').then(({ shell }) => {
                        shell.showItemInFolder(data.path)
                    })
                }
                break
        }
    })

    // Folder selection
    ipcMain.handle('selectFolder', async (event) => {
        const win = BrowserWindow.fromWebContents(event.sender)
        if (!win) return null

        const result = await dialog.showOpenDialog(win, {
            properties: ['openDirectory']
        })

        if (!result.canceled && result.filePaths.length > 0) {
            return result.filePaths[0]
        }
        return null
    })

    // Dependency check
    ipcMain.handle('checkDependencies', async () => {
        const { checkDependencies } = await import('../core/dependencyCheck')
        return await checkDependencies()
    })

    ipcMain.handle('getMissingDependencies', async () => {
        const { getMissingDependencies } = await import('../core/dependencyCheck')
        return await getMissingDependencies()
    })

    // Get supported target formats
    ipcMain.handle('getTargetFormats', async (_event, sourceExt: string) => {
        const { conversionGraph } = await import('../core/conversionGraph')
        return conversionGraph.getTargets(sourceExt)
    })

    // Start conversion
    ipcMain.handle('startConversion', async (event, { taskId, inputPath, targetFormat, outputDir }) => {
        const { convert } = await import('../core/engine')
        const { stat } = await import('node:fs/promises')

        const onProgress = (progress: any) => {
            event.sender.send('fromMain', { type: 'conversionProgress', ...progress })
        }

        try {
            const outputPath = await convert(taskId, inputPath, targetFormat, outputDir, onProgress)
            // Get output file size
            const stats = await stat(outputPath)
            return { success: true, outputPath, outputSize: stats.size }
        } catch (err: any) {
            return { success: false, error: err.message }
        }
    })

    // Download dependencies
    ipcMain.handle('downloadDependency', async (event, depName: string) => {
        const { downloadDependency } = await import('../core/downloader')
        const binDir = getBinDir()

        const onProgress = (progress: any) => {
            if (!event.sender.isDestroyed()) {
                event.sender.send('fromMain', { type: 'downloadProgress', ...progress })
            }
        }

        return await downloadDependency(depName, binDir, onProgress)
    })

    // Detect GPUs
    ipcMain.handle('detectGpus', async () => {
        const { detectGpus } = await import('../core/gpuDetect')
        return await detectGpus()
    })

    // Delete all dependencies
    ipcMain.handle('deleteAllDependencies', async () => {
        const { rm } = await import('node:fs/promises')
        const binDir = getBinDir()
        try {
            await rm(binDir, { recursive: true, force: true })
            console.log(`Deleted dependencies folder: ${binDir}`)
            return true
        } catch (error) {
            console.error('Failed to delete dependencies:', error)
            return false
        }
    })

    // Get bin directory path (for debugging/info)
    ipcMain.handle('getBinDir', () => {
        return getBinDir()
    })

    // Silent Save (Archive/Logs)
    ipcMain.handle('saveSilent', async (_event, { type, content }: { type: 'archive' | 'logs', content: string }) => {
        const { writeFile, mkdir } = await import('node:fs/promises')

        const rootDir = getAppDir()
        // Save into "Archive" or "Logs" folder at the same level as .bin
        const targetDir = join(rootDir, type === 'archive' ? 'Archive' : 'Logs')

        try {
            await mkdir(targetDir, { recursive: true })

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
            const filename = `${type}_${timestamp}.txt`
            const filePath = join(targetDir, filename)

            await writeFile(filePath, content, 'utf-8')
            return { success: true, path: filePath }
        } catch (error: any) {
            console.error(`Failed to save ${type}:`, error)
            return { success: false, error: error.message }
        }
    })
}
