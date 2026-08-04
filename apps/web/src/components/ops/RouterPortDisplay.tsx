import { Cable, Router } from "lucide-react";
import { cx } from "@/lib/cx";
import type { LanPort } from "@/lib/device-workbench";

function portState(port: LanPort): "up" | "down" | "disabled" | "unknown" {
  if (port.enabled === false) return "disabled";
  const status = port.status.trim().toLowerCase();
  if (["up", "connected", "active"].includes(status)) return "up";
  if (["down", "disconnected", "inactive", "nolink"].includes(status)) return "down";
  return "unknown";
}

const stateLabels = {
  up: "Up",
  down: "Down",
  disabled: "Desabilitada",
  unknown: "Não informado",
};

export function RouterPortDisplay({ ports }: { ports: LanPort[] }) {
  const visiblePorts: Array<LanPort | null> = ports.length
    ? ports
    : Array.from({ length: 4 }, () => null);
  const upCount = ports.filter((port) => portState(port) === "up").length;

  function portDetails(port: LanPort): string {
    const rate = port.maxBitRate
      ? /^\d+(\.\d+)?$/.test(port.maxBitRate)
        ? `${port.maxBitRate} Mb/s`
        : port.maxBitRate
      : "";
    return [rate, port.duplexMode].filter(Boolean).join(" · ") || "Velocidade não informada";
  }

  return (
    <section className="mt-4 overflow-hidden rounded-[7px] border border-rule bg-panel-2/40">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule bg-panel-2 px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-[6px] bg-signal-soft text-signal">
            <Router size={17} />
          </span>
          <div>
            <h3 className="text-[13px] font-bold text-ink">Portas Ethernet</h3>
            <p className="text-[12px] text-quiet">
              {ports.length ? `${upCount} de ${ports.length} portas com link` : "Interfaces não reportadas por este modelo"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[11px] text-quiet">
          <span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-good" />Up</span>
          <span className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full bg-rule-strong" />Down</span>
        </div>
      </div>

      <div className="grid gap-5 px-4 py-5 lg:grid-cols-[280px_1fr] lg:items-center">
        <div className="mx-auto w-full max-w-[280px]">
          <div className="rounded-t-[18px] border border-rule-strong bg-white px-6 pb-4 pt-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <span className="text-[12px] font-bold tracking-wide text-ink">Mr9 Router</span>
              <span className="h-2 w-2 rounded-full bg-good shadow-[0_0_0_3px_rgba(16,185,129,0.12)]" />
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {visiblePorts.map((port, index) => {
                const state = port ? portState(port) : "unknown";
                return (
                  <div key={port?.index ?? index} className="grid justify-items-center gap-1">
                    <span
                      className={cx(
                        "relative h-8 w-10 rounded-[4px] border-2 bg-panel-2 after:absolute after:inset-x-2 after:top-1 after:h-1 after:bg-rule-strong",
                        state === "up" && "border-good bg-good-soft after:bg-good",
                        state === "down" && "border-rule-strong",
                        state === "disabled" && "border-rule bg-panel text-quiet opacity-55",
                        state === "unknown" && "border-dashed border-rule-strong",
                      )}
                      title={port ? `${port.name}: ${stateLabels[state]}` : "Porta não reportada"}
                    />
                    <span className="text-[10px] font-semibold text-quiet">{port?.index ?? index + 1}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="mx-auto h-2 w-[88%] rounded-b-full bg-rule-strong/70" />
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {ports.map((port) => {
            const state = portState(port);
            return (
              <div key={port.index} className="rounded-[6px] border border-rule bg-white px-3 py-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2 text-[12px] font-bold text-ink"><Cable size={14} className="text-signal" />{port.name}</span>
                  <span className={cx("text-[11px] font-semibold", state === "up" ? "text-good" : "text-quiet")}>{stateLabels[state]}</span>
                </div>
                <p className="mt-1.5 text-[11px] text-quiet">
                  {portDetails(port)}
                </p>
              </div>
            );
          })}
          {!ports.length ? (
            <div className="sm:col-span-2 xl:col-span-4 rounded-[6px] border border-dashed border-rule px-3 py-4 text-center text-[12px] text-quiet">
              O equipamento não publicou o estado individual das portas LAN no inventário ACS.
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
