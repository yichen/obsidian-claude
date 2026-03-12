export interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  toolName?: string
  toolData?: unknown
  chartPath?: string
  chartData?: string  // base64 data URL
  isLoading?: boolean
}

export interface ToolResult {
  tool: string
  sql?: string
  command?: string
  result: unknown
}
