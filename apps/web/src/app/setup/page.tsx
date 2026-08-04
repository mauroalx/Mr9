"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Status = { installed: boolean; has_superadmin: boolean; acs_servers: number };

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [status, setStatus] = useState<Status | null>(null);
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
        setStatus(s);
        if (s.installed) router.push("/login");
        if (s.has_superadmin) setStep(2);
        if (s.acs_servers > 0) setStep(4);
      })
      .catch((e) => setError(String(e.message || e)));
  }, [router]);

  async function createAdmin() {
    setError(null);
    await api("/setup/superadmin", { method: "POST", auth: false, body: JSON.stringify(admin) });
    setStep(2);
  }

  async function saveSettings() {
    setError(null);
    await api("/setup/settings", {
      method: "POST",
      auth: false,
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
    await api("/setup/acs-server", { method: "POST", auth: false, body: JSON.stringify(acs) });
    setStep(4);
  }

  async function complete() {
    setError(null);
    await api("/setup/complete", { method: "POST", auth: false, body: "{}" });
    router.push("/login");
  }

  return (
    <main style={{ maxWidth: 640, margin: "6vh auto", padding: 16 }}>
      <div className="panel">
        <h1 style={{ marginTop: 0 }}>Instalação Mr9</h1>
        <p style={{ color: "var(--muted)" }}>
          Wizard para VPS · passo {step}/4 {status?.installed ? "(já instalado)" : ""}
        </p>
        {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}

        {step === 1 ? (
          <section>
            <h3>1. Super Admin</h3>
            <p style={{ fontSize: 13, color: "var(--muted)" }}>
              Conta de sistema com acesso total. Não aparece no CRUD de usuários.
            </p>
            <div className="field">
              <label>Nome</label>
              <input className="input" value={admin.name} onChange={(e) => setAdmin({ ...admin, name: e.target.value })} />
            </div>
            <div className="field">
              <label>E-mail</label>
              <input className="input" type="email" value={admin.email} onChange={(e) => setAdmin({ ...admin, email: e.target.value })} />
            </div>
            <div className="field">
              <label>Senha</label>
              <input
                className="input"
                type="password"
                value={admin.password}
                onChange={(e) => setAdmin({ ...admin, password: e.target.value })}
              />
            </div>
            <button className="btn" type="button" onClick={() => createAdmin().catch((e) => setError(e.message))}>
              Continuar
            </button>
          </section>
        ) : null}

        {step === 2 ? (
          <section>
            <h3>2. Settings operacionais</h3>
            <div className="field">
              <label>Timezone</label>
              <input className="input" value={settings.timezone} onChange={(e) => setSettings({ ...settings, timezone: e.target.value })} />
            </div>
            <div className="field">
              <label>DNS aprovados (um por linha)</label>
              <textarea
                className="textarea"
                rows={4}
                value={settings.approved_dns}
                onChange={(e) => setSettings({ ...settings, approved_dns: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Limiar online (segundos)</label>
              <input
                className="input"
                type="number"
                value={settings.online_threshold_s}
                onChange={(e) => setSettings({ ...settings, online_threshold_s: Number(e.target.value) })}
              />
            </div>
            <button className="btn" type="button" onClick={() => saveSettings().catch((e) => setError(e.message))}>
              Continuar
            </button>
          </section>
        ) : null}

        {step === 3 ? (
          <section>
            <h3>3. Servidor GenieACS (NBI)</h3>
            <p style={{ fontSize: 13, color: "var(--muted)" }}>O token fica cifrado no backend. O browser não chama o NBI.</p>
            <div className="field">
              <label>Nome</label>
              <input className="input" value={acs.name} onChange={(e) => setAcs({ ...acs, name: e.target.value })} />
            </div>
            <div className="field">
              <label>URL NBI</label>
              <input className="input" value={acs.base_url} onChange={(e) => setAcs({ ...acs, base_url: e.target.value })} />
            </div>
            <div className="field">
              <label>Bearer token</label>
              <input
                className="input"
                type="password"
                value={acs.bearer_token}
                onChange={(e) => setAcs({ ...acs, bearer_token: e.target.value })}
              />
            </div>
            <button className="btn" type="button" onClick={() => saveAcs().catch((e) => setError(e.message))}>
              Testar e salvar
            </button>
          </section>
        ) : null}

        {step === 4 ? (
          <section>
            <h3>4. Concluir</h3>
            <p>Pronto para operar. Faça login com o Super Admin.</p>
            <button className="btn" type="button" onClick={() => complete().catch((e) => setError(e.message))}>
              Ir para login
            </button>
          </section>
        ) : null}
      </div>
    </main>
  );
}
