/**
 * ConversionGraph - BFS Pathfinding for file format conversions.
 * Defines nodes (formats) and edges (converters), then finds shortest paths.
 */

type ConverterType = 'ffmpeg' | 'imagemagick' | 'pandoc' | 'libreoffice' | 'python' | 'xpdf'

interface Edge {
    target: string
    converter: ConverterType
}

export class ConversionGraph {
    private adjacencyList: Map<string, Edge[]> = new Map()

    constructor() {
        this.buildGraph()
    }

    private addEdge(source: string, target: string, converter: ConverterType) {
        if (!this.adjacencyList.has(source)) {
            this.adjacencyList.set(source, [])
        }
        this.adjacencyList.get(source)!.push({ target, converter })
    }

    private buildGraph() {
        // Video formats (FFmpeg)
        const videoFormats = ['mp4', 'mkv', 'avi', 'mov', 'webm', 'wmv', 'flv', 'gif']
        for (const src of videoFormats) {
            for (const dst of videoFormats) {
                if (src !== dst) this.addEdge(src, dst, 'ffmpeg')
            }
        }

        // Video to Audio (extract)
        const audioFormats = ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a']
        for (const video of videoFormats) {
            for (const audio of audioFormats) {
                this.addEdge(video, audio, 'ffmpeg')
            }
        }

        // Audio to Audio
        for (const src of audioFormats) {
            for (const dst of audioFormats) {
                if (src !== dst) this.addEdge(src, dst, 'ffmpeg')
            }
        }

        // Image formats (ImageMagick)
        const imageFormats = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff', 'ico', 'svg']
        for (const src of imageFormats) {
            for (const dst of imageFormats) {
                if (src !== dst) this.addEdge(src, dst, 'imagemagick')
            }
        }

        // Document formats (Pandoc & LibreOffice)
        const docFormats = ['docx', 'doc', 'odt', 'rtf', 'txt', 'html', 'md']
        for (const src of docFormats) {
            for (const dst of docFormats) {
                if (src !== dst) this.addEdge(src, dst, 'pandoc')
            }
            // To PDF via LibreOffice
            this.addEdge(src, 'pdf', 'libreoffice')
        }

        // PDF to images (ImageMagick)
        this.addEdge('pdf', 'png', 'imagemagick')
        this.addEdge('pdf', 'jpg', 'imagemagick')

        // PDF to DOCX (Python - pdf2docx)
        this.addEdge('pdf', 'docx', 'python')

        // PDF to Text (XPDF - pdftotext)
        this.addEdge('pdf', 'txt', 'xpdf')

        // eBook formats (Pandoc)
        this.addEdge('epub', 'pdf', 'pandoc')
        this.addEdge('epub', 'html', 'pandoc')
        this.addEdge('md', 'pdf', 'pandoc')
        this.addEdge('md', 'html', 'pandoc')
        this.addEdge('md', 'docx', 'pandoc')
    }

    /**
     * Find shortest conversion path using BFS.
     * Returns array of { format, converter } steps, or null if no path.
     */
    findPath(source: string, target: string): { format: string; converter: ConverterType }[] | null {
        const srcLower = source.toLowerCase()
        const tgtLower = target.toLowerCase()

        if (srcLower === tgtLower) return []
        if (!this.adjacencyList.has(srcLower)) return null

        const visited = new Set<string>()
        const queue: { node: string; path: { format: string; converter: ConverterType }[] }[] = [
            { node: srcLower, path: [] }
        ]

        while (queue.length > 0) {
            const { node, path } = queue.shift()!

            if (visited.has(node)) continue
            visited.add(node)

            const edges = this.adjacencyList.get(node) || []
            for (const edge of edges) {
                const newPath = [...path, { format: edge.target, converter: edge.converter }]

                if (edge.target === tgtLower) {
                    return newPath
                }

                if (!visited.has(edge.target)) {
                    queue.push({ node: edge.target, path: newPath })
                }
            }
        }

        return null
    }

    /**
     * Get all reachable target formats from a given source format.
     */
    getTargets(source: string): string[] {
        const srcLower = source.toLowerCase()
        const reachable = new Set<string>()
        const visited = new Set<string>()
        const queue = [srcLower]

        while (queue.length > 0) {
            const node = queue.shift()!
            if (visited.has(node)) continue
            visited.add(node)

            const edges = this.adjacencyList.get(node) || []
            for (const edge of edges) {
                reachable.add(edge.target)
                if (!visited.has(edge.target)) {
                    queue.push(edge.target)
                }
            }
        }

        return Array.from(reachable).sort()
    }
}

export const conversionGraph = new ConversionGraph()
