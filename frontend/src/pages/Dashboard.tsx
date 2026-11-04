import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { StatCard } from '../components/ui/StatCard';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { AlertBanner } from '../components/ui/AlertBanner';
import { Button } from '../components/ui/Button';
import { formatWeight, formatPurity, formatDateTime } from '../utils/formatters';
import { Coins, Vault, Users, AlertTriangle, ArrowUpRight, ArrowDownLeft, FilePlus } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { data: summary } = useQuery({
    queryKey: ['daily-summary'],
    queryFn: () => api.getDailySummary(),
    refetchInterval: 30000,
  });

  const { data: karigars, isLoading: isKarigarsLoading } = useQuery({
    queryKey: ['karigars'],
    queryFn: () => api.getKarigars(),
  });

  const { data: transactions, isLoading: isTransactionsLoading } = useQuery({
    queryKey: ['recent-transactions'],
    queryFn: () => api.getTransactions({ limit: 10 } as any),
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-parchment-300 pb-4">
        <div>
          <h2 className="text-xl font-serif font-bold text-charcoal-900 tracking-tight">
            Workshop Operations & Gold Position
          </h2>
          <p className="text-xs text-charcoal-600 mt-0.5">
            Real-time reconciliation for Coimbatore central workshop and 5 retail showrooms.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/slips">
            <Button variant="primary" size="sm" icon={<FilePlus className="w-3.5 h-3.5" />}>
              Issue / Receive Gold Slip
            </Button>
          </Link>
        </div>
      </div>

      {/* Loss Alert Warning if any alert exists */}
      {summary && summary.loss_alerts_count > 0 && (
        <AlertBanner
          type="danger"
          title="Gold Loss Alert Triggered"
          message={`${summary.loss_alerts_count} transaction(s) have exceeded the allowed workshop wastage tolerance threshold (0.100g). Immediate verification required.`}
          actionText="Review Loss Alerts"
          onAction={() => (window.location.href = '/loss-alerts')}
        />
      )}

      {/* Key Metric KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Workshop Fine Gold"
          value={formatWeight(summary?.total_workshop_gold_fine)}
          fineGoldValue={formatWeight(summary?.total_workshop_gold_fine)}
          subtitle="Vault + Outstanding in Karigar Hands"
          icon={<Coins className="w-5 h-5 text-brass-600" />}
        />

        <StatCard
          title="Central Vault Balance"
          value={formatWeight(summary?.vault_raw_gold_gross)}
          fineGoldValue={formatWeight(summary?.vault_raw_gold_fine)}
          subtitle="Bullion bars, casting grain & scrap"
          icon={<Vault className="w-5 h-5 text-brass-700" />}
        />

        <StatCard
          title="Outstanding with Karigars"
          value={formatWeight(summary?.karigar_outstanding_gross)}
          fineGoldValue={formatWeight(summary?.karigar_outstanding_fine)}
          badge={{ text: `${karigars?.length || 0} Craftsmen`, variant: 'brass' }}
          subtitle="Total work-in-progress on benches"
          icon={<Users className="w-5 h-5 text-charcoal-600" />}
        />

        <StatCard
          title="Wastage & Loss Alerts"
          value={formatWeight(summary?.total_wastage_today_gross)}
          isLossAlert={(summary?.loss_alerts_count || 0) > 0}
          badge={{
            text: `${summary?.loss_alerts_count || 0} Alerts`,
            variant: (summary?.loss_alerts_count || 0) > 0 ? 'danger' : 'success',
          }}
          subtitle="Today's reported workshop filing & scrap"
          icon={<AlertTriangle className="w-5 h-5" />}
        />
      </div>

      {/* Split Section: Active Karigars & Recent Slips */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Karigars Ledger Preview (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-charcoal-900 uppercase tracking-wider">
              Karigar Work-in-Progress Balances
            </h3>
            <Link to="/karigars" className="text-xs font-semibold text-brass-700 hover:underline">
              View All Karigars →
            </Link>
          </div>

          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Code</TableHeaderCell>
                <TableHeaderCell>Karigar Name</TableHeaderCell>
                <TableHeaderCell>Specialization</TableHeaderCell>
                <TableHeaderCell align="right">Gross Balance</TableHeaderCell>
                <TableHeaderCell align="right">Fine Balance</TableHeaderCell>
                <TableHeaderCell align="center">Status</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isKarigarsLoading ? (
                <TableRow>
                  <TableCell className="text-center py-6 text-charcoal-500" align="center">
                    Loading karigar ledger...
                  </TableCell>
                </TableRow>
              ) : karigars && karigars.length > 0 ? (
                karigars.slice(0, 5).map((k) => (
                  <TableRow key={k.id}>
                    <TableCell>
                      <span className="font-mono text-xs font-semibold text-brass-800">{k.karigar_code}</span>
                    </TableCell>
                    <TableCell className="font-medium text-charcoal-900">{k.name}</TableCell>
                    <TableCell className="text-xs text-charcoal-600">{k.specialization}</TableCell>
                    <TableCell align="right" isNumeric className="font-semibold text-charcoal-900">
                      {formatWeight(k.current_balance_gross)}
                    </TableCell>
                    <TableCell align="right" isNumeric className="text-brass-800 font-semibold">
                      {formatWeight(k.current_balance_fine)}
                    </TableCell>
                    <TableCell align="center">
                      <Badge variant={k.loss_alerts_count > 0 ? 'danger' : 'brass'} size="sm">
                        {k.loss_alerts_count > 0 ? `${k.loss_alerts_count} ALERT` : 'NORMAL'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell className="text-center py-4 text-charcoal-500" align="center">
                    No active karigars found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Recent Transaction Slips (1 Col) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-charcoal-900 uppercase tracking-wider">
              Recent Gold Slips
            </h3>
            <Link to="/slips" className="text-xs font-semibold text-brass-700 hover:underline">
              All Slips →
            </Link>
          </div>

          <div className="bg-white border border-parchment-300 rounded-sm p-3 divide-y divide-parchment-200 shadow-subtle">
            {isTransactionsLoading ? (
              <p className="text-xs text-charcoal-500 py-4 text-center">Loading slips...</p>
            ) : transactions && transactions.length > 0 ? (
              transactions.slice(0, 5).map((tx) => (
                <div key={tx.id} className="py-2.5 first:pt-0 last:pb-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1.5">
                      {tx.transaction_type === 'ISSUE' ? (
                        <ArrowUpRight className="w-3.5 h-3.5 text-brass-600" />
                      ) : (
                        <ArrowDownLeft className="w-3.5 h-3.5 text-status-success" />
                      )}
                      <span className="font-mono text-xs font-semibold text-charcoal-900">
                        {tx.slip_number}
                      </span>
                    </div>
                    <span className="font-mono text-xs font-bold text-charcoal-900 tabular-nums">
                      {formatWeight(tx.gross_weight)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-charcoal-600">
                    <span className="truncate max-w-[140px]">{tx.item_description}</span>
                    <span className="font-mono text-brass-800">{formatPurity(tx.purity_percent)}</span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-charcoal-500 mt-1">
                    <span>{formatDateTime(tx.created_at)}</span>
                    {tx.is_loss_alert && (
                      <Badge variant="danger" size="sm">
                        LOSS ALERT
                      </Badge>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-charcoal-500 py-4 text-center">No transactions recorded yet today.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
