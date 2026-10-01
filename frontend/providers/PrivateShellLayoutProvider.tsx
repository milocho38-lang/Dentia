"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";

interface PrivateShellLayoutContextValue {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: Dispatch<SetStateAction<boolean>>;
}

const PrivateShellLayoutContext = createContext<PrivateShellLayoutContextValue | null>(null);

export function PrivateShellLayoutProvider({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const value = useMemo(
    () => ({ sidebarCollapsed, setSidebarCollapsed }),
    [sidebarCollapsed],
  );

  return (
    <PrivateShellLayoutContext.Provider value={value}>
      {children}
    </PrivateShellLayoutContext.Provider>
  );
}

export function usePrivateShellLayout() {
  const context = useContext(PrivateShellLayoutContext);
  if (!context) {
    throw new Error("usePrivateShellLayout debe usarse dentro de PrivateShellLayoutProvider.");
  }
  return context;
}
