"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AuthLoadingScreen } from "@/components/auth/AuthLoadingScreen";
import { useAuth } from "@/hooks/useAuth";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { status, user } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      const returnTo = encodeURIComponent(pathname);
      router.replace(`/login?returnTo=${returnTo}&reason=session-required`);
      return;
    }
    if (
      status === "authenticated" &&
      user?.must_change_password &&
      pathname !== "/cambiar-contrasena"
    ) {
      router.replace("/cambiar-contrasena");
    }
  }, [pathname, router, status, user?.must_change_password]);

  if (status !== "authenticated") {
    return <AuthLoadingScreen />;
  }

  return children;
}
