import { describe, expect, it } from "vitest";
import { buildInventorySearchParams, type InventoryFilters } from "./device-inventory";

const defaults: InventoryFilters = {
  q: "",
  status: "all",
  manufacturer: "all",
  model: "all",
  firmware: "all",
  tag: "all",
};

describe("buildInventorySearchParams", () => {
  it("mantém paginação de dez itens sem enviar filtros neutros", () => {
    expect(buildInventorySearchParams(defaults, 2).toString()).toBe("limit=10&skip=20");
  });

  it("normaliza a busca e envia filtros ativos para a API", () => {
    const params = buildInventorySearchParams(
      { ...defaults, q: "  cliente@ ", status: "offline", manufacturer: "ZTE" },
      0,
    );
    expect(Object.fromEntries(params)).toEqual({
      limit: "10",
      skip: "0",
      q: "cliente@",
      online: "false",
      manufacturer: "ZTE",
    });
  });
});
