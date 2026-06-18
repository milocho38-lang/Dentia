"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { TemporaryPasswordDialog } from "@/components/users/TemporaryPasswordDialog";
import { UserForm } from "@/components/users/UserForm";
import { createUser } from "@/services/userService";
import type { UserCreateInput, UserUpdateInput } from "@/types/user";

export default function NewUserPage() {
  const router = useRouter();
  const [password, setPassword] = useState<string | null>(null);
  const [createdUserId, setCreatedUserId] = useState<string | null>(null);

  return (
    <PermissionGate permission="users.create">
      <PermissionGate permission="users.assign_roles">
        <PermissionGate permission="users.assign_sites">
          <div className="mx-auto max-w-4xl">
        <Link
          href="/configuracion/usuarios"
          className="text-sm font-bold text-green-700 hover:underline"
        >
          ← Volver a usuarios
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-slate-950">Crear usuario</h1>
        <p className="mt-2 text-sm text-slate-500">
          Se creará en estado Pendiente y con cambio de contraseña obligatorio.
        </p>
        <div className="mt-7">
          <UserForm
            submitLabel="Crear usuario"
            onSubmit={async (data: UserCreateInput | UserUpdateInput) => {
              const response = await createUser(data as UserCreateInput);
              setCreatedUserId(response.user.id);
              setPassword(response.temporary_password);
            }}
          />
        </div>
          </div>
          <TemporaryPasswordDialog
            password={password}
            onClose={() => {
              setPassword(null);
              router.push(
                createdUserId
                  ? `/configuracion/usuarios/${createdUserId}`
                  : "/configuracion/usuarios",
              );
            }}
          />
        </PermissionGate>
      </PermissionGate>
    </PermissionGate>
  );
}
