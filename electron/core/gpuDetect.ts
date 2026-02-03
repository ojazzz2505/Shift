/// <reference types="node" />
import { exec } from 'node:child_process'
import { promisify } from 'node:util'

const execAsync = promisify(exec)

export interface GpuInfo {
    name: string
    vendor: string
    driverVersion?: string
}

/**
 * Detect available GPUs on the system
 */
export async function detectGpus(): Promise<GpuInfo[]> {
    const gpus: GpuInfo[] = []

    try {
        // Windows: Use PowerShell with CIM for detailed info
        if (process.platform === 'win32') {
            const { stdout } = await execAsync('powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Name, VideoProcessor, DriverVersion | ConvertTo-Json"')

            try {
                // Handle potential array or single object from JSON
                const raw = JSON.parse(stdout.trim())
                const items = Array.isArray(raw) ? raw : [raw]

                for (const item of items) {
                    // Filter out basic display adapters if needed, but usually we want all
                    // Name usually contains "NVIDIA GeForce RTX 4060", etc.
                    const name = item.Name || 'Unknown GPU'
                    const vendor = name.toLowerCase().includes('nvidia') ? 'NVIDIA' :
                        name.toLowerCase().includes('amd') ? 'AMD' :
                            name.toLowerCase().includes('intel') ? 'Intel' : 'Unknown'

                    gpus.push({
                        name,
                        vendor,
                        driverVersion: item.DriverVersion
                    })
                }
            } catch (jsonErr) {
                console.error('Failed to parse GPU JSON:', jsonErr)
            }
        }
        // Linux: Use lspci
        else if (process.platform === 'linux') {
            const { stdout } = await execAsync("lspci | grep -i 'vga\\|3d\\|display'")
            const lines = stdout.trim().split('\n')

            for (const line of lines) {
                const match = line.match(/:\s*(.+)/)
                if (match) {
                    gpus.push({
                        name: match[1].trim(),
                        vendor: match[1].includes('NVIDIA') ? 'NVIDIA' :
                            match[1].includes('AMD') ? 'AMD' :
                                match[1].includes('Intel') ? 'Intel' : 'Unknown'
                    })
                }
            }
        }
    } catch {
        console.error('GPU detection failed')
    }

    // Fallback if no GPUs detected
    if (gpus.length === 0) {
        gpus.push({ name: 'Default (CPU)', vendor: 'System' })
    }

    return gpus
}

/**
 * Get FFmpeg hardware acceleration options based on GPU vendor
 */
export function getHwAccelOptions(vendor: string): string[] {
    switch (vendor.toLowerCase()) {
        case 'nvidia':
            return ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
        case 'amd':
            return ['-hwaccel', 'amf']
        case 'intel':
            return ['-hwaccel', 'qsv']
        default:
            return []
    }
}
