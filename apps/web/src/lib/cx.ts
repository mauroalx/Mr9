/** Helpers de composição — sem Tailwind “utility soup” espalhada nas páginas. */

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
