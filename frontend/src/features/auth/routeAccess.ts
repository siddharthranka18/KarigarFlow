import type { UserRole } from '../../types';

export const restrictedRoutes: Record<string, UserRole[]> = {
  '/daily-stock': ['owner', 'admin'],
  '/inventory': ['owner', 'admin'],
  '/loss-alerts': ['owner', 'admin', 'finance_head'],
};

export function signInDestination(path: string, role: UserRole): string {
  if (!path.startsWith('/') || path.startsWith('//') || path.includes('\\')) return '/';
  const route = path.toLowerCase().replace(/\/+$/, '');
  const allowed = Object.prototype.hasOwnProperty.call(restrictedRoutes, route) ? restrictedRoutes[route] : undefined;
  return allowed && !allowed.includes(role) ? '/' : path;
}
