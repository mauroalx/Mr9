"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Search } from "lucide-react";
import { api } from "@/lib/api";
import { Btn, Control, PageHead, Panel } from "@/components/ops/primitives";
import { cx } from "@/lib/cx";

type AuditEvent = {
  id: string;
  actor: string;
  action: string;
  target: string;
  status: string;
  created_at?: string;
  details?: Record<string, unknown>;
};

export default function AdminAuditPage() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  async function load(targetPage = page) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        limit: "20",
        skip: String(targetPage * 20),
      });
      if (query.trim()) params.set("q", query.trim());
      const result = await api<{ items: AuditEvent[]; has_more?: boolean }>(
        `/audit?${params}`,
      );
      setItems(result.items || []);
      setHasMore(Boolean(result.has_more));
      setPage(targetPage);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Falha ao carregar auditoria",
      );
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div className="grid gap-3">
      <PageHead
        title="Auditoria"
        subtitle="Trilha das ações executadas no Mr9"
        actions={
          <Btn
            variant="outline"
            size="sm"
            onClick={() => load()}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Atualizar
          </Btn>
        }
      />
      <Panel className="border-t-[3px] border-t-signal !p-3">
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            load(0);
          }}
        >
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-3 text-quiet" />
            <Control
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar operador, ação ou dispositivo"
              className="pl-9"
            />
          </div>
          <Btn type="submit" variant="outline">
            Buscar
          </Btn>
        </form>
      </Panel>
      {error ? (
        <div className="rounded-[6px] border border-bad/20 bg-bad-soft p-3 text-[13px] text-bad">
          {error}
        </div>
      ) : null}
      <Panel flush className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="ops-table">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Operador</th>
                <th>Ação</th>
                <th>Alvo</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {items.map((event) => (
                <tr key={event.id}>
                  <td className="tech text-[12px] text-quiet">
                    {event.created_at
                      ? new Date(event.created_at).toLocaleString("pt-BR")
                      : "—"}
                  </td>
                  <td>{event.actor}</td>
                  <td>
                    <b>{event.action}</b>
                  </td>
                  <td className="tech max-w-[320px] truncate text-[12px]">
                    {event.target || "—"}
                  </td>
                  <td>
                    <span
                      className={cx(
                        "rounded-full px-2.5 py-1 text-[11px] font-bold uppercase",
                        event.status === "success"
                          ? "bg-good-soft text-good"
                          : event.status === "queued"
                            ? "bg-caution-soft text-caution"
                            : "bg-bad-soft text-bad",
                      )}
                    >
                      {event.status === "success"
                        ? "Sucesso"
                        : event.status === "queued"
                          ? "Na fila"
                          : "Falhou"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !items.length ? (
            <div className="p-10 text-center text-[13px] text-quiet">
              Nenhum evento de auditoria registrado.
            </div>
          ) : null}
        </div>
        <div className="flex items-center justify-between border-t border-rule bg-panel-2 px-4 py-3">
          <span className="text-[12px] text-quiet">
            {items.length} eventos nesta página
          </span>
          <div className="flex items-center gap-2">
            <Btn
              size="sm"
              variant="outline"
              disabled={!page || loading}
              onClick={() => load(page - 1)}
            >
              Anterior
            </Btn>
            <b>{page + 1}</b>
            <Btn
              size="sm"
              variant="outline"
              disabled={!hasMore || loading}
              onClick={() => load(page + 1)}
            >
              Próxima
            </Btn>
          </div>
        </div>
      </Panel>
    </div>
  );
}
