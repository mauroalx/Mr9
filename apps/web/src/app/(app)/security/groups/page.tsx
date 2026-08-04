"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";

type Group = { id: string; name: string; permissions: string[] };

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [catalog, setCatalog] = useState<string[]>([]);
  const [name, setName] = useState("");
  const [perms, setPerms] = useState<string[]>(["acs.access", "dashboard.view"]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const rows = await api<Group[]>("/security/groups");
    setGroups(rows);
    const cat = await api<{ all: string[] }>("/auth/permissions-catalog");
    setCatalog(cat.all);
  }

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api("/security/groups", { method: "POST", body: JSON.stringify({ name, permissions: perms }) });
      setName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro");
    }
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div>
        <h1 style={{ margin: 0 }}>Grupos</h1>
        <p style={{ color: "var(--muted)" }}>ACL grupo → usuário (padrão MasterOLT). Super Admin não usa grupo.</p>
      </div>
      {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}
      <form className="panel" onSubmit={onCreate}>
        <div className="field">
          <label>Nome do grupo</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>Permissões</label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            {catalog.map((p) => (
              <label key={p} style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
                <input
                  type="checkbox"
                  checked={perms.includes(p)}
                  onChange={(e) => {
                    setPerms((prev) => (e.target.checked ? [...prev, p] : prev.filter((x) => x !== p)));
                  }}
                />
                <span className="mono">{p}</span>
              </label>
            ))}
          </div>
        </div>
        <button className="btn" type="submit">
          Criar grupo
        </button>
      </form>
      <div className="panel" style={{ padding: 0 }}>
        <table className="table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Permissões</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.id}>
                <td>{g.name}</td>
                <td className="mono" style={{ fontSize: 12 }}>
                  {g.permissions.join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
