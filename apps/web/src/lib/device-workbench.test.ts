import { describe, expect, it } from "vitest";
import { formatBytes, inventoryValue, wifiBand } from "./device-workbench";

describe("device workbench", () => {
  it("classifica rádio pelo canal e usa o índice apenas como fallback", () => {
    expect(wifiBand({ root: "x", ssid: "a", channel: "11", index: 8 })).toBe("24");
    expect(wifiBand({ root: "x", ssid: "a", channel: "36", index: 1 })).toBe("5");
  });

  it("formata contadores e diferencia atualização de indisponibilidade", () => {
    expect(formatBytes(2 ** 30)).toBe("1 GB");
    expect(formatBytes({} as unknown as number)).toBeNull();
    expect(inventoryValue(null, true, true)).toBe("Atualizando…");
    expect(inventoryValue(null, false, false)).toBe("Aguardando CPE online");
  });
});
