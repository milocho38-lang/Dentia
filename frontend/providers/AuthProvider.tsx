"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  clearClientSession,
  refreshSession,
  setSessionListener,
} from "@/services/apiClient";
import * as authService from "@/services/authService";
import type {
  AuthStatus,
  AuthUser,
  LoginCredentials,
  TokenResponse,
} from "@/types/auth";

interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  login: (credentials: LoginCredentials) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refresh: () => Promise<AuthUser>;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("initializing");
  const [user, setUser] = useState<AuthUser | null>(null);

  const applySession = useCallback((session: TokenResponse | null) => {
    if (session) {
      setUser(session.user);
      setStatus("authenticated");
      return;
    }
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  useEffect(() => {
    setSessionListener(applySession);
    refreshSession()
      .then(applySession)
      .catch(() => applySession(null));

    return () => {
      setSessionListener(null);
    };
  }, [applySession]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const session = await authService.login(credentials);
    applySession(session);
    return session.user;
  }, [applySession]);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      clearClientSession();
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  const refresh = useCallback(async () => {
    const session = await refreshSession();
    applySession(session);
    return session.user;
  }, [applySession]);

  const permissionSet = useMemo(
    () => new Set(user?.permissions ?? []),
    [user?.permissions],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      login,
      logout,
      refresh,
      hasPermission: (permission) => permissionSet.has(permission),
      hasAnyPermission: (permissions) =>
        permissions.some((permission) => permissionSet.has(permission)),
    }),
    [login, logout, permissionSet, refresh, status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
