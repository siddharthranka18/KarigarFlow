import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../../types';
import { useQueryClient } from '@tanstack/react-query';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  hasRole: (roles: UserRole[]) => boolean;
  isFinanceHead: boolean;
  isOwner: boolean;
  isClerk: boolean;
  isManager: boolean;
  isKarigar: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const cache = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    try {
      const storedToken = localStorage.getItem('karigarflow_token');
      const storedUser = localStorage.getItem('karigarflow_user');
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (e) {
      console.error('Failed to restore session:', e);
      localStorage.removeItem('karigarflow_token');
      localStorage.removeItem('karigarflow_user');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = (newToken: string, newUser: User) => {
    cache.clear();
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('karigarflow_token', newToken);
    localStorage.setItem('karigarflow_user', JSON.stringify(newUser));
  };

  const logout = () => {
    cache.clear();
    setToken(null);
    setUser(null);
    localStorage.removeItem('karigarflow_token');
    localStorage.removeItem('karigarflow_user');
  };

  const hasRole = (roles: UserRole[]): boolean => {
    if (!user) return false;
    if (user.role === 'admin' || user.role === 'owner') return true;
    return roles.includes(user.role);
  };

  const isOwner = user?.role === 'admin' || user?.role === 'owner';
  const isFinanceHead = isOwner || user?.role === 'finance_head';
  const isClerk = user?.role === 'issue_clerk';
  const isManager = user?.role === 'manager';
  const isKarigar = user?.role === 'karigar';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        hasRole,
        isFinanceHead,
        isOwner,
        isClerk,
        isManager,
        isKarigar,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

