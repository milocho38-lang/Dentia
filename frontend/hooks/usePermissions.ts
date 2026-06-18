"use client";

import { useAuth } from "@/hooks/useAuth";

export function usePermissions() {
  const { hasPermission, hasAnyPermission, user } = useAuth();
  return {
    permissions: user?.permissions ?? [],
    hasPermission,
    hasAnyPermission,
  };
}
