import { apiRequest } from "@/services/apiClient";
import type {
  AccessOptions,
  ManagedUser,
  TemporaryPasswordResponse,
  UserAuditEvent,
  UserCreateInput,
  UserListResponse,
  UserSession,
  UserUpdateInput,
} from "@/types/user";

export function listUsers(query = "") {
  return apiRequest<UserListResponse>(`/api/users${query}`);
}

export function getUser(userId: string) {
  return apiRequest<ManagedUser>(`/api/users/${userId}`);
}

export function getAccessOptions() {
  return apiRequest<AccessOptions>("/api/users/access-options");
}

export function createUser(data: UserCreateInput) {
  return apiRequest<TemporaryPasswordResponse>("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateUser(userId: string, data: UserUpdateInput) {
  return apiRequest<ManagedUser>(`/api/users/${userId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function changeUserStatus(
  userId: string,
  action: "activate" | "suspend" | "deactivate" | "unlock",
) {
  return apiRequest<{ success: boolean; message: string; user?: ManagedUser }>(
    `/api/users/${userId}/${action}`,
    { method: "POST" },
  );
}

export function resetUserPassword(userId: string) {
  return apiRequest<TemporaryPasswordResponse>(
    `/api/users/${userId}/reset-password`,
    { method: "POST" },
  );
}

export function updateUserRoles(userId: string, roleIds: string[]) {
  return apiRequest<ManagedUser>(`/api/users/${userId}/roles`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_ids: roleIds }),
  });
}

export function updateUserSites(
  userId: string,
  siteIds: string[],
  defaultSiteId: string,
) {
  return apiRequest<ManagedUser>(`/api/users/${userId}/sites`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      site_ids: siteIds,
      default_site_id: defaultSiteId,
    }),
  });
}

export async function getUserSessions(userId: string) {
  const response = await apiRequest<{ items: UserSession[] }>(
    `/api/users/${userId}/sessions`,
  );
  return response.items;
}

export function revokeUserSession(userId: string, sessionId: string) {
  return apiRequest<{ success: boolean; message: string }>(
    `/api/users/${userId}/sessions/${sessionId}/revoke`,
    { method: "POST" },
  );
}

export function revokeAllUserSessions(userId: string) {
  return apiRequest<{ success: boolean; message: string }>(
    `/api/users/${userId}/sessions/revoke-all`,
    { method: "POST" },
  );
}

export async function getUserAudit(userId: string) {
  const response = await apiRequest<{ items: UserAuditEvent[] }>(
    `/api/users/${userId}/audit`,
  );
  return response.items;
}
