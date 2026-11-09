import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, FileSpreadsheet, Coins, AlertOctagon, Boxes, LogOut, Menu, X } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';

export function MainLayout() {
  const { user, logout, isKarigar, isOwner, isFinanceHead } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const { data: reviews } = useQuery({
    queryKey: ['review-summary'],
    queryFn: () => api.getReviewSummary(),
    enabled: isFinanceHead,
    refetchInterval: 30000,
  });

  useEffect(() => {
    if (!menuOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [menuOpen]);

  const items = [
    { to: '/', label: isKarigar ? 'என் கணக்கு' : 'Overview', icon: LayoutDashboard, allowed: true },
    { to: '/slips', label: isKarigar ? 'என் சீட்டுகள்' : 'Gold ledger', icon: FileSpreadsheet, allowed: true },
    { to: '/karigars', label: 'Karigars', icon: Users, allowed: !isKarigar },
    { to: '/inventory', label: 'Vault inventory', icon: Boxes, allowed: isOwner },
    { to: '/loss-alerts', label: 'Loss reviews', icon: AlertOctagon, allowed: isFinanceHead },
    { to: '/daily-stock', label: 'Daily stock statement', icon: Coins, allowed: isOwner },
  ].filter(item => item.allowed);

  const section = items.find(item => item.to === pathname)?.label ?? 'Workshop';
  const signOut = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen lg:flex">
      {menuOpen && <button type="button" aria-label="Dismiss navigation" onClick={() => setMenuOpen(false)}
        className="fixed inset-0 z-30 bg-charcoal-950/35 lg:hidden" />}
      <aside id="workshop-navigation" className={`${menuOpen ? 'flex' : 'hidden'} fixed inset-y-0 left-0 z-40 w-60 flex-col border-r border-parchment-300 bg-white lg:sticky lg:top-0 lg:flex lg:h-screen lg:shrink-0`}>
        <div className="flex items-center justify-between gap-2 px-5 py-6">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-brass-100 font-serif font-bold text-brass-800">K</span>
            <div>
              <p className="font-serif text-base font-bold leading-tight">KarigarFlow</p>
              <p className="mt-1 text-xs text-charcoal-600">Coimbatore workshop</p>
            </div>
          </div>
          <button type="button" aria-label="Close menu" onClick={() => setMenuOpen(false)} className="rounded-md p-2 hover:bg-parchment-100 lg:hidden"><X size={18} /></button>
        </div>
        <nav aria-label="Workshop" className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          {items.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={() => setMenuOpen(false)}
              className={({ isActive }) => `flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm transition-colors ${isActive ? 'bg-brass-100 font-semibold text-brass-800' : 'text-charcoal-700 hover:bg-parchment-100'}`}>
              <Icon size={17} aria-hidden="true" />
              <span className="flex-1">{label}</span>
              {to === '/loss-alerts' && !!reviews?.open_count && <span className="rounded-full bg-white px-2 text-xs tabular-nums">{reviews.open_count}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-parchment-300 p-4">
          <p className="truncate text-sm font-semibold">{user?.full_name}</p>
          <p className="mt-1 text-xs capitalize text-charcoal-600">{user?.role.replace(/_/g, ' ')}</p>
          <button type="button" onClick={signOut} className="mt-3 flex min-h-10 w-full items-center gap-2 rounded-lg px-2 text-sm text-charcoal-700 hover:bg-parchment-100">
            <LogOut size={16} aria-hidden="true" /> Sign out
          </button>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="border-b border-parchment-300 bg-white">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4 sm:px-8">
            <div className="flex min-w-0 items-center gap-2">
              <button type="button" aria-label="Open navigation menu" aria-controls="workshop-navigation" aria-expanded={menuOpen}
                onClick={() => setMenuOpen(true)} className="-ml-2 rounded-lg p-2.5 hover:bg-parchment-100 lg:hidden"><Menu size={20} /></button>
              <span className="truncate text-sm font-medium text-charcoal-700">{section}</span>
            </div>
            <span className="shrink-0 text-xs text-charcoal-600">{isKarigar ? 'KarigarFlow' : 'Demo workshop'}</span>
          </div>
        </header>
        <main className="px-4 py-6 sm:px-8 sm:py-8">
          <div className="mx-auto max-w-7xl space-y-6"><Outlet /></div>
        </main>
      </div>
    </div>
  );
}
