import React, { useState, useEffect } from 'react'
import { Search, Receipt, ArrowUpRight, ArrowDownLeft, Filter, Download } from 'lucide-react'

interface TransactionsViewProps {
  initialData?: unknown[][]
}

export function TransactionsView({ initialData }: TransactionsViewProps): React.ReactElement {
  const [search, setSearch] = useState('')
  const [transactions, setTransactions] = useState<unknown[][]>(initialData || [])
  const [isLoading, setIsLoading] = useState(false)

  const fetchTransactions = async (query: string): Promise<void> => {
    if (query === '' && initialData && initialData.length > 0) {
      setTransactions(initialData)
      return
    }

    setIsLoading(true)
    try {
      const sql = `
        SELECT
          t.date,
          t.description,
          COALESCE(c.name, 'Uncategorized') as category,
          a.name as account,
          t.amount
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
      const result = window.api.dbQuery(sql)
      const resolved = await result as { rows?: unknown[][] }
      if (resolved.rows) {
        setTransactions(resolved.rows)
      }
    } catch (err) {
      console.error('Failed to search transactions:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTransactions(search)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  return (
    <div className="txn-container">
      <div className="txn-top-bar">
        <div className="txn-top-inner">
          <header className="txn-header">
            <h1 className="txn-title">Transactions</h1>
            <p className="txn-subtitle">Global history across all accounts</p>
          </header>

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
          </div>
        </div>
      </div>

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
                  const amount = Number(t[4])
                  const isOut = amount < 0
                  return (
                    <tr key={i}>
                      <td className="txn-td txn-td-date">{String(t[0])}</td>
                      <td className="txn-td txn-td-desc">{String(t[1])}</td>
                      <td className="txn-td">
                        <span className="txn-category-badge">{String(t[2])}</span>
                      </td>
                      <td className="txn-td" style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '12px' }}>{String(t[3])}</td>
                      <td className="txn-td txn-td-amount">
                        {isOut ? (
                          <span className="txn-amount-out">
                            <ArrowDownLeft size={13} strokeWidth={3} />
                            ${Math.abs(amount).toFixed(2)}
                          </span>
                        ) : (
                          <span className="txn-amount-in">
                            <ArrowUpRight size={13} strokeWidth={3} />
                            ${amount.toFixed(2)}
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
