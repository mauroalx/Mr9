export type Report = {
  score: number;
  grade: string;
  tips: string[];
  checks: Array<{
    id: string;
    title: string;
    status: string;
    penalty: number;
    summary: string;
  }>;
  neighbors?: NeighborNetwork[];
};

export type DiagnosticHistoryItem = {
  id: string;
  score: number;
  grade: string;
  created_at?: string;
  report: Report;
};

export type WifiRadio = {
  root: string;
  ssid: string;
  channel: string;
  autoChannel?: boolean | null;
  bandwidth?: string;
  enabled?: boolean | null;
  index?: number;
};

export type WanProfile = {
  root: string;
  kind: string;
  name: string;
  username: string;
  connection_status: string;
  external_ip: string;
  bytes_received?: number | string | null;
  bytes_sent?: number | string | null;
};

export type PortMapping = {
  root: string;
  wanRoot?: string;
  index?: number;
  enabled?: boolean;
  externalPort?: number;
  internalPort?: number;
  internalClient?: string;
  protocol?: string;
  description?: string;
};

export type DhcpLan = {
  lanIp?: string;
  subnetMask?: string;
  minAddress?: string;
  maxAddress?: string;
  dnsServers?: string;
  leaseTime?: number;
  enabled?: boolean;
} | null;

export type NeighborNetwork = {
  ssid: string;
  channel?: number;
  rssi?: number;
  vendor?: string;
};

export type OpticalTelemetry = {
  detected: true;
  technology: string;
  status: string;
  rxPowerDbm?: number | null;
  txPowerDbm?: number | null;
  distanceMeters?: number | null;
  temperatureC?: number | null;
  voltageV?: number | null;
  biasCurrentMa?: number | null;
  fecErrors?: number | null;
  hecErrors?: number | null;
  crcErrors?: number | null;
};

export type LanPort = {
  index: number;
  name: string;
  status: string;
  enabled?: boolean | null;
  maxBitRate?: string;
  duplexMode?: string;
};

export type Workbench = {
  wifi: WifiRadio[];
  wan: WanProfile[];
  dhcp: DhcpLan;
  hosts: Array<{ hostname: string; ip: string; mac: string; active?: boolean }>;
  lanPorts: LanPort[];
  portmap: PortMapping[];
  neighbors: NeighborNetwork[];
  optical: OpticalTelemetry | null;
};

export function wifiBand(radio: WifiRadio): "24" | "5" {
  const channel = Number(radio.channel);
  if (!Number.isNaN(channel) && channel > 0) return channel <= 14 ? "24" : "5";
  return (radio.index ?? 1) <= 1 ? "24" : "5";
}

export function hasInventoryValue(value: unknown): boolean {
  return value !== null && value !== undefined && value !== "";
}

export function workbenchNeedsRefresh(workbench: Workbench): boolean {
  const wanIncomplete =
    !workbench.wan.length ||
    workbench.wan.some(
      (profile) =>
        !hasInventoryValue(profile.connection_status) ||
        !hasInventoryValue(profile.external_ip) ||
        !hasInventoryValue(profile.bytes_received) ||
        !hasInventoryValue(profile.bytes_sent),
    );
  const wifiIncomplete =
    !workbench.wifi.length ||
    workbench.wifi.some(
      (radio) =>
        !hasInventoryValue(radio.ssid) ||
        !hasInventoryValue(radio.channel) ||
        radio.enabled == null,
    );
  const dhcpIncomplete =
    !workbench.dhcp ||
    !workbench.dhcp.lanIp ||
    !workbench.dhcp.subnetMask ||
    !workbench.dhcp.dnsServers;
  return wanIncomplete || wifiIncomplete || dhcpIncomplete;
}

export function inventoryValue(
  value: string | null,
  loading: boolean,
  online: boolean,
): string {
  if (value) return value;
  if (loading) return "Atualizando…";
  return online ? "Indisponível neste modelo" : "Aguardando CPE online";
}

export function formatBytes(raw?: number | string | null): string | null {
  if (!hasInventoryValue(raw)) return null;
  const value = Number(raw);
  if (!Number.isFinite(value) || value < 0) return null;
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = value === 0 ? 0 : Math.min(Math.floor(Math.log(value) / Math.log(1024)), 4);
  const amount = value / 1024 ** index;
  return `${amount.toLocaleString("pt-BR", { maximumFractionDigits: index ? 2 : 0 })} ${units[index]}`;
}
