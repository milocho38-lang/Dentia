"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export function PermissionGate({
  permission,
  children,
}: {
  permission: string;
  children: React.ReactNode;
}) {
  const { hasPermission } = useAuth();
  const router = useRouter();
  const allowed = hasPermission(permission);

  useEffect(() => {
    if (!allowed) {
      router.replace("/sin-acceso");
    }
  }, [allowed, router]);

  if (!allowed) {
    return null;
  }

  return children;
}
