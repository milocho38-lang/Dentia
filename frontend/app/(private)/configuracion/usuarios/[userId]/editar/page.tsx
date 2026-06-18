"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { Spinner } from "@/components/shared/Spinner";
import { UserForm } from "@/components/users/UserForm";
import { getUser, updateUser } from "@/services/userService";
import type {
  ManagedUser,
  UserCreateInput,
  UserUpdateInput,
} from "@/types/user";

export default function EditUserPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = use(params);
  const router = useRouter();
  const [user, setUser] = useState<ManagedUser | null>(null);

  useEffect(() => {
    getUser(userId).then(setUser);
  }, [userId]);

  return (
    <PermissionGate permission="users.update">
      <div className="mx-auto max-w-4xl">
        <Link
          href={`/configuracion/usuarios/${userId}`}
          className="text-sm font-bold text-green-700 hover:underline"
        >
          ← Volver al usuario
        </Link>
        <h1 className="mt-5 text-3xl font-bold text-slate-950">
          Editar usuario
        </h1>
        <div className="mt-7">
          {user ? (
            <UserForm
              user={user}
              submitLabel="Guardar cambios"
              onSubmit={async (data: UserCreateInput | UserUpdateInput) => {
                await updateUser(userId, data as UserUpdateInput);
                router.push(`/configuracion/usuarios/${userId}`);
              }}
            />
          ) : (
            <div className="flex items-center gap-3 py-16 text-slate-500">
              <Spinner className="h-6 w-6 text-dentia-primary" />
              Cargando usuario…
            </div>
          )}
        </div>
      </div>
    </PermissionGate>
  );
}
