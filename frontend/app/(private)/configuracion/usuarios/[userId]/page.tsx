"use client";

import { use } from "react";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { UserDetail } from "@/components/users/UserDetail";

export default function UserDetailPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = use(params);
  return (
    <PermissionGate permission="users.view">
      <UserDetail userId={userId} />
    </PermissionGate>
  );
}
