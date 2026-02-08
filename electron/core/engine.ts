import { spawn } from 'child_process'
import path from 'path'
import { app } from 'electron'
import { mkdir } from 'fs/promises'
import { conversionGraph } from './conversionGraph'
import { writeMetadata } from './metadata'

export interface ConversionProgress {
    taskId: string
    percent: number
    status: 'converting' | 'done' | 'error'
    message?: string
}

type ProgressCallback = (progress: ConversionProgress) => void

/**
 * Get the .bin directory path
 */
function getBinDir(): string {
    if (app.isPackaged) {
        return path.join(path.dirname(app.getPath('exe')), '.bin')
    }
    return path.join(process.cwd(), '.bin')
}

/**
 * Get full path to a binary in .bin folder
 */
function getBinaryPath(name: string): string {
    const binDir = getBinDir()
    return path.join(binDir, process.platform === 'win32' ? `${name}.exe` : name)
}

/**
 * Execute a single conversion step using the appropriate engine.
 */
async function executeStep(
    inputPath: string,
    outputPath: string,
    converter: 'ffmpeg' | 'imagemagick' | 'pandoc' | 'libreoffice' | 'python' | 'xpdf',
    onProgress?: (percent: number) => void,
    metadata?: Record<string, string>
): Promise<string> {
    return new Promise((resolve, reject) => {
        let cmd: string
        let args: string[]

        switch (converter) {
            case 'ffmpeg':
                cmd = getBinaryPath('ffmpeg')
                args = ['-i', inputPath, '-y', '-progress', 'pipe:1']

                // Inject metadata if provided
                if (metadata) {
                    Object.entries(metadata).forEach(([key, value]) => {
                        if (value) args.push('-metadata', `${key}=${value}`)
                    })
                }

                args.push(outputPath)
                break
            case 'imagemagick':
                cmd = getBinaryPath('magick')
                // ImageMagick v7 uses 'magick input output', 'convert' is legacy/optional
                args = [inputPath, outputPath]
                break
            case 'pandoc':
                cmd = getBinaryPath('pandoc')
                args = [inputPath, '-o', outputPath]
                break
            case 'libreoffice':
                cmd = getBinaryPath('soffice')
                const outDir = path.dirname(outputPath)
                // Ensure output directory exists for libreoffice specifically if needed
                const outFormat = path.extname(outputPath).slice(1)
                args = ['--headless', '--convert-to', outFormat, '--outdir', outDir, inputPath]
                break
            case 'xpdf':
                cmd = getBinaryPath('pdftotext')
                // pdftotext [options] <PDF-file> [<text-file>]
                // -enc UTF-8 ensures proper encoding
                // -layout maintains original physical layout (optional but good for readability)
                args = ['-enc', 'UTF-8', '-layout', inputPath, outputPath]
                break
            case 'python':
                // Use system python. pdf2docx should be installed.
                // Command: python -c "from pdf2docx import Converter; cv = Converter('input.pdf'); cv.convert('output.docx'); cv.close()"
                cmd = 'python'
                // Escape paths for Python string literal
                const pyInput = inputPath.replace(/\\/g, '\\\\')
                const pyOutput = outputPath.replace(/\\/g, '\\\\')
                args = ['-c', `from pdf2docx import Converter; cv = Converter('${pyInput}'); cv.convert('${pyOutput}', start=0, end=None); cv.close()`]
                break
            default:
                reject(new Error(`Unknown converter: ${converter}`))
                return
        }

        let quotedCmd = `"${cmd}"`
        let quotedArgs = args.map(arg => arg.includes(' ') ? `"${arg}"` : arg)

        if (converter === 'python') {
            quotedCmd = cmd // 'python' no quotes needed typically, or keeps simple
            // For python -c, the script arg is complex.
            // We trust the args we built above are correct strings.
            // When using spawn with shell:true, we just need to ensure the whole command string is valid.
            // The script string inside args[1] is already wrapped in backticks (template literal) in JS,
            // but it contains spaces.
            // Example: python -c "..."
            // We need to double-quote the -c argument.
            quotedArgs = args.map(arg => {
                if (arg === '-c') return arg
                // This is the script argument
                return `"${arg.replace(/"/g, '\\"')}"`
            })
        }

        console.log(`[ENGINE] Running: ${quotedCmd} ${quotedArgs.join(' ')}`)

        const proc = spawn(quotedCmd, quotedArgs, { shell: true })
        let stderr = ''

        proc.stdout?.on('data', (data) => {
            const str = data.toString()
            // Parse FFmpeg progress
            const match = str.match(/out_time_ms=(\d+)/)
            if (match && onProgress) {
                // Rough progress estimation
                onProgress(Math.min(95, parseInt(match[1]) / 1000000 * 10))
            }
        })

        proc.stderr?.on('data', (data) => {
            stderr += data.toString()
        })

        proc.on('close', (code) => {
            if (code === 0) {
                resolve(outputPath)
            } else {
                reject(new Error(stderr || `Process exited with code ${code}`))
            }
        })

        proc.on('error', reject)
    })
}

/**
 * Execute a full conversion, potentially multi-hop.
 */
export async function convert(
    taskId: string,
    inputPath: string,
    targetFormat: string,
    outputDir: string,
    onProgress: ProgressCallback,
    metadata?: Record<string, string>
): Promise<string> {
    const ext = path.extname(inputPath).slice(1).toLowerCase()
    const baseName = path.basename(inputPath, path.extname(inputPath))

    // Find conversion path
    const conversionPath = conversionGraph.findPath(ext, targetFormat.toLowerCase())

    if (!conversionPath) {
        onProgress({ taskId, percent: 0, status: 'error', message: `No conversion path from ${ext} to ${targetFormat}` })
        throw new Error(`No conversion path from ${ext} to ${targetFormat}`)
    }

    if (conversionPath.length === 0) {
        // Same format, just copy
        onProgress({ taskId, percent: 100, status: 'done' })
        return inputPath
    }

    let currentPath = inputPath
    const totalSteps = conversionPath.length

    // Ensure output directory exists
    await mkdir(outputDir, { recursive: true })

    for (let i = 0; i < conversionPath.length; i++) {
        const step = conversionPath[i]
        const isLast = i === conversionPath.length - 1
        const stepOutputPath = isLast
            ? path.join(outputDir, `${baseName}.${step.format}`)
            : path.join(outputDir, `${baseName}_temp_${i}.${step.format}`)

        const stepProgress = (i / totalSteps) * 100

        onProgress({ taskId, percent: Math.round(stepProgress), status: 'converting' })

        try {
            currentPath = await executeStep(currentPath, stepOutputPath, step.converter, (p) => {
                const overallProgress = stepProgress + (p / totalSteps)
                onProgress({ taskId, percent: Math.round(overallProgress), status: 'converting' })
            }, isLast ? metadata : undefined)
        } catch (err: any) {
            onProgress({ taskId, percent: 0, status: 'error', message: err.message })
            throw err
        }
    }

    // Apply metadata post-conversion if the last step wasn't FFmpeg
    if (metadata && Object.keys(metadata).length > 0) {
        const lastConverter = conversionPath[conversionPath.length - 1]?.converter
        if (lastConverter !== 'ffmpeg') {
            try {
                await writeMetadata(currentPath, metadata)
            } catch (err: any) {
                onProgress({ taskId, percent: 0, status: 'error', message: `Metadata write failed: ${err.message}` })
                throw err
            }
        }
    }

    onProgress({ taskId, percent: 100, status: 'done' })
    return currentPath
}
