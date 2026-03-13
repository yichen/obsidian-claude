import { describe, it, expect, vi } from 'vitest'
import { initConfig } from '../finance-core'

describe('initConfig validation', () => {
  it('throws error if Python binary does not exist', () => {
    const mockFs = {
      existsSync: vi.fn((path) => {
        if (path.includes('python')) return false
        return true
      }),
      readFileSync: vi.fn(),
      writeFileSync: vi.fn(),
      mkdirSync: vi.fn(),
      unlinkSync: vi.fn()
    }

    expect(() => initConfig({
      fs: mockFs as any,
      vaultPath: '/fake/vault',
      openai: {} as any
    })).toThrow(/Python binary not found/)
  })

  it('throws error if Finance script does not exist', () => {
    const mockFs = {
      existsSync: vi.fn((path) => {
        if (path.includes('finance_db.py')) return false
        return true
      }),
      readFileSync: vi.fn(),
      writeFileSync: vi.fn(),
      mkdirSync: vi.fn(),
      unlinkSync: vi.fn()
    }

    expect(() => initConfig({
      fs: mockFs as any,
      vaultPath: '/fake/vault',
      openai: {} as any
    })).toThrow(/Finance script not found/)
  })

  it('succeeds if all paths exist', () => {
    const mockFs = {
      existsSync: vi.fn(() => true),
      readFileSync: vi.fn(),
      writeFileSync: vi.fn(),
      mkdirSync: vi.fn(),
      unlinkSync: vi.fn()
    }

    expect(() => initConfig({
      fs: mockFs as any,
      vaultPath: '/fake/vault',
      openai: {} as any
    })).not.toThrow()
  })
})
