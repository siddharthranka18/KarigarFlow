import { Karigar, GoldTransaction, TransactionDetail, DailyStockSummary, InventoryItem, StockStatement, LossAlertRecord, ScaleReading } from '../types';

const API_BASE = '/api';

class ApiClient {
  private getToken(): string | null {
    return localStorage.getItem('karigarflow_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('karigarflow_token');
      localStorage.removeItem('karigarflow_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
      let errorMessage = 'An unexpected error occurred';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = response.statusText;
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // Health
  async getHealth(): Promise<{ status: string; database: string }> {
    return this.request('/health');
  }

  // Karigars
  async getKarigars(): Promise<Karigar[]> {
    return this.request('/karigars');
  }

  async getKarigar(id: number): Promise<Karigar> {
    return this.request(`/karigars/${id}`);
  }

  async createKarigar(data: Partial<Karigar>): Promise<Karigar> {
    return this.request('/karigars', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Transactions
  async getTransactions(params?: {
    karigar_id?: number;
    transaction_type?: string;
    loss_alerts_only?: boolean;
    limit?: number;
  }): Promise<GoldTransaction[]> {
    const searchParams = new URLSearchParams();
    if (params?.karigar_id) searchParams.append('karigar_id', params.karigar_id.toString());
    if (params?.transaction_type) searchParams.append('transaction_type', params.transaction_type);
    if (params?.loss_alerts_only) searchParams.append('loss_alerts_only', 'true');
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    
    const qs = searchParams.toString();
    return this.request(`/transactions${qs ? `?${qs}` : ''}`);
  }

  async createTransaction(data: {
    transaction_type: string;
    job_number: string;
    item_category: string;
    huid?: string;
    karigar_id?: number;
    item_description: string;
    gross_weight: number | string;
    stone_weight?: number | string;
    purity_percent: number | string;
    allowed_wastage_percent?: number | string;
    actual_wastage_weight?: number | string;
    scale_reading_confirmed?: boolean;
    scale_image_url?: string;
    scale_reading_id?: string;
    idempotency_key?: string;
    related_slip_number?: string;
    notes?: string;
  }): Promise<GoldTransaction> {
    return this.request('/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTransaction(id: number): Promise<TransactionDetail> {
    return this.request(`/transactions/${id}`);
  }

  async getDailySummary(): Promise<DailyStockSummary> {
    return this.request('/transactions/daily-summary');
  }

  async getStockStatement(date: string): Promise<StockStatement> {
    return this.request(`/stock-statement?statement_date=${encodeURIComponent(date)}`);
  }

  async updateAgreements(id: number, wastage_by_category: Record<string, string>): Promise<Karigar> {
    return this.request(`/karigars/${id}/agreements`, { method: 'PUT', body: JSON.stringify({ wastage_by_category }) });
  }

  async getReviewSummary(): Promise<{ open_count: number; drift_count: number }> {
    return this.request('/loss-alerts/summary');
  }

  async getDriftReviews(): Promise<{ karigar_id: number; karigar_name: string; item_category: string; baseline_percent: string; recent_percent: string; increase_points: string; message: string; slip_ids: number[] }[]> {
    return this.request('/loss-alerts/drift');
  }

  async getLossAlerts(status: 'open' | 'resolved'): Promise<LossAlertRecord[]> {
    return this.request(`/loss-alerts?status=${status}`);
  }

  async writeOffLoss(id: number, investigation_notes: string): Promise<GoldTransaction> {
    return this.request(`/loss-alerts/${id}/write-off`, {
      method: 'POST', body: JSON.stringify({ investigation_notes, confirm_write_off: true }),
    });
  }

  async readScale(photo: File): Promise<ScaleReading> {
    const body = new FormData();
    body.append('photo', photo);
    const token = this.getToken();
    const result = await fetch(`${API_BASE}/scale-readings`, {
      method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {}, body,
    });
    if (!result.ok) {
      const error = await result.json().catch(() => ({}));
      throw new Error(typeof error.detail === 'string' ? error.detail : 'Photo could not be read. Retry with a clear JPEG, PNG or WebP image.');
    }
    return result.json();
  }

  async getScaleReading(id: string): Promise<ScaleReading> {
    return this.request(`/scale-readings/${encodeURIComponent(id)}`);
  }

  // Inventory
  async getInventory(): Promise<InventoryItem[]> {
    return this.request('/inventory');
  }
}

export const api = new ApiClient();

