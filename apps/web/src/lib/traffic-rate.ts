export type TrafficSample = {
  available: boolean;
  received_bytes: number | null;
  sent_bytes: number | null;
  sampled_at: string;
  counter_updated_at?: string | null;
  refresh_status: "completed" | "queued" | "failed";
};

export type TrafficPoint = {
  timestamp: number;
  label: string;
  receivedBps: number | null;
  sentBps: number | null;
};

function counterRate(
  previous: number | null,
  current: number | null,
  elapsedSeconds: number,
) {
  if (previous === null || current === null || current < previous || elapsedSeconds <= 0) {
    return null;
  }
  return ((current - previous) * 8) / elapsedSeconds;
}

export function trafficPoint(
  previous: TrafficSample,
  current: TrafficSample,
): TrafficPoint | null {
  const timestamp = Date.parse(current.counter_updated_at || current.sampled_at);
  const previousTimestamp = Date.parse(
    previous.counter_updated_at || previous.sampled_at,
  );
  if (!Number.isFinite(timestamp) || !Number.isFinite(previousTimestamp)) return null;
  const elapsedSeconds = (timestamp - previousTimestamp) / 1000;
  if (elapsedSeconds <= 0) return null;
  return {
    timestamp,
    label: new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(timestamp),
    receivedBps: counterRate(
      previous.received_bytes,
      current.received_bytes,
      elapsedSeconds,
    ),
    sentBps: counterRate(previous.sent_bytes, current.sent_bytes, elapsedSeconds),
  };
}

export function formatBitRate(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const units = ["bps", "Kbps", "Mbps", "Gbps"];
  let scaled = Math.max(0, value);
  let unit = 0;
  while (scaled >= 1000 && unit < units.length - 1) {
    scaled /= 1000;
    unit += 1;
  }
  const digits = scaled >= 100 || unit === 0 ? 0 : scaled >= 10 ? 1 : 2;
  return `${scaled.toFixed(digits)} ${units[unit]}`;
}
