import { cx } from "@/lib/cx";

export function Panel({
  children,
  className,
  flush,
}: {
  children: React.ReactNode;
  className?: string;
  flush?: boolean;
}) {
  return <section className={cx("ops-panel", !flush && "p-4", className)}>{children}</section>;
}

export function PanelTitle({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-3 flex items-start justify-between gap-2">
      <div>
        <h2 className="text-[14px] font-bold tracking-tight text-ink">{title}</h2>
        {hint ? <p className="mt-0.5 text-[12px] text-quiet">{hint}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function MetricCell({
  label,
  value,
  delta,
  tone,
  onClick,
}: {
  label: string;
  value: string | number;
  delta?: string;
  tone?: "good" | "bad" | "caution" | "neutral";
  onClick?: () => void;
}) {
  const toneCls =
    tone === "good" ? "text-good" : tone === "bad" ? "text-bad" : tone === "caution" ? "text-caution" : "text-ink";
  const Comp = onClick ? "button" : "div";
  return (
    <Comp
      type={onClick ? "button" : undefined}
      onClick={onClick}
      className={cx("min-w-0 px-4 py-4 text-left", onClick && "transition-colors hover:bg-accent-soft/40")}
    >
      <div className="text-[12px] font-bold uppercase tracking-[0.05em] text-quiet">{label}</div>
      <div className={cx("mt-1 text-[30px] font-bold leading-none tabular-nums tracking-tight", toneCls)}>{value}</div>
      {delta ? <div className="mt-1.5 text-[12px] text-quiet">{delta}</div> : null}
    </Comp>
  );
}

export function StatusSignal({ status }: { status: "online" | "degraded" | "offline" | "stale" | boolean }) {
  const normalized =
    typeof status === "boolean"
      ? status
        ? "online"
        : "offline"
      : status;
  const map = {
    online: { label: "Online", bar: "bg-good", text: "text-good", bg: "bg-good-soft" },
    degraded: { label: "Degradado", bar: "bg-caution", text: "text-caution", bg: "bg-caution-soft" },
    offline: { label: "Offline", bar: "bg-bad", text: "text-bad", bg: "bg-bad-soft" },
    stale: { label: "Sem inform", bar: "bg-rule-strong", text: "text-quiet", bg: "bg-panel-2" },
  }[normalized];
  return (
    <span className={cx("inline-flex items-center gap-1.5 rounded-full border border-current/20 px-2.5 py-1", map.bg)}>
      <span className={cx("h-1.5 w-1.5 rounded-full", map.bar)} />
      <span className={cx("text-[11px] font-bold uppercase", map.text)}>{map.label}</span>
    </span>
  );
}

export function Btn({
  children,
  variant = "primary",
  size = "md",
  className,
  type = "button",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md";
}) {
  return (
    <button
      type={type}
      className={cx(
        "inline-flex items-center justify-center gap-1.5 rounded-[5px] font-semibold transition focus-visible:outline-accent disabled:pointer-events-none disabled:opacity-45",
        size === "sm" ? "h-9 px-3 text-[12px]" : "h-10 px-4 text-[13px]",
        variant === "primary" && "bg-accent text-accent-fg hover:bg-accent-strong",
        variant === "outline" && "border border-rule bg-panel text-ink hover:bg-panel-2",
        variant === "ghost" && "text-ink-soft hover:bg-panel-2",
        variant === "danger" && "bg-bad text-white hover:opacity-90",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function FieldLabel({ children }: { children: React.ReactNode }) {
  return <span className="mb-1.5 block text-[12px] font-semibold text-ink-soft">{children}</span>;
}

export function Control({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cx(
        "h-10 w-full rounded-[5px] border border-rule bg-panel px-3 text-[13px] text-ink placeholder:text-quiet transition",
        "focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15",
        className,
      )}
      {...props}
    />
  );
}

export function SelectControl({ className, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cx(
        "h-10 w-full rounded-[5px] border border-rule bg-panel px-3 text-[13px] text-ink transition",
        "focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}

export function TextArea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cx(
        "min-h-24 w-full rounded-[5px] border border-rule bg-panel px-3 py-2.5 text-[13px] text-ink transition",
        "focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15",
        className,
      )}
      {...props}
    />
  );
}

export function PageHead({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="mb-1 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-[22px] font-bold tracking-tight text-ink">{title}</h1>
        {subtitle ? <p className="mt-1 text-[13px] text-ink-soft">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}
