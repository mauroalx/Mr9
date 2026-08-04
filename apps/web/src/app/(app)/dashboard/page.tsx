"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowRight,
  BarChart3,
  ChevronDown,
  Clock3,
  RefreshCw,
  Server,
  TriangleAlert,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { cx } from "@/lib/cx";
import { Panel, StatusSignal } from "@/components/ops/primitives";

type Summary = {
  kpis: {
    acs_servers: number;
    online: number;
    offline: number;
    stale_24h: number;
    firmware_known: number;
    acs_metrics_available: boolean;
    diagnostics_24h: number;
    avg_score_24h: number;
  };
  top_models: Array<{ product_class: string; count: number }>;
  manufacturers: Array<{ name: string; count: number }>;
  series_24h: Array<{ hour: string; avg_score: number; count: number }>;
};

type Device = {
  id: string;
  serial?: string;
  manufacturer?: string;
  product_class?: string;
  software_version?: string;
  online?: boolean;
  last_inform?: string;
};
type AcsServer = {
  id: string;
  name: string;
  credentials_ok?: boolean;
  has_bearer?: boolean;
};
const palette = ["#287da5", "#51b99a", "#e8a051", "#9eacb4", "#7f70b5"];

function Module({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Panel flush className={cx("overflow-hidden", className)}>
      <header className="flex min-h-14 items-center justify-between gap-3 border-b border-rule bg-panel-2 px-4">
        <div>
          <h2 className="text-[14px] font-bold">{title}</h2>
          {subtitle ? (
            <p className="mt-0.5 text-[12px] text-quiet">{subtitle}</p>
          ) : null}
        </div>
        {action}
      </header>
      {children}
    </Panel>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-28 place-items-center px-4 py-6 text-center text-[13px] text-quiet">
      {children}
    </div>
  );
}

function Skeleton({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cx("block animate-pulse rounded-[4px] bg-panel-2", className)}
    />
  );
}

function KpiSkeleton({ featured = false }: { featured?: boolean }) {
  return (
    <div className="min-h-28 border-b border-r border-rule px-4 py-4 xl:border-b-0">
      <Skeleton className="h-3 w-24" />
      <Skeleton className={cx("mt-3 h-7", featured ? "w-28" : "w-16")} />
      <Skeleton className="mt-3 h-3 w-32 max-w-full" />
    </div>
  );
}

