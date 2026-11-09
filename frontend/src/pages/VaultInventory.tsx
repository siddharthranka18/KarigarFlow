import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { formatWeight, formatPurity, formatDateTime } from '../utils/formatters';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';

export const VaultInventory: React.FC = () => {
  const { data: inventory, isLoading, isError, refetch } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => api.getInventory(),
  });

  return (
    <div className="space-y-6">
      <div className="border-b border-parchment-300 pb-4">
        <h2 className="page-title">
          Opening Inventory Lots
        </h2>
        <p className="text-xs text-charcoal-600 mt-0.5">
          Baseline bullion, grain, scrap and refinery lots. Use Daily Stock Statement for current custody after ledger movements.
        </p>
      </div>

      {isError && <div role="alert"><AlertBanner type="danger" message="Opening inventory could not be loaded." /><Button size="sm" onClick={() => refetch()}>Retry</Button></div>}
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
            <TableHeaderCell>Last Updated</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell className="text-center py-6 text-charcoal-500" align="center">
                Loading vault inventory lots...
              </TableCell>
            </TableRow>
          ) : inventory && inventory.length > 0 ? (
            inventory.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <span className="font-mono text-xs font-semibold text-brass-800">{item.lot_code}</span>
                </TableCell>
                <TableCell className="text-xs font-semibold text-charcoal-900">{item.category}</TableCell>
                <TableCell className="text-xs text-charcoal-700">{item.description}</TableCell>
                <TableCell align="right" isNumeric className="font-semibold text-charcoal-900">
                  {formatWeight(item.gross_weight)}
                </TableCell>
                <TableCell align="right" isNumeric className="text-brass-800">
                  {formatPurity(item.purity_percent)}
                </TableCell>
                <TableCell align="right" isNumeric className="font-mono font-bold text-brass-900">
                  {formatWeight(item.fine_weight)}
                </TableCell>
                <TableCell className="text-xs text-charcoal-600">{item.location}</TableCell>
                <TableCell className="text-[11px] text-charcoal-500">{formatDateTime(item.updated_at)}</TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell className="text-center py-6 text-charcoal-500" align="center">
                No inventory lots found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
};
