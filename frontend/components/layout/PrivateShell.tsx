"use client";

import { useState } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppHeader } from "@/components/layout/AppHeader";
import { Sidebar } from "@/components/layout/Sidebar";

export function PrivateShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-dentia-background">
        <Sidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />
        <div className="min-h-screen lg:pl-72">
          <AppHeader onMenuOpen={() => setSidebarOpen(true)} />
          <main className="px-5 py-7 sm:px-7 lg:px-9 lg:py-9">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
