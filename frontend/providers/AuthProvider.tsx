"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { usePathname } from "next/navigation";
import {
  clearClientSession,
  refreshSession,
  setSessionListener,
} from "@/services/apiClient";
import { shouldBootstrapAuth } from "@/services/authBootstrap.mjs";
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
  changePassword: (data: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }) => Promise<AuthUser>;
  switchSite: (siteId: string) => Promise<AuthUser>;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("initializing");
  const [user, setUser] = useState<AuthUser | null>(null);
  const pathname = usePathname();

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

    return () => {
      setSessionListener(null);
    };
  }, [applySession]);

  useEffect(() => {
    if (status !== "initializing" || !shouldBootstrapAuth(pathname)) {
      return;
    }

    let active = true;
    refreshSession()
      .then((session) => {
        if (active) {
          applySession(session);
        }
      })
      .catch(() => {
        if (active) {
          applySession(null);
        }
      });

    return () => {
      active = false;
    };
  }, [applySession, pathname, status]);

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

  const changePassword = useCallback(
    async (data: {
      current_password: string;
      new_password: string;
      confirm_password: string;
    }) => {
      const session = await authService.changePassword(data);
      applySession(session);
      return session.user;
    },
    [applySession],
  );

  const switchSite = useCallback(async (siteId: string) => {
    const session = await authService.switchSite(siteId);
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
      changePassword,
      switchSite,
      hasPermission: (permission) => permissionSet.has(permission),
      hasAnyPermission: (permissions) =>
        permissions.some((permission) => permissionSet.has(permission)),
    }),
    [
      changePassword,
      login,
      logout,
      permissionSet,
      refresh,
      status,
      switchSite,
      user,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
