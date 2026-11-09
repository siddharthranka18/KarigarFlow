import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './features/auth/AuthContext';
import { ProtectedRoute } from './features/auth/ProtectedRoute';
import { restrictedRoutes } from './features/auth/routeAccess';
import { MainLayout } from './layouts/MainLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Karigars } from './pages/Karigars';
import { Transactions } from './pages/Transactions';
import { DailyStock } from './pages/DailyStock';
import { LossAlerts } from './pages/LossAlerts';
import { VaultInventory } from './pages/VaultInventory';
import { WorkshopOverview } from './pages/WorkshopOverview';
import { KarigarPortal } from './pages/KarigarPortal';

function Home() {
  const { isOwner, isKarigar } = useAuth();
  return isKarigar ? <KarigarPortal /> : isOwner ? <Dashboard /> : <WorkshopOverview />;
}

function Slips() {
  const { isKarigar } = useAuth();
  return isKarigar ? <KarigarPortal /> : <Transactions />;
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 15, // 15 seconds
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Home />} />
              <Route path="karigars" element={<Karigars />} />
              <Route path="slips" element={<Slips />} />
              <Route path="transactions" element={<Navigate to="/slips" replace />} />
              <Route path="daily-stock" element={<ProtectedRoute allowedRoles={restrictedRoutes['/daily-stock']}><DailyStock /></ProtectedRoute>} />
              <Route path="loss-alerts" element={<ProtectedRoute allowedRoles={restrictedRoutes['/loss-alerts']}><LossAlerts /></ProtectedRoute>} />
              <Route path="inventory" element={<ProtectedRoute allowedRoles={restrictedRoutes['/inventory']}><VaultInventory /></ProtectedRoute>} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;

