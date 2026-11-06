/**
 * Utility formatters for KarigarFlow Gold Accounting.
 * Ensures strict 3-decimal place display for weights and 2-decimal place for purities.
 */

export function formatWeight(val: number | string | undefined | null): string {
  if (val === undefined || val === null || val === '') return '0.000 g';
  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) return '0.000 g';
  return `${num.toFixed(3)} g`;
}

export function formatPurity(val: number | string | undefined | null): string {
  if (val === undefined || val === null || val === '') return '0.00%';
  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) return '0.00%';
  
  // Helpful BIS Hallmark hints
  if (Math.abs(num - 91.6) < 0.1) return '91.60% (22K)';
  if (Math.abs(num - 75.0) < 0.1) return '75.00% (18K)';
  if (Math.abs(num - 99.9) < 0.1) return '99.90% (24K)';
  
  return `${num.toFixed(2)}%`;
}

export function formatDateTime(isoString: string | undefined): string {
  if (!isoString) return '-';
  try {
    const normalized = /^\d{4}-\d{2}-\d{2}T/.test(isoString) && !/(Z|[+-]\d\d:\d\d)$/.test(isoString) ? `${isoString}Z` : isoString;
    const d = new Date(normalized);
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
      timeZone: 'Asia/Kolkata',
    }).format(d);
  } catch {
    return isoString;
  }
}

export function formatDateOnly(isoString: string | undefined): string {
  if (!isoString) return '-';
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      timeZone: 'Asia/Kolkata',
    }).format(d);
  } catch {
    return isoString;
  }
}

