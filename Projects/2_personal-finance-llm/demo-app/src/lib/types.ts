export interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  toolName?: string
  toolData?: unknown
  chartPath?: string
  chartData?: string  // base64 data URL (kept for pinned chart compat)
  charts?: Array<{ path: string; data: string; type?: string; months?: number }>
  isLoading?: boolean
}

export interface ToolResult {
  tool: string
  sql?: string
  command?: string
  result: unknown
}

export interface PinnedChart {
  id: string
  title: string
  chartData: string
  chartPath?: string
  timestamp: number
  chartType?: string
  chartMonths?: number
}
