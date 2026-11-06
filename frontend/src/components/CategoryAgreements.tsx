import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { Karigar } from '../types';
import { Modal } from './ui/Modal';
import { Button } from './ui/Button';
import { AlertBanner } from './ui/AlertBanner';

export const CATEGORIES = ['general', 'necklace', 'bangle', 'chain', 'ring'];

export function CategoryAgreements({ karigar, onClose }: { karigar: Karigar; onClose: () => void }) {
  const [values, setValues] = useState<Record<string, string>>(Object.fromEntries(Object.entries(karigar.wastage_by_category || { general: karigar.benchmark_wastage_percent }).map(([k,v]) => [k, String(v)])));
  const cache = useQueryClient();
  const save = useMutation({ mutationFn: () => api.updateAgreements(karigar.id, Object.fromEntries(Object.entries(values).filter(([,v]) => v !== ''))), onSuccess: () => { cache.invalidateQueries({ queryKey: ['karigars'] }); onClose(); } });
  return <Modal isOpen onClose={() => { if (!save.isPending) onClose(); }} title={`Category agreements · ${karigar.name}`} subtitle="Changes apply to new jobs. Issued jobs keep their recorded allowance.">
    <form className="space-y-4" onSubmit={e => { e.preventDefault(); save.mutate(); }}>
      <p className="text-xs text-charcoal-600">Enter the agreed percentage for each supported category. Blank means that category cannot be issued to this karigar.</p>
      {CATEGORIES.map(category => <label key={category} className="flex items-center justify-between gap-3 text-sm capitalize">{category}<input aria-label={`${category} wastage percent`} type="number" min="0" max="10" step="0.01" value={values[category] ?? ''} onChange={e => setValues({ ...values, [category]: e.target.value })} className="w-28 border border-parchment-300 p-2 font-mono" /></label>)}
      {save.isError && <AlertBanner type="danger" message={save.error.message} />}
      <Button type="submit" isLoading={save.isPending} disabled={!Object.values(values).some(v => v !== '')}>Save agreements</Button>
    </form>
  </Modal>;
}
