"use client";

import { useEffect, useState } from "react";
import { Check, Monitor } from "lucide-react";
import {
  applyAppearance,
  defaultAppearance,
  loadAppearance,
  type AppearancePreferences,
} from "@/lib/appearance";
import { Btn, PageHead, Panel, PanelTitle } from "@/components/ops/primitives";
import { cx } from "@/lib/cx";

export default function AdminAppearancePage() {
  const [draft, setDraft] = useState<AppearancePreferences>(defaultAppearance);
  const [saved, setSaved] = useState(false);
  useEffect(() => setDraft(loadAppearance()), []);
  function save() {
    applyAppearance(draft);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1600);
  }
  return (
    <div className="grid max-w-[900px] gap-3">
      <PageHead
        title="Aparência"
        subtitle="Preferências locais para este navegador"
        actions={
          <Btn onClick={save}>
            {saved ? (
              <>
                <Check size={14} />
                Aplicado
              </>
            ) : (
              "Salvar aparência"
            )}
          </Btn>
        }
      />
      <Panel>
        <PanelTitle
          title="Cor de identidade"
          hint="Aplicada a navegação, ações e foco; estados semânticos não mudam"
        />
        <div className="grid gap-3 sm:grid-cols-3">
          {(
            [
              { id: "teal", label: "Teal operacional", color: "#087f78" },
              { id: "blue", label: "Azul técnico", color: "#176fa6" },
              { id: "indigo", label: "Índigo sóbrio", color: "#5367b0" },
            ] as const
          ).map((option) => (
            <button
              key={option.id}
              onClick={() => setDraft({ ...draft, accent: option.id })}
              className={cx(
                "flex items-center gap-3 rounded-[7px] border p-3 text-left",
                draft.accent === option.id
                  ? "border-accent bg-accent-soft"
                  : "border-rule hover:bg-panel-2",
              )}
            >
              <span
                className="h-9 w-9 rounded-[7px]"
                style={{ background: option.color }}
              />
              <span className="font-bold">{option.label}</span>
              {draft.accent === option.id ? (
                <Check size={15} className="ml-auto text-accent" />
              ) : null}
            </button>
          ))}
        </div>
      </Panel>
      <Panel>
        <PanelTitle
          title="Densidade"
          hint="Ajusta tabelas e áreas operacionais sem esconder informações"
        />
        <div className="grid gap-3 sm:grid-cols-2">
          {(
            [
              {
                id: "comfortable",
                label: "Confortável",
                hint: "Mais respiro para uso prolongado",
              },
              {
                id: "compact",
                label: "Compacta",
                hint: "Mais linhas visíveis no NOC",
              },
            ] as const
          ).map((option) => (
            <button
              key={option.id}
              onClick={() => setDraft({ ...draft, density: option.id })}
              className={cx(
                "rounded-[7px] border p-4 text-left",
                draft.density === option.id
                  ? "border-accent bg-accent-soft"
                  : "border-rule hover:bg-panel-2",
              )}
            >
              <Monitor size={18} className="mb-3 text-accent" />
              <b>{option.label}</b>
              <p className="mt-1 text-[12px] text-quiet">{option.hint}</p>
            </button>
          ))}
        </div>
      </Panel>
      <Panel className="border-t-[3px] border-t-accent">
        <PanelTitle title="Prévia" />
        <div className="rounded-[7px] border border-rule bg-canvas p-4">
          <div className="mb-3 flex items-center justify-between">
            <b>Central de operação</b>
            <span className="rounded-full bg-good-soft px-2 py-1 text-[11px] font-bold text-good">
              ONLINE
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded bg-rule">
            <div className="h-full w-3/4 bg-accent" />
          </div>
        </div>
      </Panel>
    </div>
  );
}
