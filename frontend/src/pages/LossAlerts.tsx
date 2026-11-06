import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { AlertBanner } from '../components/ui/AlertBanner';
import { SlipInspection } from '../components/SlipInspection';
import { formatWeight, formatPurity, formatDateTime } from '../utils/formatters';
import { useAuth } from '../features/auth/AuthContext';
import { GoldTransaction } from '../types';

export function LossAlerts() {
  const { isFinanceHead, isKarigar } = useAuth();
  const cache = useQueryClient();
  const [status, setStatus] = useState<'open' | 'resolved'>('open');
  const [selected, setSelected] = useState<GoldTransaction | null>(null);
  const [inspected, setInspected] = useState<number | null>(null);
  const [notes, setNotes] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [approvedSlip, setApprovedSlip] = useState<string | null>(null);
  const alerts = useQuery({
    queryKey: ['loss-alerts', status], queryFn: () => api.getLossAlerts(status), enabled: !isKarigar,
  });
  const drift = useQuery({ queryKey: ['loss-drift'], queryFn: () => api.getDriftReviews(), enabled: isFinanceHead });
  const review = useMutation({
    mutationFn: ({ id, text }: { id: number; text: string }) => api.writeOffLoss(id, text),
    onSuccess: adjustment => {
      for (const key of ['loss-alerts', 'loss-drift', 'review-summary', 'recent-loss-alerts', 'transactions', 'recent-transactions', 'transaction-detail', 'daily-summary', 'daily-summary-badge', 'karigars', 'stock-statement']) {
        cache.invalidateQueries({ queryKey: [key] });
      }
      setSelected(null);
      setApprovedSlip(adjustment.slip_number);
    },
  });

  if (isKarigar) return <AlertBanner type="danger" message="Company loss reviews are available to workshop staff only." />;
  return <div className="space-y-5">
    <div className="border-b border-parchment-300 pb-4">
      <h2 className="text-xl font-serif font-bold text-charcoal-900">Loss & Wastage Reviews</h2>
      <p className="text-xs text-charcoal-600 mt-1">Investigate excess wastage before approving any accounting write-off.</p>
    </div>
    <AlertBanner type="info" message="Demo policy: Finance may write off the full flagged excess after investigation. This reduces karigar liability and company gold; it does not return gold to the vault. Recovered gold must be recorded as a physical receipt instead. Partial and cash settlements are not supported here." />
    {approvedSlip && <div role="status"><AlertBanner type="success" message={`Write-off saved as ${approvedSlip}. See Approved write-offs for the decision and investigation notes.`} /></div>}
    <section className="ledger-card p-4 space-y-3"><h3 className="font-semibold">Early review · rising reported wastage</h3><p className="text-xs text-charcoal-600">Compares the latest 3 receipts with the previous 3 in the same item category. A rise of at least 0.50 percentage points prompts a review. This provisional threshold is not an accusation or an automatic deduction.</p>
      {drift.isLoading && <p role="status">Checking history…</p>}
      {drift.isError && <p role="alert">History review unavailable. Refresh this page to retry.</p>}
      {drift.data?.length === 0 && <p className="text-xs text-charcoal-600">No rising-wastage reviews found. Karigars with fewer than 6 comparable receipts are not scored.</p>}
      {drift.data?.map(item => <div key={`${item.karigar_id}-${item.item_category}`} className="border-t border-parchment-200 pt-3 text-xs space-y-2"><strong>{item.karigar_name} · {item.item_category}</strong><p className="font-mono">{item.baseline_percent}% → {item.recent_percent}% (+{item.increase_points} percentage points)</p><p>{item.message}</p><div className="flex flex-wrap gap-2">{item.slip_ids.map((id, i) => <button key={id} className="underline text-brass-800" onClick={() => setInspected(id)}>Receipt {i+1}</button>)}</div></div>)}
    </section>
    <div className="flex flex-wrap gap-2">
      {(['open', 'resolved'] as const).map(value => <Button key={value} size="sm"
        variant={status === value ? 'primary' : 'secondary'} onClick={() => setStatus(value)}>
        {value === 'open' ? 'Open reviews' : 'Approved write-offs'}
      </Button>)}
      <Button variant="ghost" size="sm" disabled={alerts.isFetching} onClick={() => alerts.refetch()}>Refresh</Button>
    </div>
    {alerts.isLoading && <p role="status" className="text-sm text-charcoal-600">Loading loss reviews…</p>}
    {alerts.isError && <div role="alert"><AlertBanner type="danger" message="Loss reviews could not be loaded. Refresh to try again." /></div>}
    {!alerts.isError && alerts.data?.length === 0 && <div className="ledger-card p-6 text-sm text-charcoal-600">
      {status === 'open' ? 'No open loss reviews recorded.' : 'No approved write-offs recorded.'}
    </div>}
    {!alerts.isError && alerts.data?.map(({ alert: tx, resolution }) => <article key={tx.id} className="ledger-card p-4 space-y-3">
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div>
          <button className="text-sm font-mono font-bold text-brass-800 underline" onClick={() => setInspected(tx.id)}>{tx.slip_number}</button>
          <p className="text-xs text-charcoal-600 mt-1">{tx.karigar_name || `Karigar #${tx.karigar_id}`} · {formatDateTime(tx.created_at)}</p>
        </div>
        <span className="text-xs font-semibold text-charcoal-700">{resolution ? 'Write-off approved' : 'Awaiting investigation'}</span>
      </div>
      <p className="text-sm text-charcoal-800 break-words">{tx.item_description}</p>
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        {[
          ['Receipt gross', formatWeight(tx.gross_weight)],
          ['Reported wastage', formatWeight(tx.actual_wastage_weight)],
          ['Excess to review', formatWeight(tx.wastage_variance_weight)],
          ['Scale check', tx.scale_reading_confirmed ? 'Recorded as confirmed' : 'Unconfirmed'],
        ].map(([label, value]) => <div key={label}><dt className="text-charcoal-600">{label}</dt><dd className="font-mono font-semibold mt-1">{value}</dd></div>)}
      </dl>
      {resolution ? <div className="border-t border-parchment-200 pt-3 text-xs space-y-2">
        <button className="text-brass-800 underline font-mono" onClick={() => setInspected(resolution.id)}>Inspect adjustment {resolution.slip_number}</button>
        <p>{formatWeight(resolution.gross_weight)} gross / {formatWeight(resolution.fine_weight)} fine written off · {formatDateTime(resolution.created_at)}</p>
        <p className="whitespace-pre-wrap break-words">Investigation: {resolution.notes}</p>
      </div> : isFinanceHead ? <Button size="sm" variant="secondary" onClick={() => {
        review.reset(); setNotes(''); setConfirmed(false); setSelected(tx);
      }}>Review write-off</Button> : <p className="text-xs text-charcoal-500">Only Finance can approve a write-off.</p>}
    </article>)}
    {alerts.data && alerts.data.length >= 100 && <p className="text-xs text-charcoal-600">Showing the latest 100 reviews in this category.</p>}
    {selected && <Modal isOpen onClose={() => { if (!review.isPending) setSelected(null); }} title={`Review ${selected.slip_number}`} subtitle="Finance approval creates an auditable loss-adjustment slip.">
      <AlertBanner type="warning" message={`Write off ${formatWeight(selected.wastage_variance_weight)} excess at ${formatPurity(selected.purity_percent)} purity. Confirm that the bench investigation is complete and this amount has not been recovered or settled elsewhere.`} />
      <form className="space-y-4" onSubmit={e => {
        e.preventDefault();
        if (confirmed && !review.isPending) review.mutate({ id: selected.id, text: notes.trim() });
      }}>
        <label className="block text-xs font-semibold text-charcoal-700">Investigation findings (10–2000 characters)
          <textarea required minLength={10} maxLength={2000} value={notes} disabled={review.isPending}
            onChange={e => setNotes(e.target.value)} rows={4}
            className="block w-full mt-2 border border-parchment-300 p-2 text-sm rounded-sm" />
        </label>
        <label className="flex items-start gap-2 text-xs text-charcoal-700">
          <input type="checkbox" checked={confirmed} disabled={review.isPending} onChange={e => setConfirmed(e.target.checked)} required />
          I approve this exact excess as a company loss after investigation. No physical gold is returned by this action.
        </label>
        {review.isError && <div role="alert"><AlertBanner type="danger" message={review.error.message || 'Approval failed. Retry the unchanged review safely.'} /></div>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" disabled={review.isPending} onClick={() => setSelected(null)}>Cancel</Button>
          <Button type="submit" variant="danger" disabled={!confirmed || notes.trim().length < 10 || review.isPending} isLoading={review.isPending}>Approve write-off</Button>
        </div>
      </form>
    </Modal>}
    {inspected !== null && <SlipInspection id={inspected} onClose={() => setInspected(null)} onNavigate={setInspected} />}
  </div>;
}
