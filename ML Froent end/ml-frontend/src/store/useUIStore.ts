import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  auditDrawerOpen: boolean;
  mobileMenuOpen: boolean;
  toggleSidebar: () => void;
  toggleAuditDrawer: () => void;
  toggleMobileMenu: () => void;
  setSidebarOpen: (open: boolean) => void;
  setAuditDrawerOpen: (open: boolean) => void;
  setMobileMenuOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  auditDrawerOpen: false,
  mobileMenuOpen: false,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleAuditDrawer: () => set((state) => ({ auditDrawerOpen: !state.auditDrawerOpen })),
  toggleMobileMenu: () => set((state) => ({ mobileMenuOpen: !state.mobileMenuOpen })),

  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
  setAuditDrawerOpen: (open: boolean) => set({ auditDrawerOpen: open }),
  setMobileMenuOpen: (open: boolean) => set({ mobileMenuOpen: open }),
}));
