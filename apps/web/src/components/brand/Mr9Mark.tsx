import { cx } from "@/lib/cx";

export function Mr9Mark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      aria-hidden="true"
      className={cx("h-8 w-8 shrink-0", className)}
    >
      <path
        d="M25 13a9 9 0 1 0-9 9 9 9 0 0 0 9-9Zm0 0v7c0 5-3 8-8 8h-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="25" cy="13" r="2.25" fill="currentColor" />
      <circle cx="13" cy="28" r="2.25" fill="currentColor" />
    </svg>
  );
}
