"use client";

import { useState } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppHeader } from "@/components/layout/AppHeader";
import { Sidebar } from "@/components/layout/Sidebar";
import {
  PrivateShellLayoutProvider,
  usePrivateShellLayout,
} from "@/providers/PrivateShellLayoutProvider";

export function PrivateShell({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <PrivateShellLayoutProvider>
        <PrivateShellFrame>{children}</PrivateShellFrame>
      </PrivateShellLayoutProvider>
    </ProtectedRoute>
  );
}

function PrivateShellFrame({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { sidebarCollapsed, setSidebarCollapsed } = usePrivateShellLayout();

  return (
    <div className="min-h-screen bg-dentia-background">
      <Sidebar
        open={sidebarOpen}
        desktopCollapsed={sidebarCollapsed}
        onClose={() => setSidebarOpen(false)}
      />
      <div className={`min-h-screen transition-[padding] duration-200 ${sidebarCollapsed ? "lg:pl-0" : "lg:pl-72"}`}>
        <AppHeader
          sidebarCollapsed={sidebarCollapsed}
          onMenuOpen={() => setSidebarOpen(true)}
          onDesktopMenuOpen={() => setSidebarCollapsed(false)}
        />
        <main className="px-5 py-7 sm:px-7 lg:px-9 lg:py-9">{children}</main>
      </div>
    </div>
  );
}
