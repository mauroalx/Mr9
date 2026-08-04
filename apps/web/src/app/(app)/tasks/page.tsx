"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RefreshCw, RotateCcw, Search, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import {
  Btn,
  Control,
  PageHead,
  Panel,
  StatusSignal,
} from "@/components/ops/primitives";

type AcsTask = {
  _id?: string;
  id?: string;
  device?: string;
  name?: string;
  timestamp?: string;
  expiry?: string;
  retries?: number;
  parameterValues?: unknown[];
};

export default function TasksPage() {
  const [items, setItems] = useState<AcsTask[]>([]);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  async function load(targetPage = page) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        limit: "20",
        skip: String(targetPage * 20),
      });
      if (query.trim()) params.set("q", query.trim());
      const result = await api<{ items: AcsTask[]; has_more?: boolean }>(
        `/acs/tasks?${params}`,
      );
      setItems(result.items || []);
      setHasMore(Boolean(result.has_more));
      setPage(targetPage);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Falha ao carregar tarefas",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function retry(task: AcsTask) {
    const id = task._id || task.id;
    if (!id) return;
    setError(null);
    setNotice(null);
    setActiveTaskId(id);
    try {
      await api(`/acs/tasks/${encodeURIComponent(id)}/retry`, {
        method: "POST",
      });
      setNotice("Tarefa reenviada ao GenieACS.");
      await load();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Falha ao repetir tarefa",
      );
    } finally {
      setActiveTaskId(null);
    }
  }

  async function remove(task: AcsTask) {
    const id = task._id || task.id;
    if (!id) return;
    setError(null);
    setNotice(null);
    setActiveTaskId(id);
    try {
      await api(`/acs/tasks/${encodeURIComponent(id)}`, { method: "DELETE" });
      setItems((current) =>
        current.filter((item) => (item._id || item.id) !== id),
      );
      setNotice("Tarefa excluída da fila.");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Falha ao excluir tarefa",
      );
    } finally {
      setActiveTaskId(null);
    }
  }

  return (
    <div className="grid gap-3">
      <PageHead
        title="Tarefas"
        subtitle="Fila operacional do servidor GenieACS ativo"
        actions={
          <>
            <Btn
              variant="outline"
              size="sm"
              onClick={() => load()}
              disabled={loading}
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Atualizar
            </Btn>
            <Link href="/devices">
              <Btn size="sm">Abrir inventário</Btn>
            </Link>
          </>
        }
      />
      <Panel className="border-t-[3px] border-t-caution !p-3">
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
              placeholder="Buscar por dispositivo ou tipo de tarefa"
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
      {notice ? (
        <div
          role="status"
          className="rounded-[6px] border border-good/20 bg-good-soft p-3 text-[13px] font-medium text-good"
        >
          {notice}
        </div>
      ) : null}
      <Panel flush className="overflow-hidden border-t-[3px] border-t-accent">
        <div className="overflow-x-auto">
          <table className="ops-table">
            <thead>
              <tr>
                <th>Estado</th>
                <th>Tarefa</th>
                <th>Dispositivo</th>
                <th>Criada</th>
                <th>Tentativas</th>
                <th className="text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((task, index) => {
                const id = task._id || task.id || `${task.device}-${index}`;
                return (
                  <tr key={id}>
                    <td>
                      <StatusSignal status="stale" />
                    </td>
                    <td>
                      <b>{task.name || "Tarefa GenieACS"}</b>
                      {task.parameterValues?.length ? (
                        <div className="text-[12px] text-quiet">
                          {task.parameterValues.length} parâmetros
                        </div>
                      ) : null}
                    </td>
                    <td>
                      <Link
                        className="tech text-[12px] font-bold text-accent hover:underline"
                        href={`/devices/${encodeURIComponent(task.device || "")}`}
                      >
                        {task.device || "—"}
                      </Link>
                    </td>
                    <td className="tech text-[12px] text-quiet">
                      {task.timestamp
                        ? new Date(task.timestamp).toLocaleString("pt-BR")
                        : "—"}
                    </td>
                    <td>{task.retries ?? 0}</td>
                    <td>
                      <div className="flex justify-end gap-1">
                        <Btn
                          size="sm"
                          variant="ghost"
                          disabled={activeTaskId === (task._id || task.id)}
                          onClick={() => retry(task)}
                        >
                          <RotateCcw
                            size={13}
                            className={
                              activeTaskId === (task._id || task.id)
                                ? "animate-spin"
                                : ""
                            }
                          />
                          {activeTaskId === (task._id || task.id)
                            ? "Processando"
                            : "Repetir"}
                        </Btn>
                        <Btn
                          size="sm"
                          variant="ghost"
                          className="text-bad"
                          disabled={activeTaskId === (task._id || task.id)}
                          onClick={() => remove(task)}
                        >
                          <Trash2 size={13} />
                          Excluir
                        </Btn>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!loading && !items.length ? (
            <div className="p-10 text-center text-[13px] text-quiet">
              Nenhuma tarefa pendente no servidor selecionado.
            </div>
          ) : null}
        </div>
        <div className="flex items-center justify-between border-t border-rule bg-panel-2 px-4 py-3 text-[12px] text-quiet">
          <span>{items.length} tarefas nesta página</span>
          <div className="flex items-center gap-2">
            <Btn
              size="sm"
              variant="outline"
              disabled={!page || loading}
              onClick={() => load(page - 1)}
            >
              Anterior
            </Btn>
            <b className="text-ink">{page + 1}</b>
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
