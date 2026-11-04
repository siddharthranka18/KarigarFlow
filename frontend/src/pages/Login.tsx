import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import { Building2, ShieldCheck, KeyRound, Sparkles } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('finance@karigarflow.com');
  const [password, setPassword] = useState('Finance@123');
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
      navigate(from, { replace: true });
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
    <div className="min-h-screen bg-parchment-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Brand header */}
        <div className="flex justify-center mb-3">
          <div className="w-12 h-12 rounded-xs bg-brass-600 text-white flex items-center justify-center font-serif font-bold text-2xl shadow-brass">
            K
          </div>
        </div>
        <h2 className="text-center text-2xl font-serif font-bold text-charcoal-900 tracking-tight">
          KarigarFlow ERP
        </h2>
        <p className="mt-1 text-center text-xs font-mono uppercase tracking-widest text-brass-700">
          Coimbatore Jewellery Workshop & Gold Vault
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-subtle border border-parchment-300 rounded-sm sm:px-10 relative">
          <div className="absolute top-0 left-0 right-0 h-1 bg-brass-600" />

          {error && (
            <div className="mb-5">
              <AlertBanner type="danger" message={error} />
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Staff Email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. finance@karigarflow.com"
            />

            <Input
              label="Password"
              type="password"
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
              icon={<KeyRound className="w-4 h-4" />}
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

        {/* Security & Workshop context footer */}
        <div className="mt-4 flex items-center justify-center gap-4 text-xs text-charcoal-500">
          <div className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-brass-600" />
            <span>Decimal-Safe Gold Accounting</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1">
            <Building2 className="w-3.5 h-3.5 text-brass-600" />
            <span>Coimbatore Workshop Network</span>
          </div>
        </div>
      </div>
    </div>
  );
};