function ChartSkeleton({ compact = false }: { compact?: boolean }) {
  return (
    <div className={cx("animate-pulse p-4", compact ? "min-h-[220px]" : "h-[300px]")}>
      <Skeleton className="h-6 w-24" />
      <div className="mt-5 flex h-[75%] items-end gap-3 border-b border-rule px-2">
        {[38, 54, 46, 68, 61, 78, 70, 85, 76, 92, 84, 96].map((height, index) => (
          <span
            key={index}
            className="flex-1 rounded-t-[3px] bg-accent-soft"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function ListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="divide-y divide-rule" aria-hidden="true">
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="flex animate-pulse items-center gap-3 px-4 py-3">
          <Skeleton className="h-8 w-1 shrink-0" />
          <div className="min-w-0 flex-1">
            <Skeleton className="h-3 w-2/3" />
            <Skeleton className="mt-2 h-2.5 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<Summary | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [servers, setServers] = useState<AcsServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<6 | 12 | 24>(24);
  const [periodOpen, setPeriodOpen] = useState(false);
  const periodRef = useRef<HTMLDivElement>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [summary, inventory, acs] = await Promise.allSettled([
        api<Summary>("/dashboard/summary"),
        api<{ items: Device[] }>("/acs/devices?online=false&limit=5"),
        api<AcsServer[]>("/acs/servers"),
      ]);
      if (summary.status === "rejected") throw summary.reason;
      setData(summary.value);
      setDevices(inventory.status === "fulfilled" ? inventory.value.items || [] : []);
      setServers(acs.status === "fulfilled" ? acs.value : []);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Falha ao carregar o dashboard",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    function closePeriod(event: MouseEvent) {
      if (!periodRef.current?.contains(event.target as Node))
        setPeriodOpen(false);
    }
    document.addEventListener("mousedown", closePeriod);
    return () => document.removeEventListener("mousedown", closePeriod);
  }, []);

  const online = data?.kpis.online ?? 0;
  const offline = data?.kpis.offline ?? 0;
  const total = online + offline;
  const manufacturerData = (data?.manufacturers || []).map((item) => ({
    name: item.name,
    value: item.count,
  }));
  const firmwareKnown = data?.kpis.firmware_known ?? 0;
  const firmwareUnknown = Math.max(total - firmwareKnown, 0);
  const firmwareCoverage = total
    ? Math.round((firmwareKnown / total) * 100)
    : 0;
  const firmwareData = [
    { name: "Identificados", value: firmwareKnown },
    { name: "Sem versão", value: firmwareUnknown },
  ];
  const attention = devices
    .filter((device) => device.online === false)
    .slice(0, 5);
  const periodSeries = (data?.series_24h || []).slice(-period);
  const periodTotal = periodSeries.reduce((sum, point) => sum + point.count, 0);
  const initialLoading = loading && !data;

  const kpis = [
    {
      label: "Dispositivos",
      value: data?.kpis.acs_metrics_available ? total : "—",
      hint: `${data?.kpis.acs_servers ?? 0} instâncias ACS`,
      tone: "info",
      href: "/devices",
    },
    {
      label: "Online agora",
      value: data?.kpis.acs_metrics_available ? online : "—",
      hint: total
        ? `${((online / total) * 100).toFixed(1)}% da frota`
        : "Aguardando dados",
      tone: "good",
      href: "/devices?online=1",
    },
    {
      label: "Offline",
      value: data?.kpis.acs_metrics_available ? offline : "—",
      hint: total
        ? `${((offline / total) * 100).toFixed(1)}% da frota`
        : "Aguardando dados",
      tone: "bad",
      href: "/devices?online=0",
    },
    {
      label: "Diagnósticos 24h",
      value: data?.kpis.diagnostics_24h ?? 0,
      hint: `Score médio ${data?.kpis.avg_score_24h ?? 0}`,
      tone: "info",
      href: "/devices",
    },
    {
      label: "Sem inform > 24h",
      value: data?.kpis.acs_metrics_available ? data.kpis.stale_24h : "—",
      hint:
        data?.kpis.acs_metrics_available && total
          ? `${((data.kpis.stale_24h / total) * 100).toFixed(1)}% da frota`
          : "ACS indisponível",
      tone: "bad",
      href: "/devices",
    },
    {
      label: "Tarefas com falha",
      value: "—",
      hint: "Fila não exposta",
      tone: "neutral",
      href: "/tasks",
    },
  ];

  return (
    <div className="space-y-4" aria-busy={initialLoading}>
      <div className="flex flex-wrap items-center justify-between gap-4 px-1">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[22px] font-bold tracking-tight">
              Central de operação
            </h1>
            <span className="rounded border border-good/25 bg-good-soft px-2 py-0.5 text-[11px] font-bold uppercase text-good">
              Ao vivo
            </span>
          </div>
          <p className="mt-1 text-[13px] text-ink-soft">
            Saúde da frota, ACS, informs e operação diária
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative" ref={periodRef}>
            <button
              className="flex h-10 items-center gap-2 rounded-[5px] border border-rule bg-white px-3 text-[13px] font-semibold transition hover:bg-panel-2"
              onClick={() => setPeriodOpen((open) => !open)}
              aria-expanded={periodOpen}
              aria-haspopup="listbox"
            >
              <Clock3 size={14} />
              Últimas {period} horas
              <ChevronDown
                size={13}
                className={periodOpen ? "rotate-180" : ""}
              />
            </button>
            {periodOpen ? (
              <div
                role="listbox"
                className="absolute right-0 top-11 z-30 w-48 overflow-hidden rounded-[7px] border border-rule bg-white py-1 shadow-xl"
              >
                {([6, 12, 24] as const).map((option) => (
                  <button
                    key={option}
                    role="option"
                    aria-selected={period === option}
                    className={cx(
                      "flex w-full items-center justify-between px-3 py-2.5 text-left text-[13px] transition hover:bg-panel-2",
                      period === option &&
                        "bg-accent-soft font-bold text-accent",
                    )}
                    onClick={() => {
                      setPeriod(option);
                      setPeriodOpen(false);
                    }}
                  >
                    Últimas {option} horas
                    {period === option ? (
                      <span className="h-2 w-2 rounded-full bg-accent" />
                    ) : null}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <button
            className="grid h-10 w-10 place-items-center rounded-[5px] border border-rule bg-white text-quiet"
            onClick={load}
            disabled={loading}
            aria-label="Atualizar"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          </button>
          <button
            className="flex h-10 items-center gap-2 rounded-[5px] bg-accent px-4 text-[13px] font-bold text-white hover:bg-accent-strong"
            onClick={() => router.push("/devices")}
          >
            Abrir inventário
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
      {error ? (
        <div className="rounded-[5px] border border-bad/20 bg-bad-soft px-3 py-2 text-[13px] text-bad">
          {error}
        </div>
      ) : null}

      <section className="grid overflow-hidden rounded-[7px] border border-rule bg-white shadow-panel sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        {initialLoading
          ? Array.from({ length: 6 }, (_, index) => (
              <div key={index} className={index < 2 ? "xl:col-span-2" : "xl:col-span-1"}>
                <KpiSkeleton featured={index < 2} />
              </div>
            ))
          : kpis.map((item, index) => (
          <Link
            key={item.label}
            href={item.href}
            className={cx(
              "min-h-28 border-b border-r border-rule px-4 py-4 transition hover:bg-accent-soft/35 xl:border-b-0",
              index < 2 ? "xl:col-span-2" : "xl:col-span-1",
            )}
          >
            <div className="text-[12px] font-bold uppercase tracking-[.05em] text-quiet">
              {item.label}
            </div>
            <div className="mt-2 flex items-baseline justify-between gap-2">
              <strong
                className={
                  index < 2
                    ? "text-[28px] tracking-tight"
                    : "text-[24px] tracking-tight"
                }
              >
                {item.value}
              </strong>
              <span
                className={cx(
                  "text-[12px] font-bold",
                  item.tone === "good"
                    ? "text-good"
                    : item.tone === "bad"
                      ? "text-bad"
                      : item.tone === "info"
                        ? "text-signal"
                        : "text-quiet",
                )}
              >
                {index === 1 && total
                  ? `${((online / total) * 100).toFixed(1)}%`
                  : index === 2 && total
                    ? `${((offline / total) * 100).toFixed(1)}%`
                    : ""}
              </span>
            </div>
            <p className="mt-1 text-[12px] text-quiet">{item.hint}</p>
          </Link>
            ))}
      </section>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_330px]">
        <div className="grid gap-3 lg:grid-cols-2">
          <Module
            title="Diagnósticos processados"
            subtitle={`Execuções registradas nas últimas ${period} horas`}
            action={
              <span className="flex items-center gap-1.5 text-[12px] text-quiet">
                <i className="h-2 w-2 rounded-full bg-accent" />
                Concluídos
              </span>
            }
            className="lg:col-span-2"
          >
            {initialLoading ? (
              <ChartSkeleton />
            ) : (
            <div className="p-4">
              <div className="mb-2">
                <strong className="text-[22px]">{periodTotal}</strong>
                <span className="ml-2 text-[12px] text-quiet">
                  diagnósticos no período
                </span>
              </div>
              <div className="h-[240px]">
                {periodSeries.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={periodSeries}
                      margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid stroke="#e5ebee" vertical={false} />
                      <XAxis
                        dataKey="hour"
                        tick={{ fontSize: 12, fill: "#74848e" }}
                        axisLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: "#74848e" }}
                        axisLine={false}
                        width={38}
                      />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="count"
                        name="Diagnósticos"
                        stroke="#087f78"
                        fill="#dcefed"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty>
                    Nenhum diagnóstico registrado no período.
                  </Empty>
                )}
              </div>
            </div>
            )}
          </Module>

          <Module
            title="Distribuição por fabricante"
            subtitle={
              initialLoading
                ? "Calculando distribuição da frota"
                : `${total.toLocaleString("pt-BR")} dispositivos contabilizados`
            }
            action={<BarChart3 size={15} className="text-quiet" />}
          >
            {initialLoading ? (
              <ChartSkeleton compact />
            ) : (
            <div className="grid min-h-[220px] grid-cols-[180px_1fr] items-center gap-2 p-4">
              {manufacturerData.length ? (
                <>
                  <div className="relative h-[170px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={manufacturerData}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={48}
                          outerRadius={72}
                          paddingAngle={1}
                        >
                          {manufacturerData.map((entry, index) => (
                            <Cell
                              key={entry.name}
                              fill={palette[index % palette.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="pointer-events-none absolute inset-0 grid place-content-center text-center">
                      <strong className="text-[18px]">{total.toLocaleString("pt-BR")}</strong>
                      <span className="text-[10px] font-bold uppercase tracking-[.12em] text-quiet">
                        CPEs
                      </span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {manufacturerData.map((entry, index) => (
                      <div
                        key={entry.name}
                        className="flex items-center gap-2 text-[12px]"
                      >
                        <i
                          className="h-2.5 w-2.5 rounded-sm"
                          style={{
                            background: palette[index % palette.length],
                          }}
                        />
                        <span className="truncate">{entry.name}</span>
                        <b className="ml-auto">
                          {total
                            ? Math.round((entry.value / total) * 100)
                            : 0}
                          %
                        </b>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="col-span-2">
                  <Empty>Fabricantes não identificados.</Empty>
                </div>
              )}
            </div>
            )}
          </Module>

          <Module
            title="Firmware da frota"
            subtitle="Cobertura de versões em toda a frota"
            action={
              <Link
                href="/firmwares"
                className="text-[12px] font-bold text-accent"
              >
                Ver firmwares
              </Link>
            }
          >
            {initialLoading ? (
              <ChartSkeleton compact />
            ) : (
            <div className="grid min-h-[220px] grid-cols-[180px_1fr] items-center gap-2 p-4">
              <div className="relative h-[170px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={firmwareData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={48}
                      outerRadius={72}
                      paddingAngle={1}
                    >
                      <Cell fill="#51b99a" />
                      <Cell fill="#dfe6e9" />
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 grid place-content-center text-center">
                  <strong className="text-[18px]">{firmwareCoverage}%</strong>
                  <span className="text-[10px] font-bold uppercase tracking-[.08em] text-quiet">
                    identificados
                  </span>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-[12px]">
                    <span>Identificados</span>
                    <b>{firmwareKnown}</b>
                  </div>
                  <div className="mt-1.5 h-2 bg-[#edf1f3]">
                    <div
                      className="h-full bg-[#51b99a]"
                      style={{ width: `${firmwareCoverage}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[12px]">
                    <span>Sem versão</span>
                    <b className="text-caution">{firmwareUnknown}</b>
                  </div>
                  <div className="mt-1.5 h-2 bg-[#edf1f3]">
                    <div
                      className="h-full bg-caution"
                      style={{ width: `${100 - firmwareCoverage}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
            )}
          </Module>

          <Module
            title="Saúde dos servidores ACS"
            subtitle="Credenciais configuradas para cada instância"
            action={<Server size={15} className="text-quiet" />}
            className="lg:col-span-2"
          >
            {initialLoading ? (
              <div className="grid gap-4 p-4 sm:grid-cols-3">
                {Array.from({ length: 3 }, (_, index) => (
                  <div key={index} className="animate-pulse">
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="mt-3 h-6 w-24" />
                  </div>
                ))}
              </div>
            ) : (
            <div className="grid divide-y divide-rule sm:grid-cols-3 sm:divide-x sm:divide-y-0">
              {servers.map((server) => (
                <div key={server.id} className="p-4">
                  <div className="flex items-center justify-between gap-2">
                    <b className="truncate text-[13px]">{server.name}</b>
                    <StatusSignal
                      status={
                        server.credentials_ok === false
                          ? "degraded"
                          : server.has_bearer
                            ? "online"
                            : "stale"
                      }
                    />
                  </div>
                  <p className="mt-3 text-[12px] text-quiet">
                    {server.credentials_ok === false
                      ? "Credenciais inválidas"
                      : server.has_bearer
                        ? "Autenticação configurada"
                        : "Sem bearer"}
                  </p>
                </div>
              ))}
              {!servers.length ? (
                <div className="sm:col-span-3">
                  <Empty>Nenhum servidor ACS configurado.</Empty>
                </div>
              ) : null}
            </div>
            )}
          </Module>
        </div>

        <aside className="space-y-3">
          <Module
            title="Exigem atenção"
            subtitle={
              initialLoading
                ? "Analisando estado dos dispositivos"
                : `${offline.toLocaleString("pt-BR")} dispositivos offline na frota`
            }
            action={<TriangleAlert size={15} className="text-caution" />}
          >
            {initialLoading ? (
              <ListSkeleton />
            ) : (
            <div className="divide-y divide-rule">
              {attention.map((device) => (
                <Link
                  key={device.id}
                  href={`/devices/${encodeURIComponent(device.id)}`}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-panel-2"
                >
                  <span className="h-7 w-1 rounded bg-bad" />
                  <span className="min-w-0 flex-1">
                    <b className="block truncate font-mono text-[12px]">
                      {device.serial || device.id}
                    </b>
                    <small className="mt-0.5 block truncate text-[12px] text-quiet">
                      {device.product_class || "Modelo não identificado"}
                    </small>
                  </span>
                  <ArrowRight size={13} className="text-quiet" />
                </Link>
              ))}
              {!attention.length ? (
                <Empty>Nenhum dispositivo offline na frota atual.</Empty>
              ) : null}
            </div>
            )}
            <Link
              href="/devices?online=0"
              className="block border-t border-rule px-4 py-2.5 text-center text-[12px] font-bold text-accent"
            >
              Ver dispositivos offline
            </Link>
          </Module>
          <Module
            title="Atividade recente"
            subtitle="Eventos consolidados do ambiente"
            action={<Activity size={15} className="text-quiet" />}
          >
            <Empty>
              A API ainda não expõe um feed consolidado de atividades.
            </Empty>
          </Module>
        </aside>
      </div>
    </div>
  );
}
