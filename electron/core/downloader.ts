import path from 'path'
import fs from 'fs'
import https from 'https'
import http from 'http'
import { exec, spawn } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

export interface DownloadProgress {
    dependency: string
    percent: number
    status: 'pending' | 'downloading' | 'extracting' | 'done' | 'error'
    message?: string
}

type ProgressCallback = (progress: DownloadProgress) => void

interface DepConfig {
    url: string
    extractPath: string
    type: 'zip' | '7z' | 'pip'
}

// ALL dependencies use ZIP or 7z extraction - NO INSTALLERS!
const DOWNLOAD_URLS: Record<string, DepConfig> = {
    ffmpeg: {
        // gyan.dev always serves latest release via this URL
        url: 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
        extractPath: '', // Dynamic - will find folder starting with 'ffmpeg-'
        type: 'zip'
    },
    imagemagick: {
        // Portable 7z version - NO INSTALLER!
        url: 'https://imagemagick.org/archive/binaries/ImageMagick-7.1.2-11-portable-Q16-x64.7z',
        extractPath: '', // Files are directly in the archive root
        type: '7z'
    },
    pandoc: {
        // Updated to latest version 3.8.3
        url: 'https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-windows-x86_64.zip',
        extractPath: 'pandoc-3.8.3',
        type: 'zip'
    },
    libreoffice: {
        // Skip LibreOffice for now - it's 300MB+ and requires complex extraction
        // Users can install it manually if needed for DOC/DOCX conversion
        // Pandoc can handle most document conversions
        url: '',
        extractPath: '',
        type: 'zip'
    },
    xpdf: {
        // Updated to latest version 4.06
        url: 'https://dl.xpdfreader.com/xpdf-tools-win-4.06.zip',
        extractPath: 'xpdf-tools-win-4.06\\bin64',
        type: 'zip'
    },
    pdf2docx: {
        // Python package - installed via pip
        url: 'pdf2docx', // Name of package for pip
        extractPath: '',
        type: 'pip'
    }
}

