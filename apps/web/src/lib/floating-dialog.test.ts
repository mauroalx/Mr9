import { afterEach, describe, expect, it } from "vitest";
import {
  floatingDialogStyle,
  positionFloatingDialog,
} from "./floating-dialog";

const originalWindow = globalThis.window;

afterEach(() => {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: originalWindow,
  });
});

function viewport(width: number, height: number) {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { innerWidth: width, innerHeight: height },
  });
}

function anchor(top: number, bottom: number, right = 900): HTMLElement {
  return {
    getBoundingClientRect: () =>
      ({ top, bottom, right } as DOMRect),
  } as HTMLElement;
}

describe("posicionamento de diálogos suspensos", () => {
  it("abre acima do gatilho quando não há espaço abaixo", () => {
    viewport(1200, 800);

    const position = positionFloatingDialog(anchor(700, 736), 520, 460);

    expect(position.top).toBe(232);
    expect(position.left).toBe(380);
  });

  it("limita a altura ao espaço restante do viewport", () => {
    const style = floatingDialogStyle({ top: 232, left: 380 }, 520);

    expect(style.maxHeight).toBe("calc(100dvh - 248px)");
    expect(style.width).toBe("min(520px, calc(100vw - 32px))");
  });
});
