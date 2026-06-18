import { ApiError } from "@/services/apiClient";

export function getLoginErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "Credenciales inválidas o acceso no disponible.";
    }
    if (error.status === 429) {
      return "Demasiados intentos. Espera unos minutos e inténtalo nuevamente.";
    }
    if (error.status >= 500) {
      return "Dentia no está disponible temporalmente. Inténtalo nuevamente.";
    }
    return error.detail ?? "No fue posible iniciar sesión.";
  }

  return "No fue posible conectar con Dentia. Revisa tu conexión.";
}
