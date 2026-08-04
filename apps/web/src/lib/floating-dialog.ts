import type { CSSProperties } from "react";

export type FloatingDialogPosition = { top: number; left: number };

const VIEWPORT_GUTTER = 16;
const ANCHOR_GAP = 8;

export function positionFloatingDialog(
  anchor: HTMLElement,
  preferredWidth: number,
  estimatedHeight: number,
): FloatingDialogPosition {
  const rect = anchor.getBoundingClientRect();
  const availableHeight = window.innerHeight - VIEWPORT_GUTTER * 2;
  const width = Math.min(
    preferredWidth,
    window.innerWidth - VIEWPORT_GUTTER * 2,
  );
  const height = Math.min(estimatedHeight, availableHeight);
  const left = Math.min(
    Math.max(VIEWPORT_GUTTER, rect.right - width),
    window.innerWidth - width - VIEWPORT_GUTTER,
  );
  const spaceBelow = window.innerHeight - rect.bottom - ANCHOR_GAP;
  const spaceAbove = rect.top - ANCHOR_GAP;

  if (spaceBelow >= height || spaceBelow >= spaceAbove) {
    return {
      top: Math.min(
        rect.bottom + ANCHOR_GAP,
        window.innerHeight - height - VIEWPORT_GUTTER,
      ),
      left,
    };
  }

  return {
    top: Math.max(VIEWPORT_GUTTER, rect.top - height - ANCHOR_GAP),
    left,
  };
}

export function floatingDialogStyle(
  position: FloatingDialogPosition,
  preferredWidth: number,
): CSSProperties {
  return {
    top: position.top,
    left: position.left,
    width: `min(${preferredWidth}px, calc(100vw - ${VIEWPORT_GUTTER * 2}px))`,
    // O corpo controla o scroll para manter cabeçalho e ações dentro da viewport.
    maxHeight: `calc(100dvh - ${position.top + VIEWPORT_GUTTER}px)`,
  };
}
