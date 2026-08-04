"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DeviceRow, DeviceRowData } from "@/components/DeviceRow";

export default function DevicesPage() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<DeviceRowData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load(search?: string) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      params.set("limit", "100");
      const res = await api<{ items: DeviceRowData[] }>(`/acs/devices?${params}`);
      setItems(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    load(q);
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "end" }}>
        <div>
          <h1 style={{ margin: 0 }}>Dispositivos</h1>
          <p style={{ color: "var(--muted)", marginTop: 4 }}>Inventário GenieACS via API Mr9</p>
        </div>
        <form onSubmit={onSearch} style={{ display: "flex", gap: 8 }}>
          <input className="input" placeholder="Serial / _id" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="btn" type="submit" disabled={loading}>
            Buscar
          </button>
        </form>
      </div>
      {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}
      <div className="panel" style={{ padding: 0, overflow: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Serial</th>
              <th>Modelo</th>
              <th>SW</th>
              <th>Último inform</th>
            </tr>
          </thead>
          <tbody>
            {items.map((d) => (
              <DeviceRow key={d.id} device={d} />
            ))}
            {!items.length && !loading ? (
              <tr>
                <td colSpan={5} style={{ color: "var(--muted)" }}>
                  Nenhum dispositivo.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
