import path from 'path'
import fs from 'fs'
import { app } from 'electron'

export interface DependencyStatus {
    name: string
    found: boolean
    path: string | null
    version: string | null
}

/**
 * Get the app's root directory (where the exe is located)
 */
function getAppDir(): string {
    if (app.isPackaged) {
        return path.dirname(app.getPath('exe'))
    }
    return process.cwd()
}

/**
 * Get the .bin directory path
 */
function getBinDir(): string {
    return path.join(getAppDir(), '.bin')
}

/**
 * Check if a binary exists in .bin folder (fast - no execution)
 */
function findBinary(name: string): DependencyStatus {
    const binDir = getBinDir()
    const localPath = path.join(binDir, process.platform === 'win32' ? `${name}.exe` : name)

    // Just check if file exists - don't run it (much faster)
    if (fs.existsSync(localPath)) {
        return { name, found: true, path: localPath, version: 'installed' }
    }

    return { name, found: false, path: null, version: null }
}

import { execSync } from 'child_process'

// ... imports

// ... existing findBinary ...

/**
 * Check for a system command/package (slow - execution)
 */
function findSystemDependency(name: string, checkCmd: string, versionParseRegex?: RegExp): DependencyStatus {
    try {
        const output = execSync(checkCmd, { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] })

        let version = 'installed'
        if (versionParseRegex) {
            const match = output.match(versionParseRegex)
            if (match && match[1]) {
                version = match[1]
            }
        }

        return { name, found: true, path: 'system', version }
    } catch {
        // If system check fails, it's missing
        return { name, found: false, path: null, version: null }
    }
}

/**
 * Check all required dependencies (fast - parallel file existence check)
 */
export function checkDependencies(): DependencyStatus[] {
    const ffmpeg = findBinary('ffmpeg')
    const pandoc = findBinary('pandoc')
    const pdftotext = findBinary('pdftotext')

    // Check python (system) and pdf2docx
    const python = findSystemDependency('python', 'python --version', /Python (\S+)/)
    let pdf2docx: DependencyStatus = { name: 'pdf2docx', found: false, path: null, version: null }

    if (python.found) {
        // Check if library is installed
        pdf2docx = findSystemDependency('pdf2docx', 'pip show pdf2docx', /Version: (\S+)/)

        // If found, try to locate the actual package path for size calculation (optional, purely for UI "size")
        if (pdf2docx.found) {
            try {
                // pip show pdf2docx | grep Location
                const info = execSync('pip show pdf2docx', { encoding: 'utf-8' })
                const locMatch = info.match(/Location: (.+)/)
                if (locMatch) {
                    // We point to the folder so the UI might be able to calculate size, 
                    // or at least it doesn't look like "system"
                    // combining Location + Name gives the package folder usually
                    pdf2docx.path = path.join(locMatch[1].trim(), 'pdf2docx')
                }
            } catch { }
        }
    }

    // Check magick, fallback to convert
    let imagemagick = findBinary('magick')
    if (!imagemagick.found) {
        imagemagick = findBinary('convert')
    }
    imagemagick.name = 'imagemagick'

    const xpdf = pdftotext
    xpdf.name = 'xpdf'

    // Note: LibreOffice removed - requires manual installation due to size (300MB+)
    return [ffmpeg, imagemagick, pandoc, xpdf, python, pdf2docx]
}

/**
 * Get missing dependencies
 */
export function getMissingDependencies(): string[] {
    const deps = checkDependencies()
    return deps.filter(d => !d.found).map(d => d.name)
}
