"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatBitRate, type TrafficPoint } from "@/lib/traffic-rate";

export function TrafficLines({ points }: { points: TrafficPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={points} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
        <CartesianGrid stroke="var(--color-rule)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "var(--color-quiet)" }}
          minTickGap={28}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--color-quiet)" }}
          tickFormatter={(value) => formatBitRate(Number(value))}
          width={72}
        />
        <Tooltip
          formatter={(value, name) => [
            formatBitRate(typeof value === "number" ? value : Number(value)),
            name === "receivedBps" ? "Recebimento" : "Envio",
          ]}
          labelFormatter={(label) => `Amostra ${label}`}
        />
        <Line
          type="monotone"
          dataKey="receivedBps"
          stroke="var(--color-accent)"
          strokeWidth={2}
          dot={false}
          connectNulls={false}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="sentBps"
          stroke="var(--color-signal)"
          strokeWidth={2}
          dot={false}
          connectNulls={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