function downloadWithRedirects(url: string, dest: string, onProgress: (percent: number) => void, maxRedirects = 15): Promise<void> {
    // ... (same as before)
    return new Promise((resolve, reject) => {
        if (maxRedirects <= 0) {
            reject(new Error('Too many redirects'))
            return
        }

        const protocol = url.startsWith('https') ? https : http

        const request = protocol.get(url, { timeout: 30000 }, (res) => {
            // Handle redirects
            if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                let redirectUrl = res.headers.location
                if (redirectUrl.startsWith('/')) {
                    const urlObj = new URL(url)
                    redirectUrl = `${urlObj.protocol}//${urlObj.host}${redirectUrl}`
                }
                console.log(`Redirecting to: ${redirectUrl}`)
                downloadWithRedirects(redirectUrl, dest, onProgress, maxRedirects - 1)
                    .then(resolve)
                    .catch(reject)
                return
            }

            if (res.statusCode !== 200) {
                reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`))
                return
            }

            const totalSize = parseInt(res.headers['content-length'] || '0', 10)
            let downloaded = 0

            const file = fs.createWriteStream(dest)

            res.on('data', (chunk: Buffer) => {
                downloaded += chunk.length
                if (totalSize > 0) {
                    onProgress(Math.round((downloaded / totalSize) * 100))
                }
            })

            res.pipe(file)
            file.on('finish', () => {
                file.close()
                resolve()
            })
            file.on('error', reject)
        })

        request.on('error', reject)
        request.on('timeout', () => {
            request.destroy()
            reject(new Error('Request timeout'))
        })
    })
}

async function extractZip(zipPath: string, destDir: string, subPath?: string, depName?: string): Promise<void> {
    // ... (same as before)
    await fs.promises.mkdir(destDir, { recursive: true })
    console.log(`Extracting ${zipPath} to ${destDir}`)
    const cmd = `powershell -Command "Expand-Archive -Path '${zipPath}' -DestinationPath '${destDir}' -Force"`
    await execAsync(cmd, { timeout: 300000 }) // 5 min timeout for large files

    let actualSubPath = subPath
    if (!actualSubPath && depName === 'ffmpeg') {
        const entries = await fs.promises.readdir(destDir)
        const ffmpegDir = entries.find(e => e.startsWith('ffmpeg-'))
        if (ffmpegDir) {
            actualSubPath = path.join(ffmpegDir, 'bin')
        }
    }

    if (actualSubPath) {
        const srcDir = path.join(destDir, actualSubPath)
        if (fs.existsSync(srcDir)) {
            const files = await fs.promises.readdir(srcDir)
            for (const file of files) {
                const srcFile = path.join(srcDir, file)
                const destFile = path.join(destDir, file)
                if (!fs.existsSync(destFile)) {
                    await fs.promises.rename(srcFile, destFile)
                }
            }
        }
    }
}

async function extract7z(archivePath: string, destDir: string): Promise<void> {
    // ... (same as before)
    await fs.promises.mkdir(destDir, { recursive: true })
    console.log(`Extracting 7z ${archivePath} to ${destDir}`)

    const sevenZaPath = path.join(destDir, '7za.exe')
    if (!fs.existsSync(sevenZaPath)) {
        console.log('Downloading 7za.exe for extraction...')
        const sevenZaUrl = 'https://www.7-zip.org/a/7za920.zip'
        const sevenZaZip = path.join(destDir, '7za_temp.zip')

        await new Promise<void>((resolve, reject) => {
            const file = fs.createWriteStream(sevenZaZip)
            https.get(sevenZaUrl, (res) => {
                res.pipe(file)
                file.on('finish', () => { file.close(); resolve() })
            }).on('error', reject)
        })

        const extractCmd = `powershell -Command "Expand-Archive -Path '${sevenZaZip}' -DestinationPath '${destDir}' -Force"`
        await execAsync(extractCmd, { timeout: 30000 })
        await fs.promises.unlink(sevenZaZip)
    }

    const cmd = `"${sevenZaPath}" x "${archivePath}" -o"${destDir}" -y`
    await execAsync(cmd, { timeout: 300000 })
}

async function installPipPackage(packageName: string, onProgress: (percent: number, message?: string) => void): Promise<void> {
    console.log(`[PIP] Installing ${packageName}...`)

    return new Promise((resolve, reject) => {
        // Using spawn to get real-time output
        const cmd = 'python'
        // Add --prefer-binary to avoid source builds if possible
        const args = ['-m', 'pip', 'install', '--upgrade', packageName, '--no-warn-script-location', '--prefer-binary']

        console.log(`[PIP] Running: ${cmd} ${args.join(' ')}`)

        const child = spawn(cmd, args, {
            shell: true
        })

        // Smarter fake progress
        let fakePercent = 0
        let ticks = 0
        const timer = setInterval(() => {
            ticks++

            let shouldIncrement = false

            if (fakePercent < 50) {
                // Fast start (every tick)
                shouldIncrement = true
                fakePercent += 2
            } else if (fakePercent < 75) {
                // Moderate (every 2nd tick)
                if (ticks % 2 === 0) {
                    shouldIncrement = true
                    fakePercent += 1
                }
            } else if (fakePercent < 90) {
                // Slow (every 5th tick = 5s)
                if (ticks % 5 === 0) {
                    shouldIncrement = true
                    fakePercent += 1
                }
            } else if (fakePercent < 95) {
                // Very slow (every 10th tick = 10s)
                if (ticks % 10 === 0) {
                    shouldIncrement = true
                    fakePercent += 1
                }
            }

            if (shouldIncrement && fakePercent <= 95) {
                onProgress(fakePercent)
            }
        }, 1000)

        const handleOutput = (data: Buffer) => {
            const line = data.toString().trim()
            if (!line) return

            console.log(`[PIP] ${line}`)

            // Heuristic status updates
            if (line.includes('Building') || line.includes('running setup.py') || line.includes('metadata')) {
                onProgress(fakePercent, 'Compiling (this might take some time)...')
            } else if (line.includes('Collecting') || line.includes('Downloading')) {
                onProgress(fakePercent, 'Downloading packages...')
            } else if (line.includes('Installing')) {
                onProgress(fakePercent, 'Installing...')
            }
        }

        child.stdout.on('data', handleOutput)
        child.stderr.on('data', handleOutput)

        child.on('close', (code: number) => {
            clearInterval(timer)
            if (code === 0) {
                onProgress(100, 'Installation complete')
                resolve()
            } else {
                reject(new Error(`Pip install process exited with code ${code}`))
            }
        })

        child.on('error', (err: Error) => {
            clearInterval(timer)
            reject(err)
        })
    })
}

export async function downloadDependency(
    name: string,
    binDir: string,
    onProgress: ProgressCallback
): Promise<boolean> {
    const config = DOWNLOAD_URLS[name]
    if (!config) {
        onProgress({ dependency: name, percent: 0, status: 'error', message: `Unknown dependency: ${name}` })
        return false
    }

    if (config.type === 'pip') {
        try {
            onProgress({ dependency: name, percent: 0, status: 'downloading' }) // status mapped to UI
            // Check if python exists first
            try {
                await execAsync('python --version')
            } catch {
                throw new Error('Python is not installed or not in PATH')
            }

            onProgress({ dependency: name, percent: 10, status: 'downloading' })
            await installPipPackage(config.url, (percent, message) => {
                onProgress({ dependency: name, percent, status: 'downloading', message })
            })

            console.log(`${name} installed successfully`)
            onProgress({ dependency: name, percent: 100, status: 'done' })
            return true
        } catch (e) {
            const error = e as Error
            console.error(`Error installing ${name}:`, error.message)
            onProgress({ dependency: name, percent: 0, status: 'error', message: error.message })
            return false
        }
    }

    // Skip if no URL (like LibreOffice which is optional)
    if (!config.url) {
        // ... (rest remains same)
        onProgress({ dependency: name, percent: 0, status: 'error', message: `${name} must be installed manually` })
        return false
    }

    const urlExt = config.url.split('.').pop()?.toLowerCase() || 'zip'
    const filePath = path.join(binDir, `${name}_temp.${urlExt}`)

    try {
        await fs.promises.mkdir(binDir, { recursive: true })

        console.log(`Downloading ${name} from ${config.url}`)
        onProgress({ dependency: name, percent: 0, status: 'downloading' })
        await downloadWithRedirects(config.url, filePath, (percent) => {
            onProgress({ dependency: name, percent, status: 'downloading' })
        })

        console.log(`Extracting ${name}...`)
        onProgress({ dependency: name, percent: 100, status: 'extracting' })

        if (config.type === '7z') {
            await extract7z(filePath, binDir)
        } else {
            await extractZip(filePath, binDir, config.extractPath || undefined, name)
        }

        await fs.promises.unlink(filePath)

        console.log(`${name} installed successfully`)
        onProgress({ dependency: name, percent: 100, status: 'done' })
        return true
    } catch (e) {
        const error = e as Error
        console.error(`Error installing ${name}:`, error.message)
        onProgress({ dependency: name, percent: 0, status: 'error', message: error.message })
        try { await fs.promises.unlink(filePath) } catch { }
        return false
    }
}
