import { describe, expect, it } from "vitest";
import { formatBitRate, trafficPoint, type TrafficSample } from "./traffic-rate";

function sample(at: string, received: number, sent: number): TrafficSample {
  return {
    available: true,
    received_bytes: received,
    sent_bytes: sent,
    sampled_at: at,
    counter_updated_at: at,
    refresh_status: "completed",
  };
}

describe("trafficPoint", () => {
  it("converte o delta de bytes em bits por segundo", () => {
    const point = trafficPoint(
      sample("2026-08-04T12:00:00Z", 1_000, 2_000),
      sample("2026-08-04T12:00:05Z", 2_000, 2_500),
    );
    expect(point?.receivedBps).toBe(1_600);
    expect(point?.sentBps).toBe(800);
  });

  it("não cria pico quando o contador reinicia", () => {
    const point = trafficPoint(
      sample("2026-08-04T12:00:00Z", 5_000, 5_000),
      sample("2026-08-04T12:00:05Z", 100, 200),
    );
    expect(point?.receivedBps).toBeNull();
    expect(point?.sentBps).toBeNull();
  });

  it("não cria ponto enquanto o timestamp real do contador não avança", () => {
    const previous = sample("2026-08-04T12:00:00Z", 1_000, 2_000);
    const current = sample("2026-08-04T12:00:05Z", 1_000, 2_000);
    current.counter_updated_at = previous.counter_updated_at;

    expect(trafficPoint(previous, current)).toBeNull();
  });
});

describe("formatBitRate", () => {
  it("escolhe uma unidade legível", () => {
    expect(formatBitRate(1_600)).toBe("1.60 Kbps");
    expect(formatBitRate(12_500_000)).toBe("12.5 Mbps");
  });
});
