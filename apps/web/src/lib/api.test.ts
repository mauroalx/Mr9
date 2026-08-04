import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
const originalLocalStorage = globalThis.localStorage;

afterEach(() => {
  globalThis.fetch = originalFetch;
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: originalWindow,
  });
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: originalLocalStorage,
  });
  vi.restoreAllMocks();
});

describe("api", () => {
  it("renova a sessão e repete a chamada após um 401", async () => {
    const setItem = vi.fn();
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: {
        getItem: (key: string) =>
          key === "mr9_access_token" ? "access-antigo" : key === "mr9_refresh_token" ? "refresh-antigo" : null,
        setItem,
        removeItem: vi.fn(),
      },
    });
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: { location: { pathname: "/dashboard", replace: vi.fn() } },
    });
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(
        Response.json({ access_token: "access-novo", refresh_token: "refresh-novo" }),
      )
      .mockResolvedValueOnce(Response.json({ ok: true }));

    await expect(api<{ ok: boolean }>("/dashboard")).resolves.toEqual({ ok: true });
    expect(setItem).toHaveBeenCalledWith("mr9_access_token", "access-novo");
    expect(setItem).toHaveBeenCalledWith("mr9_refresh_token", "refresh-novo");
    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
  });

  it("limpa a sessão e redireciona chamadas autenticadas com 401", async () => {
    const removeItem = vi.fn();
    const replace = vi.fn();
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: { getItem: () => "token-expirado", removeItem },
    });
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: { location: { pathname: "/dashboard", replace } },
    });
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Token inválido" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    void api("/dashboard");
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(removeItem).toHaveBeenCalledWith("mr9_access_token");
    expect(removeItem).toHaveBeenCalledWith("mr9_refresh_token");
    expect(removeItem).toHaveBeenCalledWith("mr9_acs_server_id");
    expect(replace).toHaveBeenCalledWith("/login");
  });
});
