import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { useAuthStore } from '@/store/useAuthStore';
import { useSettingsStore } from '@/store/useSettingsStore';
import type { DecisionMode } from '@/types';
import {
  User,
  Mail,
  Shield,
  Save,
  X,
  Camera,
  Lock,
  Gauge,
  Layers,
  FileCheck,
  Building2,
  BellRing,
  Monitor,
  Palette,
  Mail as MailIcon,
  Monitor as MonitorIcon,
  Clock,
  ChevronDown,
  AlertTriangle,
  FolderCheck,
  Scale as ScaleIcon,
} from 'lucide-react';

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-action-primary focus:ring-offset-2 ${
        checked ? 'bg-action-primary' : 'bg-gray-300'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  );
}

export default function SettingsPage() {
  const { user } = useAuthStore();
  const settings = useSettingsStore();

  const [formState, setFormState] = useState({
    name: user?.name ?? '',
    email: user?.email ?? '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    riskCutoff: settings.riskCutoffPct,
    evidenceCutoff: settings.evidenceCutoff,
    decisionMode: settings.defaultDecisionMode as DecisionMode,
    enableJanSamarth: settings.enableJanSamarth,
    enablePMMY: settings.enablePMMY,
    displayNotices: settings.displayNotices,
    theme: settings.theme as 'light' | 'dark',
    emailNotifications: settings.emailNotifications,
    desktopNotifications: settings.desktopNotifications,
    auditLogFrequency: settings.auditLogFrequency as 'daily' | 'weekly' | 'monthly',
  });

  // Keep form in sync if store is updated externally (e.g. reset)
  useEffect(() => {
    setFormState((prev) => ({
      ...prev,
      riskCutoff: settings.riskCutoffPct,
      evidenceCutoff: settings.evidenceCutoff,
      decisionMode: settings.defaultDecisionMode,
      enableJanSamarth: settings.enableJanSamarth,
      enablePMMY: settings.enablePMMY,
      displayNotices: settings.displayNotices,
      theme: settings.theme,
      emailNotifications: settings.emailNotifications,
      desktopNotifications: settings.desktopNotifications,
      auditLogFrequency: settings.auditLogFrequency,
    }));
  }, [
    settings.riskCutoffPct,
    settings.evidenceCutoff,
    settings.defaultDecisionMode,
    settings.enableJanSamarth,
    settings.enablePMMY,
    settings.displayNotices,
    settings.theme,
    settings.emailNotifications,
    settings.desktopNotifications,
    settings.auditLogFrequency,
  ]);

  const [isDirty, setIsDirty] = useState(false);

  const updateField = <K extends keyof typeof formState>(key: K, value: (typeof formState)[K]) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
    setIsDirty(true);
  };

  const handleSave = () => {
    // Persist threshold + engine settings to store (flows into assessmentApi.decide)
    settings.applySettings({
      riskCutoffPct: formState.riskCutoff,
      evidenceCutoff: formState.evidenceCutoff,
      defaultDecisionMode: formState.decisionMode,
      enableJanSamarth: formState.enableJanSamarth,
      enablePMMY: formState.enablePMMY,
      displayNotices: formState.displayNotices,
      theme: formState.theme,
      emailNotifications: formState.emailNotifications,
      desktopNotifications: formState.desktopNotifications,
      auditLogFrequency: formState.auditLogFrequency,
    });
    setIsDirty(false);
  };

  const handleDiscard = () => {
    setFormState({
      name: user?.name ?? '',
      email: user?.email ?? '',
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      riskCutoff: settings.riskCutoffPct,
      evidenceCutoff: settings.evidenceCutoff,
      decisionMode: settings.defaultDecisionMode,
      enableJanSamarth: settings.enableJanSamarth,
      enablePMMY: settings.enablePMMY,
      displayNotices: settings.displayNotices,
      theme: settings.theme,
      emailNotifications: settings.emailNotifications,
      desktopNotifications: settings.desktopNotifications,
      auditLogFrequency: settings.auditLogFrequency,
    });
    setIsDirty(false);
  };

  const decisionModes = [
    { id: 'D1', label: 'D1 — Risk only', desc: 'PD threshold gate only', color: '#2E5EAA' },
    { id: 'D2', label: 'D2 — Risk + Policy', desc: 'Risk + policy eligibility gates', color: '#B9770E' },
    { id: 'D3', label: 'D3 — Risk + Evidence', desc: 'Risk + evidence quality gates', color: '#6B4C9A' },
    { id: 'D4', label: 'D4 — All layers', desc: 'Risk + Policy + Evidence stack', color: '#0E7C7E' },
  ];

  const roleDisplay = user?.role
    ? user.role.charAt(0).toUpperCase() + user.role.slice(1)
    : '';

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
          <div className="flex-1">
            <h1 className="font-bold tracking-tight text-text-primary" style={{ fontSize: '28px' }}>
              Settings
            </h1>
            <p className="mt-2 text-[#5B6B7B]">
              Manage your account, decision engine thresholds, policy rules, and notification preferences.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleDiscard}
              disabled={!isDirty}
              className={`inline-flex items-center gap-2 rounded-full border border-[#E2E8F0] bg-white px-4 py-2 text-sm font-medium transition-colors ${
                isDirty
                  ? 'text-text-secondary hover:bg-page-bg'
                  : 'text-gray-400 cursor-not-allowed'
              }`}
            >
              <X className="h-4 w-4" />
              Discard
            </button>
            <button
              onClick={handleSave}
              disabled={!isDirty}
              className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-white transition-colors ${
                isDirty
                  ? 'bg-action-primary hover:bg-action-primary-hover'
                  : 'bg-gray-300 cursor-not-allowed'
              }`}
            >
              <Save className="h-4 w-4" />
              Save changes
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div
            className="rounded-lg border border-[#E2E8F0] bg-white overflow-hidden"
            style={{ borderRadius: '12px' }}
          >
            <div
              className="px-6 py-4 border-b border-[#E2E8F0] flex items-center gap-3"
              style={{ backgroundColor: '#FAFCFF' }}
            >
              <div
                className="flex h-9 w-9 items-center justify-center rounded-md"
                style={{ backgroundColor: '#2E5EAA1A' }}
              >
                <User className="h-5 w-5" style={{ color: '#2E5EAA' }} />
              </div>
              <div>
                <h2 className="text-base font-semibold text-text-primary">Profile settings</h2>
                <p className="text-sm text-[#5B6B7B]">Your account information and credentials</p>
              </div>
            </div>

            <div className="p-6">
              <div className="flex flex-col sm:flex-row gap-6 mb-8">
                <div className="flex flex-col items-center sm:items-start gap-3">
                  <div className="relative">
                    <div
                      className="h-24 w-24 rounded-full flex items-center justify-center text-white font-bold text-2xl"
                      style={{ backgroundColor: '#2E5EAA' }}
                    >
                      {user?.name?.charAt(0) ?? 'U'}
                    </div>
                    <button
                      type="button"
                      className="absolute bottom-0 right-0 h-8 w-8 rounded-full bg-white border border-[#E2E8F0] shadow-sm flex items-center justify-center text-action-primary hover:bg-page-bg"
                    >
                      <Camera className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="text-center sm:text-left">
                    <p className="text-sm font-medium text-text-primary">{user?.name}</p>
                    <p className="text-xs capitalize text-[#5B6B7B]">{user?.role}</p>
                  </div>
                </div>

                <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      Full name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <User className="h-4 w-4 text-[#829AB1]" />
                      </div>
                      <input
                        type="text"
                        value={formState.name}
                        onChange={(e) => updateField('name', e.target.value)}
                        className="block w-full pl-10 pr-3 py-2.5 border border-[#E2E8F0] rounded-lg text-sm text-text-primary placeholder:text-[#829AB1] focus:outline-none focus:ring-2 focus:ring-action-primary focus:border-transparent bg-white"
                        placeholder="Enter your full name"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      Email address
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Mail className="h-4 w-4 text-[#829AB1]" />
                      </div>
                      <input
                        type="email"
                        value={formState.email}
                        onChange={(e) => updateField('email', e.target.value)}
                        className="block w-full pl-10 pr-3 py-2.5 border border-[#E2E8F0] rounded-lg text-sm text-text-primary placeholder:text-[#829AB1] focus:outline-none focus:ring-2 focus:ring-action-primary focus:border-transparent bg-white"
                        placeholder="you@company.in"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      User ID
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Shield className="h-4 w-4 text-[#829AB1]" />
                      </div>
                      <input
                        type="text"
                        value={user?.id ?? ''}
                        disabled
                        className="block w-full pl-10 pr-3 py-2.5 border border-[#E2E8F0] rounded-lg text-sm text-[#5B6B7B] bg-page-bg cursor-not-allowed"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      Role
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Shield className="h-4 w-4 text-[#829AB1]" />
                      </div>
                      <input
                        type="text"
                        value={roleDisplay}
                        disabled
                        className="block w-full pl-10 pr-3 py-2.5 border border-[#E2E8F0] rounded-lg text-sm text-[#5B6B7B] bg-page-bg cursor-not-allowed capitalize"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-[#E2E8F0]">
                <div className="flex items-center gap-2 mb-5">
                  <Lock className="h-4 w-4 text-[#5B6B7B]" />
                  <h3 className="text-sm font-semibold text-text-primary">Change password</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      Current password
                    </label>
                    <input
                      type="password"
                      value={formState.currentPassword}
                      onChange={(e) => updateField('currentPassword', e.target.value)}
                      className="block w-full px-3 py-2.5 border border-[#E2E8F0] rounded-lg text-sm text-text-primary placeholder:text-[#829AB1] focus:outline-none focus:ring-2 focus:ring-action-primary focus:border-transparent bg-white"
                      placeholder="••••••••"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      New password
                    </label>
                    <input
                      type="password"
                      value={formState.newPassword}
                      onChange={(e) => updateField('newPassword', e.target.value)}
                      className="block w-full px-3 py-2.5 border border-[#E2E8F0] rounded-lg text-sm text-text-primary placeholder:text-[#829AB1] focus:outline-none focus:ring-2 focus:ring-action-primary focus:border-transparent bg-white"
                      placeholder="••••••••"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      Confirm new password
                    </label>
                    <input
                      type="password"
                      value={formState.confirmPassword}
                      onChange={(e) => updateField('confirmPassword', e.target.value)}
                      className="block w-full px-3 py-2.5 border border-[#E2E8F0] rounded-lg text-sm text-text-primary placeholder:text-[#829AB1] focus:outline-none focus:ring-2 focus:ring-action-primary focus:border-transparent bg-white"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            className="rounded-lg border border-[#E2E8F0] bg-white overflow-hidden"
            style={{ borderRadius: '12px' }}
          >
            <div
              className="px-6 py-4 border-b border-[#E2E8F0] flex items-center gap-3"
              style={{ backgroundColor: '#FDF8F0' }}
            >
              <div
                className="flex h-9 w-9 items-center justify-center rounded-md"
                style={{ backgroundColor: '#B9770E1A' }}
              >
                <Gauge className="h-5 w-5" style={{ color: '#B9770E' }} />
              </div>
              <div>
                <h2 className="text-base font-semibold text-text-primary">Decision engine thresholds</h2>
                <p className="text-sm text-[#5B6B7B]">Configure risk cutoffs and default adjudication mode</p>
              </div>
            </div>

            <div className="p-6 space-y-8">
              <div>
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div
                      className="flex h-8 w-8 items-center justify-center rounded-md"
                      style={{ backgroundColor: '#2E5EAA1A' }}
                    >
                      <AlertTriangle className="h-4 w-4" style={{ color: '#2E5EAA' }} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-text-primary">Risk cutoff τ</h3>
                      <p className="text-xs text-[#5B6B7B]">Maximum PD% for auto-approve eligibility</p>
                    </div>
                  </div>
                  <div
                    className="flex-shrink-0 rounded-lg px-3 py-1.5 border"
                    style={{
                      backgroundColor: '#2E5EAA0D',
                      borderColor: '#2E5EAA33',
                    }}
                  >
                    <span className="font-mono text-lg font-bold" style={{ color: '#2E5EAA' }}>
                      {formState.riskCutoff}%
                    </span>
                  </div>
                </div>
                <div className="px-2">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={formState.riskCutoff}
                    onChange={(e) => updateField('riskCutoff', Number(e.target.value))}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #2E5EAA 0%, #2E5EAA ${formState.riskCutoff}%, #E2E8F0 ${formState.riskCutoff}%, #E2E8F0 100%)`,
                    }}
                  />
                  <div className="flex justify-between mt-2 text-xs text-[#5B6B7B]">
                    <span>0%</span>
                    <span>25%</span>
                    <span>50%</span>
                    <span>75%</span>
                    <span>100%</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div
                      className="flex h-8 w-8 items-center justify-center rounded-md"
                      style={{ backgroundColor: '#B9770E1A' }}
                    >
                      <FolderCheck className="h-4 w-4" style={{ color: '#B9770E' }} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-text-primary">
                        Evidence cutoff τ<sub>E</sub>
                      </h3>
                      <p className="text-xs text-[#5B6B7B]">
                        Minimum evidence score required for auto-approve
                      </p>
                    </div>
                  </div>
                  <div
                    className="flex-shrink-0 rounded-lg px-3 py-1.5 border"
                    style={{
                      backgroundColor: '#B9770E0D',
                      borderColor: '#B9770E33',
                    }}
                  >
                    <span className="font-mono text-lg font-bold" style={{ color: '#B9770E' }}>
                      {formState.evidenceCutoff.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="px-2">
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={Math.round(formState.evidenceCutoff * 100)}
                    onChange={(e) => updateField('evidenceCutoff', Number(e.target.value) / 100)}
                    className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #B9770E 0%, #B9770E ${formState.evidenceCutoff * 100}%, #E2E8F0 ${formState.evidenceCutoff * 100}%, #E2E8F0 100%)`,
                    }}
                  />
                  <div className="flex justify-between mt-2 text-xs text-[#5B6B7B]">
                    <span>0.00</span>
                    <span>0.25</span>
                    <span>0.50</span>
                    <span>0.75</span>
                    <span>1.00</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2.5 mb-4">
                  <div
                    className="flex h-8 w-8 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#0E7C7E1A' }}
                  >
                    <Layers className="h-4 w-4" style={{ color: '#0E7C7E' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">Default decision mode</h3>
                    <p className="text-xs text-[#5B6B7B]">
                      Stack configuration used for new assessments
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {decisionModes.map((mode) => {
                    const selected = formState.decisionMode === mode.id;
                    return (
                      <button
                        key={mode.id}
                        type="button"
                        onClick={() => updateField('decisionMode', mode.id as any)}
                        className={`relative flex items-start gap-3 p-4 rounded-lg border-2 text-left transition-all ${
                          selected
                            ? 'bg-white shadow-sm'
                            : 'border-[#E2E8F0] bg-white hover:bg-page-bg'
                        }`}
                        style={{
                          borderColor: selected ? mode.color : undefined,
                        }}
                      >
                        <div
                          className="flex-shrink-0 mt-0.5 h-5 w-5 rounded-full border-2 flex items-center justify-center"
                          style={{
                            borderColor: mode.color,
                            backgroundColor: selected ? mode.color : 'white',
                          }}
                        >
                          {selected && <div className="h-2 w-2 rounded-full bg-white" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-text-primary">{mode.label}</p>
                          <p className="text-xs text-[#5B6B7B] mt-0.5">{mode.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          <div
            className="rounded-lg border border-[#E2E8F0] bg-white overflow-hidden"
            style={{ borderRadius: '12px' }}
          >
            <div
              className="px-6 py-4 border-b border-[#E2E8F0] flex items-center gap-3"
              style={{ backgroundColor: '#FAF7FD' }}
            >
              <div
                className="flex h-9 w-9 items-center justify-center rounded-md"
                style={{ backgroundColor: '#6B4C9A1A' }}
              >
                <ScaleIcon className="h-5 w-5" style={{ color: '#6B4C9A' }} />
              </div>
              <div>
                <h2 className="text-base font-semibold text-text-primary">Policy rules</h2>
                <p className="text-sm text-[#5B6B7B]">
                  Government schemes, eligibility rules, and system notices
                </p>
              </div>
            </div>

            <div className="p-6 divide-y divide-[#E2E8F0]">
              <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#6B4C9A1A' }}
                  >
                    <Building2 className="h-4 w-4" style={{ color: '#6B4C9A' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">
                      Enable JanSamarth scheme
                    </h3>
                    <p className="text-xs text-[#5B6B7B] mt-0.5">
                      Include JanSamarth portal eligibility checks in policy gate
                    </p>
                  </div>
                </div>
                <Toggle
                  checked={formState.enableJanSamarth}
                  onChange={(v) => updateField('enableJanSamarth', v)}
                />
              </div>

              <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#6B4C9A1A' }}
                  >
                    <FileCheck className="h-4 w-4" style={{ color: '#6B4C9A' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">Enable PMMY scheme</h3>
                    <p className="text-xs text-[#5B6B7B] mt-0.5">
                      Apply Pradhan Mantri Mudra Yojana category limits and eligibility
                    </p>
                  </div>
                </div>
                <Toggle
                  checked={formState.enablePMMY}
                  onChange={(v) => updateField('enablePMMY', v)}
                />
              </div>

              <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#6B4C9A1A' }}
                  >
                    <BellRing className="h-4 w-4" style={{ color: '#6B4C9A' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">Display notices</h3>
                    <p className="text-xs text-[#5B6B7B] mt-0.5">
                      Show the NoticeBar with system announcements and alerts on dashboard
                    </p>
                  </div>
                </div>
                <Toggle
                  checked={formState.displayNotices}
                  onChange={(v) => updateField('displayNotices', v)}
                />
              </div>
            </div>
          </div>

          <div
            className="rounded-lg border border-[#E2E8F0] bg-white overflow-hidden"
            style={{ borderRadius: '12px' }}
          >
            <div
              className="px-6 py-4 border-b border-[#E2E8F0] flex items-center gap-3"
              style={{ backgroundColor: '#F6F8FA' }}
            >
              <div
                className="flex h-9 w-9 items-center justify-center rounded-md"
                style={{ backgroundColor: '#0E7C7E1A' }}
              >
                <Monitor className="h-5 w-5" style={{ color: '#0E7C7E' }} />
              </div>
              <div>
                <h2 className="text-base font-semibold text-text-primary">
                  Appearance & notifications
                </h2>
                <p className="text-sm text-[#5B6B7B]">
                  UI preferences and how you receive alerts and reports
                </p>
              </div>
            </div>

            <div className="p-6 divide-y divide-[#E2E8F0]">
              <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#0E7C7E1A' }}
                  >
                    <Palette className="h-4 w-4" style={{ color: '#0E7C7E' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">Theme</h3>
                    <p className="text-xs text-[#5B6B7B] mt-0.5">
                      Color scheme for the application interface
                    </p>
                  </div>
                </div>
                <div className="relative">
                  <select
                    value={formState.theme}
                    onChange={(e) => updateField('theme', e.target.value as any)}
                    className="appearance-none pl-3 pr-9 py-2 border border-[#E2E8F0] rounded-lg text-sm text-text-primary bg-white focus:outline-none focus:ring-2 focus:ring-action-primary focus:border-transparent cursor-pointer"
                  >
                    <option value="light">Light</option>
                    <option value="dark" disabled>
                      Dark (coming soon)
                    </option>
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#829AB1] pointer-events-none" />
                </div>
              </div>

              <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#0E7C7E1A' }}
                  >
                    <MailIcon className="h-4 w-4" style={{ color: '#0E7C7E' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">Email notifications</h3>
                    <p className="text-xs text-[#5B6B7B] mt-0.5">
                      Receive decision summaries and flagged-review alerts via email
                    </p>
                  </div>
                </div>
                <Toggle
                  checked={formState.emailNotifications}
                  onChange={(v) => updateField('emailNotifications', v)}
                />
              </div>

              <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#0E7C7E1A' }}
                  >
                    <MonitorIcon className="h-4 w-4" style={{ color: '#0E7C7E' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">
                      Desktop notifications
                    </h3>
                    <p className="text-xs text-[#5B6B7B] mt-0.5">
                      Browser push alerts for critical decisions while you work
                    </p>
                  </div>
                </div>
                <Toggle
                  checked={formState.desktopNotifications}
                  onChange={(v) => updateField('desktopNotifications', v)}
                />
              </div>

              <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md"
                    style={{ backgroundColor: '#0E7C7E1A' }}
                  >
                    <Clock className="h-4 w-4" style={{ color: '#0E7C7E' }} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">
                      Audit log email frequency
                    </h3>
                    <p className="text-xs text-[#5B6B7B] mt-0.5">
                      How often you receive summary audit reports by email
                    </p>
                  </div>
                </div>
                <div className="relative">
                  <select
                    value={formState.auditLogFrequency}
                    onChange={(e) => updateField('auditLogFrequency', e.target.value as any)}
                    className="appearance-none pl-3 pr-9 py-2 border border-[#E2E8F0] rounded-lg text-sm text-text-primary bg-white focus:outline-none focus:ring-2 focus:ring-action-primary focus:border-transparent cursor-pointer"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#829AB1] pointer-events-none" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
