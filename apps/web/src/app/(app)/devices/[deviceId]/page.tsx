"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowUpFromLine,
  Globe2,
  MonitorSmartphone,
  Network,
  Pencil,
  Plus,
  Router,
  RadioTower,
  ShieldCheck,
  Trash2,
  Wifi,
  X,
  type LucideIcon,
} from "lucide-react";
import {
  Btn,
  Control,
  FieldLabel,
  Panel,
  PanelTitle,
  SelectControl,
  StatusSignal,
} from "@/components/ops/primitives";
import { api } from "@/lib/api";
import { cx } from "@/lib/cx";
import { formatDateTime } from "@/lib/format";
import {
  positionFloatingDialog,
  type FloatingDialogPosition,
} from "@/lib/floating-dialog";
import { FloatingDialog } from "@/components/ops/FloatingDialog";
import { LiveTrafficChart } from "@/components/ops/LiveTrafficChart";
import { OpticalTelemetryPanel } from "@/components/ops/OpticalTelemetryPanel";
import { NetworkToolsPanel } from "@/components/ops/NetworkToolsPanel";
import { RouterPortDisplay } from "@/components/ops/RouterPortDisplay";
import {
  formatBytes,
  hasInventoryValue,
  inventoryValue,
  wifiBand,
  workbenchNeedsRefresh,
  type DiagnosticHistoryItem,
  type PortMapping,
  type Report,
  type WanProfile,
  type WifiRadio,
  type Workbench,
} from "@/lib/device-workbench";

const SECTIONS = [
  { id: "overview", label: "Visão geral" },
  { id: "connectivity", label: "Conectividade" },
  { id: "wifi", label: "Wi-Fi" },
  { id: "lan", label: "LAN" },
  { id: "hosts", label: "Hosts" },
  { id: "portmap", label: "Port map" },
  { id: "tools", label: "Ferramentas" },
  { id: "diagnostics", label: "Diagnósticos" },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];


