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
  financeCommand: (command: string) => ipcRenderer.invoke('finance:command', command)
})
