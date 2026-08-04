"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getToken, setTokens } from "@/lib/api";
import { Mr9Mark } from "@/components/brand/Mr9Mark";
import { Btn, Control, TextArea } from "@/components/ops/primitives";

type Status = { installed: boolean; has_superadmin: boolean; acs_servers: number };

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [admin, setAdmin] = useState({ email: "", name: "", password: "" });
  const [settings, setSettings] = useState({
    timezone: "America/Sao_Paulo",
    approved_dns: "1.1.1.1\n8.8.8.8",
    online_threshold_s: 300,
  });
  const [acs, setAcs] = useState({
    name: "GenieACS principal",
    base_url: "http://127.0.0.1:7557",
    bearer_token: "",
    verify_tls: false,
  });

  useEffect(() => {
    api<Status>("/setup/status", { auth: false })
      .then((s) => {
        if (s.installed) router.push("/login");
        if (s.has_superadmin && !getToken()) {
          router.replace("/login");
          return;
        }
        if (s.has_superadmin) setStep(2);
        if (s.acs_servers > 0) setStep(4);
      })
      .catch((e) => setError(String(e.message || e)));
  }, [router]);

  async function createAdmin() {
    setError(null);
    const tokens = await api<{ access_token: string; refresh_token: string }>("/setup/superadmin", {
      method: "POST",
      auth: false,
      body: JSON.stringify(admin),
    });
    setTokens(tokens.access_token, tokens.refresh_token);
    setStep(2);
  }

  async function saveSettings() {
    setError(null);
    await api("/setup/settings", {
      method: "POST",
      body: JSON.stringify({
        timezone: settings.timezone,
        approved_dns: settings.approved_dns
          .split(/\n|,/)
          .map((s) => s.trim())
          .filter(Boolean),
        online_threshold_s: settings.online_threshold_s,
      }),
    });
    setStep(3);
  }

  async function saveAcs() {
    setError(null);
    await api("/setup/acs-server", {
      method: "POST",
      body: JSON.stringify({
        ...acs,
        bearer_token: acs.bearer_token.trim() ? acs.bearer_token : null,
      }),
    });
    setStep(4);
  }

  async function complete() {
    setError(null);
    await api("/setup/complete", { method: "POST", body: "{}" });
    router.push("/login");
  }

  const steps = ["Admin", "Config", "ACS", "Fim"];

  return (
    <main className="grid min-h-screen place-items-center bg-canvas px-4 py-8">
      <div className="w-full max-w-lg rounded-[8px] border border-rule bg-white p-7 text-ink shadow-panel">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Mr9Mark className="h-8 w-8 text-accent" />
            <div>
              <h1 className="text-[17px] font-bold">Instalação</h1>
              <p className="text-[12px] text-quiet">Passo {step} de 4</p>
            </div>
          </div>
        </div>

        <div className="mb-5 grid grid-cols-4 gap-1.5">
          {steps.map((label, i) => (
            <div key={label} className="grid gap-1">
              <div className={`h-1 rounded-full ${i + 1 <= step ? "bg-accent" : "bg-rule"}`} />
              <span className={`text-[12px] font-semibold ${i + 1 <= step ? "text-accent-strong" : "text-quiet"}`}>
                {label}
              </span>
            </div>
          ))}
        </div>

        {error ? <p className="mb-3 rounded-[5px] border border-bad/20 bg-bad-soft px-3 py-2 text-[13px] text-bad">{error}</p> : null}

        {step === 1 ? (
          <section className="grid gap-3">
            <h2 className="text-[14px] font-bold">Super Admin</h2>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">Nome</span>
              <Control
                value={admin.name}
                onChange={(e) => setAdmin({ ...admin, name: e.target.value })}
              />
            </label>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">E-mail</span>
              <Control
                type="email"
                value={admin.email}
                onChange={(e) => setAdmin({ ...admin, email: e.target.value })}
              />
            </label>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">Senha</span>
              <Control
                type="password"
                value={admin.password}
                onChange={(e) => setAdmin({ ...admin, password: e.target.value })}
              />
            </label>
            <Btn onClick={() => createAdmin().catch((e) => setError(e.message))}>Continuar</Btn>
          </section>
        ) : null}

        {step === 2 ? (
          <section className="grid gap-3">
            <h2 className="text-[14px] font-bold">Configurações</h2>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">Timezone</span>
              <Control
                value={settings.timezone}
                onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
              />
            </label>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">DNS aprovados</span>
              <TextArea
                value={settings.approved_dns}
                onChange={(e) => setSettings({ ...settings, approved_dns: e.target.value })}
              />
            </label>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">Limiar online (s)</span>
              <Control
                type="number"
                value={settings.online_threshold_s}
                onChange={(e) => setSettings({ ...settings, online_threshold_s: Number(e.target.value) })}
              />
            </label>
            <Btn onClick={() => saveSettings().catch((e) => setError(e.message))}>Continuar</Btn>
          </section>
        ) : null}

        {step === 3 ? (
          <section className="grid gap-3">
            <h2 className="text-[14px] font-bold">GenieACS</h2>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">Nome</span>
              <Control
                value={acs.name}
                onChange={(e) => setAcs({ ...acs, name: e.target.value })}
              />
            </label>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">URL</span>
              <Control
                value={acs.base_url}
                onChange={(e) => setAcs({ ...acs, base_url: e.target.value })}
              />
            </label>
            <label className="grid gap-1">
              <span className="text-[12px] font-semibold text-ink-soft">Bearer token</span>
              <Control
                type="password"
                placeholder="Opcional"
                value={acs.bearer_token}
                onChange={(e) => setAcs({ ...acs, bearer_token: e.target.value })}
              />
            </label>
            <Btn onClick={() => saveAcs().catch((e) => setError(e.message))}>Testar e salvar</Btn>
          </section>
        ) : null}

        {step === 4 ? (
          <section className="grid gap-3">
            <h2 className="text-[14px] font-bold">Concluir</h2>
            <p className="text-[13px] text-ink-soft">Instalação pronta. Faça login com o Super Admin.</p>
            <Btn onClick={() => complete().catch((e) => setError(e.message))}>Ir para o login</Btn>
          </section>
        ) : null}
      </div>
    </main>
  );
}
