import React, { useState } from 'react';
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
import { UserPlus, Search, Phone, History, ShieldAlert } from 'lucide-react';
import { Karigar, GoldTransaction } from '../types';
import { CategoryAgreements } from '../components/CategoryAgreements';

export const Karigars: React.FC = () => {
  const queryClient = useQueryClient();
  const { isKarigar, isFinanceHead, isManager } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedKarigar, setSelectedKarigar] = useState<Karigar | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [agreementKarigar, setAgreementKarigar] = useState<Karigar | null>(null);

  // Form state for new karigar
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newSpec, setNewSpec] = useState('Chains & Bangles');
  const [newBenchmarkWastage, setNewBenchmarkWastage] = useState('2.00');
  const [newOpeningGross, setNewOpeningGross] = useState('0.000');
  const [newOpeningFine, setNewOpeningFine] = useState('0.000');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: karigars, isLoading, isError, refetch } = useQuery({
    queryKey: ['karigars'],
    queryFn: () => api.getKarigars(),
  });

  const { data: karigarTransactions, isLoading: isTxLoading } = useQuery({
    queryKey: ['karigar-transactions', selectedKarigar?.id],
    queryFn: () => api.getTransactions({ karigar_id: selectedKarigar?.id }),
    enabled: !!selectedKarigar && isHistoryModalOpen,
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createKarigar(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['karigars'] });
      setIsAddModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to create karigar');
    },
  });

  const resetForm = () => {
    setNewCode('');
    setNewName('');
    setNewPhone('');
    setNewSpec('Chains & Bangles');
    setNewBenchmarkWastage('2.00');
    setNewOpeningGross('0.000');
    setNewOpeningFine('0.000');
    setFormError(null);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    createMutation.mutate({
      karigar_code: newCode.trim().toUpperCase(),
      name: newName.trim(),
      phone: newPhone.trim(),
      specialization: newSpec,
      benchmark_wastage_percent: parseFloat(newBenchmarkWastage),
      opening_balance_gross: parseFloat(newOpeningGross),
      opening_balance_fine: parseFloat(newOpeningFine),
    });
  };

  const filteredKarigars = karigars?.filter((k) => {
    const term = searchTerm.toLowerCase();
    return (
      k.karigar_code.toLowerCase().includes(term) ||
      k.name.toLowerCase().includes(term) ||
      k.specialization.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-parchment-300 pb-4">
        <div>
          <h2 className="text-xl font-serif font-bold text-charcoal-900 tracking-tight">
            {isKarigar ? 'My Craftsman Gold Ledger' : 'Karigar Directory & Real-time Balance Ledger'}
          </h2>
          <p className="text-xs text-charcoal-600 mt-0.5">
            Real-time balance calculated directly from transaction slips (never hardcoded). Stored to 3 decimal places.
          </p>
        </div>

        {!isKarigar && (isFinanceHead || isManager) && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAddModalOpen(true)}
            icon={<UserPlus className="w-3.5 h-3.5" />}
          >
            Add New Karigar
          </Button>
        )}
      </div>

      {/* Search Bar */}
      {!isKarigar && (
        <div className="flex items-center gap-3">
          <div className="relative max-w-sm w-full">
            <Search className="w-4 h-4 text-charcoal-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by code (e.g. KG-CBE), name, or craft..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white border border-parchment-300 rounded-sm pl-9 pr-3 py-1.5 text-xs text-charcoal-900 focus:outline-none focus:border-brass-600 focus:ring-1 focus:ring-brass-500"
            />
          </div>
          <span className="text-xs font-mono text-charcoal-500">
            Showing {filteredKarigars?.length || 0} Karigars
          </span>
        </div>
      )}

      {isError && <div role="alert"><AlertBanner type="danger" message="Karigar records could not be loaded." /><Button onClick={() => refetch()}>Retry</Button></div>}
      {/* Karigars Ledger Table */}
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Karigar Code</TableHeaderCell>
            <TableHeaderCell>Master Craftsman</TableHeaderCell>
            <TableHeaderCell>Craft Specialization</TableHeaderCell>
            <TableHeaderCell align="right">Allowed Wastage %</TableHeaderCell>
            <TableHeaderCell align="right">Opening Gross</TableHeaderCell>
            <TableHeaderCell align="right">Current Gross</TableHeaderCell>
            <TableHeaderCell align="right">Current Fine (Au)</TableHeaderCell>
            <TableHeaderCell align="center">Loss Alerts</TableHeaderCell>
            <TableHeaderCell align="center">Actions</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell className="text-center py-6 text-charcoal-500" align="center">
                Calculating live karigar balances...
              </TableCell>
            </TableRow>
          ) : filteredKarigars && filteredKarigars.length > 0 ? (
            filteredKarigars.map((k) => (
              <TableRow key={k.id} isLossAlert={k.loss_alerts_count > 0}>
                <TableCell>
                  <span className="font-mono text-xs font-bold text-brass-800">{k.karigar_code}</span>
                </TableCell>
                <TableCell>
                  <div className="font-semibold text-charcoal-900">{k.name}</div>
                  {k.phone && (
                    <div className="text-[11px] text-charcoal-500 flex items-center gap-1 mt-0.5">
                      <Phone className="w-2.5 h-2.5" />
                      <span>{k.phone}</span>
                    </div>
                  )}
                </TableCell>
                <TableCell className="text-xs text-charcoal-700">{k.specialization}</TableCell>
                <TableCell align="right" isNumeric className="text-xs text-charcoal-600">
                  {Object.entries(k.wastage_by_category || { general: k.benchmark_wastage_percent }).map(([category, value]) => <div key={category} className="whitespace-nowrap capitalize">{category}: {formatPurity(value)}</div>)}
                  {isFinanceHead && <button className="underline text-brass-800 mt-2" onClick={() => setAgreementKarigar(k)}>Edit agreements</button>}
                </TableCell>
                <TableCell align="right" isNumeric className="text-xs text-charcoal-500">
                  {formatWeight(k.opening_balance_gross)}
                </TableCell>
                <TableCell align="right" isNumeric className="font-mono font-bold text-charcoal-900 text-sm">
                  {formatWeight(k.current_balance_gross)}
                </TableCell>
                <TableCell align="right" isNumeric className="font-mono font-bold text-brass-800 text-sm">
                  {formatWeight(k.current_balance_fine)}
                </TableCell>
                <TableCell align="center">
                  {k.loss_alerts_count > 0 ? (
                    <Badge variant="danger" size="sm" icon={<ShieldAlert className="w-3 h-3" />}>
                      {k.loss_alerts_count} ALERTS
                    </Badge>
                  ) : (
                    <Badge variant="default" size="sm">
                      {isFinanceHead ? 'No open review' : 'Recorded'}
                    </Badge>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedKarigar(k);
                      setIsHistoryModalOpen(true);
                    }}
                    icon={<History className="w-3 h-3" />}
                  >
                    View Slips
                  </Button>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell className="text-center py-6 text-charcoal-500" align="center">
                No matching karigars found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {/* Add New Karigar Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Register New Karigar"
        subtitle="Establish craftsman profile, opening gold balance, and benchmark wastage tolerance."
      >
        {formError && <AlertBanner type="danger" message={formError} />}

        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Karigar Code"
              required
              placeholder="e.g. KG-CBE-005"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
            />
            <Input
              label="Full Name"
              required
              placeholder="e.g. S. Arumugam"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Contact Phone"
              placeholder="+91 98421 ..."
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
            />
            <Input
              label="Specialization"
              placeholder="e.g. Temple Jewellery, Casting, Stone"
              value={newSpec}
              onChange={(e) => setNewSpec(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Allowed Wastage"
              type="number"
              step="0.01"
              unit="%"
              required
              value={newBenchmarkWastage}
              onChange={(e) => setNewBenchmarkWastage(e.target.value)}
            />
            <Input
              label="Opening Gross"
              type="number"
              step="0.001"
              unit="g"
              required
              value={newOpeningGross}
              onChange={(e) => setNewOpeningGross(e.target.value)}
            />
            <Input
              label="Opening Fine (Au)"
              type="number"
              step="0.001"
              unit="g"
              required
              value={newOpeningFine}
              onChange={(e) => setNewOpeningFine(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-parchment-200">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              isLoading={createMutation.isPending}
            >
              Confirm & Save Karigar
            </Button>
          </div>
        </form>
      </Modal>

      {agreementKarigar && <CategoryAgreements karigar={agreementKarigar} onClose={() => setAgreementKarigar(null)} />}

      {/* Karigar Transaction History Slips Modal */}
      <Modal
        isOpen={isHistoryModalOpen}
        onClose={() => setIsHistoryModalOpen(false)}
        title={`Slips History: ${selectedKarigar?.karigar_code} - ${selectedKarigar?.name}`}
        subtitle={`Live Balance: ${formatWeight(selectedKarigar?.current_balance_gross)} Gross | ${formatWeight(selectedKarigar?.current_balance_fine)} Pure Fine`}
        maxWidth="2xl"
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Slip #</TableHeaderCell>
              <TableHeaderCell>Type</TableHeaderCell>
              <TableHeaderCell>Item</TableHeaderCell>
              <TableHeaderCell align="right">Gross</TableHeaderCell>
              <TableHeaderCell align="right">Purity</TableHeaderCell>
              <TableHeaderCell align="right">Fine Gold</TableHeaderCell>
              <TableHeaderCell>Date</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isTxLoading ? (
              <TableRow>
                <TableCell className="text-center py-4 text-charcoal-500" align="center">
                  Loading slips...
                </TableCell>
              </TableRow>
            ) : karigarTransactions && karigarTransactions.length > 0 ? (
              karigarTransactions.map((tx: GoldTransaction) => (
                <TableRow key={tx.id} isLossAlert={tx.is_loss_alert}>
                  <TableCell>
                    <span className="font-mono text-xs font-semibold">{tx.slip_number}</span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={tx.transaction_type === 'ISSUE' ? 'brass' : 'success'} size="sm">
                      {tx.transaction_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-charcoal-700">{tx.item_description}</TableCell>
                  <TableCell align="right" isNumeric className="font-semibold text-charcoal-900">
                    {formatWeight(tx.gross_weight)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="text-brass-800">
                    {formatPurity(tx.purity_percent)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="font-semibold text-brass-900">
                    {formatWeight(tx.fine_weight)}
                  </TableCell>
                  <TableCell className="text-[11px] text-charcoal-500">
                    {formatDateTime(tx.created_at)}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell className="text-center py-4 text-charcoal-500" align="center">
                  No transaction slips recorded for this karigar yet.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Modal>
    </div>
  );
};

