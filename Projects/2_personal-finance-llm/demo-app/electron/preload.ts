import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  // Returns { text, chartPath? } — final response delivered via Promise return value
  sendChat: (
    messages: { role: string; content: string }[]
  ): Promise<{ text: string; chartPath?: string; chartData?: string }> => ipcRenderer.invoke('chat:send', messages),

  // Tool-call progress updates (informational, shown while waiting)
  onToolResult: (cb: (data: unknown) => void) => {
    const handler = (_e: Electron.IpcRendererEvent, data: unknown): void => cb(data)
    ipcRenderer.on('chat:tool-result', handler)
    return (): void => { ipcRenderer.removeListener('chat:tool-result', handler) }
  },

  // Streaming tokens — subscribe for live text updates during final response
  onStreamToken: (cb: (data: { token: string }) => void) => {
    const handler = (_e: Electron.IpcRendererEvent, data: { token: string }): void => cb(data)
    ipcRenderer.on('chat:stream-token', handler)
    return (): void => { ipcRenderer.removeListener('chat:stream-token', handler) }
  },

  dbQuery: (sql: string) => ipcRenderer.invoke('db:query', sql),
  financeCommand: (command: string) => ipcRenderer.invoke('finance:command', command),

  // Run a non-SELECT SQL statement (INSERT/UPDATE/DELETE)
  dbExecute: (sql: string) => ipcRenderer.invoke('db:execute', sql),

  // Returns up to 3 recent chat query strings from session logs
  recentTopics: (): Promise<string[]> => ipcRenderer.invoke('finance:recent-topics'),

  // Parse a receipt text with AI and return structured fields
  parseReceipt: (text: string): Promise<{ date?: string; amount?: number; description?: string; notes?: string }> =>
    ipcRenderer.invoke('finance:parse-receipt', text),

  // Generate a standard chart by type and return base64 data URL
  generateChart: (type: string, months: number): Promise<string | null> =>
    ipcRenderer.invoke('finance:generate-chart', type, months)
})
