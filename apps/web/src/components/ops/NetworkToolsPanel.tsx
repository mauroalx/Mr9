"use client";

import { useState } from "react";
import { Activity, Radio, Route, Server } from "lucide-react";
import { Btn, Control, FieldLabel, Panel, PanelTitle } from "@/components/ops/primitives";

type NetworkToolAction = "ping" | "traceroute";

function ToolCard({
  action,
  title,
  description,
  initialHost,
  busy,
  onRun,
}: {
  action: NetworkToolAction;
  title: string;
  description: string;
  initialHost: string;
  busy: boolean;
  onRun: (action: NetworkToolAction, host: string) => Promise<void>;
}) {
  const [host, setHost] = useState(initialHost);
  const Icon = action === "ping" ? Activity : Route;

  return (
    <Panel className="!p-0 overflow-hidden border-t-[3px] border-t-signal">
      <div className="flex items-start gap-3 border-b border-rule bg-panel-2/65 px-4 py-3.5">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[6px] bg-signal-soft text-signal">
          <Icon size={18} />
        </span>
        <div>
          <h3 className="text-[14px] font-bold text-ink">{title}</h3>
          <p className="mt-0.5 text-[12px] leading-relaxed text-quiet">{description}</p>
        </div>
      </div>
      <form
        className="grid gap-3 px-4 py-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (host.trim()) void onRun(action, host.trim());
        }}
      >
        <div>
          <FieldLabel>Destino</FieldLabel>
          <Control
            value={host}
            onChange={(event) => setHost(event.target.value)}
            placeholder="Host ou endereço IP"
            className="tech"
            disabled={busy}
          />
        </div>
        <Btn type="submit" disabled={busy || !host.trim()} className="w-fit">
          <Icon size={15} />
          Executar {title}
        </Btn>
      </form>
      <div className="flex items-center gap-2 border-t border-rule bg-panel-2/45 px-4 py-2.5 text-[11px] text-quiet">
        <Radio size={13} />
        O ACS solicita uma sessão imediata com o CPE para iniciar o teste.
      </div>
    </Panel>
  );
}

export function NetworkToolsPanel({
  busy,
  onRun,
}: {
  busy: boolean;
  onRun: (action: NetworkToolAction, host: string) => Promise<void>;
}) {
  return (
    <div className="grid gap-3">
      <Panel>
        <PanelTitle
          title="Ferramentas de rede"
          hint="Testes iniciados remotamente pelo CPE através do GenieACS"
          action={
            <span className="inline-flex items-center gap-1.5 rounded-[4px] bg-accent-soft px-2 py-1 text-[11px] font-semibold text-accent">
              <Server size={13} />
              Execução via ACS
            </span>
          }
        />
        <p className="max-w-4xl text-[12.5px] leading-relaxed text-ink-soft">
          Use um endereço alcançável pelo próprio equipamento. Ping confirma alcance e latência;
          Traceroute identifica o caminho e o ponto em que a comunicação deixa de responder.
        </p>
      </Panel>

      <div className="grid gap-3 lg:grid-cols-2">
        <ToolCard
          action="ping"
          title="Ping"
          description="Verifica conectividade, tempo de resposta e perda de pacotes até um destino."
          initialHost="8.8.8.8"
          busy={busy}
          onRun={onRun}
        />
        <ToolCard
          action="traceroute"
          title="Traceroute"
          description="Mapeia os saltos da rota para localizar latência, bloqueio ou interrupção."
          initialHost="1.1.1.1"
          busy={busy}
          onRun={onRun}
        />
      </div>
    </div>
  );
}
