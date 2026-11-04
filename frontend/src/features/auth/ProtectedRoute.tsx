import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { UserRole } from '../../types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, token, isLoading, hasRole } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-parchment-100">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-brass-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-medium text-charcoal-600 tracking-wide">Connecting to Coimbatore Workshop Vault...</p>
        </div>
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !hasRole(allowedRoles)) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6">
        <div className="w-12 h-12 rounded-full bg-status-warning-bg text-status-warning flex items-center justify-center mb-4 border border-status-warning-border">
          <span className="font-mono font-bold text-lg">!</span>
        </div>
        <h2 className="text-xl font-semibold text-charcoal-900 mb-2">Access Restricted</h2>
        <p className="text-sm text-charcoal-600 max-w-md">
          Your role (<span className="font-mono font-semibold">{user.role}</span>) does not have authorization to view this section of the gold ledger.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};

