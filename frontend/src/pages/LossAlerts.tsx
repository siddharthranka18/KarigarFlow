import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { formatWeight, formatPurity, formatDateTime } from '../utils/formatters';
import { AlertTriangle, ShieldCheck, Scale, Info } from 'lucide-react';

export const LossAlerts: React.FC = () => {
  const { data: alerts, isLoading } = useQuery({
    queryKey: ['loss-alerts'],
    queryFn: () => api.getTransactions({ loss_alerts_only: true }),
  });

  const { data: karigars } = useQuery({
    queryKey: ['karigars'],
    queryFn: () => api.getKarigars(),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-parchment-300 pb-4">
        <h2 className="text-xl font-serif font-bold text-charcoal-900 tracking-tight">
          Loss & Wastage Discrepancy Audits
        </h2>
        <p className="text-xs text-charcoal-600 mt-0.5">
          Automatic flags triggered whenever actual craft wastage exceeds allowed job tolerance by &gt; 0.100 grams.
        </p>
      </div>

      {/* Explanation Banner */}
      <div className="bg-white border border-parchment-300 rounded-sm p-4 shadow-subtle flex items-start gap-3">
        <Info className="w-5 h-5 text-brass-700 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-charcoal-700 space-y-1">
          <p className="font-semibold text-charcoal-900">Coimbatore Workshop Wastage Governance Rule:</p>
          <p>
            Gold issued for fabrication has a benchmark allowed wastage (typically 1.80% - 2.50% depending on ornamentation complexity). 
            When ornaments, scrap, and filings are returned, any negative variance exceeding <strong>100 milligrams (0.100 g)</strong> automatically triggers a Loss Alert for physical bench sweep and audit before settling the karigar slip.
          </p>
        </div>
      </div>

      {/* Loss Alerts Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-charcoal-900 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-status-danger" />
            Flagged Transactions ({alerts?.length || 0})
          </h3>
        </div>

        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Slip #</TableHeaderCell>
              <TableHeaderCell>Karigar</TableHeaderCell>
              <TableHeaderCell>Job Order / Item</TableHeaderCell>
              <TableHeaderCell align="right">Gross Issued</TableHeaderCell>
              <TableHeaderCell align="right">Allowed Wastage</TableHeaderCell>
              <TableHeaderCell align="right">Actual Wastage</TableHeaderCell>
              <TableHeaderCell align="right">Loss Variance</TableHeaderCell>
              <TableHeaderCell align="center">Scale Check</TableHeaderCell>
              <TableHeaderCell>Date Flagged</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell className="text-center py-6 text-charcoal-500" align="center">
                  Scanning ledger for wastage anomalies...
                </TableCell>
              </TableRow>
            ) : alerts && alerts.length > 0 ? (
              alerts.map((tx) => (
                <TableRow key={tx.id} isLossAlert={true}>
                  <TableCell>
                    <span className="font-mono text-xs font-bold text-status-danger">{tx.slip_number}</span>
                  </TableCell>
                  <TableCell className="text-xs font-semibold text-charcoal-900">
                    {karigars?.find((k) => k.id === tx.karigar_id)?.name || `Karigar #${tx.karigar_id}`}
                  </TableCell>
                  <TableCell className="text-xs text-charcoal-700">{tx.item_description}</TableCell>
                  <TableCell align="right" isNumeric className="font-semibold text-charcoal-900">
                    {formatWeight(tx.gross_weight)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="text-xs text-charcoal-600">
                    {formatPurity(tx.allowed_wastage_percent)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="font-semibold text-status-danger">
                    {formatWeight(tx.actual_wastage_weight)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="font-mono font-bold text-status-danger text-sm">
                    +{formatWeight(tx.wastage_variance_weight)}
                  </TableCell>
                  <TableCell align="center">
                    <Badge variant="brass" size="sm" icon={<Scale className="w-3 h-3" />}>
                      CONFIRMED
                    </Badge>
                  </TableCell>
                  <TableCell className="text-[11px] text-charcoal-500">
                    {formatDateTime(tx.created_at)}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell className="text-center py-8 text-charcoal-500" align="center">
                  <div className="flex flex-col items-center gap-2">
                    <ShieldCheck className="w-8 h-8 text-status-success" />
                    <span className="font-semibold text-charcoal-800">No Wastage Loss Discrepancies</span>
                    <span className="text-xs text-charcoal-500">
                      All settled slips are strictly within allowed workshop tolerances.
                    </span>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
