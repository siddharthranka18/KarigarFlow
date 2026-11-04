import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  FileSpreadsheet,
  Coins,
  AlertOctagon,
  Boxes,
  LogOut,
  Building2,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { Badge } from '../components/ui/Badge';
import { clsx } from 'clsx';

export const MainLayout: React.FC = () => {
  const { user, logout, isKarigar } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    {
      to: '/',
      label: 'Workshop Dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
      allowed: true,
    },
    {
      to: '/karigars',
      label: isKarigar ? 'My Slip & Balance' : 'Karigar Ledger',
      icon: <Users className="w-4 h-4" />,
      allowed: true,
    },
    {
      to: '/slips',
      label: 'Gold Issue & Receipts',
      icon: <FileSpreadsheet className="w-4 h-4" />,
      allowed: true,
    },
    {
      to: '/daily-stock',
      label: 'Daily Stock Statement',
      icon: <Coins className="w-4 h-4" />,
      allowed: !isKarigar,
    },
    {
      to: '/loss-alerts',
      label: 'Loss & Wastage Alerts',
      icon: <AlertOctagon className="w-4 h-4" />,
      allowed: !isKarigar,
    },
    {
      to: '/inventory',
      label: 'Vault Inventory',
      icon: <Boxes className="w-4 h-4" />,
      allowed: !isKarigar,
    },
  ];

  return (
    <div className="min-h-screen flex bg-parchment-100 text-charcoal-900">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-white border-r border-parchment-300 flex flex-col justify-between shadow-subtle z-20">
        <div>
          {/* Brand header */}
          <div className="p-4 border-b border-parchment-300 bg-[#FAF7F0] relative">
            <div className="absolute top-0 left-0 right-0 h-1 bg-brass-600" />
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xs bg-brass-600 text-white flex items-center justify-center font-serif font-bold text-lg shadow-brass">
                K
              </div>
              <div>
                <h1 className="text-base font-serif font-bold tracking-tight text-charcoal-900 leading-none">
                  KarigarFlow
                </h1>
                <p className="text-[10px] tracking-widest text-brass-700 uppercase font-mono mt-1 font-medium">
                  Jewellery ERP
                </p>
              </div>
            </div>

            {/* Coimbatore Workshop Location Badge */}
            <div className="mt-3.5 pt-3 border-t border-parchment-200/80 flex items-center gap-1.5 text-[11px] text-charcoal-600">
              <Building2 className="w-3.5 h-3.5 text-brass-700 flex-shrink-0" />
              <span className="font-medium truncate">Coimbatore Main Workshop</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            <div className="px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-charcoal-500 font-semibold">
              Operations & Ledgers
            </div>
            {navItems
              .filter((item) => item.allowed)
              .map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-2.5 px-3 py-2 rounded-xs text-xs font-medium transition-colors duration-150',
                      isActive
                        ? 'bg-brass-50 text-brass-900 border-l-2 border-brass-600 font-semibold shadow-xs'
                        : 'text-charcoal-700 hover:bg-parchment-100 hover:text-charcoal-900'
                    )
                  }
                >
                  <span className="text-brass-700">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
          </nav>
        </div>

        {/* Footer / User Profile section */}
        <div className="p-3 border-t border-parchment-300 bg-parchment-50">
          <div className="p-2 rounded-xs border border-parchment-300 bg-white mb-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-charcoal-900 truncate">
                {user?.full_name || 'Staff User'}
              </span>
              <Badge variant={user?.role === 'admin' ? 'brass' : 'default'} size="sm">
                {user?.role?.replace('_', ' ')}
              </Badge>
            </div>
            <p className="text-[11px] font-mono text-charcoal-500 truncate">{user?.email}</p>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium text-charcoal-700 hover:text-status-danger hover:bg-red-50 border border-parchment-300 rounded-xs transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Operational Header */}
        <header className="h-14 bg-white border-b border-parchment-300 px-6 flex items-center justify-between shadow-subtle z-10">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
              <span className="text-xs font-mono font-medium text-charcoal-700">
                Shift Active: Coimbatore Workshop Vault
              </span>
            </div>
            <span className="text-parchment-400">|</span>
            <div className="flex items-center gap-1.5 text-xs text-charcoal-600">
              <ShieldCheck className="w-3.5 h-3.5 text-brass-700" />
              <span>Decimal-Safe Gold Engine (3 Decimals)</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-[10px] font-mono uppercase text-charcoal-500">Benchmark Hallmark</div>
              <div className="text-xs font-mono font-semibold text-brass-800">22K 916 (91.60%) / 24K (99.90%)</div>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-parchment-100">
          <div className="max-w-7xl mx-auto space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

