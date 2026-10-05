import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { currentUser } from '@/data/mockData';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  signup: (name: string, email: string, password: string) => Promise<void>;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ loading: true, error: null });

        await new Promise((resolve) => setTimeout(resolve, 500));

        if (!EMAIL_REGEX.test(email)) {
          set({ loading: false, error: 'Please enter a valid email address.' });
          return;
        }

        if (password.length < 6) {
          set({ loading: false, error: 'Password must be at least 6 characters long.' });
          return;
        }

        set({
          user: { ...currentUser, email },
          isAuthenticated: true,
          loading: false,
          error: null,
        });
      },

      logout: () => {
        set({
          user: null,
          isAuthenticated: false,
          loading: false,
          error: null,
        });
      },

      signup: async (name: string, email: string, password: string) => {
        set({ loading: true, error: null });

        await new Promise((resolve) => setTimeout(resolve, 700));

        if (!name || name.trim().length < 2) {
          set({ loading: false, error: 'Please enter a valid name.' });
          return;
        }

        if (!EMAIL_REGEX.test(email)) {
          set({ loading: false, error: 'Please enter a valid email address.' });
          return;
        }

        if (password.length < 6) {
          set({ loading: false, error: 'Password must be at least 6 characters long.' });
          return;
        }

        const newUser: User = {
          id: `USR-${Date.now()}`,
          email,
          name: name.trim(),
          role: 'analyst',
          createdAt: new Date().toISOString(),
        };

        set({
          user: newUser,
          isAuthenticated: true,
          loading: false,
          error: null,
        });
      },
    }),
    {
      name: 'ml-auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
