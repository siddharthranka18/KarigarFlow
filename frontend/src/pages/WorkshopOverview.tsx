import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';
import { formatWeight } from '../utils/formatters';

export function WorkshopOverview() {
  const { isFinanceHead } = useAuth();
  const slips = useQuery({ queryKey: ['recent-transactions'], queryFn: () => api.getTransactions({ limit: 8 }) });
  const reviews = useQuery({ queryKey: ['review-summary'], queryFn: () => api.getReviewSummary(), enabled: isFinanceHead });
  return <div className="space-y-6">
    <div><h2 className="text-2xl font-serif font-bold">Workshop desk</h2><p className="text-sm text-charcoal-600 mt-2">Record a weighed issue or return. Keep the job number on every slip.</p></div>
    <div className="grid sm:grid-cols-2 gap-4">
      <Link to="/slips" className="ledger-card p-5 hover:border-brass-500"><h3 className="font-semibold">Issue & receipt register →</h3><p className="text-xs mt-2 text-charcoal-600">Read a scale photo, confirm the measurement and record a slip.</p></Link>
      <Link to="/karigars" className="ledger-card p-5 hover:border-brass-500"><h3 className="font-semibold">Karigars & agreements →</h3><p className="text-xs mt-2 text-charcoal-600">Check individual running balances and agreed category wastage.</p></Link>
      {isFinanceHead && <Link to="/loss-alerts" className="ledger-card p-5 hover:border-brass-500"><h3 className="font-semibold">Finance reviews →</h3><p className="text-xs mt-2">{reviews.data ? `${reviews.data.open_count} open discrepancies · ${reviews.data.drift_count} rising-wastage reviews` : 'Open review desk'}</p></Link>}
    </div>
    <section className="ledger-card p-4 space-y-3"><h3 className="font-semibold">Recent slips</h3>
      {slips.isLoading && <p role="status">Loading slips…</p>}
      {slips.isError && <p role="alert">Slips unavailable. Check your connection and open the register to retry.</p>}
      {slips.data?.length === 0 && <p>No slips recorded yet.</p>}
      {slips.data?.map(tx => <div key={tx.id} className="flex justify-between gap-3 border-t border-parchment-200 pt-3 text-xs"><div><p className="font-mono">{tx.slip_number}</p><p className="text-charcoal-600 mt-1">{tx.job_number || 'Legacy slip'} · {tx.transaction_type.replace(/_/g, ' ')}</p></div><strong className="font-mono whitespace-nowrap">{formatWeight(tx.fine_weight)} fine</strong></div>)}
    </section>
  </div>;
}
