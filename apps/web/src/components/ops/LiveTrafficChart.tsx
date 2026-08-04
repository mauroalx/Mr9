"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Pause, Play, RotateCcw } from "lucide-react";
import { Btn, Panel, PanelTitle } from "@/components/ops/primitives";
import { api } from "@/lib/api";
import {
  formatBitRate,
  trafficPoint,
  type TrafficPoint,
  type TrafficSample,
} from "@/lib/traffic-rate";

const SAMPLE_INTERVAL_MS = 5_000;
const MAX_POINTS = 60;
const TrafficLines = dynamic(
  () => import("@/components/ops/TrafficLines").then((module) => module.TrafficLines),
  { ssr: false },
);

export function LiveTrafficChart({ deviceId, online }: { deviceId: string; online: boolean }) {
  const [running, setRunning] = useState(false);
  const [sampling, setSampling] = useState(false);
  const [points, setPoints] = useState<TrafficPoint[]>([]);
  const [latest, setLatest] = useState<TrafficPoint | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queued, setQueued] = useState(false);
  const previousRef = useRef<TrafficSample | null>(null);

  useEffect(() => {
    if (!running || !online) return;
    let cancelled = false;
    let timer: number | undefined;
    let controller: AbortController | undefined;

    async function collect() {
      const startedAt = Date.now();
      controller = new AbortController();
      setSampling(true);
      try {
        const sample = await api<TrafficSample>(
          `/acs/devices/${encodeURIComponent(deviceId)}/actions`,
          {
            method: "POST",
            body: JSON.stringify({ action: "traffic_sample", params: {} }),
            signal: controller.signal,
          },
        );
        if (cancelled) return;
        if (sample.refresh_status === "failed") {
          setQueued(false);
          setError("O ACS recusou a atualização dos contadores nesta amostra.");
        } else if (!sample.available) {
          setQueued(sample.refresh_status === "queued");
          setError("Este CPE não informou contadores de tráfego compatíveis.");
        } else {
          setQueued(sample.refresh_status === "queued");
          setError(null);
          const previous = previousRef.current;
          if (previous) {
            const point = trafficPoint(previous, sample);
            if (point) {
              setLatest(point);
              setPoints((current) => [...current, point].slice(-MAX_POINTS));
            }
          }
          previousRef.current = sample;
        }
      } catch (reason) {
        if (cancelled || (reason instanceof DOMException && reason.name === "AbortError")) return;
        setError(reason instanceof Error ? reason.message : "Falha ao coletar o tráfego.");
      } finally {
        if (!cancelled) {
          setSampling(false);
          const remaining = Math.max(0, SAMPLE_INTERVAL_MS - (Date.now() - startedAt));
          timer = window.setTimeout(collect, remaining);
        }
      }
    }

    collect();
    return () => {
      cancelled = true;
      controller?.abort();
      if (timer) window.clearTimeout(timer);
    };
  }, [deviceId, online, running]);

  function continueSampling() {
    previousRef.current = null;
    setError(null);
    setQueued(false);
    setRunning(true);
  }

  function clear() {
    previousRef.current = null;
    setPoints([]);
    setLatest(null);
  }

  return (
    <Panel>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PanelTitle
          title="Tráfego em tempo real"
          hint="Taxa calculada pelos contadores WAN a cada 5 segundos"
        />
        <div className="flex items-center gap-2">
          <Btn variant="outline" size="sm" onClick={clear} disabled={!points.length}>
            <RotateCcw size={13} /> Limpar
          </Btn>
          {running ? (
            <Btn variant="outline" size="sm" onClick={() => setRunning(false)}>
              <Pause size={13} /> Pausar
            </Btn>
          ) : (
            <Btn size="sm" onClick={continueSampling} disabled={!online}>
              <Play size={13} /> Continuar
            </Btn>
          )}
        </div>
      </div>

      <div className="mt-3 grid gap-3 border-y border-rule py-3 sm:grid-cols-2">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-[0.08em] text-quiet">
            Recebimento atual
          </div>
          <div className="mt-1 text-[20px] font-bold tabular-nums text-accent">
            {formatBitRate(latest?.receivedBps)}
          </div>
        </div>
        <div className="sm:border-l sm:border-rule sm:pl-4">
          <div className="text-[11px] font-bold uppercase tracking-[0.08em] text-quiet">
            Envio atual
          </div>
          <div className="mt-1 text-[20px] font-bold tabular-nums text-signal">
            {formatBitRate(latest?.sentBps)}
          </div>
        </div>
      </div>

      <div className="mt-3 h-[260px]">
        {points.length ? (
          <TrafficLines points={points} />
        ) : (
          <div className="grid h-full place-items-center border border-dashed border-rule bg-panel-2 px-6 text-center text-[13px] text-quiet">
            <div>
              <p className="font-semibold text-ink">
                {sampling ? "Coletando a primeira amostra…" : "Monitoramento pausado"}
              </p>
              <p className="mt-1">
                {online
                  ? "Continue para formar a série; são necessárias duas amostras para calcular a taxa."
                  : "O CPE precisa estar online para atualizar os contadores."}
              </p>
            </div>
          </div>
        )}
      </div>
      <div className="mt-2 flex min-h-5 items-center justify-between gap-3 text-[12px] text-quiet">
        <span>
          {running
            ? sampling
              ? "Atualizando o CPE…"
              : queued
                ? "Atualização enfileirada no ACS; aguardando novo contador"
                : "Próxima amostra em até 5 s"
            : "Pausado"}
        </span>
        {error ? <span className="text-bad">{error}</span> : null}
      </div>
    </Panel>
  );
}