export default function DeviceDetailPage() {
  const params = useParams<{ deviceId: string }>();
  const deviceId = decodeURIComponent(params.deviceId);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [wb, setWb] = useState<Workbench | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [history, setHistory] = useState<DiagnosticHistoryItem[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(
    null,
  );
  const [section, setSection] = useState<SectionId>("overview");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [inventoryHydrating, setInventoryHydrating] = useState(false);
  const inventoryRefreshAttempted = useRef(false);

  const [wifiEdit, setWifiEdit] = useState<WifiRadio | null>(null);
  const [wifiDialogPosition, setWifiDialogPosition] = useState<FloatingDialogPosition>({
    top: 96,
    left: 24,
  });
  const [wifiDraft, setWifiDraft] = useState({
    root: "",
    ssid: "",
    password: "",
    channel: "",
    bandwidth: "",
    enabled: true,
  });
  const [lanEdit, setLanEdit] = useState(false);
  const [lanDialogPosition, setLanDialogPosition] = useState<FloatingDialogPosition>({
    top: 96,
    left: 24,
  });
  const [mappingEdit, setMappingEdit] = useState<PortMapping | "new" | null>(
    null,
  );
  const [mappingDialogPosition, setMappingDialogPosition] =
    useState<FloatingDialogPosition>({ top: 96, left: 24 });
  const [mappingDraft, setMappingDraft] = useState({
    root: "",
    wanRoot: "",
    externalPort: "",
    internalPort: "",
    internalClient: "",
    protocol: "TCP",
    description: "",
    enabled: true,
  });
  const [dhcpDraft, setDhcpDraft] = useState({
    enabled: true,
    lanIp: "",
    subnetMask: "",
    minAddress: "",
    maxAddress: "",
    dnsServers: "",
    leaseTime: "",
  });
  const [wanEdit, setWanEdit] = useState<WanProfile | null>(null);
  const [wanDialogPosition, setWanDialogPosition] = useState<FloatingDialogPosition>({
    top: 96,
    left: 24,
  });
  const [wanDraft, setWanDraft] = useState({
    root: "",
    username: "",
    password: "",
  });
  const [tag, setTag] = useState("");

  const ppp = useMemo(
    () => (wb?.wan || []).find((w) => w.kind === "ppp") || wb?.wan?.[0],
    [wb],
  );

  async function refresh(preferredHistoryId?: string | null) {
    const res = await api<{
      summary: Record<string, unknown>;
      workbench: Workbench;
    }>(`/acs/devices/${encodeURIComponent(deviceId)}`);
    setSummary(res.summary);
    setWb(res.workbench);
    const diag = await api<{
      items: DiagnosticHistoryItem[];
    }>(`/acs/devices/${encodeURIComponent(deviceId)}/diagnostics`);
    setHistory(diag.items);
    const targetId =
      preferredHistoryId === undefined
        ? selectedHistoryId
        : preferredHistoryId;
    const selected =
      diag.items.find((item) => item.id === targetId) || diag.items[0];
    setSelectedHistoryId(selected?.id || null);
    setReport(selected?.report || null);
  }

  useEffect(() => {
    inventoryRefreshAttempted.current = false;
    refresh().catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId]);

  useEffect(() => {
    if (
      !wb ||
      !summary?.online ||
      inventoryRefreshAttempted.current ||
      !workbenchNeedsRefresh(wb)
    ) {
      return;
    }

    inventoryRefreshAttempted.current = true;
    setInventoryHydrating(true);
    api(`/acs/devices/${encodeURIComponent(deviceId)}/actions`, {
      method: "POST",
      body: JSON.stringify({ action: "inventory_refresh", params: {} }),
    })
      .then(() => refresh())
      // A leitura ativa complementa o cache. Sua falha não invalida o
      // inventário já carregado nem deve virar um erro global da página.
      .catch(() => undefined)
      .finally(() => setInventoryHydrating(false));
    // `refresh` é intencionalmente estável durante o ciclo desta página.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId, summary?.online, wb]);

  async function runAction(name: string, params: Record<string, unknown> = {}) {
    setMsg(null);
    setError(null);
    setBusy(true);
    try {
      const res = await api<{ ok?: boolean; queued?: boolean; report?: Report }>(
        `/acs/devices/${encodeURIComponent(deviceId)}/actions`,
        { method: "POST", body: JSON.stringify({ action: name, params }) },
      );
      const isInteractiveDiagnostic = name === "ping" || name === "traceroute";
      setMsg(
        isInteractiveDiagnostic
          ? "Diagnóstico iniciado em uma sessão imediata com o CPE."
          : res.queued
            ? "Alteração enfileirada. O CPE aplicará no próximo contato com o ACS."
            : "Alteração confirmada pelo ACS.",
      );
      if (res.report) setReport(res.report);
      await refresh(name === "diagnostic_full" ? null : undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setBusy(false);
    }
  }

  function openWifi(radio: WifiRadio, anchor: HTMLElement) {
    setWifiDraft({
      root: radio.root,
      ssid: radio.ssid || "",
      password: "",
      channel: radio.autoChannel ? "0" : radio.channel || "",
      bandwidth: radio.bandwidth || "",
      enabled: radio.enabled !== false,
    });
    setWifiDialogPosition(positionFloatingDialog(anchor, 680, 680));
    setWifiEdit(radio);
  }

  function openLan(anchor: HTMLElement) {
    const dhcp = wb?.dhcp;
    setDhcpDraft({
      enabled: dhcp?.enabled !== false,
      lanIp: dhcp?.lanIp || "",
      subnetMask: dhcp?.subnetMask || "",
      minAddress: dhcp?.minAddress || "",
      maxAddress: dhcp?.maxAddress || "",
      dnsServers: dhcp?.dnsServers || "",
      leaseTime: dhcp?.leaseTime != null ? String(dhcp.leaseTime) : "",
    });
    setLanDialogPosition(positionFloatingDialog(anchor, 620, 700));
    setLanEdit(true);
  }

  function openWan(profile: WanProfile, anchor: HTMLElement) {
    setWanDraft({
      root: profile.root,
      username: profile.username || "",
      password: "",
    });
    setWanDialogPosition(positionFloatingDialog(anchor, 520, 460));
    setWanEdit(profile);
  }

  function openMapping(mapping: PortMapping | "new", anchor: HTMLElement) {
    const firstWan = (wb?.wan || [])[0]?.root || "";
    setMappingDraft(
      mapping === "new"
        ? {
            root: "",
            wanRoot: firstWan,
            externalPort: "",
            internalPort: "",
            internalClient: "",
            protocol: "TCP",
            description: "",
            enabled: true,
          }
        : {
            root: mapping.root,
            wanRoot: mapping.wanRoot || firstWan,
            externalPort: String(mapping.externalPort || ""),
            internalPort: String(mapping.internalPort || ""),
            internalClient: mapping.internalClient || "",
            protocol: mapping.protocol || "TCP",
            description: mapping.description || "",
            enabled: mapping.enabled !== false,
          },
    );
    setMappingDialogPosition(positionFloatingDialog(anchor, 620, 650));
    setMappingEdit(mapping);
  }

  async function saveMapping() {
    const params = {
      ...mappingDraft,
      externalPort: Number(mappingDraft.externalPort),
      internalPort: Number(mappingDraft.internalPort),
    };
    if (mappingEdit === "new") {
      await runAction("port_mapping_add", params);
    } else {
      await runAction("port_mapping_set", params);
    }
    setMappingEdit(null);
  }

  const tags = (summary?.tags as string[]) || [];
  const online = Boolean(summary?.online);
  const inventoryResolving = Boolean(
    inventoryHydrating ||
      (wb &&
        online &&
        workbenchNeedsRefresh(wb) &&
        !inventoryRefreshAttempted.current),
  );
  const selectedHistory = history.find(
    (item) => item.id === selectedHistoryId,
  );
  const latestHistoryId = history[0]?.id;

  return (
    <div className="device-workbench grid w-full gap-3">
      <Link
        href="/devices"
        className="text-[12px] font-medium text-accent hover:underline"
      >
        ← Inventário
      </Link>

      <Panel className="!p-0 overflow-hidden border-t-[3px] border-t-accent">
        <div className="grid gap-0 lg:grid-cols-[1fr_220px]">
          <div className="p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[8px] bg-signal-soft text-signal">
                  <Activity size={22} />
                </span>
                <div>
                  <div className="tech text-[20px] font-semibold tracking-tight text-ink">
                    {String(summary?.serial || deviceId)}
                  </div>
                  <div className="mt-0.5 text-[13px] text-ink-soft">
                    {String(summary?.manufacturer || "—")} ·{" "}
                    {String(summary?.product_class || "—")}
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-3">
                  <StatusSignal status={online} />
                  <span className="text-[12px] text-quiet">
                    Inform {formatDateTime(summary?.last_inform as string)}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Btn
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={() => runAction("sync")}
                >
                  Sync
                </Btn>
                <Btn
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={() => runAction("reboot")}
                >
                  Reboot
                </Btn>
                <Btn
                  size="sm"
                  disabled={busy}
                  onClick={() => runAction("diagnostic_full")}
                >
                  Diagnóstico
                </Btn>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 border-t border-rule pt-3 md:grid-cols-4 xl:grid-cols-6">
              <Meta label="IP WAN / CPE" value={ppp?.external_ip || "—"} tech />
              <Meta label="PPPoE" value={ppp?.username || "—"} tech />
              <Meta
                label="Firmware"
                value={String(summary?.software_version || "—")}
                tech
              />
              <Meta label="ID" value={String(summary?.id || deviceId)} tech />
              <Meta label="Tags" value={tags.join(", ") || "—"} />
              <Meta label="Status WAN" value={ppp?.connection_status || "—"} />
            </div>
          </div>

          <div className="border-t border-rule bg-good-soft/55 p-4 lg:border-l lg:border-t-0">
            <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-quiet">
              Health score
            </div>
            <div className="mt-2 flex items-end justify-between gap-3">
              <div className="flex items-center gap-2">
                <ShieldCheck size={22} className="text-good" />
                <div className="text-[36px] font-semibold leading-none tabular-nums text-good">
                  {report?.score ?? "—"}
                </div>
              </div>
              <span className="pb-0.5 text-[12px] font-medium text-quiet">
                {report ? `Grade ${report.grade}` : "Pendente"}
              </span>
            </div>
            {report?.tips?.length ? (
              <button
                type="button"
                onClick={() => setSection("diagnostics")}
                className="mt-3 flex w-full items-center justify-between rounded-[5px] border border-caution/25 bg-white/65 px-2.5 py-2 text-left text-[12px] font-semibold text-caution transition hover:border-caution/45 hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-caution/25"
              >
                <span>
                  {report.tips.length}{" "}
                  {report.tips.length === 1
                    ? "alerta para revisar"
                    : "alertas para revisar"}
                </span>
                <span aria-hidden="true">→</span>
              </button>
            ) : (
              <p className="mt-2 text-[12px] text-quiet">
                {report ? "Nenhum alerta ativo" : "Sem diagnóstico ainda"}
              </p>
            )}
          </div>
        </div>
      </Panel>

      {msg ? <p className="text-[13px] text-good">{msg}</p> : null}
      {error ? <p className="text-[13px] text-bad">{error}</p> : null}

      <div className="grid gap-3 lg:grid-cols-[180px_1fr]">
        <aside className="ops-panel h-fit border-t-[3px] border-t-signal p-1.5 lg:sticky lg:top-3">
          <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-quiet">
            Seções
          </div>
          <nav className="grid gap-0.5">
            {SECTIONS.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setSection(s.id)}
                className={cx(
                  "rounded-[2px] px-2.5 py-1.5 text-left text-[12.5px] font-medium",
                  section === s.id
                    ? "bg-accent-soft text-accent"
                    : "text-ink-soft hover:bg-panel-2",
                )}
              >
                {s.label}
              </button>
            ))}
          </nav>
        </aside>

        <div className="min-w-0 grid gap-3">
          {section === "overview" ? (
            <>
              <div className={cx("grid gap-3 md:grid-cols-2", wb?.optical ? "xl:grid-cols-5" : "xl:grid-cols-4")}>
                <SummaryTile
                  title="WAN"
                  body={`${ppp?.kind || "—"} · ${ppp?.connection_status || "—"}`}
                  tone="signal"
                  icon={Globe2}
                />
                <SummaryTile
                  title="Wi-Fi"
                  body={`${(wb?.wifi || []).filter((radio) => radio.enabled !== false).length} de ${wb?.wifi?.length || 0} APs ativos`}
                  tone="accent"
                  icon={Wifi}
                />
                <SummaryTile
                  title="LAN"
                  body={wb?.dhcp?.lanIp || "—"}
                  tone="signal"
                  icon={Network}
                />
                <SummaryTile
                  title="Hosts"
                  body={`${wb?.hosts?.length || 0} reportados`}
                  tone="good"
                  icon={MonitorSmartphone}
                />
                {wb?.optical ? (
                  <SummaryTile
                    title={wb.optical.technology || "Óptica"}
                    body={
                      wb.optical.rxPowerDbm != null
                        ? `${wb.optical.rxPowerDbm.toLocaleString("pt-BR")} dBm`
                        : wb.optical.status || "Detectada"
                    }
                    tone="signal"
                    icon={RadioTower}
                  />
                ) : null}
              </div>
              <Panel>
                <PanelTitle title="Resumo operacional" />
                <div className="grid gap-3 text-[13px] md:grid-cols-2">
                  <p>
                    <span className="text-quiet">Serial </span>
                    <span className="tech">
                      {String(summary?.serial || "—")}
                    </span>
                  </p>
                  <p>
                    <span className="text-quiet">Modelo </span>
                    {String(summary?.product_class || "—")}
                  </p>
                  <p>
                    <span className="text-quiet">Firmware </span>
                    <span className="tech">
                      {String(summary?.software_version || "—")}
                    </span>
                  </p>
                  <p>
                    <span className="text-quiet">Último inform </span>
                    {formatDateTime(summary?.last_inform as string)}
                  </p>
                </div>
                <form
                  className="mt-4 flex flex-wrap items-end gap-2 border-t border-rule pt-3"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!tag.trim()) return;
                    runAction("tags_add", { tag: tag.trim() });
                    setTag("");
                  }}
                >
                  <div className="min-w-[180px] flex-1">
                    <FieldLabel>Nova tag</FieldLabel>
                    <Control
                      value={tag}
                      onChange={(e) => setTag(e.target.value)}
                      placeholder="ex.: noc-norte"
                    />
                  </div>
                  <Btn
                    type="submit"
                    size="sm"
                    variant="outline"
                    disabled={busy || !tag.trim()}
                  >
                    + tag
                  </Btn>
                </form>
                {tags.length ? (
                  <p className="mt-2 text-[12px] text-quiet">
                    Atuais: {tags.join(", ")}
                  </p>
                ) : null}
              </Panel>
              <Panel>
                <PanelTitle
                  title="Tráfego e configuração"
                  hint="Contadores acumulados e parâmetros ativos do CPE"
                />
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <OperationalMetric
                    label="Bytes recebidos"
                    value={inventoryValue(
                      formatBytes(ppp?.bytes_received),
                      inventoryResolving,
                      online,
                    )}
                    hint="Acumulado na conexão WAN"
                    icon={ArrowDownToLine}
                    tone="accent"
                    loading={inventoryResolving && !hasInventoryValue(ppp?.bytes_received)}
                  />
                  <OperationalMetric
                    label="Bytes enviados"
                    value={inventoryValue(
                      formatBytes(ppp?.bytes_sent),
                      inventoryResolving,
                      online,
                    )}
                    hint="Acumulado na conexão WAN"
                    icon={ArrowUpFromLine}
                    tone="signal"
                    loading={inventoryResolving && !hasInventoryValue(ppp?.bytes_sent)}
                  />
                  <OperationalMetric
                    label="DNS da rede local"
                    value={inventoryValue(
                      wb?.dhcp?.dnsServers || null,
                      inventoryResolving,
                      online,
                    )}
                    hint={
                      report?.checks.find((check) => check.id === "dns")
                        ?.status === "warn"
                        ? "Fora do padrão configurado"
                        : "Configuração reportada pelo CPE"
                    }
                    icon={Network}
                    tone={
                      report?.checks.find((check) => check.id === "dns")
                        ?.status === "warn"
                        ? "caution"
                        : "neutral"
                    }
                    technical
                    loading={inventoryResolving && !wb?.dhcp?.dnsServers}
                  />
                  <OperationalMetric
                    label="Faixa DHCP"
                    value={
                      wb?.dhcp?.minAddress && wb?.dhcp?.maxAddress
                        ? `${wb.dhcp.minAddress} – ${wb.dhcp.maxAddress}`
                        : inventoryValue(null, inventoryResolving, online)
                    }
                    hint={
                      wb?.dhcp?.enabled === false
                        ? "Servidor DHCP desativado"
                        : "Servidor DHCP ativo"
                    }
                    icon={Router}
                    tone="neutral"
                    technical
                    loading={
                      inventoryResolving &&
                      (!wb?.dhcp?.minAddress || !wb?.dhcp?.maxAddress)
                    }
                  />
                </div>
              </Panel>
              {wb?.optical ? <OpticalTelemetryPanel optical={wb.optical} /> : null}
              <LiveTrafficChart deviceId={deviceId} online={online} />
            </>
          ) : null}

          {section === "connectivity" ? (
            <Panel>
              <PanelTitle
                title="Conectividade WAN"
                hint="Conexões de internet reportadas pelo equipamento"
              />
              <div className="overflow-x-auto">
                <table className="ops-table">
                  <thead>
                    <tr>
                      <th>Tipo</th>
                      <th>Status</th>
                      <th>Usuário</th>
                      <th>IP externo</th>
                      <th className="text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(wb?.wan || []).map((w) => (
                      <tr key={w.root}>
                        <td>{w.kind === "ppp" ? "PPPoE" : "IP"}</td>
                        <td>{w.connection_status || w.name || "—"}</td>
                        <td className="tech">{w.username || "—"}</td>
                        <td className="tech">{w.external_ip || "—"}</td>
                        <td className="text-right">
                          {w.kind === "ppp" ? (
                            <Btn
                              size="sm"
                              variant="outline"
                              onClick={(event) =>
                                openWan(w, event.currentTarget)
                              }
                            >
                              Gerenciar
                            </Btn>
                          ) : (
                            <span className="text-[12px] text-quiet">
                              Somente leitura
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!wb?.wan?.length ? (
                  <p className="p-3 text-[13px] text-quiet">
                    Nenhum perfil WAN.
                  </p>
                ) : null}
              </div>
            </Panel>
          ) : null}

          {section === "wifi" ? (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(wb?.wifi || []).map((radio, index) => (
                <WifiCard
                  key={radio.root}
                  label={`AP ${radio.index ?? index + 1} · ${wifiBand(radio) === "24" ? "2.4 GHz" : "5 GHz"}`}
                  radio={radio}
                  onEdit={(anchor) => openWifi(radio, anchor)}
                />
              ))}
              {!wb?.wifi?.length ? (
                <Panel className="md:col-span-2 xl:col-span-3">
                  <p className="text-[13px] text-quiet">
                    Nenhum access point Wi-Fi foi reportado por este CPE.
                  </p>
                </Panel>
              ) : null}
            </div>
          ) : null}

          {section === "lan" ? (
            <Panel>
              <div className="mb-3 flex items-start justify-between gap-2">
                <PanelTitle title="LAN / DHCP" />
                <Btn
                  size="sm"
                  variant="outline"
                  onClick={(event) => openLan(event.currentTarget)}
                >
                  Gerenciar DHCP
                </Btn>
              </div>
              <dl className="grid gap-2 text-[13px] sm:grid-cols-2">
                <Item k="Gateway" v={wb?.dhcp?.lanIp || "—"} tech />
                <Item k="Máscara" v={wb?.dhcp?.subnetMask || "—"} tech />
                <Item
                  k="DHCP"
                  v={
                    wb?.dhcp?.enabled
                      ? "Habilitado"
                      : wb?.dhcp
                        ? "Desabilitado"
                        : "—"
                  }
                />
                <Item
                  k="Pool"
                  v={
                    wb?.dhcp?.minAddress && wb?.dhcp?.maxAddress
                      ? `${wb.dhcp.minAddress} → ${wb.dhcp.maxAddress}`
                      : "—"
                  }
                  tech
                />
                <Item k="DNS" v={wb?.dhcp?.dnsServers || "—"} tech />
                <Item
                  k="Lease"
                  v={
                    wb?.dhcp?.leaseTime != null
                      ? String(wb.dhcp.leaseTime)
                      : "—"
                  }
                  tech
                />
              </dl>
              <RouterPortDisplay ports={wb?.lanPorts || []} />
            </Panel>
          ) : null}

          {section === "hosts" ? (
            <Panel flush className="h-fit self-start overflow-hidden">
              <div className="flex items-center justify-between gap-3 border-b border-rule bg-panel-2 px-3.5 py-2.5">
                <div>
                  <h2 className="text-[14px] font-bold text-ink">
                    Dispositivos conectados
                  </h2>
                  <p className="text-[12px] text-quiet">
                    {wb?.hosts?.length || 0}{" "}
                    {wb?.hosts?.length === 1
                      ? "host reportado pelo CPE"
                      : "hosts reportados pelo CPE"}
                  </p>
                </div>
                <span className="rounded-[4px] bg-good-soft px-2 py-1 text-[11px] font-semibold text-good">
                  {(wb?.hosts || []).filter((host) => host.active).length} ativos
                </span>
              </div>
              <table className="ops-table">
                <thead>
                  <tr>
                    <th>Host</th>
                    <th>IP</th>
                    <th>MAC</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {(wb?.hosts || []).map((h, i) => (
                    <tr key={`${h.mac}-${i}`}>
                      <td>{h.hostname || "—"}</td>
                      <td className="tech">{h.ip || "—"}</td>
                      <td className="tech">{h.mac || "—"}</td>
                      <td>
                        <span
                          className={cx(
                            "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold",
                            h.active
                              ? "bg-good-soft text-good"
                              : "bg-panel-2 text-quiet",
                          )}
                        >
                          <i
                            className={cx(
                              "h-1.5 w-1.5 rounded-full",
                              h.active ? "bg-good" : "bg-rule-strong",
                            )}
                          />
                          {h.active ? "Ativo" : "Inativo"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!wb?.hosts?.length ? (
                <p className="p-4 text-[13px] text-quiet">
                  Nenhum host reportado.
                </p>
              ) : null}
            </Panel>
          ) : null}

          {section === "portmap" ? (
            <Panel flush>
              <div className="flex items-center justify-between border-b border-rule bg-panel-2 px-4 py-3">
                <div>
                  <h2 className="text-[14px] font-bold">Portas NAT</h2>
                  <p className="text-[12px] text-quiet">
                    Mapeamentos publicados nas conexões WAN
                  </p>
                </div>
                <Btn
                  size="sm"
                  onClick={(event) => openMapping("new", event.currentTarget)}
                >
                  <Plus size={14} />
                  Adicionar regra
                </Btn>
              </div>
              <table className="ops-table">
                <thead>
                  <tr>
                    <th>Ext</th>
                    <th>Int</th>
                    <th>Proto</th>
                    <th>Destino</th>
                    <th>Desc</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {(wb?.portmap || []).map((m) => (
                    <tr key={m.root}>
                      <td className="tech">{m.externalPort ?? "—"}</td>
                      <td className="tech">{m.internalPort ?? "—"}</td>
                      <td>{m.protocol || "—"}</td>
                      <td className="tech">{m.internalClient || "—"}</td>
                      <td>{m.description || "—"}</td>
                      <td>
                        <div className="flex justify-end gap-1">
                          <Btn
                            size="sm"
                            variant="ghost"
                            disabled={busy}
                            onClick={(event) =>
                              openMapping(m, event.currentTarget)
                            }
                          >
                            <Pencil size={13} />
                            Editar
                          </Btn>
                          <Btn
                            size="sm"
                            variant="ghost"
                            className="text-bad"
                            disabled={busy}
                            onClick={() =>
                              runAction("port_mapping_delete", { root: m.root })
                            }
                          >
                            <Trash2 size={13} />
                            Remover
                          </Btn>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!wb?.portmap?.length ? (
                <p className="p-4 text-[13px] text-quiet">
                  Nenhum mapeamento de porta.
                </p>
              ) : null}
            </Panel>
          ) : null}

          {section === "tools" ? (
            <NetworkToolsPanel
              busy={busy}
              onRun={(action, host) => runAction(action, { host })}
            />
          ) : null}

          {section === "diagnostics" ? (
            <>
              {report ? (
                <Panel>
                  <PanelTitle
                    title={`Score ${report.score} (${report.grade})`}
                    hint={
                      selectedHistory
                        ? `Executado em ${formatDateTime(selectedHistory.created_at)}`
                        : undefined
                    }
                    action={
                      selectedHistoryId &&
                      latestHistoryId &&
                      selectedHistoryId !== latestHistoryId ? (
                        <Btn
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            const latest = history[0];
                            if (!latest) return;
                            setSelectedHistoryId(latest.id);
                            setReport(latest.report);
                          }}
                        >
                          Voltar ao mais recente
                        </Btn>
                      ) : (
                        <span className="rounded-full bg-good-soft px-2 py-1 text-[11px] font-semibold text-good">
                          Resultado mais recente
                        </span>
                      )
                    }
                  />
                  <div className="grid gap-2">
                    {report.checks.map((c) => (
                      <div
                        key={c.id}
                        className="flex items-start justify-between gap-3 border-b border-rule/70 py-2 text-[13px]"
                      >
                        <div>
                          <div className="font-semibold">{c.title}</div>
                          <div className="text-[12px] text-quiet">
                            {c.summary}
                          </div>
                        </div>
                        <span
                          className={cx(
                            "rounded-[2px] px-2 py-0.5 text-[11px] font-bold uppercase",
                            c.status === "ok" && "bg-good-soft text-good",
                            c.status === "warn" &&
                              "bg-caution-soft text-caution",
                            c.status !== "ok" &&
                              c.status !== "warn" &&
                              "bg-bad-soft text-bad",
                          )}
                        >
                          {c.status}
                          {c.penalty ? ` +${c.penalty}` : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                  {(report.neighbors || wb?.neighbors || []).length ? (
                    <div className="mt-4 border-t border-rule pt-3">
                      <div className="mb-2 text-[12px] font-bold uppercase tracking-[0.05em] text-quiet">
                        Redes vizinhas
                      </div>
                      <ul className="space-y-1 text-[12.5px]">
                        {(report.neighbors || wb?.neighbors || [])
                          .slice(0, 20)
                          .map((n) => (
                            <li key={`${n.ssid}-${n.vendor}-${n.channel}`}>
                              <span className="font-medium">{n.ssid}</span>
                              <span className="text-quiet">
                                {" "}
                                · ch {n.channel} · {n.rssi} dBm · {n.vendor}
                              </span>
                            </li>
                          ))}
                      </ul>
                    </div>
                  ) : null}
                </Panel>
              ) : (
                <Panel>
                  <PanelTitle title="Diagnósticos" />
                  <p className="text-[13px] text-quiet">
                    Nenhum diagnóstico ainda. Use o botão Diagnóstico no
                    cabeçalho.
                  </p>
                </Panel>
              )}
              <Panel flush>
                <div className="border-b border-rule px-3.5 py-2.5">
                  <PanelTitle title="Histórico" />
                </div>
                <table className="ops-table">
                  <thead>
                    <tr>
                      <th>Quando</th>
                      <th>Score</th>
                      <th>Grade</th>
                      <th className="text-right">Resultado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => (
                      <tr
                        key={h.id}
                        className={cx(
                          selectedHistoryId === h.id && "bg-accent-soft/45",
                        )}
                      >
                        <td className="tech">{formatDateTime(h.created_at)}</td>
                        <td>{h.score}</td>
                        <td>{h.grade}</td>
                        <td className="text-right">
                          <Btn
                            size="sm"
                            variant={
                              selectedHistoryId === h.id ? "ghost" : "outline"
                            }
                            onClick={() => {
                              setSelectedHistoryId(h.id);
                              setReport(h.report);
                            }}
                          >
                            {selectedHistoryId === h.id
                              ? "Em exibição"
                              : "Ver resultado"}
                          </Btn>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!history.length ? (
                  <p className="p-4 text-[13px] text-quiet">Sem histórico.</p>
                ) : null}
              </Panel>
            </>
          ) : null}
        </div>
      </div>

      {mappingEdit ? (
        <FloatingDialog
          labelledBy="mapping-dialog-title"
          onClose={() => setMappingEdit(null)}
          position={mappingDialogPosition}
          width={620}
        >
            <div className="flex shrink-0 items-start justify-between border-b border-rule px-5 py-4">
              <div>
                <h2 id="mapping-dialog-title" className="text-[17px] font-bold">
                  {mappingEdit === "new"
                    ? "Adicionar port mapping"
                    : "Editar port mapping"}
                </h2>
                <p className="text-[12px] text-quiet">
                  Publicação NAT contextual no CPE
                </p>
              </div>
              <button
                type="button"
                onClick={() => setMappingEdit(null)}
                className="grid h-8 w-8 place-items-center rounded-[5px] hover:bg-panel-2"
              >
                <X size={17} />
              </button>
            </div>
            <div className="ops-scroll grid min-h-0 gap-4 overflow-y-auto p-5">
              <section className="grid gap-4 rounded-[7px] border border-rule p-4">
                <div>
                  <FieldLabel>Conexão WAN</FieldLabel>
                  <SelectControl
                    value={mappingDraft.wanRoot}
                    onChange={(event) =>
                      setMappingDraft({
                        ...mappingDraft,
                        wanRoot: event.target.value,
                      })
                    }
                    disabled={mappingEdit !== "new"}
                  >
                    {(wb?.wan || []).map((wan) => (
                      <option key={wan.root} value={wan.root}>
                        {wan.name || wan.kind} · {wan.external_ip || "sem IP"}
                      </option>
                    ))}
                  </SelectControl>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Porta externa</FieldLabel>
                    <Control
                      type="number"
                      min="1"
                      max="65535"
                      value={mappingDraft.externalPort}
                      onChange={(event) =>
                        setMappingDraft({
                          ...mappingDraft,
                          externalPort: event.target.value,
                        })
                      }
                    />
                  </div>
                  <div>
                    <FieldLabel>Porta interna</FieldLabel>
                    <Control
                      type="number"
                      min="1"
                      max="65535"
                      value={mappingDraft.internalPort}
                      onChange={(event) =>
                        setMappingDraft({
                          ...mappingDraft,
                          internalPort: event.target.value,
                        })
                      }
                    />
                  </div>
                  <div>
                    <FieldLabel>Cliente interno</FieldLabel>
                    <Control
                      className="tech"
                      placeholder="192.168.1.10"
                      value={mappingDraft.internalClient}
                      onChange={(event) =>
                        setMappingDraft({
                          ...mappingDraft,
                          internalClient: event.target.value,
                        })
                      }
                    />
                  </div>
                  <div>
                    <FieldLabel>Protocolo</FieldLabel>
                    <SelectControl
                      value={mappingDraft.protocol}
                      onChange={(event) =>
                        setMappingDraft({
                          ...mappingDraft,
                          protocol: event.target.value,
                        })
                      }
                    >
                      <option value="TCP">TCP</option>
                      <option value="UDP">UDP</option>
                    </SelectControl>
                  </div>
                </div>
                <div>
                  <FieldLabel>Descrição</FieldLabel>
                  <Control
                    value={mappingDraft.description}
                    onChange={(event) =>
                      setMappingDraft({
                        ...mappingDraft,
                        description: event.target.value,
                      })
                    }
                    placeholder="Ex.: câmera recepção"
                  />
                </div>
                <label className="flex items-center justify-between rounded-[6px] bg-panel-2 px-3 py-2.5 text-[13px] font-semibold">
                  Regra habilitada
                  <input
                    type="checkbox"
                    checked={mappingDraft.enabled}
                    onChange={(event) =>
                      setMappingDraft({
                        ...mappingDraft,
                        enabled: event.target.checked,
                      })
                    }
                    className="h-4 w-4 accent-accent"
                  />
                </label>
              </section>
            </div>
            <div className="flex shrink-0 justify-end gap-2 border-t border-rule bg-panel-2 px-5 py-3.5">
              <Btn variant="ghost" onClick={() => setMappingEdit(null)}>
                Cancelar
              </Btn>
              <Btn
                disabled={
                  busy ||
                  !mappingDraft.wanRoot ||
                  !mappingDraft.externalPort ||
                  !mappingDraft.internalPort ||
                  !mappingDraft.internalClient
                }
                onClick={saveMapping}
              >
                {mappingEdit === "new" ? "Adicionar" : "Salvar"}
              </Btn>
            </div>
        </FloatingDialog>
      ) : null}

      {wanEdit ? (
        <FloatingDialog
          labelledBy="wan-dialog-title"
          onClose={() => setWanEdit(null)}
          position={wanDialogPosition}
          width={520}
        >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-rule px-5 py-4">
              <div>
                <h2 id="wan-dialog-title" className="text-[17px] font-bold">
                  Gerenciar conexão PPPoE
                </h2>
                <p className="mt-0.5 text-[12px] text-quiet">
                  {wanEdit.name || "Perfil WAN"} · alterações aplicadas via ACS
                </p>
              </div>
              <button
                type="button"
                onClick={() => setWanEdit(null)}
                className="grid h-8 w-8 shrink-0 place-items-center rounded-[5px] text-quiet hover:bg-panel-2 hover:text-ink"
                aria-label="Fechar"
              >
                <X size={17} />
              </button>
            </div>
            <div className="ops-scroll grid min-h-0 gap-4 overflow-y-auto p-5">
              <div className="grid gap-3 rounded-[7px] bg-panel-2 p-3 text-[12px] sm:grid-cols-2">
                <div>
                  <span className="block text-quiet">Status</span>
                  <strong>
                    {inventoryValue(
                      wanEdit.connection_status || null,
                      inventoryResolving,
                      online,
                    )}
                  </strong>
                </div>
                <div>
                  <span className="block text-quiet">IP externo</span>
                  <strong className="tech">
                    {inventoryValue(
                      wanEdit.external_ip || null,
                      inventoryResolving,
                      online,
                    )}
                  </strong>
                </div>
              </div>
              <div>
                <FieldLabel>Usuário PPPoE</FieldLabel>
                <Control
                  value={wanDraft.username}
                  onChange={(event) =>
                    setWanDraft({ ...wanDraft, username: event.target.value })
                  }
                  autoComplete="off"
                />
              </div>
              <div>
                <FieldLabel>Nova senha</FieldLabel>
                <Control
                  type="password"
                  value={wanDraft.password}
                  onChange={(event) =>
                    setWanDraft({ ...wanDraft, password: event.target.value })
                  }
                  placeholder="Deixe vazio para manter a senha atual"
                  autoComplete="new-password"
                />
              </div>
            </div>
            <div className="flex shrink-0 justify-end gap-2 border-t border-rule bg-panel-2 px-5 py-3.5">
              <Btn variant="ghost" onClick={() => setWanEdit(null)}>
                Cancelar
              </Btn>
              <Btn
                disabled={busy || !wanDraft.root || !wanDraft.username.trim()}
                onClick={async () => {
                  await runAction("wan_set_pppoe", wanDraft);
                  setWanEdit(null);
                }}
              >
                Salvar alterações
              </Btn>
            </div>
        </FloatingDialog>
      ) : null}

      {wifiEdit ? (
        <FloatingDialog
          labelledBy="wifi-dialog-title"
          onClose={() => setWifiEdit(null)}
          position={wifiDialogPosition}
          width={680}
        >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-rule px-5 py-4">
              <div>
                <h2 id="wifi-dialog-title" className="text-[17px] font-bold">
                  Editar AP Wi-Fi {wifiEdit.index ?? ""}
                </h2>
                <p className="mt-0.5 text-[12px] text-quiet">
                  {wifiBand(wifiEdit) === "24" ? "2.4 GHz" : "5 GHz"} · alteração
                  contextual via ACS
                </p>
              </div>
              <button
                type="button"
                onClick={() => setWifiEdit(null)}
                className="grid h-8 w-8 place-items-center rounded-[5px] text-quiet hover:bg-panel-2 hover:text-ink"
                aria-label="Fechar"
              >
                <X size={17} />
              </button>
            </div>
            <div className="ops-scroll grid min-h-0 gap-4 overflow-y-auto p-5">
              <section className="grid gap-4 rounded-[7px] border border-rule p-4">
                <div>
                  <FieldLabel>SSID</FieldLabel>
                  <Control
                    value={wifiDraft.ssid}
                    onChange={(e) =>
                      setWifiDraft({ ...wifiDraft, ssid: e.target.value })
                    }
                  />
                </div>
                <div>
                  <FieldLabel>Senha</FieldLabel>
                  <Control
                    type="password"
                    value={wifiDraft.password}
                    onChange={(e) =>
                      setWifiDraft({ ...wifiDraft, password: e.target.value })
                    }
                    placeholder="Manter atual"
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Canal</FieldLabel>
                    <SelectControl
                      value={wifiDraft.channel}
                      onChange={(event) =>
                        setWifiDraft({
                          ...wifiDraft,
                          channel: event.target.value,
                        })
                      }
                    >
                      <option value="0">Automático</option>
                      {(wifiBand(wifiEdit) === "24"
                        ? [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
                        : [
                            36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112,
                            116, 120, 124, 128, 132, 136, 140, 149, 153, 157,
                            161,
                          ]
                      ).map((channel) => (
                        <option key={channel} value={channel}>
                          {channel}
                        </option>
                      ))}
                    </SelectControl>
                  </div>
                  <div>
                    <FieldLabel>Largura do canal</FieldLabel>
                    <SelectControl
                      value={wifiDraft.bandwidth}
                      onChange={(event) =>
                        setWifiDraft({
                          ...wifiDraft,
                          bandwidth: event.target.value,
                        })
                      }
                    >
                      <option value="">Manter atual</option>
                      <option value="Auto">Automática</option>
                      <option value="20MHz">20 MHz</option>
                      <option value="40MHz">40 MHz</option>
                      {wifiBand(wifiEdit) === "5" ? (
                        <>
                          <option value="80MHz">80 MHz</option>
                          <option value="160MHz">160 MHz</option>
                        </>
                      ) : null}
                    </SelectControl>
                  </div>
                </div>
                <label className="flex items-center justify-between rounded-[6px] border border-rule bg-panel-2 px-3 py-2.5 text-[13px] font-semibold">
                  <span>
                    <span className="block">Access point habilitado</span>
                    <span className="text-[12px] font-normal text-quiet">
                      Permite ativar ou desativar esta rede Wi-Fi.
                    </span>
                  </span>
                  <input
                    type="checkbox"
                    checked={wifiDraft.enabled}
                    onChange={(event) =>
                      setWifiDraft({
                        ...wifiDraft,
                        enabled: event.target.checked,
                      })
                    }
                    className="h-4 w-4 accent-accent"
                  />
                </label>
              </section>
            </div>
            <div className="flex shrink-0 justify-end gap-2 border-t border-rule bg-panel-2 px-5 py-3.5">
              <Btn variant="ghost" onClick={() => setWifiEdit(null)}>
                Cancelar
              </Btn>
              <Btn
                disabled={busy || !wifiDraft.root}
                onClick={async () => {
                  await runAction("wifi_set", wifiDraft);
                  setWifiEdit(null);
                }}
              >
                Aplicar
              </Btn>
            </div>
        </FloatingDialog>
      ) : null}

      {lanEdit ? (
        <FloatingDialog
          labelledBy="lan-dialog-title"
          onClose={() => setLanEdit(false)}
          position={lanDialogPosition}
          width={620}
        >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-rule px-5 py-4">
              <div>
                <h2 id="lan-dialog-title" className="text-[17px] font-bold">
                  Gerenciar LAN e DHCP
                </h2>
                <p className="mt-0.5 text-[12px] text-quiet">
                  Endereçamento e distribuição automática da rede local
                </p>
              </div>
              <button
                type="button"
                onClick={() => setLanEdit(false)}
                className="grid h-8 w-8 place-items-center rounded-[5px] text-quiet hover:bg-panel-2"
                aria-label="Fechar"
              >
                <X size={17} />
              </button>
            </div>
            <div className="ops-scroll grid min-h-0 gap-4 overflow-y-auto p-5">
              <label className="flex items-center justify-between rounded-[7px] border border-rule bg-panel-2 px-3 py-2.5 text-[13px] font-semibold">
                <span>
                  <span className="block">Servidor DHCP habilitado</span>
                  <span className="mt-0.5 block text-[12px] font-normal text-quiet">
                    Distribui endereços automaticamente para os dispositivos da LAN.
                  </span>
                </span>
                <input
                  type="checkbox"
                  checked={dhcpDraft.enabled}
                  onChange={(event) =>
                    setDhcpDraft({
                      ...dhcpDraft,
                      enabled: event.target.checked,
                    })
                  }
                  className="h-4 w-4 shrink-0 accent-accent"
                />
              </label>

              <section className="grid gap-4 rounded-[7px] border border-rule p-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Gateway da LAN</FieldLabel>
                    <Control
                      value={dhcpDraft.lanIp}
                      onChange={(event) =>
                        setDhcpDraft({
                          ...dhcpDraft,
                          lanIp: event.target.value,
                        })
                      }
                      placeholder="192.168.1.1"
                      className="tech"
                    />
                  </div>
                  <div>
                    <FieldLabel>Máscara de rede</FieldLabel>
                    <Control
                      value={dhcpDraft.subnetMask}
                      onChange={(event) =>
                        setDhcpDraft({
                          ...dhcpDraft,
                          subnetMask: event.target.value,
                        })
                      }
                      placeholder="255.255.255.0"
                      className="tech"
                    />
                  </div>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Início do pool</FieldLabel>
                    <Control
                      value={dhcpDraft.minAddress}
                      onChange={(event) =>
                        setDhcpDraft({
                          ...dhcpDraft,
                          minAddress: event.target.value,
                        })
                      }
                      placeholder="192.168.1.2"
                      className="tech"
                    />
                  </div>
                  <div>
                    <FieldLabel>Fim do pool</FieldLabel>
                    <Control
                      value={dhcpDraft.maxAddress}
                      onChange={(event) =>
                        setDhcpDraft({
                          ...dhcpDraft,
                          maxAddress: event.target.value,
                        })
                      }
                      placeholder="192.168.1.254"
                      className="tech"
                    />
                  </div>
                </div>
              </section>

              <section className="grid gap-4 rounded-[7px] border border-rule p-4 sm:grid-cols-[1fr_180px]">
                <div>
                  <FieldLabel>Servidores DNS</FieldLabel>
                  <Control
                    value={dhcpDraft.dnsServers}
                    onChange={(event) =>
                      setDhcpDraft({
                        ...dhcpDraft,
                        dnsServers: event.target.value,
                      })
                    }
                    placeholder="1.1.1.1, 8.8.8.8"
                    className="tech"
                  />
                  <p className="mt-1.5 text-[11px] text-quiet">
                    Separe múltiplos servidores por vírgula.
                  </p>
                </div>
                <div>
                  <FieldLabel>Tempo de concessão</FieldLabel>
                  <div className="flex items-center gap-2">
                    <Control
                      type="number"
                      min="60"
                      value={dhcpDraft.leaseTime}
                      onChange={(event) =>
                        setDhcpDraft({
                          ...dhcpDraft,
                          leaseTime: event.target.value,
                        })
                      }
                      placeholder="86400"
                      className="tech"
                    />
                    <span className="text-[12px] text-quiet">s</span>
                  </div>
                </div>
              </section>

              <p className="border-l-2 border-caution bg-caution-soft/55 px-3 py-2 text-[12px] leading-relaxed text-ink-soft">
                Alterar gateway, máscara ou pool pode interromper temporariamente
                os clientes conectados.
              </p>
            </div>
            <div className="flex shrink-0 justify-end gap-2 border-t border-rule bg-panel-2 px-5 py-3.5">
              <Btn variant="ghost" onClick={() => setLanEdit(false)}>
                Cancelar
              </Btn>
              <Btn
                disabled={busy}
                onClick={async () => {
                  await runAction("dhcp_set", {
                    ...dhcpDraft,
                    leaseTime: dhcpDraft.leaseTime
                      ? Number(dhcpDraft.leaseTime)
                      : undefined,
                  });
                  setLanEdit(false);
                }}
              >
                Aplicar configuração
              </Btn>
            </div>
        </FloatingDialog>
      ) : null}
    </div>
  );
}

function Meta({
  label,
  value,
  tech,
}: {
  label: string;
  value: string;
  tech?: boolean;
}) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-[0.05em] text-quiet">
        {label}
      </div>
      <div
        className={cx(
          "mt-0.5 truncate text-[12.5px] font-medium",
          tech && "tech",
        )}
      >
        {value}
      </div>
    </div>
  );
}

function Item({ k, v, tech }: { k: string; v: string; tech?: boolean }) {
  return (
    <div className="flex justify-between gap-3 border-b border-rule/70 py-1.5">
      <dt className="text-quiet">{k}</dt>
      <dd className={cx("font-medium", tech && "tech")}>{v}</dd>
    </div>
  );
}

function SummaryTile({
  title,
  body,
  tone,
  icon: Icon,
}: {
  title: string;
  body: string;
  tone: "signal" | "accent" | "caution" | "good";
  icon: LucideIcon;
}) {
  const tones = {
    signal: "border-t-signal bg-signal-soft/45 text-signal",
    accent: "border-t-accent bg-accent-soft/45 text-accent",
    caution: "border-t-caution bg-caution-soft/45 text-caution",
    good: "border-t-good bg-good-soft/45 text-good",
  };
  return (
    <div className={cx("ops-panel border-t-[3px] px-3 py-3", tones[tone])}>
      <div className="flex items-center gap-2">
        <span className="grid h-8 w-8 place-items-center rounded-[6px] bg-white/80">
          <Icon size={16} />
        </span>
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-quiet">
            {title}
          </div>
          <div className="mt-0.5 truncate text-[13px] font-semibold text-ink">
            {body}
          </div>
        </div>
      </div>
    </div>
  );
}

function OperationalMetric({
  label,
  value,
  hint,
  icon: Icon,
  tone,
  technical = false,
  loading = false,
}: {
  label: string;
  value: string;
  hint: string;
  icon: LucideIcon;
  tone: "accent" | "signal" | "caution" | "neutral";
  technical?: boolean;
  loading?: boolean;
}) {
  const tones = {
    accent: "bg-accent-soft text-accent",
    signal: "bg-signal-soft text-signal",
    caution: "bg-caution-soft text-caution",
    neutral: "bg-panel-2 text-ink-soft",
  };
  return (
    <div className="min-w-0 border-l border-rule pl-3 first:border-l-0 first:pl-0">
      <div className="flex items-center gap-2">
        <span className={cx("grid h-8 w-8 shrink-0 place-items-center rounded-[5px]", tones[tone])}>
          <Icon size={16} />
        </span>
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-quiet">
            {label}
          </div>
          {loading ? (
            <span className="mt-1 block h-4 w-28 animate-pulse rounded bg-rule" />
          ) : (
            <div
              className={cx(
                "mt-0.5 truncate text-[16px] font-semibold text-ink",
                technical && "tech text-[13px]",
              )}
            >
              {value}
            </div>
          )}
        </div>
      </div>
      <p className={cx("mt-2 text-[12px] text-quiet", tone === "caution" && "font-medium text-caution")}>
        {hint}
      </p>
    </div>
  );
}

function WifiCard({
  label,
  radio,
  onEdit,
}: {
  label: string;
  radio: WifiRadio;
  onEdit: (anchor: HTMLButtonElement) => void;
}) {
  return (
    <Panel
      className={cx(
        "!p-0 overflow-hidden border-t-[3px]",
        radio.enabled === false ? "border-t-rule-strong" : "border-t-accent",
      )}
    >
      <div className="flex items-center justify-between gap-3 border-b border-rule bg-panel-2 px-3.5 py-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span
            className={cx(
              "grid h-8 w-8 shrink-0 place-items-center rounded-[6px]",
              radio.enabled === false
                ? "bg-panel text-quiet"
                : "bg-accent-soft text-accent",
            )}
          >
            <Wifi size={16} />
          </span>
          <div>
            <h3 className="text-[13px] font-bold">{label}</h3>
            <p
              className={cx(
                "text-[12px] font-semibold",
                radio.enabled === false ? "text-quiet" : "text-good",
              )}
            >
              {radio.enabled === false ? "Desativado" : "Ativo"}
            </p>
          </div>
        </div>
        <Btn
          size="sm"
          variant="outline"
          onClick={(event) => onEdit(event.currentTarget)}
        >
          Editar
        </Btn>
      </div>
      <dl className="grid gap-1.5 px-3.5 py-3 text-[12.5px]">
        <Item k="SSID" v={radio.ssid || "—"} />
        <Item k="Canal" v={radio.channel || "—"} tech />
        <Item k="Largura" v={radio.bandwidth || "—"} tech />
      </dl>
    </Panel>
  );
}
