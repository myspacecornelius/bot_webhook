const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let mainWindow
let pythonProcess

// Python backend server
function startPythonBackend() {
  const isDev = !app.isPackaged
  
  if (isDev) {
    // Development: use local Python
    pythonProcess = spawn('python3', [
      path.join(__dirname, '..', '..', 'main.py'),
      '--mode', 'server',
      '--port', '8081',
      '--host', '127.0.0.1'
    ], {
      cwd: path.join(__dirname, '..', '..')
    })
  } else {
    // Production: use packaged Python binary
    const pythonBinary = path.join(
      process.resourcesPath,
      'python',
      process.platform === 'win32' ? 'main.exe' : 'main'
    )
    
    pythonProcess = spawn(pythonBinary, [
      '--mode', 'server',
      '--port', '8081',
      '--host', '127.0.0.1'
    ])
  }
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Python] ${data}`)
  })
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Python Error] ${data}`)
  })
  
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`)
  })
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    backgroundColor: '#09090b',
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  })
  
  // Load app
  const isDev = !app.isPackaged
  
  // Always load built files (production mode)
  const indexPath = path.join(__dirname, '..', 'dist', 'index.html')
  console.log('Loading:', indexPath)
  
  mainWindow.loadFile(indexPath).catch(err => {
    console.error('Failed to load:', err)
  })
  
  // Open DevTools for debugging
  mainWindow.webContents.openDevTools()
  
  // Auto-updater events (disabled for now)
  // TODO: Re-enable when electron-updater is properly configured
}

app.whenReady().then(() => {
  createWindow()
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  // Kill Python process
  if (pythonProcess) {
    pythonProcess.kill()
  }
  
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC handlers
ipcMain.handle('get-version', () => {
  return app.getVersion()
})

ipcMain.handle('check-for-updates', () => {
  return { available: false }
})

ipcMain.handle('install-update', () => {
  return { success: false }
})

// License validation (communicate with Python backend)
ipcMain.handle('validate-license', async (event, licenseKey) => {
  try {
    const response = await fetch('http://localhost:8081/api/auth/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_key: licenseKey })
    })
    
    return await response.json()
  } catch (error) {
    return { valid: false, error: error.message }
  }
})
