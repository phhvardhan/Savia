import { createContext, useContext } from 'react';

/** Mirrors LocalUserProfile in app/schemas/entities/auth_entity.py. */
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  department: string | null;
  roles: string[];
  workspace_id: string | null;
  avatar_initials: string | null;
  is_active: boolean;
}

export interface AuthContextValue {
  user: User | null;
  /** True until the stored token has been checked against /auth/me. */
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AUTH_REQUIRED = import.meta.env.VITE_AUTH_REQUIRED === 'true';

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside an AuthProvider');
  return context;
}
