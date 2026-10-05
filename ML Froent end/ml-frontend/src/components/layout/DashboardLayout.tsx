import type { ReactNode } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileCheck2,
  BarChart3,
  Database,
  History,
  Settings,
  LogOut,
  X,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { useUIStore } from '@/store/useUIStore';
import NoticeBar from './NoticeBar';
import Header from './Header';
import Footer from './Footer';
import AuditDrawer from './AuditDrawer';

interface DashboardLayoutProps {
  children?: ReactNode;
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/assessment', label: 'Assessment', icon: FileCheck2 },
  { to: '/models', label: 'Models', icon: BarChart3 },
  { to: '/datasets', label: 'Datasets', icon: Database },
  { to: '/history', label: 'History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { sidebarOpen, mobileMenuOpen, toggleMobileMenu } = useUIStore();
  const { logout, user } = useAuthStore();
  const location = useLocation();

  const content = children ?? <Outlet />;

  return (
    <div className="flex min-h-screen bg-[#F6F8FA]">
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r border-border-subtle bg-white transition-all duration-300 lg:static ${
          sidebarOpen ? 'w-64' : 'w-20'
        } ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
      >
        <div className="flex h-16 items-center justify-between border-b border-border-subtle px-4">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-action-primary text-white font-bold">
              SG
            </div>
            {sidebarOpen && (
              <div className="whitespace-nowrap">
                <div className="text-sm font-semibold text-text-primary">SynthGigCredit</div>
                <div className="text-xs text-text-secondary">Decision Engine</div>
              </div>
            )}
          </div>
          <button
            onClick={toggleMobileMenu}
            className="rounded-md p-1.5 text-text-muted hover:bg-page-bg lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.map(({ to, label, icon: Icon }) => {
            const isActive = location.pathname === to;
            return (
              <NavLink
                key={to}
                to={to}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-action-primary/5 text-action-primary'
                    : 'text-text-secondary hover:bg-page-bg hover:text-text-primary'
                }`}
                title={!sidebarOpen ? label : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {sidebarOpen && <span className="whitespace-nowrap">{label}</span>}
              </NavLink>
            );
          })}
        </nav>

        <div className="border-t border-border-subtle p-3">
          <div
            className={`mb-3 flex items-center gap-3 overflow-hidden rounded-lg p-2 ${
              sidebarOpen ? '' : 'justify-center'
            }`}
          >
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-domain-risk text-white text-sm font-semibold">
              {user?.name?.charAt(0) ?? 'U'}
            </div>
            {sidebarOpen && (
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-text-primary">{user?.name}</div>
                <div className="truncate text-xs text-text-muted capitalize">{user?.role}</div>
              </div>
            )}
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-text-secondary hover:bg-page-bg hover:text-status-decline"
            title={!sidebarOpen ? 'Logout' : undefined}
          >
            <LogOut className="h-5 w-5 flex-shrink-0" />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={toggleMobileMenu}
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="w-full flex-shrink-0">
          <NoticeBar />
        </div>

        <Header user={user} />

        <div className="flex flex-1">
          <main className="flex-1 min-w-0">
            <div className="mx-auto max-w-7xl">
              {content}
            </div>
          </main>
        </div>

        <Footer />

        <AuditDrawer />
      </div>
    </div>
  );
}
