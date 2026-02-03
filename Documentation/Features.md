# Shift - Features & Capabilities

**Shift** is a powerful, offline-first universal file converter designed for privacy, speed, and ease of use. It handles widely used formats across video, audio, images, and documents without uploading data to the cloud.

---

## ✨ Key Features

### 🚀 Core Functionality
*   **Universal Conversion**: Convert between hundreds of media and document formats.
*   **Batch Processing**: Drag and drop multiple files or entire folders to convert them simultaneously.
*   **Queue Management**: Reorder tasks, remove items, or clear the entire queue with a single click.
*   **Smart Automation**: "Convert All" functionality to apply a single target format to every item in the queue.

### 🛠️ Advanced Engine
*   **Zero-Config Dependencies**: Shift automatically downloads and configures **FFmpeg**, **ImageMagick**, **Pandoc**, and **LibreOffice**.
*   **GPU Acceleration**: Automatically detects and utilizes NVIDIA, AMD, or Intel GPUs for faster video encoding.
*   **Offline Privacy**: All conversions happen locally on your machine. No files are ever uploaded.

### 💾 Data Management
*   **Archive System**: Keeps a history of your converted files for quick access.
*   **Auto-Save**: Options to automatically save converted files and conversion logs to disk.
*   **Logs Panel**: Real-time distinct logs for debugging and process monitoring.

### 🎨 Modern UI/UX
*   **Floating Panels**: Detachable Logs and Archive panels for a customizable workspace.
*   **UI Scaling**: Adjust the interface size to match your display preferences.
*   **Dependency Manager**: Built-in tools to verify, repair, or reinstall conversion engines.

---

## 📋 Supported Conversion Formats

### 🎥 Video Formats
**Engine:** FFmpeg

| Input Format | Compatible Output Formats |
| :--- | :--- |
| `.mp4`, `.mkv`, `.avi`, `.mov`<br>`.webm`, `.wmv`, `.flv`, `.gif` | **Video:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.wmv`, `.flv`, `.gif`<br>**Audio:** `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, `.m4a` |

### 🎵 Audio Formats
**Engine:** FFmpeg

| Input Format | Compatible Output Formats |
| :--- | :--- |
| `.mp3`, `.wav`, `.aac`<br>`.flac`, `.ogg`, `.m4a` | `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, `.m4a` |

### 🖼️ Image Formats
**Engine:** ImageMagick

| Input Format | Compatible Output Formats |
| :--- | :--- |
| `.jpg`, `.jpeg`, `.png`, `.webp`<br>`.gif`, `.bmp`, `.tiff`, `.ico`, `.svg` | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp`, `.tiff`, `.ico`, `.svg` |

### 📄 Document Formats
**Engines:** Pandoc, LibreOffice

| Input Format | Compatible Output Formats | Notes |
| :--- | :--- | :--- |
| `.docx`, `.doc`, `.odt`<br>`.rtf`, `.txt`, `.html` | `.docx`, `.doc`, `.odt`, `.rtf`<br>`.txt`, `.html`, `.md`, `.pdf` | _PDF conversion uses LibreOffice._ |
| `.md` (Markdown) | `.pdf`, `.html`, `.docx` | _Direct conversions via Pandoc._ |
| `.epub` (E-book) | `.pdf`, `.html` | _Uses Pandoc._ |
| `.pdf` | `.png`, `.jpg` | _Uses ImageMagick (Extract pages)._ |

> **Note:** PDF to DOCX conversion is currently a known limitation with LibreOffice.
> **Planned Fix:** Integration of `pdf2docx` (Python) for reliable text extraction.
