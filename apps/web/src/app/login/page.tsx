"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, setTokens } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const tokens = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email, password }),
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 420, margin: "10vh auto", padding: 16 }}>
      <div className="panel">
        <h1 style={{ marginTop: 0 }}>
          Mr<span style={{ color: "var(--brand)" }}>9</span>
        </h1>
        <p style={{ color: "var(--muted)" }}>Acesso ao painel micro-ACS.</p>
        <form onSubmit={onSubmit}>
          <div className="field">
            <label>E-mail</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Senha</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}
          <button className="btn" disabled={loading} type="submit">
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 16 }}>
          Primeira vez? Conclua o <a href="/setup">wizard de instalação</a>.
        </p>
      </div>
    </main>
  );
}
