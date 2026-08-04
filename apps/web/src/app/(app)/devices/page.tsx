"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Filter, RefreshCw, Search, X } from "lucide-react";
import { api } from "@/lib/api";
import { cx } from "@/lib/cx";
import { formatDateTime } from "@/lib/format";
import {
  buildInventorySearchParams,
  type InventoryFilters,
} from "@/lib/device-inventory";
import {
  Btn,
  Control,
  FieldLabel,
  PageHead,
  Panel,
  SelectControl,
  StatusSignal,
} from "@/components/ops/primitives";

type DeviceRow = {
  id: string;
  serial?: string;
  manufacturer?: string;
  product_class?: string;
  software_version?: string;
  pppoe_username?: string;
  online?: boolean;
  last_inform?: string;
  tags?: string[];
};

function DeviceTableSkeleton() {
  return (
    <>
      {Array.from({ length: 10 }, (_, index) => (
        <tr key={index} aria-hidden="true" className="animate-pulse">
          <td>
            <span className="block h-4 w-4 rounded border border-rule bg-panel-2" />
          </td>
          <td>
            <span className="block h-6 w-20 rounded-full bg-good-soft" />
          </td>
          <td>
            <span className="block h-3 w-36 rounded bg-rule" />
            <span className="mt-2 block h-2.5 w-24 rounded bg-panel-2" />
          </td>
          <td>
            <span className="block h-3 w-32 rounded bg-rule" />
            <span className="mt-2 block h-2.5 w-20 rounded bg-panel-2" />
          </td>
          <td>
            <span className="block h-3 w-36 rounded bg-rule" />
          </td>
          <td>
            <span className="block h-5 w-16 rounded bg-panel-2" />
          </td>
          <td>
            <span className="block h-3 w-32 rounded bg-rule" />
          </td>
          <td>
            <span className="ml-auto block h-8 w-24 rounded bg-panel-2" />
          </td>
        </tr>
      ))}
    </>
  );
}

