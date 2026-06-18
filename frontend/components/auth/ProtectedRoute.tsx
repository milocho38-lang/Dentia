"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AuthLoadingScreen } from "@/components/auth/AuthLoadingScreen";
import { useAuth } from "@/hooks/useAuth";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      const returnTo = encodeURIComponent(pathname);
      router.replace(`/login?returnTo=${returnTo}&reason=session-required`);
    }
  }, [pathname, router, status]);

  if (status !== "authenticated") {
    return <AuthLoadingScreen />;
  }

  return children;
}
