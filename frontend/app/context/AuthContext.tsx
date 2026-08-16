'use client';

import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

import { apiGet } from '@/lib/api';
import type { Me } from '@/lib/types';

interface AuthContextType {
  user: Me | null;
  isAuthenticated: boolean;
  token: string | null;
  /** True while the profile is being fetched, so guards do not redirect early. */
  loadingUser: boolean;
  login: (token: string) => void;
  logout: () => void;
  /** Re-read /me after finishing a test, so the level in the header updates. */
  refreshUser: () => Promise<Me | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingUser, setLoadingUser] = useState(false);
  const router = useRouter();

  const fetchUser = useCallback(async (activeToken: string): Promise<Me | null> => {
    setLoadingUser(true);
    try {
      const me = await apiGet<Me>('/me', activeToken);
      setUser(me);
      return me;
    } catch {
      // An expired or invalid token should not leave a half-signed-in shell.
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
      return null;
    } finally {
      setLoadingUser(false);
    }
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      setToken(storedToken);
      void fetchUser(storedToken).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [fetchUser]);

  const login = useCallback(
    (newToken: string) => {
      localStorage.setItem('access_token', newToken);
      setToken(newToken);
      void fetchUser(newToken).then((me) => {
        // Send first-time users straight into the placement test - there is
        // nothing else on the dashboard for them until it is done.
        router.push(me && !me.placement_completed ? '/placement' : '/dashboard');
      });
    },
    [fetchUser, router],
  );

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('preferred_language');
    setToken(null);
    setUser(null);
    router.push('/login');
  }, [router]);

  const refreshUser = useCallback(async () => {
    if (!token) return null;
    return fetchUser(token);
  }, [fetchUser, token]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500 font-medium">
        Loading…
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!token,
        token,
        loadingUser,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
