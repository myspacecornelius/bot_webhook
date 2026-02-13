# Electron Desktop App

## Structure

```
electron/
├── main.js          # Main process (spawns Python backend)
├── preload.js       # Bridge to renderer
└── assets/          # Icons (512x512 PNG)
```

## Building

### 1. Package Python Backend

```bash
source venv/bin/activate
pip install pyinstaller
pyinstaller pyinstaller.spec

mkdir -p python-dist
cp -r dist/phantom-bot python-dist/
```

### 2. Build Electron App

```bash
cd frontend
npm run build
npm run electron:build
```

**Output:**

- macOS: `dist-electron/Phantom Bot-1.0.0.dmg`
- Windows: `dist-electron/Phantom Bot Setup 1.0.0.exe`
- Linux: `dist-electron/Phantom Bot-1.0.0.AppImage`

## Features

- **Bundled Python Backend** — Users don't need Python installed
- **Auto-Updates** — Checks GitHub for new versions via `electron-updater`
- **License Validation** — Integrated with auth system
- **Cross-Platform** — macOS, Windows, Linux

## Architecture

The Electron main process spawns the Python backend as a child process, then loads the built React frontend. The frontend communicates with the local backend via `http://localhost:8080`.
