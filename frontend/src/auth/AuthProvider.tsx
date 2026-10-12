import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { ApiError, getToken, request, setToken } from '../lib/api';
import { AuthContext } from './context';
import type { User } from './context';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  // Only a stored token needs verifying; with none we are settled from the start.
  const [loading, setLoading] = useState(() => Boolean(getToken()));

  // On boot, trade whatever token we kept for the profile it belongs to.
  // A token that no longer decodes gets dropped rather than left to fail later.
  useEffect(() => {
    if (!getToken()) return;

    let cancelled = false;

    request<User>('/auth/me')
      .then((profile) => {
        if (!cancelled) setUser(profile);
      })
      .catch(() => {
        if (!cancelled) {
          setToken(null);
          setUser(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await request<{ access_token: string; token_type: string }>(
      '/auth/login',
      { method: 'POST', body: { username, password }, anonymous: true },
    );

    setToken(access_token);

    try {
      setUser(await request<User>('/auth/me'));
    } catch (error) {
      // The token was issued but is unusable — don't leave a half-session behind.
      setToken(null);
      setUser(null);
      throw error instanceof ApiError
        ? error
        : new ApiError('Signed in, but the profile could not be loaded.', 0);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
