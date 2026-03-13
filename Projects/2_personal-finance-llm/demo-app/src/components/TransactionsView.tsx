import React, { useState, useEffect } from 'react'
import { Search, Receipt, ArrowUpRight, ArrowDownLeft, Filter, Download } from 'lucide-react'

interface TransactionsViewProps {
  initialData?: any[]
}

export function TransactionsView({ initialData }: TransactionsViewProps): React.ReactElement {
  const [search, setSearch] = useState('')
  const [transactions, setTransactions] = useState<any[]>(initialData || [])
  const [isLoading, setIsLoading] = useState(false)

  const fetchTransactions = async (query: string) => {
    if (query === '' && initialData) {
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
          AND (t.description LIKE '%${query}%' 
               OR category LIKE '%${query}%'
               OR account LIKE '%${query}%')
        ORDER BY t.date DESC
        LIMIT 100
      `
      const result = await window.api.dbQuery(sql) as any
      if (result.rows) {
        setTransactions(result.rows)
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
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-50/50">
      <div className="p-8 pb-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <header>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Transactions</h1>
            <p className="text-sm text-gray-500 font-medium">Global history across all accounts</p>
          </header>
          
          <div className="flex items-center gap-2">
            <div className="relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={16} />
              <input 
                type="text" 
                placeholder="Search description, category, or account..." 
                className="w-full md:w-[400px] pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all shadow-sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                autoFocus
              />
            </div>
            <button className="p-2.5 bg-white border border-gray-200 rounded-lg text-gray-500 hover:bg-gray-50 transition-colors shadow-sm">
              <Filter size={18} />
            </button>
            <button className="p-2.5 bg-white border border-gray-200 rounded-lg text-gray-500 hover:bg-gray-50 transition-colors shadow-sm">
              <Download size={18} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-8 pb-8">
        <div className="max-w-6xl mx-auto bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="px-6 py-4 bg-gray-50/50 text-left text-xs font-bold text-gray-400 uppercase tracking-widest w-[120px]">Date</th>
                <th className="px-6 py-4 bg-gray-50/50 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Description</th>
                <th className="px-6 py-4 bg-gray-50/50 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Category</th>
                <th className="px-6 py-4 bg-gray-50/50 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Account</th>
                <th className="px-6 py-4 bg-gray-50/50 text-right text-xs font-bold text-gray-400 uppercase tracking-widest w-[140px]">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-400 italic">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                      Searching transactions...
                    </div>
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
                    <div className="flex flex-col items-center gap-3">
                      <Receipt size={32} className="text-gray-200" />
                      No transactions found matching "{search}"
                    </div>
                  </td>
                </tr>
              ) : (
                transactions.map((t, i) => (
                  <tr key={i} className="hover:bg-gray-50/50 transition-colors group">
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500 font-medium tabular-nums font-mono text-[13px]">{t[0]}</td>
                    <td className="px-6 py-4 font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">{t[1]}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-100 text-gray-600 border border-gray-200">
                        {t[2]}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-500 font-medium italic">{t[3]}</td>
                    <td className={`px-6 py-4 text-right font-bold tabular-nums font-mono text-[15px]`}>
                      <div className="flex items-center justify-end gap-1.5">
                        {t[4] < 0 ? (
                          <span className="text-rose-600 flex items-center gap-1">
                            <ArrowDownLeft size={14} strokeWidth={3} />
                            ${Math.abs(t[4]).toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-emerald-600 flex items-center gap-1">
                            <ArrowUpRight size={14} strokeWidth={3} />
                            ${t[4].toFixed(2)}
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
