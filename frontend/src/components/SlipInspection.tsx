import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Modal } from './ui/Modal';
import { Button } from './ui/Button';
import { AlertBanner } from './ui/AlertBanner';
import { formatWeight, formatPurity, formatDateTime } from '../utils/formatters';

interface Props {
  id: number;
  onClose: () => void;
  onNavigate: (id: number) => void;
}

export function SlipInspection({ id, onClose, onNavigate }: Props) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['transaction-detail', id],
    queryFn: () => api.getTransaction(id),
    retry: false,
  });
  const tx = data?.transaction;
  const photoId = tx?.scale_image_url?.match(/^\/api\/scale-readings\/([a-f0-9-]+)$/)?.[1];
  const photo = useQuery({
    queryKey: ['scale-reading', photoId], queryFn: () => api.getScaleReading(photoId!), enabled: Boolean(photoId), retry: false,
  });
  return (
    <Modal isOpen onClose={onClose} title={tx?.slip_number || 'Slip inspection'}
      subtitle="Stored ledger values and directly linked accounting entries" maxWidth="2xl">
      {isLoading && <p role="status" className="text-sm text-charcoal-600">Loading slip details…</p>}
      {isError && <div className="space-y-3" role="alert">
        <AlertBanner type="danger" message="This slip could not be loaded. It may be unavailable or outside your access." />
        <Button onClick={() => refetch()} size="sm">Try again</Button>
      </div>}
      {tx && data && <>
        <div className="space-y-1">
          <p className="text-xs font-mono text-brass-800">{tx.transaction_type.replace(/_/g, ' ')}</p>
          <p className="font-semibold text-charcoal-900 break-words">{tx.item_description}</p>
          <p className="text-xs text-charcoal-600">{tx.karigar_name || 'No karigar assigned'} {tx.karigar_code && `· ${tx.karigar_code}`}</p>
          <p className="text-xs text-charcoal-600">Job: {tx.job_number || 'Legacy / opening record'} · Category: {tx.item_category || 'Unclassified'} {tx.huid && `· HUID: ${tx.huid}`}</p>
        </div>
        {tx.is_loss_alert && <AlertBanner type="danger" message="Excess wastage flagged for review. This flag is not evidence of an approved loss write-off." />}
        <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-parchment-100 border border-parchment-300 p-3 text-xs">
          {[
            ['Gross weight', formatWeight(tx.gross_weight)],
            ['Stone weight', formatWeight(tx.stone_weight)],
            ['Net weight', formatWeight(tx.net_weight)],
            ['Purity', formatPurity(tx.purity_percent)],
            ['Fine gold', formatWeight(tx.fine_weight)],
            ['Wastage allowance', formatPurity(tx.allowed_wastage_percent)],
            ['Reported wastage', formatWeight(tx.actual_wastage_weight)],
            ['Wastage variance', formatWeight(tx.wastage_variance_weight)],
            ['Scale confirmation', tx.scale_reading_confirmed ? 'Recorded as confirmed' : 'Unconfirmed'],
          ].map(([label, value]) => <div key={label}>
            <dt className="text-charcoal-600">{label}</dt>
            <dd className="font-mono font-semibold text-charcoal-900 mt-1 break-words">{value}</dd>
          </div>)}
        </dl>
        <div className="text-xs space-y-2 text-charcoal-700">
          <p>Recorded by: <strong>{data.recorded_by_name || 'Not recorded'}</strong></p>
          <p>Created: {formatDateTime(tx.created_at)}</p>
          <p className="whitespace-pre-wrap break-words">Notes: {tx.notes || 'No notes recorded.'}</p>
          <p>{tx.scale_image_url ? 'Scale evidence attached. Confirmation records a human review of the OCR proposal.' : 'No scale photo attached. Confirmation records a manual human check.'}</p>
          {photo.isLoading && photoId && <p role="status">Loading scale evidence…</p>}
          {photo.isError && <p role="alert">Scale photo could not be loaded or is outside your access.</p>}
          {photo.data && <img src={photo.data.image_url} alt="Recorded scale photo evidence" className="max-h-64 w-full object-contain border border-parchment-300" />}
        </div>
        <section className="border-t border-parchment-300 pt-3 space-y-2">
          <h4 className="text-sm font-semibold text-charcoal-900">Linked accounting entries</h4>
          <p className="text-xs text-charcoal-600">Direct slip links only. These entries do not represent a complete job history.</p>
          {data.parent && <Button size="sm" variant="secondary" onClick={() => onNavigate(data.parent!.id)}>
            Open parent {data.parent.slip_number}
          </Button>}
          {tx.related_slip_number && !data.parent && <p className="text-xs text-charcoal-600">Parent slip unavailable.</p>}
          {data.linked_entries.map(entry => <button key={entry.id} onClick={() => onNavigate(entry.id)}
            className="w-full text-left border border-parchment-300 p-3 hover:bg-parchment-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brass-600">
            <span className="block text-xs font-mono font-semibold text-brass-800">{entry.slip_number}</span>
            <span className="block text-xs mt-1">{entry.transaction_type.replace(/_/g, ' ')} · {formatWeight(entry.gross_weight)} gross · {formatWeight(entry.fine_weight)} fine</span>
          </button>)}
          {!data.parent && !tx.related_slip_number && data.linked_entries.length === 0 &&
            <p className="text-xs text-charcoal-500">No linked entries recorded.</p>}
        </section>
      </>}
    </Modal>
  );
}
