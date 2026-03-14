import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { readdirSync } from 'fs'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { initConfig, makeDeps, handleChat, queryDB, runFinanceCommand, initCategoryContext, initFinanceCache, migratePendingYamlToSQLite, openrouterClient, VAULT_PATH, generateChart } from './finance-core'

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
  migratePendingYamlToSQLite(startupDeps).catch(e => console.warn('[startup] migratePendingYamlToSQLite failed:', e))
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

  ipcMain.handle('db:execute', async (_event, sql: string) => {
    try {
      const output = await runFinanceCommand('execute', [sql], makeDeps())
      const parsed = JSON.parse(output)
      return parsed
    } catch (err) {
      return { error: String(err) }
    }
  })

  ipcMain.handle('finance:command', async (_event, command: string) => {
    return runFinanceCommand(command, [], makeDeps())
  })

  ipcMain.handle('finance:generate-chart', async (_event, type: string, months: number) => {
    return generateChart(type, months, makeDeps())
  })

  ipcMain.handle('finance:recent-topics', async () => {
    try {
      const sessionDir = `${VAULT_PATH}/Finance/reports/debug/sessions`
      const files = readdirSync(sessionDir)
        .filter(f => f.endsWith('.json'))
        .sort()
        .slice(-5)
        .reverse()

      const topics: string[] = []
      for (const file of files) {
        try {
          const raw = require('fs').readFileSync(join(sessionDir, file), 'utf-8')
          const session = JSON.parse(raw)
          const rounds: any[] = session.rounds || []
          for (const round of rounds) {
            const messages: any[] = round?.request?.messages || []
            const userMsgs = messages.filter((m: any) => m.role === 'user')
            if (userMsgs.length > 0) {
              const last = userMsgs[userMsgs.length - 1]
              const text = typeof last.content === 'string' ? last.content : (last.content?.[0]?.text ?? '')
              const trimmed = text.trim().slice(0, 120)
              if (trimmed && !topics.includes(trimmed)) {
                topics.push(trimmed)
              }
            }
          }
        } catch (_) { /* skip malformed files */ }
        if (topics.length >= 3) break
      }
      return topics
    } catch (_) {
      return []
    }
  })

  ipcMain.handle('finance:parse-receipt', async (_event, text: string) => {
    try {
      const client = openrouterClient
      if (!client) return {}
      const response = await client.chat.completions.create({
        model: 'anthropic/claude-3-haiku',
        max_tokens: 256,
        messages: [
          {
            role: 'user',
            content: `Extract transaction details from this receipt text. Return JSON only, no explanation:\n{"date":"YYYY-MM-DD","amount":0.00,"description":"merchant name","notes":""}\n\nReceipt text:\n${text}`
          }
        ]
      })
      const content = response.choices[0]?.message?.content ?? ''
      const match = content.match(/\{[\s\S]*\}/)
      if (match) return JSON.parse(match[0])
      return {}
    } catch (err) {
      console.error('[parse-receipt] error:', err)
      return {}
    }
  })

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
