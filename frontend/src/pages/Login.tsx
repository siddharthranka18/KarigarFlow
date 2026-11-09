import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import { signInDestination } from '../features/auth/routeAccess';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import { ArrowDownLeft, ArrowUpRight, Scale, Sparkles } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        if (res.status >= 500) {
          throw new Error(import.meta.env.DEV
            ? 'The local backend is unavailable. Check the FastAPI server on port 8000 and its terminal, then retry.'
            : 'The workshop service is temporarily unavailable. Try again in a moment.');
        }
        const data = await res.json().catch(() => ({ detail: 'Authentication failed' }));
        throw new Error(data.detail || 'Invalid email or password');
      }

      const data = await res.json();
      login(data.access_token, {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        is_active: true,
        created_at: new Date().toISOString(),
      });
      navigate(signInDestination(from, data.role), { replace: true });
    } catch (err: any) {
      setError(err.message || 'Login error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectDemoUser = (userEmail: string, userPass: string) => {
    setEmail(userEmail);
    setPassword(userPass);
    setError(null);
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside className="flex flex-col justify-between gap-8 bg-brass-100 px-6 py-7 sm:px-12 lg:px-14 lg:py-12">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-lg bg-brass-800 font-serif text-xl font-bold text-white">K</span>
          <span className="font-serif text-lg font-bold">KarigarFlow</span>
        </div>
        <div className="hidden max-w-md lg:block">
          <h1 className="text-5xl font-semibold leading-[1.08] tracking-tight">The workshop<br />gold ledger</h1>
          <p className="mt-5 max-w-sm text-base leading-relaxed text-charcoal-700">Follow gold from issue to return, with measured weights and a record of who handled each slip.</p>
          <dl className="mt-10 divide-y divide-brass-200 border-y border-brass-200 text-sm">
            <div className="flex items-center gap-3 py-4"><ArrowUpRight size={18} aria-hidden="true" /><dt>Issue to karigar</dt><dd className="ml-auto font-semibold tabular-nums">109.920 g</dd></div>
            <div className="flex items-center gap-3 py-4"><ArrowDownLeft size={18} aria-hidden="true" /><dt>Fine gold returned</dt><dd className="ml-auto font-semibold tabular-nums">106.027 g</dd></div>
            <div className="flex items-center gap-3 py-4"><Scale size={18} aria-hidden="true" /><dt>Fine gold outstanding</dt><dd className="ml-auto font-semibold tabular-nums">3.893 g</dd></div>
          </dl>
          <p className="mt-3 text-xs text-charcoal-700">Sample ledger · Murugesan S · fine gold</p>
        </div>
        <p className="hidden text-sm text-charcoal-700 lg:block">Coimbatore workshop</p>
      </aside>
      <main className="flex items-start justify-center px-5 py-12 sm:items-center lg:py-16">
        <div className="w-full max-w-md">
          <div className="mb-6">
            <h2 className="page-title">Sign in</h2>
            <p className="mt-2 text-sm text-charcoal-600">Open your workshop account.</p>
          </div>
          <div className="ledger-card p-5 sm:p-8">
          {error && (
            <div className="mb-5">
              <AlertBanner type="danger" message={error} />
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Staff Email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
            />

            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full mt-2"
              size="md"
              isLoading={isLoading}
            >
              Sign In to Workshop Ledger
            </Button>
          </form>

          {/* Quick Demo Credentials Switcher (Development & Assessment Mode Only) */}
          {import.meta.env.DEV && (
            <div className="mt-6 pt-5 border-t border-parchment-200">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-charcoal-700 uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5 text-brass-600" />
                  <span>Quick Demo Role Switcher</span>
                </div>
                <span className="text-[10px] font-mono text-status-warning bg-status-warning-bg border border-status-warning-border px-1.5 py-0.5 rounded-xs">
                  Dev Mode
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button type="button" onClick={() => handleSelectDemoUser('owner@karigarflow.com', 'Owner@123')} className="text-left p-2 rounded-xs border border-parchment-300 bg-parchment-50 hover:bg-brass-50"><div className="font-semibold">Managing Partner / Owner</div><div className="text-[10px] font-mono">owner@karigarflow.com</div></button>
                <button
                  type="button"
                  onClick={() => handleSelectDemoUser('finance@karigarflow.com', 'Finance@123')}
                  className="text-left p-2 rounded-xs border border-parchment-300 bg-parchment-50 hover:bg-brass-50 hover:border-brass-300 transition-colors"
                >
                  <div className="font-semibold text-charcoal-900">Finance Head</div>
                  <div className="text-[10px] text-charcoal-500 font-mono">finance@karigarflow.com</div>
                </button>

                <button
                  type="button"
                  onClick={() => handleSelectDemoUser('clerk@karigarflow.com', 'Clerk@123')}
                  className="text-left p-2 rounded-xs border border-parchment-300 bg-parchment-50 hover:bg-brass-50 hover:border-brass-300 transition-colors"
                >
                  <div className="font-semibold text-charcoal-900">Issue Clerk</div>
                  <div className="text-[10px] text-charcoal-500 font-mono">clerk@karigarflow.com</div>
                </button>

                <button
                  type="button"
                  onClick={() => handleSelectDemoUser('manager@karigarflow.com', 'Manager@123')}
                  className="text-left p-2 rounded-xs border border-parchment-300 bg-parchment-50 hover:bg-brass-50 hover:border-brass-300 transition-colors"
                >
                  <div className="font-semibold text-charcoal-900">Workshop Master</div>
                  <div className="text-[10px] text-charcoal-500 font-mono">manager@karigarflow.com</div>
                </button>

                <button
                  type="button"
                  onClick={() => handleSelectDemoUser('karigar1@karigarflow.com', 'Karigar@123')}
                  className="text-left p-2 rounded-xs border border-parchment-300 bg-parchment-50 hover:bg-brass-50 hover:border-brass-300 transition-colors"
                >
                  <div className="font-semibold text-charcoal-900">Karigar (Craftsman)</div>
                  <div className="text-[10px] text-charcoal-500 font-mono">karigar1@karigarflow.com</div>
                </button>
              </div>
            </div>
          )}
        </div>

        </div>
      </main>
    </div>
  );
};
