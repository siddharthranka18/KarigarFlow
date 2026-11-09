import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Plus } from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';
import { formatWeight } from '../utils/formatters';

export function WorkshopOverview() {
  const { isFinanceHead } = useAuth();
  const slips = useQuery({ queryKey: ['recent-transactions'], queryFn: () => api.getTransactions({ limit: 8 }) });
  const reviews = useQuery({ queryKey: ['review-summary'], queryFn: () => api.getReviewSummary(), enabled: isFinanceHead });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="page-title">{isFinanceHead ? 'Finance desk' : 'Workshop desk'}</h2>
          <p className="mt-2 text-sm text-charcoal-600">
            {isFinanceHead ? 'Review discrepancies and check recent workshop activity.' : 'Record a weighed issue or return and check recent slips.'}
          </p>
        </div>
        <Link to={isFinanceHead ? '/loss-alerts' : '/slips'} state={isFinanceHead ? undefined : { newSlip: true }}
          className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-brass-600 px-4 text-sm font-medium text-white hover:bg-brass-700">
          {isFinanceHead ? <><span>Open loss reviews</span><ArrowRight size={16} aria-hidden="true" /></> : <><Plus size={16} aria-hidden="true" /> New slip</>}
        </Link>
      </div>
      {isFinanceHead && (
        <section className="ledger-card p-5" aria-label="Review queue">
          <h3 className="font-semibold">Review queue</h3>
          {reviews.isLoading && <p className="mt-2 text-sm text-charcoal-600" role="status">Loading review counts…</p>}
          {reviews.isError && <p className="mt-2 text-sm text-charcoal-600" role="alert">Review counts are unavailable. Open loss reviews to retry.</p>}
          {reviews.data && <dl className="mt-4 grid grid-cols-2 gap-4">
            <div><dt className="text-sm text-charcoal-600">Open discrepancies</dt><dd className="mt-1 text-2xl font-semibold tabular-nums">{reviews.data.open_count}</dd></div>
            <div><dt className="text-sm text-charcoal-600">Rising wastage</dt><dd className="mt-1 text-2xl font-semibold tabular-nums">{reviews.data.drift_count}</dd></div>
          </dl>}
        </section>
      )}
      <section className="ledger-card">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-parchment-300 p-5">
          <h3 className="font-semibold">Recent slips</h3>
          <Link to="/slips" className="text-sm font-medium text-brass-700 hover:underline">View gold ledger</Link>
        </div>
        {slips.isLoading && <p className="p-5 text-sm text-charcoal-600" role="status">Loading slips…</p>}
        {slips.isError && <p className="p-5 text-sm text-charcoal-600" role="alert">Slips unavailable. Open the ledger to retry.</p>}
        {slips.data?.length === 0 && <p className="p-5 text-sm text-charcoal-600">No slips recorded yet.</p>}
        <ul className="divide-y divide-parchment-200">
          {slips.data?.map(tx => (
            <li key={tx.id} className="flex items-start justify-between gap-3 px-5 py-3.5 text-sm">
              <div className="min-w-0">
                <p className="break-words font-semibold">{tx.slip_number}</p>
                <p className="mt-1 break-words text-xs text-charcoal-600">{tx.job_number || 'Legacy slip'} · {tx.transaction_type.toLowerCase().replace(/_/g, ' ')}</p>
              </div>
              <strong className="shrink-0 font-medium tabular-nums">{formatWeight(tx.fine_weight)} fine</strong>
            </li>
          ))}
        </ul>
      </section>
      <Link to="/karigars" className="inline-flex items-center gap-2 text-sm font-medium text-brass-700 hover:underline">
        Karigar balances and agreements <ArrowRight size={16} aria-hidden="true" />
      </Link>
    </div>
  );
}
