"use client";

import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { HealthScore } from "@/components/HealthScore";
import { StatusBadge } from "@/components/StatusBadge";

type Report = {
  score: number;
  grade: string;
  tips: string[];
  checks: Array<{ id: string; title: string; status: string; penalty: number; summary: string }>;
  neighbors?: Array<{ ssid: string; channel?: number; rssi?: number; vendor?: string }>;
};

type Workbench = {
  wifi: Array<{ root: string; ssid: string; channel: string; enabled?: boolean }>;
  wan: Array<{ root: string; kind: string; name: string; username: string; connection_status: string; external_ip: string }>;
  dhcp: {
    lanIp?: string;
    subnetMask?: string;
    minAddress?: string;
    maxAddress?: string;
    dnsServers?: string;
    leaseTime?: number;
    enabled?: boolean;
  } | null;
  hosts: Array<{ hostname: string; ip: string; mac: string; active?: boolean }>;
  portmap: Array<{ root: string; externalPort?: number; internalPort?: number; internalClient?: string; protocol?: string; description?: string }>;
  neighbors: Array<{ ssid: string; channel?: number; rssi?: number; vendor?: string }>;
};

const TABS = ["resumo", "wifi", "wan", "dhcp", "hosts", "portmap", "tools", "diagnóstico"] as const;

