"use client";

import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart } from "recharts";
import { api } from "@/lib/api";
import { KpiStrip } from "@/components/KpiStrip";

type Summary = {
  kpis: {
    acs_servers: number;
    online: number;
    offline: number;
    diagnostics_24h: number;
    avg_score_24h: number;
  };
  top_models: Array<{ product_class: string; count: number }>;
  series_24h: Array<{ hour: string; avg_score: number; count: number }>;
  series_7d: Array<{ day: string; avg_score: number; count: number }>;
};

export default function DashboardPage() {
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Summary>("/dashboard/summary")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const k = data?.kpis;
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div>
        <h1 style={{ margin: 0 }}>Dashboard</h1>
        <p style={{ color: "var(--muted)", marginTop: 4 }}>Visão operacional estilo BI · frota ACS</p>
      </div>
      {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}
      <KpiStrip
        items={[
          { label: "Servidores ACS", value: k?.acs_servers ?? "—" },
          { label: "Online", value: k?.online ?? "—", tone: "ok" },
          { label: "Offline", value: k?.offline ?? "—", tone: "crit" },
          { label: "Diagnósticos 24h", value: k?.diagnostics_24h ?? "—" },
          { label: "Score médio 24h", value: k?.avg_score_24h ?? "—" },
        ]}
      />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 16 }}>
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>Score médio · 24h</h3>
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer>
              <LineChart data={data?.series_24h || []}>
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="avg_score" stroke="#0f766e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>Score médio · 7d</h3>
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer>
              <LineChart data={data?.series_7d || []}>
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="avg_score" stroke="#14b8a6" strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Top modelos</h3>
        <div style={{ width: "100%", height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={data?.top_models || []}>
              <XAxis dataKey="product_class" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
