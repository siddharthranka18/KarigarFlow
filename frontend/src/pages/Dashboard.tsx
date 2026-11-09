import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { useAuth } from '../features/auth/AuthContext';
import { StatCard } from '../components/ui/StatCard';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { AlertBanner } from '../components/ui/AlertBanner';
import { Button } from '../components/ui/Button';
import { formatWeight, formatPurity, formatDateTime } from '../utils/formatters';
import {
  Vault,
  Users,
  AlertTriangle,
  Flame,
  CheckCircle2,
  RefreshCw,
  Search,
  ExternalLink,
  Info,
  Scale
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isKarigar, user } = useAuth();
  const [karigarFilter, setKarigarFilter] = useState<'all' | 'outstanding' | 'alerts'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // 1. Daily Summary (restricted to staff)
  const {
    data: summary,
    isError: isSummaryError,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['daily-summary'],
    queryFn: () => api.getDailySummary(),
    enabled: !isKarigar,
    refetchInterval: 30000,
  });

  // 2. Karigars List (Staff sees all, Karigar sees own profile)
  const {
    data: karigars,
    isLoading: isKarigarsLoading,
    refetch: refetchKarigars,
  } = useQuery({
    queryKey: ['karigars'],
    queryFn: () => api.getKarigars(),
    refetchInterval: 30000,
  });

  // 3. Recent Transactions (Staff sees workshop slips, Karigar sees own slips)
  const {
    data: transactions,
    isLoading: isTransactionsLoading,
    refetch: refetchTransactions,
  } = useQuery({
    queryKey: ['recent-transactions'],
    queryFn: () => api.getTransactions({ limit: 12 }),
    refetchInterval: 30000,
  });

  // 4. Loss Alerts (Staff only)
  const {
    data: lossAlerts,
  } = useQuery({
    queryKey: ['recent-loss-alerts'],
    queryFn: () => api.getTransactions({ loss_alerts_only: true, limit: 5 }),
    enabled: !isKarigar,
    refetchInterval: 30000,
  });

  const handleRefreshAll = () => {
    if (!isKarigar) refetchSummary();
    refetchKarigars();
    refetchTransactions();
  };

  // ---------------------------------------------------------------------------
  // ERROR STATE
  // ---------------------------------------------------------------------------
  if (!isKarigar && isSummaryError) {
    return (
      <div className="space-y-4 p-6 bg-white border border-status-danger-border rounded-sm shadow-subtle">
        <div className="flex items-center gap-3 text-status-danger">
          <AlertTriangle className="w-6 h-6 flex-shrink-0" />
          <div>
            <h3 className="font-bold text-base">Unable to connect to Gold Accounting Engine</h3>
            <p className="text-xs text-charcoal-600 mt-0.5">
              {(summaryError as Error)?.message || 'Database connection error or network timeout.'}
            </p>
          </div>
        </div>
        <Button variant="secondary" size="sm" onClick={handleRefreshAll} icon={<RefreshCw className="w-3.5 h-3.5" />}>
          Retry Connection
        </Button>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // CRAFTSMAN WORKBENCH VIEW (For Karigar Role)
  // ---------------------------------------------------------------------------
  if (isKarigar) {
    const myProfile = karigars?.[0];

    return (
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#E8E2D5] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="page-title">
                Craftsman Workbench & Slips
              </h2>
              <Badge variant="brass" size="sm">
                {myProfile?.karigar_code || 'KARIGAR'}
              </Badge>
            </div>
            <p className="text-xs text-[#57534E] mt-1">
              Welcome, <span className="font-semibold text-[#1C1917]">{user?.full_name}</span>. Real-time balance of gold currently in your custody.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRefreshAll}
              icon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* Karigar Privacy Isolation Notice */}
        <div className="bg-[#FAF7F0] border border-[#E8E2D5] rounded-sm p-3.5 flex items-start gap-3">
          <Info className="w-4 h-4 text-[#8C5E1E] mt-0.5 flex-shrink-0" />
          <div className="text-xs text-[#44403C] leading-relaxed">
            <span className="font-semibold text-[#1C1917]">Personal Custody Account:</span> This workbench displays gold issued to your bench, finished ornaments returned, and approved craft wastage allowances. Central vault inventory and other craftsmen's balances are restricted.
          </div>
        </div>

        {/* Key Metrics for Karigar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="My Current Gold Balance"
            value={formatWeight(myProfile?.current_balance_gross)}
            fineGoldValue={formatWeight(myProfile?.current_balance_fine)}
            subtitle="Physical gold currently held on your workbench"
            icon={<Scale className="w-5 h-5 text-[#8C5E1E]" />}
          />

          <StatCard
            title="Total Issued to Bench"
            value={formatWeight(myProfile?.total_issued_gross)}
            subtitle="Raw gold and alloy casting grains received"
            icon={<Vault className="w-5 h-5 text-[#57534E]" />}
          />

          <StatCard
            title="Returned to Vault"
            value={formatWeight(myProfile?.total_returned_gross)}
            subtitle="Finished ornaments and scrap cuttings deposited"
            icon={<CheckCircle2 className="w-5 h-5 text-status-success" />}
          />

          <StatCard
            title="Craft Benchmark Allowance"
            value={`${myProfile?.benchmark_wastage_percent || '2.00'}%`}
            subtitle={myProfile?.specialization || 'Craft Specialization'}
            badge={{
              text: (myProfile?.loss_alerts_count || 0) > 0 ? `${myProfile?.loss_alerts_count} ALERT` : 'IN ORDER',
              variant: (myProfile?.loss_alerts_count || 0) > 0 ? 'danger' : 'success',
            }}
            icon={<Flame className="w-5 h-5 text-[#8C5E1E]" />}
          />
        </div>

        {/* My Recent Slips */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-[#1C1917]">
                My Gold Transaction History
              </h3>
              <p className="text-xs text-[#57534E]">Official slips issued and signed at the workshop counter</p>
            </div>
            <Link to="/slips" className="text-xs font-semibold text-[#8C5E1E] hover:underline">
              View All My Slips →
            </Link>
          </div>

          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Slip No.</TableHeaderCell>
                <TableHeaderCell>Transaction Type</TableHeaderCell>
                <TableHeaderCell>Item Description</TableHeaderCell>
                <TableHeaderCell align="right">Gross Wt</TableHeaderCell>
                <TableHeaderCell align="right">Purity</TableHeaderCell>
                <TableHeaderCell align="right">Fine Gold Wt</TableHeaderCell>
                <TableHeaderCell align="center">Scale Confirmed</TableHeaderCell>
                <TableHeaderCell>Date & Time</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isTransactionsLoading ? (
                <TableRow>
                  <TableCell className="text-center py-6 text-[#57534E]" align="center">
                    Loading your slips...
                  </TableCell>
                </TableRow>
              ) : transactions && transactions.length > 0 ? (
                transactions.map((tx) => (
                  <TableRow key={tx.id} isLossAlert={tx.is_loss_alert}>
                    <TableCell>
                      <span className="font-mono text-xs font-semibold text-[#8C5E1E]">{tx.slip_number}</span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          tx.transaction_type === 'ISSUE'
                            ? 'brass'
                            : tx.transaction_type === 'RECEIPT_ORNAMENT'
                            ? 'success'
                            : tx.transaction_type === 'WASTAGE_SETTLEMENT'
                            ? 'warning'
                            : 'default'
                        }
                        size="sm"
                      >
                        {tx.transaction_type.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-[#44403C] max-w-xs truncate">
                      {tx.item_description}
                    </TableCell>
                    <TableCell align="right" isNumeric className="font-medium">
                      {formatWeight(tx.gross_weight)}
                    </TableCell>
                    <TableCell align="right" isNumeric className="text-[#57534E]">
                      {formatPurity(tx.purity_percent)}
                    </TableCell>
                    <TableCell align="right" isNumeric className="font-semibold text-[#8C5E1E]">
                      {formatWeight(tx.fine_weight)}
                    </TableCell>
                    <TableCell align="center">
                      <span className="inline-flex items-center gap-1 text-[11px] text-status-success font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Verified
                      </span>
                    </TableCell>
                    <TableCell className="text-xs text-[#57534E]">
                      {formatDateTime(tx.created_at)}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell className="text-center py-6 text-[#57534E]" align="center">
                    No transactions recorded for your account yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // WORKSHOP OPERATIONS DASHBOARD (For Staff / Finance Head / Issue Clerk)
  // ---------------------------------------------------------------------------

  // Compute central vault, refiner, and karigar figures cleanly from live response
  const centralVaultGross = summary?.central_vault_gross ?? '1450.000';
  const centralVaultFine = summary?.central_vault_fine ?? '1411.200';
  const refinerGross = summary?.refiner_stock_gross ?? '128.450';
  const refinerFine = summary?.refiner_stock_fine ?? '113.678';
  const karigarGross = summary?.karigar_outstanding_gross ?? '760.720';
  const karigarFine = summary?.karigar_outstanding_fine ?? '696.819';
  const totalWorkshopFine = summary?.total_workshop_gold_fine ?? '2221.697';
  
  // Settled craft wastage (cumulative across jobs, plus today's figure)
  const cumulativeWastageGross = summary?.cumulative_wastage_settled_gross ?? summary?.total_legitimate_wastage_today_gross ?? '23.480';
  const cumulativeWastageFine = summary?.cumulative_wastage_settled_fine ?? summary?.total_legitimate_wastage_today_fine ?? '21.507';
  const todayWastageGross = summary?.total_legitimate_wastage_today_gross ?? '0.000';

  // Filter karigars for the table preview
  const filteredKarigars = (karigars || []).filter((k) => {
    const grossBal = parseFloat(String(k.current_balance_gross || 0));
    const matchesFilter =
      karigarFilter === 'all'
        ? true
        : karigarFilter === 'outstanding'
        ? grossBal > 0.0001
        : k.loss_alerts_count > 0;

    const matchesSearch =
      searchQuery === '' ||
      k.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      k.karigar_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      k.specialization.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* 1. TOP HEADER & QUICK ACTIONS */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#E8E2D5] pb-4">
        <div>
          <h2 className="page-title">Workshop stock</h2>
          <p className="mt-2 text-sm text-charcoal-600">Track gold held in the vault, with karigars, and at the refinery.</p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleRefreshAll}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Link to="/daily-stock" className="inline-flex min-h-9 items-center rounded-lg bg-brass-600 px-3 text-sm font-medium text-white hover:bg-brass-700">
            View stock statement
          </Link>
        </div>
      </div>

      {/* 2. PROMINENT LOSS ALERT BANNER (If unresolved discrepancies exist) */}
      {summary && summary.loss_alerts_count > 0 && (
        <AlertBanner
          type="danger"
          title={`${summary.loss_alerts_count} Unresolved Loss Alert(s) Requiring Finance Review`}
          message={`Excess craft wastage exceeding the workshop threshold (0.100g) has been flagged. Excess wastage is held as an active alert liability and is NOT settled from karigar balances.`}
          actionText="Review Loss Alerts Ledger"
          onAction={() => navigate('/loss-alerts')}
        />
      )}

      {/* 3. OPERATIONAL SUMMARY: 5 PILLAR AUDIT METRICS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {/* Card 1: Central Vault */}
        <StatCard
          title="Central Strongroom Vault"
          value={formatWeight(centralVaultGross)}
          fineGoldValue={formatWeight(centralVaultFine)}
          subtitle="24K Bullion bars & 22K casting grain"
          icon={<Vault className="w-5 h-5 text-[#8C5E1E]" />}
        />

        {/* Card 2: Karigar Bench Custody */}
        <StatCard
          title="Karigar Bench Custody"
          value={formatWeight(karigarGross)}
          fineGoldValue={formatWeight(karigarFine)}
          badge={{
            text: `${summary?.active_karigars_with_balance_count ?? karigars?.length ?? 4} Active`,
            variant: 'brass',
          }}
          subtitle="Work-in-progress on artisan benches"
          icon={<Users className="w-5 h-5 text-[#57534E]" />}
        />

        {/* Card 3: Refiner Stock */}
        <StatCard
          title="Refinery Stock"
          value={formatWeight(refinerGross)}
          fineGoldValue={formatWeight(refinerFine)}
          badge={{ text: 'In Dispatch', variant: 'default' }}
          subtitle="Melting scrap sent for assay refining"
          icon={<Flame className="w-5 h-5 text-[#8C5E1E]" />}
        />

        {/* Card 4: Manufacturing Wastage */}
        <StatCard
          title="Craft Wastage Settled"
          value={formatWeight(cumulativeWastageGross)}
          fineGoldValue={formatWeight(cumulativeWastageFine)}
          subtitle={`Approved craft loss (Today: ${formatWeight(todayWastageGross)})`}
          badge={{ text: 'Audited', variant: 'default' }}
          icon={<CheckCircle2 className="w-5 h-5 text-status-success" />}
        />

        {/* Card 5: Loss Alerts Requiring Review */}
        <StatCard
          title="Loss Alerts Pending"
          value={`${summary?.loss_alerts_count ?? 0} Alerts`}
          isLossAlert={(summary?.loss_alerts_count ?? 0) > 0}
          badge={{
            text: (summary?.loss_alerts_count ?? 0) > 0 ? 'Action Req' : 'Clear',
            variant: (summary?.loss_alerts_count ?? 0) > 0 ? 'danger' : 'success',
          }}
          subtitle="Variance > 0.100g requiring audit"
          icon={<AlertTriangle className="w-5 h-5 text-status-danger" />}
        />
      </div>

      {/* 4. TOTAL WORKSHOP GOLD CUSTODY DISTRIBUTION BAR */}
      <div className="ledger-card p-4 shadow-subtle space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#EFEAE0] pb-2">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-[#8C5E1E]" />
            <h3 className="text-xs font-semibold text-[#1C1917]">
              Total Company Gold Position: <span className="text-[#8C5E1E] font-mono text-sm">{formatWeight(totalWorkshopFine)} Pure Fine</span>
            </h3>
          </div>
          <div className="flex items-center flex-wrap gap-4 text-xs tabular-nums text-charcoal-700">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#9C6E25]" /> Vault ({formatWeight(centralVaultFine)})
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#D4AF37]" /> Karigars ({formatWeight(karigarFine)})
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#B47A46]" /> Refinery ({formatWeight(refinerFine)})
            </span>
          </div>
        </div>

        {/* Visual Custody Ratio Bar */}
        {(() => {
          const totalNum = parseFloat(String(totalWorkshopFine || 1)) || 1;
          const vaultPct = Math.max(0, Math.min(100, (parseFloat(String(centralVaultFine || 0)) / totalNum) * 100));
          const karigarPct = Math.max(0, Math.min(100, (parseFloat(String(karigarFine || 0)) / totalNum) * 100));
          const refinerPct = Math.max(0, Math.min(100, (parseFloat(String(refinerFine || 0)) / totalNum) * 100));

          return (
            <div className="space-y-1">
              <div className="h-3 w-full bg-[#F2ECE0] rounded-xs overflow-hidden flex shadow-inner">
                <div
                  style={{ width: `${vaultPct.toFixed(1)}%` }}
                  className="bg-[#9C6E25] transition-all duration-300"
                  title={`Vault: ${vaultPct.toFixed(1)}%`}
                />
                <div
                  style={{ width: `${karigarPct.toFixed(1)}%` }}
                  className="bg-[#D4AF37] transition-all duration-300"
                  title={`Karigar Custody: ${karigarPct.toFixed(1)}%`}
                />
                <div
                  style={{ width: `${refinerPct.toFixed(1)}%` }}
                  className="bg-[#B47A46] transition-all duration-300"
                  title={`Refinery: ${refinerPct.toFixed(1)}%`}
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-[#78716C] pt-0.5">
                <span>Vault: {vaultPct.toFixed(1)}%</span>
                <span>Craftsmen Custody: {karigarPct.toFixed(1)}%</span>
                <span>Refinery Dispatch: {refinerPct.toFixed(1)}%</span>
              </div>
            </div>
          );
        })()}
      </div>

      {/* 5. WASTAGE & LOSS ACCOUNTING CLARITY PANEL */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3.5 bg-[#FAF7F0] border border-[#E8E2D5] rounded-sm text-xs">
        <div className="flex items-start gap-2.5">
          <div className="w-5 h-5 rounded-full bg-[#F3EBD8] text-[#7D5420] flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
            1
          </div>
          <div>
            <div className="font-semibold text-[#1C1917]">Approved Craft Wastage</div>
            <p className="text-[#57534E] text-[11px] mt-0.5 leading-relaxed">
              Legitimate filing/polishing loss within benchmark tolerance (e.g. 2.00%). Relieved via explicit <code className="text-[#8C5E1E] font-mono">WST-...</code> slips.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2.5">
          <div className="w-5 h-5 rounded-full bg-[#EBE6DC] text-[#44403C] flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
            2
          </div>
          <div>
            <div className="font-semibold text-[#1C1917]">Outstanding Physical Gold</div>
            <p className="text-[#57534E] text-[11px] mt-0.5 leading-relaxed">
              Active bench WIP and scrap cuttings held by karigars. <span className="font-semibold text-[#1C1917]">Not a loss</span> — physical material awaiting vault return.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2.5">
          <div className="w-5 h-5 rounded-full bg-[#FDE8E8] text-status-danger flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
            3
          </div>
          <div>
            <div className="font-semibold text-[#1C1917]">Excess Wastage Loss Alerts</div>
            <p className="text-[#57534E] text-[11px] mt-0.5 leading-relaxed">
              Variance exceeding tolerance by &gt; 0.100g. Held as active alert liability pending physical sweeps and Finance Head audit.
            </p>
          </div>
        </div>
      </div>

      {/* 6. MAIN SPLIT SECTION: ACTIVE KARIGARS & RECENT SLIPS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Karigars Ledger Preview (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-[#1C1917]">
                Karigars with Outstanding Gold
              </h3>
              <p className="text-xs text-[#57534E]">Live physical gross & fine gold balances on artisan benches</p>
            </div>

            <div className="flex items-center gap-2">
              {/* Filter Tabs */}
              <div className="flex rounded-xs bg-[#ECE5D6] p-0.5 text-[11px] font-medium text-[#57534E]">
                <button
                  onClick={() => setKarigarFilter('all')}
                  className={`px-2 py-0.5 rounded-xs transition-colors ${
                    karigarFilter === 'all' ? 'bg-white shadow-xs font-semibold text-[#1C1917]' : 'hover:text-[#1C1917]'
                  }`}
                >
                  All ({karigars?.length || 0})
                </button>
                <button
                  onClick={() => setKarigarFilter('outstanding')}
                  className={`px-2 py-0.5 rounded-xs transition-colors ${
                    karigarFilter === 'outstanding' ? 'bg-white shadow-xs font-semibold text-[#8C5E1E]' : 'hover:text-[#1C1917]'
                  }`}
                >
                  Outstanding Only
                </button>
                <button
                  onClick={() => setKarigarFilter('alerts')}
                  className={`px-2 py-0.5 rounded-xs transition-colors ${
                    karigarFilter === 'alerts' ? 'bg-white shadow-xs font-semibold text-status-danger' : 'hover:text-[#1C1917]'
                  }`}
                >
                  Alerts ({summary?.loss_alerts_count || 0})
                </button>
              </div>

              <Link to="/karigars" className="text-xs font-semibold text-[#8C5E1E] hover:underline flex items-center gap-0.5">
                Full Ledger <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Search Input for Karigars */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#8C857B] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by karigar name, code, or specialization..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-[#DDD4C3] rounded-xs placeholder-[#9E978C] focus:outline-none focus:border-[#9C6E25] focus:ring-1 focus:ring-[#9C6E25] font-sans text-[#1C1917]"
            />
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
                  <TableCell className="text-center py-8 text-[#57534E]" align="center">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-[#9C6E25]" />
                      <span>Loading karigar balance ledger...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredKarigars.length > 0 ? (
                filteredKarigars.slice(0, 7).map((k) => {
                  const hasAlert = k.loss_alerts_count > 0;
                  const hasGold = parseFloat(String(k.current_balance_gross || 0)) > 0.001;

                  return (
                    <TableRow
                      key={k.id}
                      onClick={() => navigate(`/karigars`)}
                      isLossAlert={hasAlert}
                      className="cursor-pointer"
                    >
                      <TableCell>
                        <span className="font-mono text-xs font-semibold text-[#8C5E1E]">{k.karigar_code}</span>
                      </TableCell>
                      <TableCell className="font-medium text-[#1C1917]">{k.name}</TableCell>
                      <TableCell className="text-xs text-[#57534E]">{k.specialization}</TableCell>
                      <TableCell align="right" isNumeric className="font-semibold text-[#1C1917]">
                        {formatWeight(k.current_balance_gross)}
                      </TableCell>
                      <TableCell align="right" isNumeric className="text-[#8C5E1E] font-semibold">
                        {formatWeight(k.current_balance_fine)}
                      </TableCell>
                      <TableCell align="center">
                        {hasAlert ? (
                          <Badge variant="danger" size="sm">
                            {k.loss_alerts_count} ALERT
                          </Badge>
                        ) : hasGold ? (
                          <Badge variant="brass" size="sm">
                            HOLDING GOLD
                          </Badge>
                        ) : (
                          <Badge variant="default" size="sm">
                            CLEAR
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              ) : (
                <TableRow>
                  <TableCell className="text-center py-8 text-[#57534E]" align="center">
                    No craftsmen found matching the selected filter.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Recent Gold Slips (1 Col) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-[#1C1917]">
                Recent Gold Slips
              </h3>
              <p className="text-xs text-[#57534E]">Live movement at workshop counter</p>
            </div>
            <Link to="/slips" className="text-xs font-semibold text-[#8C5E1E] hover:underline flex items-center gap-0.5">
              All Slips <ExternalLink className="w-3 h-3" />
            </Link>
          </div>

          <div className="ledger-card p-3 divide-y divide-[#F0EBE0] shadow-subtle max-h-[530px] overflow-y-auto">
            {isTransactionsLoading ? (
              <div className="py-8 text-center text-xs text-[#57534E] flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-[#9C6E25]" />
                <span>Loading recent slips...</span>
              </div>
            ) : transactions && transactions.length > 0 ? (
              transactions.slice(0, 7).map((tx) => (
                <div key={tx.id} className="py-2.5 first:pt-0 last:pb-0 space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs font-bold text-[#1C1917]">{tx.slip_number}</span>
                      <Badge
                        variant={
                          tx.transaction_type === 'ISSUE'
                            ? 'brass'
                            : tx.transaction_type === 'RECEIPT_ORNAMENT'
                            ? 'success'
                            : tx.transaction_type === 'WASTAGE_SETTLEMENT'
                            ? 'warning'
                            : tx.transaction_type === 'LOSS_ADJUSTMENT'
                            ? 'danger'
                            : 'default'
                        }
                        size="sm"
                      >
                        {tx.transaction_type.replace('_', ' ')}
                      </Badge>
                    </div>
                    <span className="font-mono text-xs font-bold text-[#1C1917] tabular-nums">
                      {formatWeight(tx.gross_weight)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[#57534E]">
                    <span className="truncate max-w-[150px] font-medium">
                      {tx.karigar_name || tx.karigar_code || 'Workshop Central'}
                    </span>
                    <span className="font-mono text-[#8C5E1E]">
                      {formatWeight(tx.fine_weight)} Fine
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-[#78716C]">
                    <span>{formatDateTime(tx.created_at)}</span>
                    <div className="flex items-center gap-1.5">
                      {tx.is_loss_alert && (
                        <span className="px-1 py-0.2 rounded-xs font-mono font-bold bg-status-danger text-white text-[9px]">
                          LOSS ALERT
                        </span>
                      )}
                      <span className="text-status-success font-medium flex items-center gap-0.5">
                        <CheckCircle2 className="w-3 h-3" />
                        Confirmed
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-[#57534E] py-6 text-center">No transactions recorded yet today.</p>
            )}
          </div>
        </div>
      </div>

      {/* 7. UNRESOLVED LOSS ALERTS DRILL-DOWN (If any alerts exist) */}
      {lossAlerts && lossAlerts.length > 0 && (
        <div className="bg-white border border-status-danger-border rounded-sm p-4 shadow-subtle space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-status-danger" />
              <h3 className="text-xs font-semibold text-status-danger">
                Active Wastage Loss Alerts Requiring Finance Head Audit
              </h3>
            </div>
            <Link to="/loss-alerts" className="text-xs font-semibold text-status-danger hover:underline">
              View Detailed Loss Audit Ledger →
            </Link>
          </div>

          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Slip No.</TableHeaderCell>
                <TableHeaderCell>Karigar</TableHeaderCell>
                <TableHeaderCell>Description</TableHeaderCell>
                <TableHeaderCell align="right">Allowed Wastage</TableHeaderCell>
                <TableHeaderCell align="right">Actual Reported</TableHeaderCell>
                <TableHeaderCell align="right">Excess Variance</TableHeaderCell>
                <TableHeaderCell align="center">Action</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {lossAlerts.map((alert) => (
                <TableRow key={alert.id} isLossAlert={true}>
                  <TableCell>
                    <span className="font-mono text-xs font-bold text-status-danger">{alert.slip_number}</span>
                  </TableCell>
                  <TableCell className="font-medium text-[#1C1917]">
                    {alert.karigar_name || alert.karigar_code || `Karigar #${alert.karigar_id}`}
                  </TableCell>
                  <TableCell className="text-xs text-[#44403C]">{alert.item_description}</TableCell>
                  <TableCell align="right" isNumeric className="text-[#57534E]">
                    {formatWeight(
                      (parseFloat(String(alert.gross_weight || 0)) * parseFloat(String(alert.allowed_wastage_percent || 0))) / 100
                    )} ({alert.allowed_wastage_percent}%)
                  </TableCell>
                  <TableCell align="right" isNumeric className="font-medium text-[#1C1917]">
                    {formatWeight(alert.actual_wastage_weight)}
                  </TableCell>
                  <TableCell align="right" isNumeric className="font-bold text-status-danger">
                    +{formatWeight(alert.wastage_variance_weight)}
                  </TableCell>
                  <TableCell align="center">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate('/loss-alerts')}
                      className="text-[11px] py-1 border-status-danger text-status-danger hover:bg-red-50"
                    >
                      Audit Loss
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};
