import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Printer } from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import { formatWeight, formatDateOnly } from '../utils/formatters';
import { StockRow } from '../types';

const columns: { key: keyof Omit<StockRow, 'location' | 'unit'>; label: string }[] = [
  { key: 'opening', label: 'Opening' }, { key: 'issues', label: 'Issues ±' },
  { key: 'receipts', label: 'Returns ±' }, { key: 'purchases', label: 'Purchases +' },
  { key: 'wastage', label: 'Wastage −' }, { key: 'loss_adjustments', label: 'Loss −' },
  { key: 'closing', label: 'Closing' },
];

function workshopToday() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date());
}

export function DailyStock() {
  const [date, setDate] = useState(workshopToday);
  const { data, isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ['stock-statement', date],
    queryFn: () => api.getStockStatement(date),
    enabled: Boolean(date),
  });
  const ready = Boolean(data) && !isError && !isFetching;

  function downloadCsv() {
    if (!data || !ready) return;
    // Export fixed labels and decimal strings, never free-text notes.
    const records = [
      ['Statement date', data.date, 'Timezone', data.timezone],
      ['Synthetic demo data; reconstructed from opening baseline and ledger'],
      ['Location', 'Weight basis (grams)', ...columns.map(c => c.label)],
      ...data.rows.map(row => [row.location, row.unit, ...columns.map(c => row[c.key])]),
    ];
    const csv = records.map(row => row.map(value => `"${value.replace(/"/g, '""')}"`).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `karigarflow-stock-${data.date}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return <div className="stock-statement space-y-6">
    <div className="flex flex-col sm:flex-row justify-between gap-4 border-b border-parchment-300 pb-4">
      <div>
        <h2 className="page-title">Daily Gold Stock Statement</h2>
        <p className="text-xs text-charcoal-600 mt-1">Opening custody + signed movements = closing custody. All weights in grams.</p>
      </div>
      <div className="statement-controls flex flex-wrap items-center gap-2">
        <Button size="sm" variant="secondary" disabled={!ready} onClick={downloadCsv} icon={<Download className="w-4 h-4" />}>Export CSV</Button>
        <Button size="sm" variant="secondary" disabled={!ready} onClick={() => window.print()} icon={<Printer className="w-4 h-4" />}>Print</Button>
      </div>
    </div>
    <div className="statement-controls flex flex-wrap items-end gap-3">
      <label className="text-xs font-semibold text-charcoal-700">Workshop date (India)
        <input type="date" value={date} max={workshopToday()} onChange={e => setDate(e.target.value)}
          className="block mt-1 rounded-sm border border-parchment-300 p-2 bg-white" />
      </label>
      <Button size="sm" variant="secondary" disabled={!date || isFetching} onClick={() => refetch()}>Refresh</Button>
    </div>
    {!date && <p role="status" className="text-sm text-charcoal-600">Choose a date to load the statement.</p>}
    {date && isLoading && <p role="status" className="text-sm text-charcoal-600">Loading opening balances and daily movements…</p>}
    {isError && <div role="alert"><AlertBanner type="danger" message="The stock statement could not be loaded. Check the date and connection, then refresh. Export and print are disabled." /></div>}
    {data && !isError && <>
      <div className="bg-white border border-parchment-300 p-4 space-y-2">
        <p className="font-bold text-charcoal-900">{formatDateOnly(data.date)} · {data.timezone}</p>
        <p className="text-xs text-charcoal-600">{data.transaction_count} ledger entries on this date, including generated settlements. Today's closing is as recorded so far.</p>
        {isFetching && <p role="status" className="text-xs text-brass-800">Refreshing statement…</p>}
        {data.transaction_count === 0 && <p className="text-xs text-charcoal-600">No movements recorded. Closing balances carry forward from opening.</p>}
      </div>
      <div className="statement-table overflow-x-auto border border-parchment-300 bg-white">
        <table className="w-full text-xs text-left">
          <caption className="sr-only">Daily custody reconciliation, signed gram movements</caption>
          <thead className="bg-parchment-100"><tr>
            <th scope="col" className="p-3">Custody / basis</th>
            {columns.map(c => <th scope="col" key={c.key} className="p-3 text-right whitespace-nowrap">{c.label}</th>)}
          </tr></thead>
          <tbody>{data.rows.map(row => <tr key={`${row.location}-${row.unit}`}
            className={`border-t border-parchment-200 ${row.location === 'Company total' ? 'bg-brass-50 font-semibold' : ''}`}>
            <th scope="row" className="p-3 whitespace-nowrap font-medium">{row.location}<span className="block text-[10px] text-charcoal-500 uppercase">{row.unit} gold</span></th>
            {columns.map(c => <td key={c.key} className={`p-3 text-right font-mono whitespace-nowrap ${c.key === 'closing' ? 'font-bold text-brass-900' : ''}`}>{formatWeight(row[c.key])}</td>)}
          </tr>)}</tbody>
        </table>
      </div>
      <div className="text-xs text-charcoal-600 space-y-2">
        <p>Issues transfer custody from vault to karigar; physical returns reverse it. Company totals cancel these internal movements. Approved wastage and loss adjustments reduce company stock.</p>
        <p>Synthetic demo data. Opening lots and karigar balances are assumed to precede ledger history. This is a reconstructed ledger statement, not a signed physical stock count.</p>
        <p>Refinery classification uses existing lot categories and locations. Refinery transfers are not implemented. Historical statements change if opening baselines are edited.</p>
      </div>
    </>}
  </div>;
}
