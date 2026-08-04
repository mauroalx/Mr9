"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";

type Settings = {
  timezone: string;
  locale: string;
  approved_dns: string[];
  online_threshold_s: number;
  diagnostic_cooldown_s: number;
  diagnostic_timeout_s: number;
};

export default function SettingsPage() {
  const [form, setForm] = useState<Settings | null>(null);
  const [dnsText, setDnsText] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Settings>("/settings")
      .then((s) => {
        setForm(s);
        setDnsText((s.approved_dns || []).join("\n"));
      })
      .catch((e) => setError(e.message));
  }, []);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setMsg(null);
    setError(null);
    try {
      const saved = await api<Settings>("/settings", {
        method: "PATCH",
        body: JSON.stringify({
          ...form,
          approved_dns: dnsText
            .split(/\n|,/)
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      });
      setForm(saved);
      setDnsText((saved.approved_dns || []).join("\n"));
      setMsg("Settings salvos.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro");
    }
  }

  if (!form) return <p>{error || "Carregando…"}</p>;

  return (
    <div style={{ maxWidth: 640, display: "grid", gap: 16 }}>
      <div>
        <h1 style={{ margin: 0 }}>Settings</h1>
        <p style={{ color: "var(--muted)" }}>Valores usados pelo diagnóstico (DNS, limiares). Configuráveis pós-wizard.</p>
      </div>
      <form className="panel" onSubmit={onSave}>
        <div className="field">
          <label>Timezone</label>
          <input className="input" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
        </div>
        <div className="field">
          <label>Locale</label>
          <input className="input" value={form.locale} onChange={(e) => setForm({ ...form, locale: e.target.value })} />
        </div>
        <div className="field">
          <label>DNS aprovados</label>
          <textarea className="textarea" rows={5} value={dnsText} onChange={(e) => setDnsText(e.target.value)} />
        </div>
        <div className="field">
          <label>Limiar online (s)</label>
          <input
            className="input"
            type="number"
            value={form.online_threshold_s}
            onChange={(e) => setForm({ ...form, online_threshold_s: Number(e.target.value) })}
          />
        </div>
        {msg ? <p style={{ color: "var(--ok)" }}>{msg}</p> : null}
        {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}
        <button className="btn" type="submit">
          Salvar
        </button>
      </form>
    </div>
  );
}
