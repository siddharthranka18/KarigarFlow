import { useState, useRef } from 'react';
import { api } from '../services/api';
import { ScaleReading } from '../types';
import { AlertBanner } from './ui/AlertBanner';

interface Props {
  reading: ScaleReading | null;
  onReading: (reading: ScaleReading | null) => void;
  onBusy: (busy: boolean) => void;
  onValues: (weight: string, purity: string | null) => void;
}

export function ScalePhoto({ reading, onReading, onValues, onBusy }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const request = useRef(0);
  return <section className="border border-parchment-300 p-3 space-y-3 bg-parchment-50">
    <label className="block text-xs font-semibold text-charcoal-800">Read a scale photo (optional for manual entry)
      <input type="file" accept="image/jpeg,image/png,image/webp" disabled={busy}
        className="block w-full text-xs mt-2" onChange={async e => {
          const file = e.target.files?.[0];
          if (!file) return;
          const current = ++request.current;
          onReading(null); setError(null);
          if (file.size > 5 * 1024 * 1024) { setError('Photo must be 5 MB or smaller.'); return; }
          setBusy(true); onBusy(true);
          try {
            const result = await api.readScale(file);
            if (current !== request.current) return;
            onReading(result);
            if (result.status === 'ready' && result.weight) onValues(result.weight, result.purity);
          } catch (err) { setError(err instanceof Error ? err.message : 'Photo reader unavailable.'); }
          finally { if (current === request.current) { setBusy(false); onBusy(false); } }
          e.target.value = '';
        }} />
    </label>
    <p className="text-xs text-charcoal-600">Crop to one reading with a visible gram unit. OCR runs locally; inspect the photo before confirming. Confidence is an OCR score, not a guarantee.</p>
    {busy && <p role="status" className="text-xs text-brass-800">Reading the display…</p>}
    {error && <div role="alert"><AlertBanner type="danger" message={error} /></div>}
    {reading && <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <img src={reading.image_url} alt="Uploaded scale display for human verification" className="w-full max-h-48 object-contain bg-white" />
      <div className="text-xs space-y-2">
        <p className="font-semibold">{reading.status === 'ready' ? 'Proposed reading — confirm below' : 'Uncertain — retake the photo'}</p>
        <p className="font-mono">Weight: {reading.weight ? `${reading.weight} g` : 'Not reliable'}</p>
        <p className="font-mono">Purity: {reading.purity ? `${reading.purity}%` : 'Not found; enter tested purity manually'}</p>
        <p>OCR score: {Math.round(reading.confidence * 100)}%</p>
        <details><summary>Recognized text</summary><pre className="whitespace-pre-wrap break-words mt-1">{reading.raw_text || 'No readable text'}</pre></details>
        <button type="button" className="underline text-brass-800" onClick={() => { request.current++; onReading(null); }}>Remove photo and use manual entry</button>
      </div>
    </div>}
  </section>;
}
