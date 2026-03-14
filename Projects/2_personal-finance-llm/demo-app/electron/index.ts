import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { initConfig, makeDeps, handleChat, queryDB, runFinanceCommand, initCategoryContext, initFinanceCache } from './finance-core'

// ── Electron app setup ─────────────────────────────────────────────────────

function createWindow(): void {
  const win = new BrowserWindow({
    width: 1100,
    height: 760,
    show: false,
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0f0f0f',
    webPreferences: {
      preload: join(__dirname, '../preload/preload.js'),
      sandbox: false
    }
  })

  win.on('ready-to-show', () => win.show())

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(async () => {
  initConfig()
  const startupDeps = makeDeps()
  initCategoryContext(startupDeps).catch(e => console.warn('[startup] initCategoryContext failed:', e))
  initFinanceCache(startupDeps).catch(e => console.warn('[startup] initFinanceCache failed:', e))
  electronApp.setAppUserModelId('com.finance.demo')
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  ipcMain.handle('chat:send', async (event, messages) => {
    try {
      return await handleChat(messages, event.sender, makeDeps())
    } catch (err: any) {
      const status = err?.status ?? err?.statusCode
      let message: string
      if (status === 401) {
        message = 'API key expired or invalid — please update your OpenRouter API key in .env and restart the app.'
      } else if (status === 403) {
        message = 'Access denied — your API key does not have permission for this model.'
      } else if (status === 429) {
        message = 'Rate limit exceeded — please wait a moment and try again.'
      } else if (status === 402) {
        message = 'Insufficient credits — please top up your OpenRouter account.'
      } else {
        message = `Error: ${String(err)}`
      }
      return { text: message }
    }
  })

  ipcMain.handle('db:query', async (_event, sql: string) => {
    return await queryDB(sql, makeDeps())
  })

  ipcMain.handle('finance:command', async (_event, command: string) => {
    return runFinanceCommand(command, [], makeDeps())
  })

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
