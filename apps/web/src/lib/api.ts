export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000/api/v1";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mr9_access_token");
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mr9_refresh_token");
}

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem("mr9_access_token", access);
  if (refresh) localStorage.setItem("mr9_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("mr9_access_token");
  localStorage.removeItem("mr9_refresh_token");
  localStorage.removeItem("mr9_acs_server_id");
}

export function getAcsServerId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mr9_acs_server_id");
}

export function setAcsServerId(id: string | null) {
  if (!id) localStorage.removeItem("mr9_acs_server_id");
  else localStorage.setItem("mr9_acs_server_id", id);
}

export async function api<T>(
  path: string,
  options: RequestInit & { auth?: boolean; retryAuth?: boolean } = {},
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (options.body) headers.set("Content-Type", "application/json");
  if (options.auth !== false) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const acs = getAcsServerId();
  if (acs) headers.set("X-Acs-Server-Id", acs);

  let res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (
    res.status === 401 &&
    options.auth !== false &&
    options.retryAuth !== false &&
    typeof window !== "undefined" &&
    getRefreshToken()
  ) {
    const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: getRefreshToken() }),
    });
    if (refreshResponse.ok) {
      const tokens = (await refreshResponse.json()) as {
        access_token: string;
        refresh_token: string;
      };
      setTokens(tokens.access_token, tokens.refresh_token);
      headers.set("Authorization", `Bearer ${tokens.access_token}`);
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    }
  }
  if (
    res.status === 401 &&
    options.auth !== false &&
    typeof window !== "undefined"
  ) {
    clearTokens();
    if (window.location.pathname !== "/login") {
      window.location.replace("/login");
      // A navegação encerra a tela atual. Manter a promise pendente evita que
      // componentes renderizem mensagens de API como "Token inválido" antes
      // de o browser concluir o redirecionamento.
      return new Promise<T>(() => undefined);
    }
  }
  if (!res.ok) {
    let detail: unknown = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
