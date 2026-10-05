import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import { Mail, Lock, LogIn, CheckCircle2, AlertCircle, User } from 'lucide-react';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CURRENT_YEAR = new Date().getFullYear();

export default function SignupPage() {
  const navigate = useNavigate();
  const { signup, loading, error } = useAuthStore();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    agreeTerms?: string;
  }>({});

  const validate = (): boolean => {
    const errors: typeof fieldErrors = {};

    if (!name || name.trim().length < 2) {
      errors.name = 'Please enter your full name (at least 2 characters).';
    }

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

    if (!confirmPassword) {
      errors.confirmPassword = 'Please confirm your password.';
    } else if (confirmPassword !== password) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    if (!agreeTerms) {
      errors.agreeTerms = 'You must agree to the terms.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    await signup(name, email, password);

    const authState = useAuthStore.getState();
    if (authState.isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
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
              Start making fairer, evidence-based credit decisions.
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
              <h1 className="text-2xl font-bold text-text-primary">Create account</h1>
              <p className="mt-1 text-sm text-text-secondary">Set up your SynthGigCredit account.</p>
            </div>

            {error && (
              <div className="mb-5 flex items-start gap-2 rounded-md border border-status-decline/30 bg-status-decline-surface px-3 py-2.5 text-sm text-status-decline">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-text-primary">
                  Full name
                </label>
                <div className="relative">
                  <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                  <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      if (fieldErrors.name) setFieldErrors((prev) => ({ ...prev, name: undefined }));
                    }}
                    placeholder="Ananya Menon"
                    className={`w-full rounded-md border bg-white py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-action-primary/30 ${
                      fieldErrors.name ? 'border-status-decline' : 'border-border-subtle'
                    }`}
                    autoComplete="name"
                  />
                </div>
                {fieldErrors.name && (
                  <p className="mt-1.5 text-xs text-status-decline">{fieldErrors.name}</p>
                )}
              </div>

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
                    placeholder="At least 6 characters"
                    className={`w-full rounded-md border bg-white py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-action-primary/30 ${
                      fieldErrors.password ? 'border-status-decline' : 'border-border-subtle'
                    }`}
                    autoComplete="new-password"
                  />
                </div>
                {fieldErrors.password && (
                  <p className="mt-1.5 text-xs text-status-decline">{fieldErrors.password}</p>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="mb-1.5 block text-sm font-medium text-text-primary">
                  Confirm password
                </label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (fieldErrors.confirmPassword) setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                    }}
                    placeholder="Re-enter password"
                    className={`w-full rounded-md border bg-white py-2.5 pl-10 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-action-primary/30 ${
                      fieldErrors.confirmPassword ? 'border-status-decline' : 'border-border-subtle'
                    }`}
                    autoComplete="new-password"
                  />
                </div>
                {fieldErrors.confirmPassword && (
                  <p className="mt-1.5 text-xs text-status-decline">{fieldErrors.confirmPassword}</p>
                )}
              </div>

              <div>
                <label className="flex cursor-pointer items-start gap-2 text-sm text-text-secondary">
                  <input
                    type="checkbox"
                    checked={agreeTerms}
                    onChange={(e) => {
                      setAgreeTerms(e.target.checked);
                      if (fieldErrors.agreeTerms) setFieldErrors((prev) => ({ ...prev, agreeTerms: undefined }));
                    }}
                    className="mt-0.5 h-4 w-4 rounded border-border-subtle text-action-primary focus:ring-action-primary/30"
                  />
                  <span>
                    I agree to the{' '}
                    <a href="#" className="font-medium text-action-primary hover:text-action-primary-hover">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="#" className="font-medium text-action-primary hover:text-action-primary-hover">
                      Privacy Policy
                    </a>
                    .
                  </span>
                </label>
                {fieldErrors.agreeTerms && (
                  <p className="mt-1.5 text-xs text-status-decline">{fieldErrors.agreeTerms}</p>
                )}
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
                {loading ? 'Creating account…' : 'Create Account'}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-text-secondary">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-action-primary hover:text-action-primary-hover">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