export default function DeviceDetailPage() {
  const params = useParams<{ deviceId: string }>();
  const deviceId = decodeURIComponent(params.deviceId);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [wb, setWb] = useState<Workbench | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [history, setHistory] = useState<Array<{ id: string; score: number; grade: string; created_at?: string }>>([]);
  const [tab, setTab] = useState<(typeof TABS)[number]>("resumo");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tag, setTag] = useState("");
  const [toolHost, setToolHost] = useState("8.8.8.8");
  const [wifiForm, setWifiForm] = useState({ root: "", ssid: "", password: "" });
  const [wanForm, setWanForm] = useState({ root: "", username: "", password: "" });
  const [dhcpDns, setDhcpDns] = useState("");

  async function refresh() {
    const res = await api<{
      summary: Record<string, unknown>;
      workbench: Workbench;
    }>(`/acs/devices/${encodeURIComponent(deviceId)}`);
    setSummary(res.summary);
    setWb(res.workbench);
    if (res.workbench?.wifi?.[0] && !wifiForm.root) {
      setWifiForm({ root: res.workbench.wifi[0].root, ssid: res.workbench.wifi[0].ssid, password: "" });
    }
    if (res.workbench?.wan?.find((w) => w.kind === "ppp") && !wanForm.root) {
      const ppp = res.workbench.wan.find((w) => w.kind === "ppp")!;
      setWanForm({ root: ppp.root, username: ppp.username, password: "" });
    }
    if (res.workbench?.dhcp?.dnsServers) setDhcpDns(res.workbench.dhcp.dnsServers);
    const diag = await api<{ items: Array<{ id: string; score: number; grade: string; created_at?: string; report: Report }> }>(
      `/acs/devices/${encodeURIComponent(deviceId)}/diagnostics`,
    );
    setHistory(diag.items);
    if (diag.items[0]?.report) setReport(diag.items[0].report);
  }

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId]);

  async function runAction(name: string, params: Record<string, unknown> = {}) {
    setMsg(null);
    setError(null);
    try {
      const res = await api<{ ok?: boolean; report?: Report }>(`/acs/devices/${encodeURIComponent(deviceId)}/actions`, {
        method: "POST",
        body: JSON.stringify({ action: name, params }),
      });
      setMsg(`Ação ${name} ok`);
      if (res.report) setReport(res.report);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    }
  }

  function onWifi(e: FormEvent) {
    e.preventDefault();
    runAction("wifi_set", wifiForm);
  }
  function onWan(e: FormEvent) {
    e.preventDefault();
    runAction("wan_set_pppoe", wanForm);
  }
  function onDhcp(e: FormEvent) {
    e.preventDefault();
    runAction("dhcp_set", { dnsServers: dhcpDns });
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "start", flexWrap: "wrap" }}>
        <div>
          <h1 style={{ margin: 0 }} className="mono">
            {(summary?.serial as string) || deviceId}
          </h1>
          <p style={{ color: "var(--muted)" }}>
            {String(summary?.manufacturer || "")} · {String(summary?.product_class || "")}
          </p>
          <StatusBadge online={Boolean(summary?.online)} />
        </div>
        {report ? <HealthScore score={report.score} grade={report.grade} /> : null}
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button className="btn secondary" type="button" onClick={() => runAction("sync")}>
          Sync
        </button>
        <button className="btn secondary" type="button" onClick={() => runAction("reboot")}>
          Reboot
        </button>
        <button className="btn" type="button" onClick={() => runAction("diagnostic_full")}>
          Diagnóstico
        </button>
      </div>
      {msg ? <p style={{ color: "var(--ok)" }}>{msg}</p> : null}
      {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", borderBottom: "1px solid var(--line)", paddingBottom: 8 }}>
        {TABS.map((t) => (
          <button key={t} type="button" className={`btn ${tab === t ? "" : "secondary"}`} onClick={() => setTab(t)} style={{ textTransform: "capitalize" }}>
            {t}
          </button>
        ))}
      </div>

      {tab === "resumo" ? (
        <div className="panel">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 12 }}>
            <div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Software</div>
              <div className="mono">{String(summary?.software_version || "—")}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Último inform</div>
              <div className="mono" style={{ fontSize: 12 }}>
                {String(summary?.last_inform || "—")}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>Tags</div>
              <div className="mono">{((summary?.tags as string[]) || []).join(", ") || "—"}</div>
            </div>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              runAction("tags_add", { tag });
              setTag("");
            }}
            style={{ display: "flex", gap: 8, marginTop: 12 }}
          >
            <input className="input" placeholder="Nova tag" value={tag} onChange={(e) => setTag(e.target.value)} />
            <button className="btn secondary" type="submit">
              + tag
            </button>
          </form>
        </div>
      ) : null}

      {tab === "wifi" ? (
        <div className="panel" style={{ display: "grid", gap: 12 }}>
          <table className="table">
            <thead>
              <tr>
                <th>SSID</th>
                <th>Canal</th>
                <th>Root</th>
              </tr>
            </thead>
            <tbody>
              {(wb?.wifi || []).map((w) => (
                <tr key={w.root} style={{ cursor: "pointer" }} onClick={() => setWifiForm({ root: w.root, ssid: w.ssid, password: "" })}>
                  <td>{w.ssid}</td>
                  <td className="mono">{w.channel}</td>
                  <td className="mono" style={{ fontSize: 11 }}>
                    {w.root}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <form onSubmit={onWifi} style={{ display: "grid", gap: 8, maxWidth: 420 }}>
            <input className="input" value={wifiForm.root} onChange={(e) => setWifiForm({ ...wifiForm, root: e.target.value })} placeholder="root" />
            <input className="input" value={wifiForm.ssid} onChange={(e) => setWifiForm({ ...wifiForm, ssid: e.target.value })} placeholder="SSID" />
            <input className="input" type="password" value={wifiForm.password} onChange={(e) => setWifiForm({ ...wifiForm, password: e.target.value })} placeholder="Senha (opcional)" />
            <button className="btn" type="submit">
              Aplicar Wi‑Fi
            </button>
          </form>
        </div>
      ) : null}

      {tab === "wan" ? (
        <div className="panel" style={{ display: "grid", gap: 12 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Status</th>
                <th>User</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {(wb?.wan || []).map((w) => (
                <tr key={w.root} onClick={() => w.kind === "ppp" && setWanForm({ root: w.root, username: w.username, password: "" })} style={{ cursor: "pointer" }}>
                  <td>{w.kind}</td>
                  <td>{w.connection_status || w.name}</td>
                  <td className="mono">{w.username || "—"}</td>
                  <td className="mono">{w.external_ip || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <form onSubmit={onWan} style={{ display: "grid", gap: 8, maxWidth: 420 }}>
            <input className="input" value={wanForm.root} onChange={(e) => setWanForm({ ...wanForm, root: e.target.value })} placeholder="PPP root" />
            <input className="input" value={wanForm.username} onChange={(e) => setWanForm({ ...wanForm, username: e.target.value })} placeholder="usuário PPPoE" />
            <input className="input" type="password" value={wanForm.password} onChange={(e) => setWanForm({ ...wanForm, password: e.target.value })} placeholder="senha" />
            <button className="btn" type="submit">
              Aplicar PPPoE
            </button>
          </form>
        </div>
      ) : null}

      {tab === "dhcp" ? (
        <div className="panel" style={{ display: "grid", gap: 12 }}>
          <div className="mono" style={{ fontSize: 13 }}>
            LAN {wb?.dhcp?.lanIp || "—"} / {wb?.dhcp?.subnetMask || "—"}
            <br />
            pool {wb?.dhcp?.minAddress || "—"} → {wb?.dhcp?.maxAddress || "—"}
          </div>
          <form onSubmit={onDhcp} style={{ display: "flex", gap: 8, maxWidth: 520 }}>
            <input className="input" value={dhcpDns} onChange={(e) => setDhcpDns(e.target.value)} placeholder="DNSServers (vírgula)" />
            <button className="btn" type="submit">
              Salvar DNS
            </button>
          </form>
        </div>
      ) : null}

      {tab === "hosts" ? (
        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>Host</th>
                <th>IP</th>
                <th>MAC</th>
              </tr>
            </thead>
            <tbody>
              {(wb?.hosts || []).map((h, i) => (
                <tr key={`${h.mac}-${i}`}>
                  <td>{h.hostname || "—"}</td>
                  <td className="mono">{h.ip}</td>
                  <td className="mono">{h.mac}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "portmap" ? (
        <div className="panel">
          <table className="table">
            <thead>
              <tr>
                <th>Ext</th>
                <th>Int</th>
                <th>Proto</th>
                <th>Destino</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(wb?.portmap || []).map((m) => (
                <tr key={m.root}>
                  <td className="mono">{m.externalPort}</td>
                  <td className="mono">{m.internalPort}</td>
                  <td>{m.protocol}</td>
                  <td className="mono">{m.internalClient}</td>
                  <td>
                    <button className="btn secondary" type="button" onClick={() => runAction("port_mapping_delete", { root: m.root })}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "tools" ? (
        <div className="panel" style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "end" }}>
          <input className="input" style={{ maxWidth: 220 }} value={toolHost} onChange={(e) => setToolHost(e.target.value)} />
          <button className="btn secondary" type="button" onClick={() => runAction("ping", { host: toolHost })}>
            Ping (queue)
          </button>
          <button className="btn secondary" type="button" onClick={() => runAction("traceroute", { host: toolHost })}>
            Traceroute (queue)
          </button>
        </div>
      ) : null}

      {tab === "diagnóstico" ? (
        <>
          {report ? (
            <div className="panel">
              <h3 style={{ marginTop: 0 }}>
                Score {report.score} ({report.grade})
              </h3>
              <div style={{ display: "grid", gap: 8 }}>
                {report.checks.map((c) => (
                  <div key={c.id} style={{ display: "flex", justifyContent: "space-between", gap: 12, borderBottom: "1px solid #eef3f4", paddingBottom: 8 }}>
                    <div>
                      <strong>{c.title}</strong>
                      <div style={{ fontSize: 13, color: "var(--muted)" }}>{c.summary}</div>
                    </div>
                    <span className={`badge ${c.status === "ok" ? "ok" : c.status === "warn" ? "warn" : "crit"}`}>
                      {c.status} {c.penalty ? `+${c.penalty}pt` : ""}
                    </span>
                  </div>
                ))}
              </div>
              {(report.neighbors || wb?.neighbors || []).length ? (
                <div style={{ marginTop: 12 }}>
                  <strong>Redes vizinhas</strong>
                  <ul>
                    {(report.neighbors || wb?.neighbors || []).slice(0, 20).map((n) => (
                      <li key={`${n.ssid}-${n.vendor}-${n.channel}`}>
                        {n.ssid} · ch {n.channel} · {n.rssi} dBm · {n.vendor}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {report.tips?.length ? (
                <ul>
                  {report.tips.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : (
            <p style={{ color: "var(--muted)" }}>Nenhum diagnóstico ainda.</p>
          )}
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Histórico</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>Quando</th>
                  <th>Score</th>
                  <th>Grade</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id}>
                    <td className="mono">{h.created_at || "—"}</td>
                    <td>{h.score}</td>
                    <td>{h.grade}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </div>
  );
}
