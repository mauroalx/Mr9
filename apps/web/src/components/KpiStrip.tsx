type Kpi = { label: string; value: string | number; tone?: "ok" | "warn" | "crit" | "default" };

export function KpiStrip({ items }: { items: Kpi[] }) {
  return (
    <div className="kpi-strip">
      {items.map((k) => (
        <div className="kpi" key={k.label}>
          <div className="label">{k.label}</div>
          <div className="value" style={k.tone && k.tone !== "default" ? { color: `var(--${k.tone})` } : undefined}>
            {k.value}
          </div>
        </div>
      ))}
    </div>
  );
}
