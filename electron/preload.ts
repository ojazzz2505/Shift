import { contextBridge, ipcRenderer, webUtils } from 'electron'

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
    // Get file path (Electon security helper)
    getPathForFile: (file: File) => {
        return webUtils.getPathForFile(file)
    },

    // One-way messages (fire-and-forget)
    send: (channel: string, data: any) => {
        const validChannels = ['toMain']
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data)
        }
    },

    // Receive messages from main
    receive: (channel: string, func: (...args: any[]) => void) => {
        const validChannels = ['fromMain']
        if (validChannels.includes(channel)) {
            ipcRenderer.on(channel, (_event, ...args) => func(...args))
        }
    },

    // Invoke handlers (request-response)
    invoke: async (channel: string, ...args: any[]) => {
        const validChannels = [
            'checkDependencies',
            'getMissingDependencies',
            'getTargetFormats',
            'startConversion',
            'downloadDependency',
            'detectGpus',
            'deleteAllDependencies',
            'selectFolder', // Added missing channel
            'readMetadata',
            'writeMetadata',
            'saveSilent'
        ]
        if (validChannels.includes(channel)) {
            return await ipcRenderer.invoke(channel, ...args)
        }
        throw new Error(`Invalid channel: ${channel}`)
    },

    // Remove listener
    removeListener: (channel: string, func: (...args: any[]) => void) => {
        ipcRenderer.removeListener(channel, func)
    }
})
