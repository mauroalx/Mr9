"use client";

import { FormEvent, useEffect, useState } from "react";
import { Btn, Control, FieldLabel, PageHead, Panel, PanelTitle, TextArea } from "@/components/ops/primitives";
import { api } from "@/lib/api";

type Settings = {
  timezone: string;
  locale: string;
  approved_dns: string[];
  online_threshold_s: number;
  diagnostic_cooldown_s: number;
  diagnostic_timeout_s: number;
};

export default function AdminGeneralPage() {
  const [form, setForm] = useState<Settings | null>(null);
  const [dnsText, setDnsText] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

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
    setSaving(true);
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
      setMsg("Configurações salvas.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro");
    } finally {
      setSaving(false);
    }
  }

  if (!form) {
    return <p className="text-[13px] text-quiet">{error || "Carregando…"}</p>;
  }

  return (
    <div className="grid max-w-[640px] gap-3">
      <PageHead
        title="Geral"
        subtitle="Valores usados pelo diagnóstico (DNS, limiares). Configuráveis pós-wizard."
      />
      {msg ? <p className="text-[13px] text-good">{msg}</p> : null}
      {error ? <p className="text-[13px] text-bad">{error}</p> : null}

      <Panel>
        <PanelTitle title="Parâmetros globais" />
        <form className="grid gap-3" onSubmit={onSave}>
          <div>
            <FieldLabel>Timezone</FieldLabel>
            <Control
              value={form.timezone}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
            />
          </div>
          <div>
            <FieldLabel>Locale</FieldLabel>
            <Control value={form.locale} onChange={(e) => setForm({ ...form, locale: e.target.value })} />
          </div>
          <div>
            <FieldLabel>DNS aprovados</FieldLabel>
            <TextArea
              rows={5}
              value={dnsText}
              onChange={(e) => setDnsText(e.target.value)}
              placeholder="Um por linha ou separados por vírgula"
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <FieldLabel>Limiar online (s)</FieldLabel>
              <Control
                type="number"
                value={form.online_threshold_s}
                onChange={(e) => setForm({ ...form, online_threshold_s: Number(e.target.value) })}
              />
            </div>
            <div>
              <FieldLabel>Cooldown diag. (s)</FieldLabel>
              <Control
                type="number"
                value={form.diagnostic_cooldown_s}
                onChange={(e) => setForm({ ...form, diagnostic_cooldown_s: Number(e.target.value) })}
              />
            </div>
            <div>
              <FieldLabel>Timeout diag. (s)</FieldLabel>
              <Control
                type="number"
                value={form.diagnostic_timeout_s}
                onChange={(e) => setForm({ ...form, diagnostic_timeout_s: Number(e.target.value) })}
              />
            </div>
          </div>
          <div className="flex justify-end pt-1">
            <Btn type="submit" disabled={saving}>
              Salvar
            </Btn>
          </div>
        </form>
      </Panel>
    </div>
  );
}
