# Shift

**Shift** is a powerful, privacy-focused desktop application designed for seamless local file conversions. Built with performance and security in mind, Shift handles your images, videos, audio documents, and more without ever uploading a single byte to the cloud.

## Features

-   **Zero-Cloud Privacy**: all conversions happen 100% locally on your machine.
-   **Smart Dependency Management**: automatically detects, installs, and manages required tools (FFmpeg, ImageMagick, Pandoc, LibreOffice).
-   **Hardware Acceleration**: optimized to utilize your specific GPU for faster video processing.
-   **Intelligent Queue**: drag-and-drop multiple files, pause/resume conversions, and manage priority.
-   **Organized Output**: automatically sorts converted files into logical folders (Video, Audio, Images, Documents).
-   **Archive History**: keeps a searchable log of all past conversions for easy access.
-   **Modern UI**: a sleek, dark-themed interface built for focus and efficiency.

## Tech Stack

-   **Runtime**: Electron
-   **Framework**: React 19 + TypeScript
-   **Build Tool**: Vite
-   **Styling**: TailwindCSS
-   **Animation**: Framer Motion
-   **State Management**: Zustand
-   **Core Engines**: FFmpeg, ImageMagick, Pandoc, LibreOffice

## Installation

### Prerequisites
-   Node.js (v18 or higher recommended)
-   npm or yarn

### Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/shift.git
    cd shift
    ```

2.  Install dependencies:
    ```bash
    npm install
    # or
    yarn install
    ```

## Development

To start the development server with hot-reloading:

```bash
npm run dev:fast
```

This runs the Vite server and launches the Electron application.

## Building

To create a production-ready installer/executable:

```bash
npm run build
```

The output files will be generated in the `release/` directory.

## License

[MIT](LICENSE)
