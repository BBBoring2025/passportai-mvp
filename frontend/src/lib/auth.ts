export interface AuthData {
  access_token: string;
  role: string;
  tenant_id: string;
}

export function saveAuth(data: AuthData) {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("role", data.role);
  localStorage.setItem("tenant_id", data.tenant_id);
}

export function getRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("role");
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("role");
  localStorage.removeItem("tenant_id");
}

export function getRoleRedirect(role: string): string {
  switch (role) {
    case "supplier":
      return "/supplier/cases";
    case "buyer":
      return "/buyer/dashboard";
    case "admin":
      return "/admin/review-queue";
    default:
      return "/login";
  }
}
