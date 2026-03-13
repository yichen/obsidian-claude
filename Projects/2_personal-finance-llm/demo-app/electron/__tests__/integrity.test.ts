import { describe, it, expect } from 'vitest'
import { SYSTEM_PROMPT, TOOLS } from '../finance-core'

describe('Code Integrity & Constants', () => {
  it('SYSTEM_PROMPT is loaded correctly and not truncated', () => {
    expect(typeof SYSTEM_PROMPT).toBe('string')
    expect(SYSTEM_PROMPT.length).toBeGreaterThan(1000)
    
    // Ensure key sections exist (proves the string wasn't terminated early by a stray backtick)
    expect(SYSTEM_PROMPT).toContain('HEADLESS ANALYST MODE')
    expect(SYSTEM_PROMPT).toContain('SQL LIMITS')
    expect(SYSTEM_PROMPT).toContain('CHARTS')
    
    // The specific issue we had: nested backticks in the CHARTS section
    // If it was truncated, this last section would be missing or broken
    expect(SYSTEM_PROMPT).toContain('pandas')
    expect(SYSTEM_PROMPT).toContain('numpy')
  })

  it('TOOLS array is valid and contains all required tools', () => {
    expect(Array.isArray(TOOLS)).toBe(true)
    const toolNames = TOOLS.map(t => t.function.name)
    expect(toolNames).toContain('execute_batch_sql')
    expect(toolNames).toContain('generate_standard_chart')
    expect(toolNames).toContain('execute_sql')
    expect(toolNames).toContain('generate_chart')
  })
})
