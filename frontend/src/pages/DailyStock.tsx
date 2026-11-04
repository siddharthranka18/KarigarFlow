import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { StatCard } from '../components/ui/StatCard';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { formatWeight, formatPurity, formatDateOnly } from '../utils/formatters';
import { Coins, Vault, Users, Calendar, Printer } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const DailyStock: React.FC = () => {
  const { data: summary } = useQuery({
    queryKey: ['daily-summary'],
    queryFn: () => api.getDailySummary(),
  });

  const { data: inventory, isLoading: isInventoryLoading } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => api.getInventory(),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-parchment-300 pb-4">
        <div>
          <h2 className="text-xl font-serif font-bold text-charcoal-900 tracking-tight">
            Daily Gold Stock Statement & Vault Audit
          </h2>
          <p className="text-xs text-charcoal-600 mt-0.5">
            Full physical and fine-gold reconciliation across central strongroom, bench stocks, and recovery.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => window.print()}
            icon={<Printer className="w-3.5 h-3.5" />}
          >
            Print Stock Statement
          </Button>
        </div>
      </div>

      {/* Date and Summary Banner */}
      <div className="bg-white border border-parchment-300 rounded-sm p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-subtle">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xs bg-brass-100 text-brass-800 flex items-center justify-center">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-mono uppercase text-charcoal-500 font-semibold">Statement Date</div>
            <div className="text-sm font-serif font-bold text-charcoal-900">
              {formatDateOnly(summary?.date || new Date().toISOString())}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-[10px] font-mono uppercase text-charcoal-500">Total Workshop Fine Gold</div>
            <div className="text-base font-mono font-bold text-brass-900">
              {formatWeight(summary?.total_workshop_gold_fine)}
            </div>
          </div>
          <div className="text-right border-l border-parchment-200 pl-6">
            <div className="text-[10px] font-mono uppercase text-charcoal-500">Loss Alerts Logged</div>
            <div className={`text-base font-mono font-bold ${summary && summary.loss_alerts_count > 0 ? 'text-status-danger' : 'text-status-success'}`}>
              {summary?.loss_alerts_count || 0}
            </div>
          </div>
        </div>
      </div>

      {/* 3 Pillars of Gold Accounting */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="1. Central Strongroom Vault"
          value={formatWeight(summary?.vault_raw_gold_gross)}
          fineGoldValue={formatWeight(summary?.vault_raw_gold_fine)}
          subtitle="Physical bullion, casting grain, melting scrap"
          icon={<Vault className="w-5 h-5 text-brass-700" />}
        />

        <StatCard
          title="2. Outstanding In Karigar Hands"
          value={formatWeight(summary?.karigar_outstanding_gross)}
          fineGoldValue={formatWeight(summary?.karigar_outstanding_fine)}
          subtitle="Work-in-progress on craftsman workbenches"
          icon={<Users className="w-5 h-5 text-charcoal-600" />}
        />

        <StatCard
          title="3. Legitimate Craft Wastage Settled"
          value={formatWeight(summary?.total_legitimate_wastage_today_gross)}
          fineGoldValue={formatWeight(summary?.total_legitimate_wastage_today_fine)}
          subtitle="Auditable approved filing & craft burn loss"
          badge={{ text: 'Audited', variant: 'default' }}
          icon={<Coins className="w-5 h-5 text-brass-600" />}
        />
      </div>

      {/* Breakdown: Vault Lots */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-charcoal-900 uppercase tracking-wider">
          Central Vault Inventory Lots
        </h3>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Lot Code</TableHeaderCell>
              <TableHeaderCell>Category</TableHeaderCell>
              <TableHeaderCell>Description / Ingot Ref</TableHeaderCell>
              <TableHeaderCell align="right">Gross Weight</TableHeaderCell>
              <TableHeaderCell align="right">Purity %</TableHeaderCell>
              <TableHeaderCell align="right">Fine Gold (Au)</TableHeaderCell>
              <TableHeaderCell>Storage Location</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isInventoryLoading ? (
              <TableRow>
                <TableCell className="text-center py-4 text-charcoal-500" align="center">
                  Loading vault inventory lots...
                </TableCell>
              </TableRow>
            ) : inventory && inventory.length > 0 ? (
              inventory.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <span className="font-mono text-xs font-semibold text-brass-800">{item.lot_code}</span>
                  </TableCell>
                  <TableCell className="text-xs font-medium text-charcoal-900">{item.category}</TableCell>
                  <TableCell className="text-xs text-charcoal-700">{item.description}</TableCell>
                  <TableCell align="right" isNumeric className="font-semibold text-charcoal-900">
                    {formatWeight(item.gross_weight)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="text-brass-800">
                    {formatPurity(item.purity_percent)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="font-bold text-brass-900">
                    {formatWeight(item.fine_weight)}
                  </TableCell>
                  <TableCell className="text-xs text-charcoal-600">{item.location}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell className="text-center py-4 text-charcoal-500" align="center">
                  No inventory lots registered.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
