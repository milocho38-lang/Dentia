import type { Metadata } from "next";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { UserList } from "@/components/users/UserList";

export const metadata: Metadata = { title: "Usuarios" };

export default function UsersPage() {
  return (
    <PermissionGate permission="users.view">
      <UserList />
    </PermissionGate>
  );
}
