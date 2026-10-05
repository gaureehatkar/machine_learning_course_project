import { useState, useRef, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { ChevronDown, Users, LogOut, Menu, X } from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { useAssessmentStore } from '@/store/useAssessmentStore';
import type { AssessmentPresetId, User } from '@/types';
import { getPreset } from '@/utils/assessment';

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/assessment', label: 'Assessment' },
  { to: '/models', label: 'Models' },
  { to: '/datasets', label: 'Datasets' },
  { to: '/history', label: 'History' },
  { to: '/settings', label: 'Settings' },
];

const presetLabels: Record<AssessmentPresetId, string> = {
  1: 'Preset 1 · Rajesh (Approve)',
  2: 'Preset 2 · Priya (Approve)',
  3: 'Preset 3 · Amit (Review)',
  4: 'Preset 4 · Sunita (Decline)',
  5: 'Preset 5 · Iqbal (Approve)',
};

interface HeaderProps {
  user?: User | null;
}

export default function Header({ user: userProp }: HeaderProps) {
  const navigate = useNavigate();
  const storeUser = useAuthStore((s) => s.user);
  const { logout } = useAuthStore();
  const user = userProp ?? storeUser;
  const { loadPreset, assessmentState } = useAssessmentStore();
  const [presetOpen, setPresetOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const presetRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (presetRef.current && !presetRef.current.contains(e.target as Node)) {
        setPresetOpen(false);
      }
      if (userRef.current && !userRef.current.contains(e.target as Node)) {
        setUserOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handlePresetSelect = (id: AssessmentPresetId) => {
    loadPreset(id);
    setPresetOpen(false);
    navigate('/assessment');
  };

  const handleLogout = () => {
    logout();
    setUserOpen(false);
    navigate('/login', { replace: true });
  };

  const currentPresetId = (() => {
    for (let i = 1 as AssessmentPresetId; i <= 5; i = (i + 1) as AssessmentPresetId) {
      const preset = getPreset(i);
      if (
        preset.applicant.id === assessmentState.applicant.id &&
        preset.finances.monthlyIncome === assessmentState.finances.monthlyIncome
      ) {
        return i;
      }
    }
    return 1 as AssessmentPresetId;
  })();

  const initials = user?.name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'AM';

  return (
    <header
      className="sticky top-8 z-40 w-full border-b border-[#E2E8F0] bg-white"
      style={{ height: '64px' }}
    >
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <NavLink to="/dashboard" className="flex items-center gap-2.5">
            <svg
              width="32"
              height="32"
              viewBox="0 0 32 32"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect width="32" height="32" rx="8" fill="#0E7C7E" />
              <path
                d="M10 20V12H12V18H16V12H18V20H10Z"
                fill="white"
              />
              <path
                d="M20 12H22.5C23.8807 12 25 13.1193 25 14.5V17.5C25 18.8807 23.8807 20 22.5 20H20V12ZM22 14V18H22.5C22.7761 18 23 17.7761 23 17.5V14.5C23 14.2239 22.7761 14 22.5 14H22Z"
                fill="white"
              />
            </svg>
            <div className="flex flex-col">
              <span className="text-[15px] font-bold tracking-tight text-[#0F2137] leading-tight">
                SynthGigCredit
              </span>
              <span className="text-[10px] font-medium text-[#5B6B7B] leading-tight">
                ML Decisioning Console
              </span>
            </div>
          </NavLink>

          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'text-[#0E7C7E]'
                      : 'text-[#486581] hover:text-[#0F2137] hover:bg-[#F6F8FA]'
                  }`
                }
                style={({ isActive }) =>
                  isActive
                    ? { backgroundColor: 'rgba(14, 124, 126, 0.1)', borderRadius: '6px' }
                    : { borderRadius: '6px' }
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:block relative" ref={presetRef}>
            <button
              onClick={() => setPresetOpen((prev) => !prev)}
              className="flex items-center gap-2 border border-[#E2E8F0] bg-[#F6F8FA] px-3 py-1.5 text-sm font-medium text-[#0F2137] hover:bg-[#E2E8F0] transition-colors"
              style={{ borderRadius: '6px' }}
            >
              <Users className="h-4 w-4 text-[#5B6B7B]" />
              <span className="max-w-[180px] truncate text-[13px]">
                {presetLabels[currentPresetId]}
              </span>
              <ChevronDown className={`h-4 w-4 text-[#5B6B7B] transition-transform ${presetOpen ? 'rotate-180' : ''}`} />
            </button>
            {presetOpen && (
              <div
                className="absolute right-0 top-full mt-1.5 w-72 border border-[#E2E8F0] bg-white shadow-lg"
                style={{ borderRadius: '12px', zIndex: 50 }}
              >
                <div className="py-1.5">
                  {([1, 2, 3, 4, 5] as AssessmentPresetId[]).map((id) => {
                    const preset = getPreset(id);
                    const isActive = currentPresetId === id;
                    return (
                      <button
                        key={id}
                        onClick={() => handlePresetSelect(id)}
                        className={`w-full px-4 py-2.5 text-left hover:bg-[#F6F8FA] transition-colors ${
                          isActive ? 'bg-[#F6F8FA]' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-semibold text-[#0F2137]">
                              {preset.applicant.displayName}
                            </div>
                            <div className="text-[11px] text-[#5B6B7B] mt-0.5">
                              {preset.applicant.occupation} · INR {preset.finances.monthlyIncome.toLocaleString()}/mo
                            </div>
                          </div>
                          <span className="text-[10px] font-bold text-[#0E7C7E] bg-[#E6F4F4] px-2 py-0.5 rounded-sm" style={{ borderRadius: '6px' }}>
                            P{id}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <div
            className="hidden md:flex items-center gap-1.5 bg-[#FFF8E6] border border-[#F0C000] px-2.5 py-1"
            style={{ borderRadius: '6px' }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#E3B341]" />
            <span className="text-[11px] font-semibold text-[#533F03]">
              Phase 1 · heuristic risk
            </span>
          </div>

          <div className="relative" ref={userRef}>
            <button
              onClick={() => setUserOpen((prev) => !prev)}
              className="flex items-center gap-2 border border-[#E2E8F0] bg-white pl-1 pr-2 py-1 hover:bg-[#F6F8FA] transition-colors"
              style={{ borderRadius: '999px' }}
            >
              <div
                className="flex h-7 w-7 items-center justify-center text-[11px] font-bold text-white"
                style={{
                  backgroundColor: '#0E7C7E',
                  borderRadius: '999px',
                }}
              >
                {initials}
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-[12px] font-semibold text-[#0F2137] leading-tight">
                  {user?.name || 'Ananya Menon'}
                </div>
                <div className="text-[10px] text-[#5B6B7B] leading-tight capitalize">
                  {user?.role || 'analyst'}
                </div>
              </div>
              <ChevronDown className={`h-3.5 w-3.5 text-[#5B6B7B] transition-transform ${userOpen ? 'rotate-180' : ''}`} />
            </button>
            {userOpen && (
              <div
                className="absolute right-0 top-full mt-1.5 w-56 border border-[#E2E8F0] bg-white shadow-lg"
                style={{ borderRadius: '12px', zIndex: 50 }}
              >
                <div className="px-4 py-3 border-b border-[#E2E8F0]">
                  <div className="text-sm font-semibold text-[#0F2137]">
                    {user?.name || 'Ananya Menon'}
                  </div>
                  <div className="text-[12px] text-[#5B6B7B] mt-0.5">
                    {user?.email || 'analyst@microfinance.in'}
                  </div>
                </div>
                <div className="py-1.5">
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm text-[#CF222E] hover:bg-[#FDF0EF] transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    <span className="font-medium">Log out</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="lg:hidden flex items-center justify-center h-9 w-9 border border-[#E2E8F0] rounded-md text-[#486581] hover:bg-[#F6F8FA]"
            style={{ borderRadius: '6px' }}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-[#E2E8F0] bg-white px-4 py-3">
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `px-3 py-2.5 text-sm font-medium rounded-md ${
                    isActive
                      ? 'text-[#0E7C7E]'
                      : 'text-[#486581] hover:text-[#0F2137] hover:bg-[#F6F8FA]'
                  }`
                }
                style={({ isActive }) =>
                  isActive
                    ? { backgroundColor: 'rgba(14, 124, 126, 0.1)', borderRadius: '6px' }
                    : { borderRadius: '6px' }
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}