function DevicesInner() {
  const sp = useSearchParams();
  const urlQuery = sp.get("q") || "";
  const [items, setItems] = useState<DeviceRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [debouncing, setDebouncing] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [advOpen, setAdvOpen] = useState(false);
  const [filters, setFilters] = useState<InventoryFilters>({
    q: sp.get("q") || "",
    status:
      sp.get("online") === "1"
        ? "online"
        : sp.get("online") === "0"
          ? "offline"
          : "all",
    manufacturer: "all",
    model: "all",
    firmware: "all",
    tag: "all",
  });
  const requestRef = useRef<AbortController | null>(null);
  const lastRequestedQuery = useRef(filters.q);

  async function load(targetPage = page, queryOverride?: string) {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const queryText = queryOverride ?? filters.q;
      const params = buildInventorySearchParams(filters, targetPage, queryText);
      const res = await api<{
        items: DeviceRow[];
        has_more?: boolean;
        total?: number;
      }>(
        `/acs/devices?${params}`,
        {
          signal: controller.signal,
        },
      );
      setItems(res.items || []);
      setHasMore(Boolean(res.has_more));
      setTotal(res.total ?? 0);
      setPage(targetPage);
      setSelected(new Set());
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setError(e instanceof Error ? e.message : "Erro");
      setItems([]);
      setTotal(0);
    } finally {
      if (requestRef.current === controller) setLoading(false);
    }
  }

  useEffect(() => {
    setPage(0);
    load(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.status]);

  useEffect(() => {
    if (urlQuery === filters.q) return;
    setDebouncing(false);
    setFilters((current) => ({ ...current, q: urlQuery }));
    lastRequestedQuery.current = urlQuery;
    load(0, urlQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlQuery]);

  useEffect(() => {
    if (filters.q === lastRequestedQuery.current) {
      setDebouncing(false);
      return;
    }
    requestRef.current?.abort();
    setDebouncing(true);
    const timer = window.setTimeout(() => {
      setDebouncing(false);
      lastRequestedQuery.current = filters.q;
      load(0, filters.q);
    }, 400);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.q]);

  useEffect(() => () => requestRef.current?.abort(), []);

  const manufacturers = useMemo(
    () => [...new Set(items.map((i) => i.manufacturer || "—"))].sort(),
    [items],
  );
  const models = useMemo(
    () => [...new Set(items.map((i) => i.product_class || "—"))].sort(),
    [items],
  );
  const firmwares = useMemo(
    () => [...new Set(items.map((i) => i.software_version || "—"))].sort(),
    [items],
  );
  const tags = useMemo(
    () => [...new Set(items.flatMap((i) => i.tags || []))].sort(),
    [items],
  );

  const rows = items;

  function set<K extends keyof InventoryFilters>(key: K, value: InventoryFilters[K]) {
    setFilters((f) => ({ ...f, [key]: value }));
  }

  const activeCount = [
    filters.status !== "all",
    filters.manufacturer !== "all",
    filters.model !== "all",
    filters.firmware !== "all",
    filters.tag !== "all",
  ].filter(Boolean).length;
  const controlsDisabled = loading || debouncing;

  return (
    <div className="device-inventory grid gap-3">
      <PageHead
        title="Dispositivos"
        subtitle={`${total.toLocaleString("pt-BR")} encontrados · ${rows.length} nesta página${loading ? " · carregando" : debouncing ? " · aguardando busca" : ""}`}
        actions={
          <>
            <Btn
              variant="outline"
              size="sm"
              onClick={() => load()}
              disabled={controlsDisabled}
            >
              <RefreshCw size={13} /> Atualizar
            </Btn>
            <Btn size="sm" onClick={() => load()} disabled={controlsDisabled}>
              Sincronizar
            </Btn>
          </>
        }
      />

      <Panel className="!p-3 border-t-[3px] border-t-signal">
        <div className="mb-3 flex items-center gap-2 border-b border-rule pb-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-[6px] bg-signal-soft text-signal">
            <Search size={16} />
          </span>
          <div>
            <div className="text-[13px] font-bold">Localizar na frota</div>
            <div className="text-[12px] text-quiet">
              Combine busca livre e filtros operacionais
            </div>
          </div>
        </div>
        <div className="grid gap-2 lg:grid-cols-12 lg:items-end">
          <div className="lg:col-span-3">
            <FieldLabel>Status</FieldLabel>
            <SelectControl
              disabled={controlsDisabled}
              value={filters.status}
              onChange={(e) =>
                set("status", e.target.value as InventoryFilters["status"])
              }
            >
              <option value="all">Todos</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
            </SelectControl>
          </div>
          <div className="lg:col-span-5">
            <FieldLabel>Servidor ACS</FieldLabel>
            <SelectControl
              defaultValue="current"
              disabled
              title="Use o seletor da topbar"
            >
              <option value="current">Instância ativa (topbar)</option>
            </SelectControl>
          </div>
          <div className="flex lg:col-span-2 lg:justify-end">
            <Btn
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => setAdvOpen(true)}
              disabled={controlsDisabled}
            >
              <Filter size={13} /> Filtros
              {activeCount ? (
                <span className="rounded-full bg-accent px-1.5 text-[10px] text-accent-fg">
                  {activeCount}
                </span>
              ) : null}
            </Btn>
          </div>
        </div>
        <form
          className="mt-2"
          onSubmit={(e) => {
            e.preventDefault();
            setDebouncing(false);
            lastRequestedQuery.current = filters.q;
            load(0);
          }}
        >
          <Control
            placeholder="Serial, PPPoE, IP, modelo, cliente…"
            value={filters.q}
            onChange={(e) => set("q", e.target.value)}
          />
        </form>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {[
            {
              label: "Todos",
              apply: () =>
                setFilters((f) => ({ ...f, status: "all" })),
            },
            { label: "Online", apply: () => set("status", "online") },
            { label: "Offline", apply: () => set("status", "offline") },
          ].map((v) => (
            <button
              key={v.label}
              type="button"
              onClick={v.apply}
              disabled={controlsDisabled}
              className={cx(
                "rounded-full border px-3 py-1 text-[12px] font-bold transition disabled:cursor-wait disabled:opacity-50",
                (v.label === "Online" && filters.status === "online") ||
                  (v.label === "Offline" && filters.status === "offline") ||
                  (v.label === "Todos" && filters.status === "all")
                  ? v.label === "Online"
                    ? "border-good/25 bg-good-soft text-good"
                    : v.label === "Offline"
                      ? "border-bad/25 bg-bad-soft text-bad"
                      : "border-accent/25 bg-accent-soft text-accent"
                  : "border-rule bg-panel-2 text-ink-soft hover:border-accent",
              )}
            >
              {v.label}
            </button>
          ))}
        </div>
      </Panel>

      {selected.size > 0 ? (
        <div className="flex flex-wrap items-center gap-2 border border-accent/30 bg-accent-soft px-3 py-2 text-[12px]">
          <strong>{selected.size} selecionados</strong>
          <Btn size="sm" variant="outline" disabled>
            Sync
          </Btn>
          <Btn size="sm" variant="ghost" onClick={() => setSelected(new Set())}>
            Limpar
          </Btn>
        </div>
      ) : null}

      {error ? <p className="text-[13px] text-bad">{error}</p> : null}

      <Panel flush className="overflow-hidden border-t-[3px] border-t-accent">
        <div className="ops-scroll max-h-[calc(100vh-300px)] overflow-auto">
          <table className="ops-table">
            <thead>
              <tr>
                <th className="w-9">
                  <input
                    type="checkbox"
                    disabled={loading}
                    checked={rows.length > 0 && selected.size === rows.length}
                    onChange={() =>
                      setSelected(
                        selected.size === rows.length
                          ? new Set()
                          : new Set(rows.map((r) => r.id)),
                      )
                    }
                    aria-label="Selecionar"
                  />
                </th>
                <th>Estado</th>
                <th>Identificação</th>
                <th>Usuário PPPoE</th>
                <th>Modelo / SW</th>
                <th>Tags</th>
                <th>Inform</th>
                <th className="w-28 text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <DeviceTableSkeleton />
              ) : (
                rows.map((d) => (
                  <tr
                    key={d.id}
                    className={
                      d.online
                        ? "[&>td:first-child]:border-l-[3px] [&>td:first-child]:border-l-good"
                        : "[&>td:first-child]:border-l-[3px] [&>td:first-child]:border-l-bad"
                    }
                  >
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(d.id)}
                        onChange={() => {
                          const n = new Set(selected);
                          if (n.has(d.id)) n.delete(d.id);
                          else n.add(d.id);
                          setSelected(n);
                        }}
                        aria-label={d.serial || d.id}
                      />
                    </td>
                    <td>
                      <StatusSignal status={Boolean(d.online)} />
                    </td>
                    <td>
                      <Link
                        href={`/devices/${encodeURIComponent(d.id)}`}
                        className="tech text-[12px] font-bold text-accent hover:underline"
                      >
                        {d.serial || d.id}
                      </Link>
                      <div className="text-[11px] text-quiet">
                        {d.manufacturer || "—"}
                      </div>
                    </td>
                    <td>
                      <div
                        className="tech max-w-[220px] truncate text-[12px]"
                        title={d.pppoe_username || undefined}
                      >
                        {d.pppoe_username || "—"}
                      </div>
                    </td>
                    <td>
                      <div className="max-w-[220px] truncate font-semibold">
                        {d.product_class || "—"}
                      </div>
                      <div className="tech text-[10px] text-quiet">
                        {d.software_version || "—"}
                      </div>
                    </td>
                    <td>
                      <div className="flex max-w-[140px] flex-wrap gap-1">
                        {(d.tags || []).slice(0, 2).map((t) => (
                          <span
                            key={t}
                            className="rounded-[2px] bg-panel-2 px-1.5 py-0.5 text-[10px] font-semibold text-quiet"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="tech text-[11px] text-quiet">
                      {formatDateTime(d.last_inform)}
                    </td>
                    <td className="text-right">
                      <Link
                        href={`/devices/${encodeURIComponent(d.id)}`}
                        className="inline-flex h-8 items-center gap-1.5 rounded-[5px] border border-rule bg-white px-2.5 text-[12px] font-bold text-ink-soft transition hover:border-accent hover:bg-accent-soft hover:text-accent"
                      >
                        Gerenciar <ArrowRight size={12} />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          {!loading && !rows.length ? (
            <p className="px-4 py-10 text-center text-[13px] text-quiet">
              Nenhum dispositivo.
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-rule bg-panel-2 px-4 py-3 text-[12px] text-quiet">
          <span>
            {loading ? (
              "Atualizando inventário…"
            ) : (
              <>
                Exibindo {rows.length ? page * 10 + 1 : 0}–
                {page * 10 + rows.length} de {total.toLocaleString("pt-BR")} ·
                10 por página
              </>
            )}
          </span>
          <div className="flex items-center gap-2">
            <Btn
              size="sm"
              variant="outline"
              disabled={page === 0 || loading}
              onClick={() => load(page - 1)}
            >
              Anterior
            </Btn>
            <span className="min-w-10 text-center font-bold text-ink">
              {page + 1}/{Math.max(1, Math.ceil(total / 10))}
            </span>
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

      {advOpen ? (
        <div className="fixed inset-0 z-50 flex justify-end">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="Fechar"
            onClick={() => setAdvOpen(false)}
          />
          <div className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-rule bg-panel shadow-xl">
            <div className="flex items-center justify-between border-b border-rule px-4 py-3">
              <div>
                <h2 className="text-[15px] font-bold">Filtros avançados</h2>
                <p className="text-[11px] text-quiet">Inventário ACS</p>
              </div>
              <button
                type="button"
                onClick={() => setAdvOpen(false)}
                aria-label="Fechar"
              >
                <X size={16} />
              </button>
            </div>
            <div className="ops-scroll grid flex-1 gap-3 overflow-auto p-4">
              <div>
                <FieldLabel>Fabricante</FieldLabel>
                <SelectControl
                  value={filters.manufacturer}
                  onChange={(e) => set("manufacturer", e.target.value)}
                >
                  <option value="all">Todos</option>
                  {manufacturers.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </SelectControl>
              </div>
              <div>
                <FieldLabel>Modelo</FieldLabel>
                <SelectControl
                  value={filters.model}
                  onChange={(e) => set("model", e.target.value)}
                >
                  <option value="all">Todos</option>
                  {models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </SelectControl>
              </div>
              <div>
                <FieldLabel>Firmware</FieldLabel>
                <SelectControl
                  value={filters.firmware}
                  onChange={(e) => set("firmware", e.target.value)}
                >
                  <option value="all">Todos</option>
                  {firmwares.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </SelectControl>
              </div>
              <div>
                <FieldLabel>Tag</FieldLabel>
                <SelectControl
                  value={filters.tag}
                  onChange={(e) => set("tag", e.target.value)}
                >
                  <option value="all">Todas</option>
                  {tags.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </SelectControl>
              </div>
            </div>
            <div className="flex justify-between gap-2 border-t border-rule px-4 py-3">
              <Btn
                variant="ghost"
                onClick={() =>
                  setFilters((f) => ({
                    ...f,
                    manufacturer: "all",
                    model: "all",
                    firmware: "all",
                    tag: "all",
                  }))
                }
              >
                Limpar
              </Btn>
              <Btn
                onClick={() => {
                  setAdvOpen(false);
                  load();
                }}
              >
                Aplicar
              </Btn>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function DevicesPage() {
  return (
    <Suspense fallback={<p className="text-[13px] text-quiet">Carregando…</p>}>
      <DevicesInner />
    </Suspense>
  );
}
