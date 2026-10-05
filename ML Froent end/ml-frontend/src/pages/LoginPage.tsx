import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import { Mail, Lock, LogIn, CheckCircle2, AlertCircle } from 'lucide-react';

interface LocationState {
  from?: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CURRENT_YEAR = new Date().getFullYear();

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | null;
  const { login, loading, error } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  const validate = (): boolean => {
    const errors: { email?: string; password?: string } = {};

    if (!email) {
      errors.email = 'Email is required.';
    } else if (!EMAIL_REGEX.test(email)) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    await login(email, password);

    const authState = useAuthStore.getState();
    if (authState.isAuthenticated) {
      const redirectTo = state?.from ?? '/dashboard';
      navigate(redirectTo, { replace: true });
    }
  };

  const fillDemo = () => {
    setEmail('demo@synthgig.credit');
    setPassword('demo1234');
    setFieldErrors({});
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-page-bg p-4">
      <div className="flex w-full max-w-5xl overflow-hidden rounded-lg border border-border-subtle bg-surface-card shadow-lg" style={{ borderRadius: '12px' }}>
        <div className="hidden w-1/2 flex-col justify-between bg-gradient-to-br from-action-primary to-action-primary-alt p-10 text-white md:flex">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-white/15 backdrop-blur-sm">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <div className="text-lg font-bold tracking-tight">SynthGigCredit</div>
                <div className="text-xs text-white/80">ML-Powered Credit Decisioning</div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <h2 className="text-2xl font-semibold leading-tight">
              Trusted decisions backed by multi-signal intelligence.
            </h2>
            <ul className="space-y-4">
              {[
                'Multi-signal risk assessment across income, behaviour, and tenure',
                'Evidence scoring with AA & ULI completeness weighting',
                'Configurable policy gates with transparent pass/fail outcomes',
              ].map((text) => (
                <li key={text} className="flex items-start gap-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-white/90" />
                  <span className="text-sm text-white/90">{text}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="text-xs text-white/70">
            © {CURRENT_YEAR} SynthGigCredit. All rights reserved.
          </div>
        </div>

        <div className="w-full p-8 md:w-1/2 md:p-10">
          <div className="mx-auto max-w-sm">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-text-primary">Welcome back</h1>
              <p className="mt-1 text-sm text-text-secondary">Sign in to your account to continue.</p>
            </div>

            {error && (
              <div className="mb-5 flex items-start gap-2 rounded-md border border-status-decline/30 bg-status-decline-surface px-3 py-2.5 text-sm text-status-decline">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-text-primary">
                  Email
                </label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (fieldErrors.email) setFieldErrors((prev) => ({ ...prev, email: undefined }));
                    }}
                    placeholder="you@company.com"
                    className={`w-full rounded-md border bg-white py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-action-primary/30 ${
                      fieldErrors.email ? 'border-status-decline' : 'border-border-subtle'
                    }`}
                    autoComplete="email"
                  />
                </div>
                {fieldErrors.email && (
                  <p className="mt-1.5 text-xs text-status-decline">{fieldErrors.email}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-text-primary">
                  Password
                </label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: undefined }));
                    }}
                    placeholder="••••••••"
                    className={`w-full rounded-md border bg-white py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-action-primary/30 ${
                      fieldErrors.password ? 'border-status-decline' : 'border-border-subtle'
                    }`}
                    autoComplete="current-password"
                  />
                </div>
                {fieldErrors.password && (
                  <p className="mt-1.5 text-xs text-status-decline">{fieldErrors.password}</p>
                )}
              </div>

              <div className="flex items-center justify-between">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-text-secondary">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border-border-subtle text-action-primary focus:ring-action-primary/30"
                  />
                  Remember me
                </label>
                <a href="#" className="text-sm font-medium text-action-primary hover:text-action-primary-hover">
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-md bg-action-primary px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-action-primary-hover focus:outline-none focus:ring-2 focus:ring-action-primary/30 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? (
                  <LogIn className="h-4 w-4 animate-spin" />
                ) : (
                  <LogIn className="h-4 w-4" />
                )}
                {loading ? 'Signing in…' : 'Sign In'}
              </button>
            </form>

            <div className="mt-6 rounded-md border border-notice-banner-border bg-notice-banner-bg px-3 py-2.5">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-notice-banner-text" />
                <div className="text-xs text-notice-banner-text">
                  <span className="font-semibold">Demo credentials</span>
                  <div className="mt-0.5 flex flex-wrap items-center gap-x-1.5">
                    <span>Try</span>
                    <button
                      type="button"
                      onClick={fillDemo}
                      className="font-mono font-semibold underline decoration-dotted underline-offset-2 hover:text-action-primary"
                    >
                      demo@synthgig.credit / demo1234
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <p className="mt-6 text-center text-sm text-text-secondary">
              Don&apos;t have an account?{' '}
              <Link to="/signup" className="font-medium text-action-primary hover:text-action-primary-hover">
                Create account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
