import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatWeight } from '../utils/formatters';
import { SlipInspection } from '../components/SlipInspection';
import { Button } from '../components/ui/Button';

const labels: Record<string, string> = { ISSUE: 'பெற்ற தங்கம்', RECEIPT_ORNAMENT: 'நகை திருப்பி அளித்தல்', RECEIPT_SCRAP: 'மீதித் தங்கம்', RECEIPT_DUST: 'தங்கத் தூள்', WASTAGE_SETTLEMENT: 'ஒப்புக்கொண்ட சேதாரம்', LOSS_ADJUSTMENT: 'கணக்கு சரிசெய்தல்' };

export function KarigarPortal() {
  const [tamil, setTamil] = useState(true);
  const [id, setId] = useState<number | null>(null);
  const profile = useQuery({ queryKey: ['karigars'], queryFn: () => api.getKarigars() });
  const slips = useQuery({ queryKey: ['transactions', 'my-slips'], queryFn: () => api.getTransactions({ limit: 100 }) });
  return <div lang={tamil ? 'ta' : 'en'} className="space-y-5">
    <div className="flex justify-between items-start gap-3"><div><h2 className="text-xl font-bold">{tamil ? 'என் தங்கக் கணக்கு' : 'My gold ledger'}</h2><p className="text-sm mt-2">{profile.data?.[0]?.name}</p></div><Button size="sm" variant="secondary" onClick={() => setTamil(!tamil)}>{tamil ? 'English' : 'தமிழ்'}</Button></div>
    {(profile.isLoading || slips.isLoading) && <p role="status">{tamil ? 'பதிவுகள் ஏற்றப்படுகின்றன…' : 'Loading your records…'}</p>}
    {(profile.isError || slips.isError) && <div role="alert"><p>{tamil ? 'இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.' : 'Check your connection and try again.'}</p><Button onClick={() => { profile.refetch(); slips.refetch(); }}>{tamil ? 'மீண்டும் முயற்சி' : 'Retry'}</Button></div>}
    {profile.data?.[0] && <div className="ledger-card p-5 bg-brass-50"><p className="text-xs">{tamil ? 'உங்களிடம் உள்ள நிகரத் தூய தங்க இருப்பு' : 'Outstanding fine gold in your custody'}</p><p className="font-mono text-3xl font-bold mt-3">{formatWeight(profile.data[0].current_balance_fine)}</p><p className="text-xs mt-2">{tamil ? 'மொத்த எடை' : 'Gross weight'}: {formatWeight(profile.data[0].current_balance_gross)}</p></div>}
    <h3 className="font-semibold">{tamil ? 'என் சீட்டுகள் · கடைசி 100 பதிவுகள்' : 'My slips · latest 100 entries'}</h3>
    {slips.data?.length === 0 && <p>{tamil ? 'சீட்டுகள் எதுவும் இல்லை.' : 'No slips recorded.'}</p>}
    {slips.data?.map(tx => <article key={tx.id} className="ledger-card p-4 space-y-2"><div className="flex justify-between gap-2"><strong className="font-mono text-xs">{tx.slip_number}</strong><span className="text-xs">{tamil ? labels[tx.transaction_type] : tx.transaction_type.replace(/_/g, ' ')}</span></div><p className="text-xs">{tamil ? 'வேலை எண்' : 'Job'}: {tx.job_number || '—'}</p><p className="text-sm break-words">{tx.item_description}</p><dl className="grid grid-cols-2 gap-3 text-xs"><div><dt>{tamil ? 'மொத்த எடை' : 'Gross weight'}</dt><dd className="font-mono font-bold mt-1">{formatWeight(tx.gross_weight)}</dd></div><div><dt>{tamil ? 'தூய தங்கம்' : 'Fine gold'}</dt><dd className="font-mono font-bold mt-1">{formatWeight(tx.fine_weight)}</dd></div></dl><p className="text-xs">{tamil ? 'தூய்மை' : 'Purity'}: {tx.purity_percent}% · {tamil ? 'சேதார அனுமதி' : 'Allowance'}: {tx.allowed_wastage_percent}%</p><Button size="sm" variant="secondary" onClick={() => setId(tx.id)}>{tamil ? 'புகைப்படம் மற்றும் விவரங்கள்' : 'Photo and details'}</Button></article>)}
    {id !== null && <SlipInspection id={id} onClose={() => setId(null)} onNavigate={setId} />}
  </div>;
}
