import {
  Activity,
  Cable,
  Gauge,
  RadioTower,
  Thermometer,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { Panel, PanelTitle } from "@/components/ops/primitives";
import type { OpticalTelemetry } from "@/lib/device-workbench";

function numeric(value: number | null | undefined, unit = ""): string {
  if (value == null) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}${unit}`;
}

function distance(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1000) return `${(value / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} km`;
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 0 })} m`;
}

function Metric({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: LucideIcon;
}) {
  return (
    <div className="min-w-0 border-l-2 border-l-signal/45 bg-panel-2/55 px-3 py-2.5">
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.05em] text-quiet">
        <Icon size={14} className="text-signal" />
        {label}
      </div>
      <div className="mt-1 text-[17px] font-semibold tabular-nums text-ink">{value}</div>
      <div className="mt-0.5 text-[12px] text-quiet">{hint}</div>
    </div>
  );
}

export function OpticalTelemetryPanel({ optical }: { optical: OpticalTelemetry }) {
  const errors = [
    ["FEC", optical.fecErrors],
    ["HEC", optical.hecErrors],
    ["CRC", optical.crcErrors],
  ] as const;

  return (
    <Panel>
      <PanelTitle
        title="Enlace óptico"
        hint="Telemetria GPON/ONU reportada pelo equipamento"
        action={
          <span className="rounded-[4px] bg-signal-soft px-2 py-1 text-[11px] font-semibold text-signal">
            {optical.technology || "Óptica"}
            {optical.status ? ` · ${optical.status}` : ""}
          </span>
        }
      />
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Potência recebida" value={numeric(optical.rxPowerDbm, " dBm")} hint="Sinal recebido pela ONU" icon={RadioTower} />
        <Metric label="Potência transmitida" value={numeric(optical.txPowerDbm, " dBm")} hint="Sinal transmitido pela ONU" icon={Activity} />
        <Metric label="Distância óptica" value={distance(optical.distanceMeters)} hint="Estimativa reportada pelo enlace" icon={Cable} />
        <Metric label="Temperatura" value={numeric(optical.temperatureC, " °C")} hint="Módulo óptico" icon={Thermometer} />
      </div>
      <div className="mt-3 grid gap-3 border-t border-rule pt-3 lg:grid-cols-[1fr_1.4fr]">
        <div className="grid grid-cols-2 gap-2">
          <Metric label="Tensão" value={numeric(optical.voltageV, " V")} hint="Alimentação do transceptor" icon={Zap} />
          <Metric label="Corrente de bias" value={numeric(optical.biasCurrentMa, " mA")} hint="Laser da ONU" icon={Gauge} />
        </div>
        <div className="rounded-[6px] border border-rule bg-white">
          <div className="border-b border-rule px-3 py-2 text-[12px] font-semibold text-ink">
            Contadores do enlace
          </div>
          <div className="grid grid-cols-3 divide-x divide-rule">
            {errors.map(([label, value]) => (
              <div key={label} className="px-3 py-2.5">
                <div className="text-[11px] font-semibold uppercase tracking-[0.05em] text-quiet">{label}</div>
                <div className="mt-1 text-[17px] font-semibold tabular-nums text-ink">{numeric(value)}</div>
              </div>
            ))}
          </div>
          <p className="border-t border-rule px-3 py-2 text-[11px] text-quiet">
            Valores acumulados. A variação entre amostras é que indica erros atuais.
          </p>
        </div>
      </div>
    </Panel>
  );
}
