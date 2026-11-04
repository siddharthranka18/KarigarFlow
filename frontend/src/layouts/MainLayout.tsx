import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  FileSpreadsheet,
  Coins,
  AlertOctagon,
  Boxes,
  LogOut,
  Building2,
  Menu,
  X,
  ChevronRight,
  Bell,
  Scale
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { Badge } from '../components/ui/Badge';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { clsx } from 'clsx';

export const MainLayout: React.FC = () => {
  const { user, logout, isKarigar } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // For staff users, poll daily summary to provide live alert indicators
  const { data: summary } = useQuery({
    queryKey: ['daily-summary-badge'],
    queryFn: () => api.getDailySummary(),
    enabled: !isKarigar,
    refetchInterval: 30000,
  });

  const lossAlertsCount = summary?.loss_alerts_count || 0;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Canonical navigation in requested order:
  // 1. Overview, 2. Gold Transactions, 3. Karigars, 4. Inventory, 5. Loss Alerts, 6. Daily Stock Statement
  const navItems = [
    {
      to: '/',
      label: isKarigar ? 'Craftsman Overview' : 'Overview',
      icon: <LayoutDashboard className="w-4 h-4" />,
      allowed: true,
      badge: null,
    },
    {
      to: '/slips',
      label: 'Gold Transactions',
      icon: <FileSpreadsheet className="w-4 h-4" />,
      allowed: true,
      badge: null,
    },
    {
      to: '/karigars',
      label: isKarigar ? 'My Slip & Balance' : 'Karigars',
      icon: <Users className="w-4 h-4" />,
      allowed: true,
      badge: null,
    },
    {
      to: '/inventory',
      label: 'Inventory',
      icon: <Boxes className="w-4 h-4" />,
      allowed: !isKarigar,
      badge: null,
    },
    {
      to: '/loss-alerts',
      label: 'Loss Alerts',
      icon: <AlertOctagon className="w-4 h-4" />,
      allowed: !isKarigar,
      badge: lossAlertsCount > 0 ? (
        <span className="ml-auto px-1.5 py-0.2 rounded-xs text-[10px] font-mono font-bold bg-status-danger text-white animate-pulse">
          {lossAlertsCount}
        </span>
      ) : null,
    },
    {
      to: '/daily-stock',
      label: 'Daily Stock Statement',
      icon: <Coins className="w-4 h-4" />,
      allowed: !isKarigar,
      badge: null,
    },
  ];

  // Dynamic breadcrumb label
  const getBreadcrumb = () => {
    const path = location.pathname;
    if (path === '/') return 'Overview';
    if (path.startsWith('/slips') || path.startsWith('/transactions')) return 'Gold Transactions';
    if (path.startsWith('/karigars')) return isKarigar ? 'My Slip & Balance' : 'Karigars';
    if (path.startsWith('/inventory')) return 'Inventory';
    if (path.startsWith('/loss-alerts')) return 'Loss Alerts';
    if (path.startsWith('/daily-stock')) return 'Daily Stock Statement';
    return 'Workshop ERP';
  };

  const NavContent = () => (
    <div className="flex flex-col h-full justify-between">
      <div>
        {/* Brand Header */}
        <div className="p-4 border-b border-parchment-300 bg-[#FAF7F0] relative">
          <div className="absolute top-0 left-0 right-0 h-1 bg-brass-600" />
          <div className="flex items-center justify-between">
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

            {/* Mobile close button */}
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden p-1 text-charcoal-500 hover:text-charcoal-900"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Workshop Location Badge */}
          <div className="mt-3.5 pt-3 border-t border-parchment-200/80 flex items-center gap-1.5 text-[11px] text-charcoal-600">
            <Building2 className="w-3.5 h-3.5 text-brass-700 flex-shrink-0" />
            <span className="font-medium truncate">Coimbatore Main Workshop</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          <div className="px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-charcoal-500 font-semibold">
            {isKarigar ? 'Craftsman Portal' : 'Operations & Ledgers'}
          </div>
          {navItems
            .filter((item) => item.allowed)
            .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setMobileMenuOpen(false)}
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
                <span className="flex-1">{item.label}</span>
                {item.badge}
              </NavLink>
            ))}
        </nav>
      </div>

      {/* User Session & Logout Footer */}
      <div className="p-3 border-t border-parchment-300 bg-parchment-50">
        <div className="p-2.5 rounded-xs border border-parchment-300 bg-white mb-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-charcoal-900 truncate">
              {user?.full_name || 'Staff User'}
            </span>
            <Badge variant={user?.role === 'admin' || user?.role === 'finance_head' ? 'brass' : 'default'} size="sm">
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
    </div>
  );

  return (
    <div className="min-h-screen flex bg-parchment-100 text-charcoal-900">
      {/* Desktop Sidebar Navigation */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-parchment-300 flex-col justify-between shadow-subtle z-20 flex-shrink-0">
        <NavContent />
      </aside>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-charcoal-900/50 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />
          {/* Drawer content */}
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white border-r border-parchment-300 shadow-xl">
            <NavContent />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Operational Header */}
        <header className="h-14 bg-white border-b border-parchment-300 px-4 sm:px-6 flex items-center justify-between shadow-subtle z-10 flex-shrink-0">
          <div className="flex items-center gap-3">
            {/* Mobile menu trigger button */}
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-1.5 rounded-xs text-charcoal-700 hover:bg-parchment-200"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Breadcrumb Navigation */}
            <div className="flex items-center gap-1.5 text-xs font-medium text-charcoal-600">
              <span className="font-serif font-bold text-charcoal-900 hidden sm:inline">KarigarFlow</span>
              <ChevronRight className="w-3.5 h-3.5 text-charcoal-400 hidden sm:inline" />
              <span className="text-brass-800 font-semibold">{getBreadcrumb()}</span>
            </div>

            <span className="hidden md:inline text-parchment-400">|</span>

            {/* Shift & Workshop Status */}
            <div className="hidden md:flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
              <span className="text-xs font-mono font-medium text-charcoal-700">
                Shift Active • Vault Online
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            {/* Loss Alert Notification Indicator for Staff */}
            {!isKarigar && lossAlertsCount > 0 && (
              <button
                onClick={() => navigate('/loss-alerts')}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-xs bg-status-danger-bg text-status-danger border border-status-danger-border text-xs font-medium hover:bg-red-100 transition-colors"
                title={`${lossAlertsCount} Loss Alert(s) require review`}
              >
                <Bell className="w-3.5 h-3.5 animate-bounce" />
                <span className="font-mono font-bold">{lossAlertsCount}</span>
                <span className="hidden sm:inline">Alert{lossAlertsCount > 1 ? 's' : ''}</span>
              </button>
            )}

            {/* Scale Confirmation Engine indicator */}
            <div className="hidden sm:flex items-center gap-1 text-[11px] text-charcoal-600 bg-parchment-100 px-2.5 py-1 rounded-xs border border-parchment-300">
              <Scale className="w-3 h-3 text-brass-700" />
              <span className="font-mono font-medium">0.001g Precision</span>
            </div>

            {/* Current Benchmark Purity */}
            <div className="text-right hidden sm:block">
              <div className="text-[10px] font-mono uppercase text-charcoal-500">Benchmark Purity</div>
              <div className="text-xs font-mono font-semibold text-brass-800">22K 916 (91.60%)</div>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-parchment-100">
          <div className="max-w-7xl mx-auto space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
