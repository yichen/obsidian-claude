import React, { useState, useEffect } from 'react'
import { Search, Receipt, ArrowUpRight, ArrowDownLeft, Filter, Download, Plus, ChevronDown } from 'lucide-react'

interface TransactionsViewProps {
  initialData?: unknown[][]
}

interface Category {
  id: number
  name: string
  parent_id: number | null
}

interface Account {
  id: number
  name: string
}

export function TransactionsView({ initialData }: TransactionsViewProps): React.ReactElement {
  const [search, setSearch] = useState('')
  const [transactions, setTransactions] = useState<unknown[][]>(initialData || [])
  const [isLoading, setIsLoading] = useState(false)

  // Pending
  const [pending, setPending] = useState<unknown[][]>([])
  const [pendingOpen, setPendingOpen] = useState(true)

  // Slide-out detail panel
  const [selectedTxn, setSelectedTxn] = useState<unknown[] | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCatId, setSelectedCatId] = useState<string>('')
  const [isSaving, setIsSaving] = useState(false)
  const [selectedIsPending, setSelectedIsPending] = useState(false)

  // Add transaction modal
  const [showAddModal, setShowAddModal] = useState(false)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [parseText, setParseText] = useState('')
  const [isParsing, setIsParsing] = useState(false)
  const [addForm, setAddForm] = useState({ date: '', description: '', amount: '', account_id: '', category_id: '', notes: '' })

  const fetchTransactions = async (query: string): Promise<void> => {
    setIsLoading(true)
    try {
      const sql = `
        SELECT
          t.id,
          t.date,
          t.description,
          COALESCE(c.name, 'Uncategorized') as category,
          a.name as account,
          t.amount,
          t.category_id,
          t.notes
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        JOIN accounts a ON a.id = t.account_id
        WHERE t.is_transfer = 0
          AND (t.description LIKE '%${query.replace(/'/g, "''")}%'
               OR c.name LIKE '%${query.replace(/'/g, "''")}%'
               OR a.name LIKE '%${query.replace(/'/g, "''")}%')
        ORDER BY t.date DESC
        LIMIT 100
      `
      const resolved = await window.api.dbQuery(sql) as { rows?: unknown[][] }
      if (resolved.rows) setTransactions(resolved.rows)
    } catch (err) {
      console.error('Failed to search transactions:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchPending = async (): Promise<void> => {
    try {
      const sql = `
        SELECT pt.id, pt.date, pt.description,
               COALESCE(c.name, 'Uncategorized') as category,
               COALESCE(a.name, '—') as account,
               pt.amount,
               pt.category_id,
               pt.notes
        FROM pending_transactions pt
        LEFT JOIN categories c ON c.id = pt.category_id
        LEFT JOIN accounts a ON a.id = pt.account_id
        WHERE pt.status = 'pending'
        ORDER BY pt.date DESC
      `
      const res = await window.api.dbQuery(sql) as { rows?: unknown[][] }
      if (res.rows) setPending(res.rows)
    } catch (_) {
      // Table may not exist yet — silently skip
    }
  }

  const fetchCategories = async (): Promise<void> => {
    try {
      const res = await window.api.dbQuery('SELECT MIN(id) as id, name, MIN(parent_id) as parent_id FROM categories GROUP BY LOWER(TRIM(name)) ORDER BY name') as { rows?: unknown[][] }
      if (res.rows) setCategories(res.rows.map(r => ({ id: Number(r[0]), name: String(r[1]), parent_id: r[2] != null ? Number(r[2]) : null })))
    } catch (_) { /* ignore */ }
  }

  const fetchAccounts = async (): Promise<void> => {
    try {
      const res = await window.api.dbQuery('SELECT id, display_name FROM accounts ORDER BY display_name') as { rows?: unknown[][] }
      if (res.rows) setAccounts(res.rows.map(r => ({ id: Number(r[0]), name: String(r[1]) })))
    } catch (_) { /* ignore */ }
  }

  useEffect(() => {
    const timer = setTimeout(() => { fetchTransactions(search) }, 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    fetchPending()
    fetchCategories()
    fetchAccounts()
  }, [])

  // ── Slide-out panel handlers ────────────────────────────────────────────

  const openDetail = (t: unknown[], isPending = false): void => {
    setSelectedTxn(t)
    setSelectedIsPending(isPending)
    setSelectedCatId(t[6] != null ? String(t[6]) : '')
  }

  const saveCategory = async (): Promise<void> => {
    if (!selectedTxn) return
    const txnId = Number(selectedTxn[0])
    const catSql = selectedCatId
      ? `UPDATE transactions SET category_id = ${Number(selectedCatId)} WHERE id = ${txnId}`
      : `UPDATE transactions SET category_id = NULL WHERE id = ${txnId}`
    setIsSaving(true)
    try {
      await window.api.dbExecute(catSql)
      await fetchTransactions(search)
      setSelectedTxn(null)
    } catch (err) {
      console.error('Failed to save category:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const savePendingCategory = async (): Promise<void> => {
    if (!selectedTxn) return
    const txnId = Number(selectedTxn[0])
    const catSql = selectedCatId
      ? `UPDATE pending_transactions SET category_id = ${Number(selectedCatId)} WHERE id = ${txnId}`
      : `UPDATE pending_transactions SET category_id = NULL WHERE id = ${txnId}`
    setIsSaving(true)
    try {
      await window.api.dbExecute(catSql)
      await fetchPending()
      setSelectedTxn(null)
    } catch (err) {
      console.error('Failed to save pending category:', err)
    } finally {
      setIsSaving(false)
    }
  }

  // ── Add modal handlers ──────────────────────────────────────────────────

  const parseReceipt = async (): Promise<void> => {
    if (!parseText.trim()) return
    setIsParsing(true)
    try {
      const parsed = await window.api.parseReceipt(parseText)
      setAddForm(prev => ({
        ...prev,
        date: parsed.date || prev.date,
        amount: parsed.amount != null ? String(Math.abs(parsed.amount)) : prev.amount,
        description: parsed.description || prev.description,
        notes: parsed.notes || prev.notes
      }))
    } catch (err) {
      console.error('Parse receipt failed:', err)
    } finally {
      setIsParsing(false)
    }
  }

  const savePending = async (): Promise<void> => {
    const { date, description, amount, account_id, category_id, notes } = addForm
    if (!date || !description || !amount) return
    const amtNum = -Math.abs(parseFloat(amount))
    const sql = `INSERT INTO pending_transactions (date, description, amount, account_id, category_id, notes, status) VALUES ('${date.replace(/'/g, "''")}', '${description.replace(/'/g, "''")}', ${amtNum}, ${account_id || 'NULL'}, ${category_id || 'NULL'}, '${notes.replace(/'/g, "''")}', 'pending')`
    try {
      await window.api.dbExecute(sql)
      await fetchPending()
      setShowAddModal(false)
      setAddForm({ date: '', description: '', amount: '', account_id: '', category_id: '', notes: '' })
      setParseText('')
    } catch (err) {
      console.error('Failed to save pending:', err)
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────

  const renderAmount = (amount: number): React.ReactElement => {
    const isOut = amount < 0
    return isOut ? (
      <span className="txn-amount-out">
        <ArrowDownLeft size={13} strokeWidth={3} />
        ${Math.abs(amount).toFixed(2)}
      </span>
    ) : (
      <span className="txn-amount-in">
        <ArrowUpRight size={13} strokeWidth={3} />
        ${amount.toFixed(2)}
      </span>
    )
  }

  return (
    <div className="txn-container">
      <header className="page-header txn-top-bar">
        <div className="page-header-left">
          <h1>Transactions</h1>
          <p className="subtitle">Global history across all accounts</p>
        </div>

        <div className="txn-controls">
          <div className="txn-search-wrap">
            <span className="txn-search-icon">
              <Search size={15} />
            </span>
            <input
              type="text"
              placeholder="Search description, category, or account..."
              className="txn-search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
          <button className="txn-icon-btn" aria-label="Filter">
            <Filter size={16} />
          </button>
          <button className="txn-icon-btn" aria-label="Download">
            <Download size={16} />
          </button>
          <button className="txn-add-btn" onClick={() => setShowAddModal(true)}>
            <Plus size={16} /> Add
          </button>
        </div>
      </header>

      <div className="txn-body">
        <div className="txn-table-wrap">
          <table className="txn-table">
            <thead>
              <tr>
                <th className="txn-th" style={{ width: '110px' }}>Date</th>
                <th className="txn-th">Description</th>
                <th className="txn-th">Category</th>
                <th className="txn-th">Account</th>
                <th className="txn-th txn-th-right" style={{ width: '130px' }}>Amount</th>
              </tr>
            </thead>
            <tbody>
              {/* Pending section */}
              {pending.length > 0 && (
                <>
                  <tr>
                    <td colSpan={5} style={{ padding: 0 }}>
                      <div className="txn-section-header" onClick={() => setPendingOpen(o => !o)}>
                        <span className={`txn-section-chevron${pendingOpen ? '' : ' collapsed'}`}>
                          <ChevronDown size={14} />
                        </span>
                        Pending ({pending.length})
                      </div>
                    </td>
                  </tr>
                  {pendingOpen && pending.map((t, i) => {
                    const amount = Number(t[5])
                    return (
                      <tr key={`p-${i}`} className="txn-row-pending txn-row-clickable" onClick={() => openDetail(t, true)}>
                        <td className="txn-td txn-td-date">{String(t[1])}</td>
                        <td className="txn-td txn-td-desc">
                          {String(t[2])}
                          <span className="txn-pending-badge">PENDING</span>
                        </td>
                        <td className="txn-td">
                          <span className="txn-category-badge">{String(t[3])}</span>
                        </td>
                        <td className="txn-td" style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '12px' }}>{String(t[4])}</td>
                        <td className="txn-td txn-td-amount">{renderAmount(amount)}</td>
                      </tr>
                    )
                  })}
                </>
              )}

              {/* Main transactions */}
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="txn-empty">
                    <div className="txn-empty-inner">
                      <div className="txn-spinner" />
                      <span>Searching transactions...</span>
                    </div>
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="txn-empty">
                    <div className="txn-empty-inner">
                      <Receipt size={28} />
                      <span>No transactions found{search ? ` matching "${search}"` : ''}</span>
                    </div>
                  </td>
                </tr>
              ) : (
                transactions.map((t, i) => {
                  // col indices: [0]=id, [1]=date, [2]=description, [3]=category, [4]=account, [5]=amount, [6]=category_id, [7]=notes
                  const amount = Number(t[5])
                  return (
                    <tr key={i} className="txn-row-clickable" onClick={() => openDetail(t)}>
                      <td className="txn-td txn-td-date">{String(t[1])}</td>
                      <td className="txn-td txn-td-desc">{String(t[2])}</td>
                      <td className="txn-td">
                        <span className="txn-category-badge">{String(t[3])}</span>
                      </td>
                      <td className="txn-td" style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '12px' }}>{String(t[4])}</td>
                      <td className="txn-td txn-td-amount">{renderAmount(amount)}</td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Slide-out detail panel ── */}
      {selectedTxn && (
        <>
          <div className="txn-detail-overlay" onClick={() => setSelectedTxn(null)} />
          <div className="txn-detail-panel">
            <div className="txn-detail-header">
              <h3>{selectedIsPending ? 'Pending Transaction' : 'Transaction Detail'}</h3>
              <button className="txn-detail-close" onClick={() => setSelectedTxn(null)}>✕</button>
            </div>
            <div className="txn-detail-body">
              <div className="txn-detail-field">
                <label>Amount</label>
                <div className={Number(selectedTxn[5]) < 0 ? 'txn-detail-amount-out' : 'txn-detail-amount-in'}>
                  {Number(selectedTxn[5]) < 0 ? '-' : '+'}${Math.abs(Number(selectedTxn[5])).toFixed(2)}
                </div>
              </div>
              <div className="txn-detail-field">
                <label>Description</label>
                <div className="txn-detail-value">{String(selectedTxn[2])}</div>
              </div>
              <div className="txn-detail-field">
                <label>Date</label>
                <div className="txn-detail-value">{String(selectedTxn[1])}</div>
              </div>
              <div className="txn-detail-field">
                <label>Account</label>
                <div className="txn-detail-value">{String(selectedTxn[4])}</div>
              </div>
              {selectedTxn[7] != null && String(selectedTxn[7]) && (
                <div className="txn-detail-field">
                  <label>Notes</label>
                  <div className="txn-detail-value">{String(selectedTxn[7])}</div>
                </div>
              )}
              <div className="txn-detail-field">
                <label>Category</label>
                <select value={selectedCatId} onChange={e => setSelectedCatId(e.target.value)}>
                  <option value="">Uncategorized</option>
                  {(() => {
                    const parentCats = categories.filter(c => c.parent_id == null)
                    const childrenOf = (parentId: number) => categories.filter(c => c.parent_id === parentId)
                    return parentCats.map(parent => {
                      const kids = childrenOf(parent.id)
                      return kids.length > 0 ? (
                        <optgroup key={parent.id} label={parent.name}>
                          {kids.map(child => <option key={child.id} value={String(child.id)}>{child.name}</option>)}
                        </optgroup>
                      ) : (
                        <option key={parent.id} value={String(parent.id)}>{parent.name}</option>
                      )
                    })
                  })()}
                </select>
              </div>
            </div>
            <div className="txn-detail-footer">
              <button className="txn-detail-cancel" onClick={() => setSelectedTxn(null)}>Cancel</button>
              <button className="txn-detail-save" onClick={selectedIsPending ? savePendingCategory : saveCategory} disabled={isSaving}>
                {isSaving ? 'Saving…' : 'Save'}
              </button>
            </div>
          </div>
        </>
      )}

      {/* ── Add Transaction modal ── */}
      {showAddModal && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) setShowAddModal(false) }}>
          <div className="modal-box">
            <div className="modal-header">
              <h3>Add Transaction</h3>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>✕</button>
            </div>

            <div className="modal-section">
              <textarea
                className="modal-parse-area"
                placeholder="Paste email receipt or transaction text here..."
                value={parseText}
                onChange={e => setParseText(e.target.value)}
              />
              <div className="modal-parse-row">
                <button className="modal-parse-btn" onClick={parseReceipt} disabled={isParsing || !parseText.trim()}>
                  {isParsing ? 'Parsing…' : 'Parse with AI ▶'}
                </button>
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-fields">
                <div className="modal-field">
                  <label>Date</label>
                  <input type="text" placeholder="YYYY-MM-DD" value={addForm.date} onChange={e => setAddForm(f => ({ ...f, date: e.target.value }))} />
                </div>
                <div className="modal-field">
                  <label>Amount ($)</label>
                  <input type="text" placeholder="0.00" value={addForm.amount} onChange={e => setAddForm(f => ({ ...f, amount: e.target.value }))} />
                </div>
                <div className="modal-field full">
                  <label>Description</label>
                  <input type="text" placeholder="Merchant name" value={addForm.description} onChange={e => setAddForm(f => ({ ...f, description: e.target.value }))} />
                </div>
                <div className="modal-field">
                  <label>Account</label>
                  <select value={addForm.account_id} onChange={e => setAddForm(f => ({ ...f, account_id: e.target.value }))}>
                    <option value="">— Select —</option>
                    {accounts.map(a => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
                  </select>
                </div>
                <div className="modal-field">
                  <label>Category</label>
                  <select value={addForm.category_id} onChange={e => setAddForm(f => ({ ...f, category_id: e.target.value }))}>
                    <option value="">Uncategorized</option>
                    {(() => {
                      const parentCats = categories.filter(c => c.parent_id == null)
                      const childrenOf = (parentId: number) => categories.filter(c => c.parent_id === parentId)
                      return parentCats.map(parent => {
                        const kids = childrenOf(parent.id)
                        return kids.length > 0 ? (
                          <optgroup key={parent.id} label={parent.name}>
                            {kids.map(child => <option key={child.id} value={String(child.id)}>{child.name}</option>)}
                          </optgroup>
                        ) : (
                          <option key={parent.id} value={String(parent.id)}>{parent.name}</option>
                        )
                      })
                    })()}
                  </select>
                </div>
                <div className="modal-field full">
                  <label>Notes</label>
                  <input type="text" placeholder="Optional notes" value={addForm.notes} onChange={e => setAddForm(f => ({ ...f, notes: e.target.value }))} />
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="modal-cancel" onClick={() => setShowAddModal(false)}>Cancel</button>
              <button className="modal-save" onClick={savePending} disabled={!addForm.date || !addForm.description || !addForm.amount}>
                Save as Pending
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
