import { describe, expect, it } from "vitest";
import { isNavigationActive, operationalNavigation } from "./navigation";

describe("isNavigationActive", () => {
  it("ativa a rota exata e suas páginas filhas", () => {
    expect(isNavigationActive("/devices", "/devices")).toBe(true);
    expect(isNavigationActive("/devices/ABC123", "/devices")).toBe(true);
  });

  it("não ativa módulos com prefixos apenas semelhantes", () => {
    expect(isNavigationActive("/devices-old", "/devices")).toBe(false);
    expect(isNavigationActive("/dashboard", "/devices")).toBe(false);
  });

  it("mantém diagnósticos como recurso contextual do CPE", () => {
    expect(operationalNavigation.some((item) => item.href === "/diagnostics")).toBe(false);
  });

  it("mantém fora do MVP os módulos de catálogo avançado", () => {
    expect(operationalNavigation.map((item) => item.href)).not.toEqual(
      expect.arrayContaining(["/presets", "/templates", "/parameters"]),
    );
  });
});
