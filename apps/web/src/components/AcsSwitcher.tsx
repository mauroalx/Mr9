"use client";

type Server = { id: string; name: string; is_default?: boolean };

export function AcsSwitcher({
  servers,
  value,
  onChange,
}: {
  servers: Server[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <select className="select" style={{ width: 220 }} value={value} onChange={(e) => onChange(e.target.value)} aria-label="ACS ativo">
      <option value="">ACS ativo…</option>
      {servers.map((s) => (
        <option key={s.id} value={s.id}>
          {s.name}
          {s.is_default ? " (default)" : ""}
        </option>
      ))}
    </select>
  );
}
