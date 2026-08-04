"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";

type Group = { id: string; name: string };
type User = { id: string; email: string; name: string; group_id: string | null; is_active: boolean };

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [form, setForm] = useState({ email: "", name: "", password: "", group_id: "" });
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setUsers(await api("/security/users"));
    setGroups(await api("/security/groups"));
  }

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api("/security/users", { method: "POST", body: JSON.stringify(form) });
      setForm({ email: "", name: "", password: "", group_id: form.group_id });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro");
    }
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div>
        <h1 style={{ margin: 0 }}>Usuários</h1>
        <p style={{ color: "var(--muted)" }}>Super Admin não é listado nem gerenciável aqui.</p>
      </div>
      {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}
      <form className="panel" onSubmit={onCreate}>
        <div className="field">
          <label>Nome</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div className="field">
          <label>E-mail</label>
          <input
            className="input"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </div>
        <div className="field">
          <label>Senha</label>
          <input
            className="input"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            minLength={8}
          />
        </div>
        <div className="field">
          <label>Grupo</label>
          <select className="select" value={form.group_id} onChange={(e) => setForm({ ...form, group_id: e.target.value })} required>
            <option value="">Selecione…</option>
            {groups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </div>
        <button className="btn" type="submit">
          Criar usuário
        </button>
      </form>
      <div className="panel" style={{ padding: 0 }}>
        <table className="table">
          <thead>
            <tr>
              <th>E-mail</th>
              <th>Nome</th>
              <th>Grupo</th>
              <th>Ativo</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="mono">{u.email}</td>
                <td>{u.name}</td>
                <td className="mono">{u.group_id || "—"}</td>
                <td>{u.is_active ? "sim" : "não"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
