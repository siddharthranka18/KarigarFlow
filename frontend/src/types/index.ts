export type UserRole = 'admin' | 'finance_head' | 'manager' | 'issue_clerk' | 'karigar';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthSession {
  token: string;
  user: User;
}

export interface Karigar {
  id: number;
  karigar_code: string;
  name: string;
  phone?: string;
  specialization: string;
  benchmark_wastage_percent: number | string;
  opening_balance_gross: number | string;
  opening_balance_fine: number | string;
  is_active: boolean;
  created_at: string;
  current_balance_gross: number | string;
  current_balance_fine: number | string;
  total_issued_gross: number | string;
  total_returned_gross: number | string;
  active_jobs_count: number;
  loss_alerts_count: number;
}

export type TransactionType = 'ISSUE' | 'RECEIPT_ORNAMENT' | 'RECEIPT_SCRAP' | 'RECEIPT_DUST' | 'WASTAGE_SETTLEMENT' | 'LOSS_ADJUSTMENT' | 'PURCHASE';

export interface GoldTransaction {
  id: number;
  slip_number: string;
  idempotency_key?: string;
  related_slip_number?: string;
  transaction_type: TransactionType;
  karigar_id?: number;
  karigar_name?: string;
  karigar_code?: string;
  created_by_user_id?: number;
  item_description: string;
  gross_weight: string;
  stone_weight: string;
  net_weight: string;
  purity_percent: string;
  fine_weight: string;
  allowed_wastage_percent: string;
  actual_wastage_weight: string;
  wastage_variance_weight: string;
  is_loss_alert: boolean;
  scale_reading_confirmed: boolean;
  scale_image_url?: string;
  notes?: string;
  created_at: string;
}

export interface ScaleReading {
  id: string;
  status: 'ready' | 'uncertain';
  weight: string | null;
  purity: string | null;
  confidence: number;
  raw_text: string;
  image_url: string;
}

export interface LossAlertRecord {
  alert: GoldTransaction;
  resolution: GoldTransaction | null;
}

export interface TransactionDetail {
  transaction: GoldTransaction;
  recorded_by_name: string | null;
  parent: GoldTransaction | null;
  linked_entries: GoldTransaction[];
}

export interface DailyStockSummary {
  date: string;
  vault_raw_gold_gross: string;
  vault_raw_gold_fine: string;
  central_vault_gross?: string;
  central_vault_fine?: string;
  refiner_stock_gross?: string;
  refiner_stock_fine?: string;
  karigar_outstanding_gross: string;
  karigar_outstanding_fine: string;
  total_workshop_gold_fine: string;
  total_issues_today_gross: string;
  total_receipts_today_gross: string;
  total_legitimate_wastage_today_gross: string;
  total_legitimate_wastage_today_fine: string;
  cumulative_wastage_settled_gross?: string;
  cumulative_wastage_settled_fine?: string;
  total_wastage_today_gross: string;
  total_excess_wastage_today_gross?: string;
  loss_alerts_count: number;
  active_karigars_with_balance_count?: number;
  pending_reconciliations_count?: number;
}

export interface StockRow {
  location: string;
  unit: 'gross' | 'fine';
  opening: string;
  issues: string;
  receipts: string;
  purchases: string;
  wastage: string;
  loss_adjustments: string;
  closing: string;
}

export interface StockStatement {
  date: string;
  timezone: string;
  transaction_count: number;
  rows: StockRow[];
}

export interface InventoryItem {
  id: number;
  lot_code: string;
  category: string;
  description: string;
  gross_weight: string;
  purity_percent: string;
  fine_weight: string;
  location: string;
  updated_at: string;
}

