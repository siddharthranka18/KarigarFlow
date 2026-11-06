import React, { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { AlertBanner } from '../components/ui/AlertBanner';
import { formatWeight, formatPurity, formatDateTime } from '../utils/formatters';
import { useAuth } from '../features/auth/AuthContext';
import { FilePlus, Camera, CheckCircle2, ArrowUpRight, ArrowDownLeft } from 'lucide-react';
import { TransactionType } from '../types';
import { SlipInspection } from '../components/SlipInspection';

export const Transactions: React.FC = () => {
  const queryClient = useQueryClient();
  const { isKarigar } = useAuth();
  const [filterType, setFilterType] = useState<string>('ALL');
  const [isSlipModalOpen, setIsSlipModalOpen] = useState(false);
  const [inspectedId, setInspectedId] = useState<number | null>(null);
  const submission = useRef<{ fingerprint: string; key: string } | null>(null);

  // Form states
  const [slipType, setSlipType] = useState<TransactionType>('ISSUE');
  const [karigarId, setKarigarId] = useState<string>('');
  const [itemDescription, setItemDescription] = useState('');
  const [grossWeight, setGrossWeight] = useState('');
  const [stoneWeight, setStoneWeight] = useState('0.000');
  const [purityPercent, setPurityPercent] = useState('91.60');
  const [allowedWastagePercent, setAllowedWastagePercent] = useState('2.00');
  const [actualWastageWeight, setActualWastageWeight] = useState('0.000');
  const [scaleReadingConfirmed, setScaleReadingConfirmed] = useState(true);
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: karigars } = useQuery({
    queryKey: ['karigars'],
    queryFn: () => api.getKarigars(),
  });

  const { data: transactions, isLoading, isError, refetch } = useQuery({
    queryKey: ['transactions', filterType],
    queryFn: () =>
      api.getTransactions(filterType === 'ALL' ? undefined : { transaction_type: filterType }),
  });

  // Live Fine Gold Preview calculation
  const grossNum = parseFloat(grossWeight) || 0;
  const stoneNum = parseFloat(stoneWeight) || 0;
  const purityNum = parseFloat(purityPercent) || 0;
  const netNum = Math.max(0, grossNum - stoneNum);
  const previewFineGold = ((netNum * purityNum) / 100).toFixed(3);

  // Live Wastage Preview & Alert Detection
  const allowedWastageNum = parseFloat(allowedWastagePercent) || 0;
  const actualWastageNum = parseFloat(actualWastageWeight) || 0;
  const allowedWeightCalc = (grossNum * allowedWastageNum) / 100;
  const wastageVarianceCalc = actualWastageNum - allowedWeightCalc;
  const isLossAlertPreview = slipType === 'RECEIPT_ORNAMENT' && wastageVarianceCalc > 0.100;

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createTransaction(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['karigars'] });
      queryClient.invalidateQueries({ queryKey: ['daily-summary'] });
      setIsSlipModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to record gold slip');
    },
  });

  const resetForm = () => {
    setSlipType('ISSUE');
    setKarigarId('');
    setItemDescription('');
    setGrossWeight('');
    setStoneWeight('0.000');
    setPurityPercent('91.60');
    setAllowedWastagePercent('2.00');
    setActualWastageWeight('0.000');
    setScaleReadingConfirmed(true);
    setNotes('');
    setFormError(null);
    submission.current = null;
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!karigarId) {
      setFormError('Please select a karigar for this slip.');
      return;
    }

    if (createMutation.isPending) return;

    const payload = {
      transaction_type: slipType,
      karigar_id: parseInt(karigarId, 10),
      item_description: itemDescription.trim(),
      gross_weight: parseFloat(grossWeight),
      stone_weight: parseFloat(stoneWeight),
      purity_percent: parseFloat(purityPercent),
      allowed_wastage_percent: parseFloat(allowedWastagePercent),
      actual_wastage_weight: parseFloat(actualWastageWeight),
      scale_reading_confirmed: scaleReadingConfirmed,
      notes: notes.trim(),
    };
    const fingerprint = JSON.stringify(payload);
    if (submission.current?.fingerprint !== fingerprint) {
      submission.current = { fingerprint, key: crypto.randomUUID() };
    }
    createMutation.mutate({ ...payload, idempotency_key: submission.current.key });
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-parchment-300 pb-4">
        <div>
          <h2 className="text-xl font-serif font-bold text-charcoal-900 tracking-tight">
            Gold Issue & Receipt Slips Register
          </h2>
          <p className="text-xs text-charcoal-600 mt-0.5">
            Every gram accounted: issues to karigars, returned ornaments, scrap recovery, and fine gold balances.
          </p>
        </div>

        {!isKarigar && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsSlipModalOpen(true)}
            icon={<FilePlus className="w-3.5 h-3.5" />}
          >
            Create New Slip
          </Button>
        )}
      </div>

      {/* Type Filters */}
      <div className="flex flex-wrap items-center gap-2 border-b border-parchment-200 pb-3">
        {['ALL', 'ISSUE', 'RECEIPT_ORNAMENT', 'RECEIPT_SCRAP', 'RECEIPT_DUST'].map((t) => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            className={`px-3 py-1.5 text-xs font-mono font-medium rounded-xs transition-colors ${
              filterType === t
                ? 'bg-brass-600 text-white font-semibold shadow-xs'
                : 'bg-white text-charcoal-700 hover:bg-parchment-100 border border-parchment-300'
            }`}
          >
            {t.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Transactions Table */}
      {isError && <div role="alert" className="space-y-2">
        <AlertBanner type="danger" message="The slip register could not be loaded." />
        <Button size="sm" onClick={() => refetch()}>Try again</Button>
      </div>}
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Slip #</TableHeaderCell>
            <TableHeaderCell>Type</TableHeaderCell>
            <TableHeaderCell>Karigar</TableHeaderCell>
            <TableHeaderCell>Item / Description</TableHeaderCell>
            <TableHeaderCell align="right">Gross Wt</TableHeaderCell>
            <TableHeaderCell align="right">Purity %</TableHeaderCell>
            <TableHeaderCell align="right">Net Fine (Au)</TableHeaderCell>
            <TableHeaderCell align="right">Wastage</TableHeaderCell>
            <TableHeaderCell align="center">Scale Confirmed</TableHeaderCell>
            <TableHeaderCell>Date & Time</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell className="text-center py-6 text-charcoal-500" align="center">
                Loading gold ledger slips...
              </TableCell>
            </TableRow>
          ) : transactions && transactions.length > 0 ? (
            transactions.map((tx) => (
              <TableRow key={tx.id} isLossAlert={tx.is_loss_alert}>
                <TableCell>
                  <button onClick={() => setInspectedId(tx.id)} aria-label={`Inspect slip ${tx.slip_number}`}
                    className="font-mono text-xs font-semibold text-brass-800 underline underline-offset-4 hover:text-brass-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brass-600">{tx.slip_number}</button>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1.5">
                    {tx.transaction_type === 'ISSUE' ? (
                      <ArrowUpRight className="w-3.5 h-3.5 text-brass-700" />
                    ) : (
                      <ArrowDownLeft className="w-3.5 h-3.5 text-status-success" />
                    )}
                    <Badge variant={tx.transaction_type === 'ISSUE' ? 'brass' : 'success'} size="sm">
                      {tx.transaction_type.replace('_', ' ')}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell className="text-xs font-medium text-charcoal-800">
                  {karigars?.find((k) => k.id === tx.karigar_id)?.name || `Karigar #${tx.karigar_id}`}
                </TableCell>
                <TableCell className="text-xs text-charcoal-700">{tx.item_description}</TableCell>
                <TableCell align="right" isNumeric className="font-semibold text-charcoal-900">
                  {formatWeight(tx.gross_weight)}
                </TableCell>
                <TableCell align="right" isNumeric className="text-brass-800">
                  {formatPurity(tx.purity_percent)}
                </TableCell>
                <TableCell align="right" isNumeric className="font-bold text-brass-900">
                  {formatWeight(tx.fine_weight)}
                </TableCell>
                <TableCell align="right" isNumeric className="text-xs">
                  {parseFloat(tx.actual_wastage_weight || '0') > 0 ? (
                    <div>
                      <span className={tx.is_loss_alert ? 'text-status-danger font-bold' : 'text-charcoal-700'}>
                        {formatWeight(tx.actual_wastage_weight)}
                      </span>
                      {tx.is_loss_alert && (
                        <div className="text-[10px] text-status-danger font-mono font-semibold uppercase">
                          Exceeds tol.
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-charcoal-400">-</span>
                  )}
                </TableCell>
                <TableCell align="center">
                  {tx.scale_reading_confirmed ? (
                    <span className="inline-flex items-center text-status-success text-xs font-mono gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Confirmed
                    </span>
                  ) : (
                    <span className="text-status-warning text-xs font-mono">Unverified</span>
                  )}
                </TableCell>
                <TableCell className="text-[11px] text-charcoal-500">
                  {formatDateTime(tx.created_at)}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell className="text-center py-6 text-charcoal-500" align="center">
                {isError ? 'Slip register unavailable.' : 'No slips match the selected filter.'}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {inspectedId !== null && <SlipInspection id={inspectedId} onClose={() => setInspectedId(null)} onNavigate={setInspectedId} />}

      {/* Create New Gold Slip Modal */}
      <Modal
        isOpen={isSlipModalOpen}
        onClose={() => setIsSlipModalOpen(false)}
        title="Record Gold Issue / Receipt Slip"
        subtitle="Precision workshop slip generation. Automatic fine-gold & wastage tolerance auditing."
        maxWidth="xl"
      >
        {formError && <AlertBanner type="danger" message={formError} />}

        {isLossAlertPreview && (
          <AlertBanner
            type="danger"
            title="Wastage Loss Alert Warning"
            message={`Actual wastage (${actualWastageNum.toFixed(3)}g) exceeds allowed tolerance (${allowedWeightCalc.toFixed(3)}g) by ${(wastageVarianceCalc).toFixed(3)}g (> 0.100g threshold). This slip will trigger an audit alert.`}
          />
        )}

        <form onSubmit={handleFormSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-charcoal-700 uppercase tracking-wider mb-1.5">
                Slip Type *
              </label>
              <select
                value={slipType}
                onChange={(e) => setSlipType(e.target.value as TransactionType)}
                className="w-full bg-white border border-parchment-300 text-xs text-charcoal-900 rounded-sm px-3 py-2 focus:outline-none focus:border-brass-600"
              >
                <option value="ISSUE">ISSUE (Raw/Grain Gold to Karigar)</option>
                <option value="RECEIPT_ORNAMENT">RECEIPT (Finished Ornaments)</option>
                <option value="RECEIPT_SCRAP">RECEIPT (Melting Scrap / Cuttings)</option>
                <option value="RECEIPT_DUST">RECEIPT (Polishing / Filing Dust)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-charcoal-700 uppercase tracking-wider mb-1.5">
                Select Karigar *
              </label>
              <select
                required
                value={karigarId}
                onChange={(e) => {
                  setKarigarId(e.target.value);
                  const selected = karigars?.find((k) => k.id.toString() === e.target.value);
                  if (selected) {
                    setAllowedWastagePercent(selected.benchmark_wastage_percent.toString());
                  }
                }}
                className="w-full bg-white border border-parchment-300 text-xs text-charcoal-900 rounded-sm px-3 py-2 focus:outline-none focus:border-brass-600"
              >
                <option value="">-- Choose Craftsman --</option>
                {karigars?.map((k) => (
                  <option key={k.id} value={k.id}>
                    {k.karigar_code} - {k.name} ({formatWeight(k.current_balance_gross)} held)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Input
            label="Item Description / Job Order"
            required
            placeholder="e.g. 22K Coimbatore Traditional Casting Bangles - Batch #84"
            value={itemDescription}
            onChange={(e) => setItemDescription(e.target.value)}
          />

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Gross Weight"
              type="number"
              step="0.001"
              unit="g"
              required
              placeholder="0.000"
              value={grossWeight}
              onChange={(e) => setGrossWeight(e.target.value)}
            />

            <Input
              label="Stone / Dust Wt"
              type="number"
              step="0.001"
              unit="g"
              placeholder="0.000"
              value={stoneWeight}
              onChange={(e) => setStoneWeight(e.target.value)}
            />

            <Input
              label="Gold Purity %"
              type="number"
              step="0.01"
              unit="%"
              required
              placeholder="91.60"
              value={purityPercent}
              onChange={(e) => setPurityPercent(e.target.value)}
            />
          </div>

          {/* Receipt specific wastage calculation fields */}
          {slipType === 'RECEIPT_ORNAMENT' && (
            <div className="p-3 bg-parchment-100 border border-parchment-300 rounded-sm space-y-3">
              <div className="text-xs font-semibold text-charcoal-800 uppercase tracking-wider">
                Wastage & Loss Verification
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Allowed Wastage %"
                  type="number"
                  step="0.01"
                  unit="%"
                  value={allowedWastagePercent}
                  onChange={(e) => setAllowedWastagePercent(e.target.value)}
                  helperText={`Allowed: ${allowedWeightCalc.toFixed(3)} g`}
                />

                <Input
                  label="Actual Wastage Reported"
                  type="number"
                  step="0.001"
                  unit="g"
                  value={actualWastageWeight}
                  onChange={(e) => setActualWastageWeight(e.target.value)}
                  helperText={`Variance: ${wastageVarianceCalc.toFixed(3)} g`}
                />
              </div>
            </div>
          )}

          {/* Live Calculated Fine Gold Summary Box */}
          <div className="p-3 bg-brass-50/60 border border-brass-200 rounded-sm flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-brass-800 font-semibold">
                Pure Fine Gold Calculation (Backend Verified)
              </div>
              <div className="text-xs text-charcoal-600 mt-0.5">
                Formula: ({grossNum.toFixed(3)}g - {stoneNum.toFixed(3)}g) × {purityNum.toFixed(2)}% ÷ 100
              </div>
            </div>
            <div className="text-right">
              <span className="text-xl font-mono font-bold text-brass-900 tabular-nums">
                {previewFineGold} g
              </span>
              <div className="text-[10px] text-brass-700 font-medium">Fine Gold Equivalent</div>
            </div>
          </div>

          {/* AI-Assisted Scale Reading Confirmation */}
          <div className="p-3 bg-white border border-parchment-300 rounded-sm flex items-start gap-3">
            <input
              type="checkbox"
              id="scaleConfirm"
              checked={scaleReadingConfirmed}
              onChange={(e) => setScaleReadingConfirmed(e.target.checked)}
              className="mt-0.5 rounded-xs border-parchment-300 text-brass-600 focus:ring-brass-500"
            />
            <label htmlFor="scaleConfirm" className="text-xs text-charcoal-800 cursor-pointer">
              <span className="font-semibold block flex items-center gap-1.5">
                <Camera className="w-3.5 h-3.5 text-brass-700" />
                Human Confirmation of Scale Reading
              </span>
              <span>
                Verified on calibrated Sartorius precision workshop scale (3 decimals). Human confirmation required by ERP compliance rule.
              </span>
            </label>
          </div>

          <Input
            label="Internal Notes / Slag Remarks"
            placeholder="Optional verification remarks or showroom order reference..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-parchment-200">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsSlipModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              isLoading={createMutation.isPending}
            >
              Sign & Record Slip
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
