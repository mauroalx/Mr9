"use client";

import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import {
  Btn,
  Control,
  FieldLabel,
  PageHead,
  Panel,
  StatusSignal,
} from "@/components/ops/primitives";
import { api } from "@/lib/api";
import {
  positionFloatingDialog,
  type FloatingDialogPosition,
} from "@/lib/floating-dialog";
import { FloatingDialog } from "@/components/ops/FloatingDialog";

type Server = {
  id: string;
  name: string;
  base_url: string;
  verify_tls: boolean;
  online_threshold_s: number;
  is_default: boolean;
  has_bearer: boolean;
  credentials_ok: boolean;
};

type ProbeResult = {
  ok?: boolean;
  status_code?: number;
  latency_ms?: number;
};

type ServerForm = {
  name: string;
  base_url: string;
  bearer_token: string;
  verify_tls: boolean;
  online_threshold_s: string;
  is_default: boolean;
  clear_bearer: boolean;
};

const EMPTY_FORM: ServerForm = {
  name: "",
  base_url: "",
  bearer_token: "",
  verify_tls: false,
  online_threshold_s: "300",
  is_default: false,
  clear_bearer: false,
};

export default function AcsServersPage() {
  const [items, setItems] = useState<Server[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [editing, setEditing] = useState<Server | "new" | null>(null);
  const [form, setForm] = useState<ServerForm>(EMPTY_FORM);
  const [dialogPosition, setDialogPosition] =
    useState<FloatingDialogPosition>({ top: 96, left: 24 });
  const [probeOut, setProbeOut] = useState<Record<string, ProbeResult>>({});

  async function load() {
    setItems(await api<Server[]>("/acs/servers"));
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  function openNew(anchor: HTMLElement) {
    setForm({ ...EMPTY_FORM, is_default: items.length === 0 });
    setDialogPosition(positionFloatingDialog(anchor, 560, 650));
    setEditing("new");
  }

  function openEdit(server: Server, anchor: HTMLElement) {
    setForm({
      name: server.name,
      base_url: server.base_url,
      bearer_token: "",
      verify_tls: server.verify_tls,
      online_threshold_s: String(server.online_threshold_s),
      is_default: server.is_default,
      clear_bearer: false,
    });
    setDialogPosition(positionFloatingDialog(anchor, 560, 650));
    setEditing(server);
  }

  function closeDialog() {
    if (busyId) return;
    setEditing(null);
    setForm(EMPTY_FORM);
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    const id = editing === "new" ? "new" : editing?.id;
    if (!id) return;
    setBusyId(id);
    setError(null);
    setMsg(null);
    try {
      const body: Record<string, unknown> = {
        name: form.name.trim(),
        base_url: form.base_url.trim(),
        verify_tls: form.verify_tls,
        online_threshold_s: Number(form.online_threshold_s),
        is_default: form.is_default,
      };
      if (editing === "new" || form.bearer_token.trim()) {
        body.bearer_token = form.bearer_token.trim() || null;
      } else if (form.clear_bearer) {
        body.bearer_token = "";
      }
      await api(
        id === "new" ? "/acs/servers" : `/acs/servers/${id}`,
        {
          method: id === "new" ? "POST" : "PATCH",
          body: JSON.stringify(body),
        },
      );
      setMsg(
        editing === "new"
          ? "Servidor ACS adicionado."
          : "Servidor ACS atualizado.",
      );
      setEditing(null);
      setForm(EMPTY_FORM);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar.");
    } finally {
      setBusyId(null);
    }
  }

  async function probe(id: string) {
    setBusyId(id);
    setError(null);
    try {
      const res = await api<ProbeResult>(`/acs/servers/${id}/probe`, {
        method: "POST",
      });
      setProbeOut((current) => ({ ...current, [id]: res }));
      setMsg(res.ok ? "Conexão com o ACS validada." : "O probe falhou.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro no probe.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="grid gap-3">
      <PageHead
        title="Servidores ACS"
        subtitle="Instâncias GenieACS conectadas ao Mr9"
        actions={
          <Btn onClick={(event) => openNew(event.currentTarget)}>
            <Plus size={15} />
            Novo servidor
          </Btn>
        }
      />
      {msg ? <p className="text-[13px] text-good">{msg}</p> : null}
      {error ? <p className="text-[13px] text-bad">{error}</p> : null}

      <Panel flush>
        <table className="ops-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>URL da NBI</th>
              <th>Autenticação</th>
              <th>Credenciais</th>
              <th>Padrão</th>
              <th>Último probe</th>
              <th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {items.map((server) => {
              const result = probeOut[server.id];
              return (
                <tr key={server.id}>
                  <td className="font-semibold">{server.name}</td>
                  <td className="tech max-w-[260px] truncate">
                    {server.base_url}
                  </td>
                  <td className="text-[12px]">
                    {server.has_bearer ? "Bearer configurado" : "Sem bearer"}
                  </td>
                  <td>
                    <StatusSignal
                      status={
                        server.credentials_ok === false
                          ? "degraded"
                          : server.has_bearer
                            ? "online"
                            : "stale"
                      }
                    />
                  </td>
                  <td>{server.is_default ? "Sim" : "—"}</td>
                  <td className="tech text-[12px]">
                    {result
                      ? result.ok
                        ? `OK · ${result.latency_ms ?? "—"} ms`
                        : `Falha · HTTP ${result.status_code ?? "—"}`
                      : "—"}
                  </td>
                  <td>
                    <div className="flex justify-end gap-1.5">
                      <Btn
                        size="sm"
                        variant="ghost"
                        disabled={busyId === server.id}
                        onClick={() => probe(server.id)}
                      >
                        Probe
                      </Btn>
                      <Btn
                        size="sm"
                        variant="outline"
                        onClick={(event) =>
                          openEdit(server, event.currentTarget)
                        }
                      >
                        Gerenciar
                      </Btn>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!items.length ? (
          <p className="p-4 text-[13px] text-quiet">
            Nenhum servidor cadastrado. Use “Novo servidor” para conectar uma
            instância GenieACS.
          </p>
        ) : null}
      </Panel>

      {editing ? (
        <FloatingDialog
          labelledBy="acs-dialog-title"
          onClose={closeDialog}
          position={dialogPosition}
          width={560}
        >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-rule px-5 py-4">
              <div>
                <h2 id="acs-dialog-title" className="text-[17px] font-bold">
                  {editing === "new"
                    ? "Adicionar servidor ACS"
                    : "Gerenciar servidor ACS"}
                </h2>
                <p className="mt-0.5 text-[12px] text-quiet">
                  A conexão será validada pela NBI antes de salvar.
                </p>
              </div>
              <button
                type="button"
                onClick={closeDialog}
                className="grid h-8 w-8 shrink-0 place-items-center rounded-[5px] text-quiet hover:bg-panel-2 hover:text-ink"
                aria-label="Fechar"
              >
                <X size={17} />
              </button>
            </div>

            <form
              className="ops-scroll grid min-h-0 gap-4 overflow-y-auto p-5"
              onSubmit={save}
            >
              <div className="grid gap-4 rounded-[7px] border border-rule p-4">
                <div>
                  <FieldLabel>Nome</FieldLabel>
                  <Control
                    value={form.name}
                    onChange={(event) =>
                      setForm({ ...form, name: event.target.value })
                    }
                    placeholder="Ex.: GenieACS principal"
                    required
                  />
                </div>
                <div>
                  <FieldLabel>URL da NBI</FieldLabel>
                  <Control
                    type="url"
                    value={form.base_url}
                    onChange={(event) =>
                      setForm({ ...form, base_url: event.target.value })
                    }
                    placeholder="https://acs.exemplo.local:7557"
                    required
                  />
                </div>
                <div>
                  <FieldLabel>
                    {editing === "new"
                      ? "Token bearer (opcional)"
                      : "Novo token bearer (opcional)"}
                  </FieldLabel>
                  <Control
                    type="password"
                    value={form.bearer_token}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        bearer_token: event.target.value,
                        clear_bearer: false,
                      })
                    }
                    placeholder={
                      editing === "new"
                        ? "Cole o token, se necessário"
                        : "Deixe vazio para manter o token atual"
                    }
                    autoComplete="new-password"
                  />
                  {editing !== "new" && editing.has_bearer ? (
                    <label className="mt-2 flex items-center gap-2 text-[12px] text-ink-soft">
                      <input
                        type="checkbox"
                        checked={form.clear_bearer}
                        onChange={(event) =>
                          setForm({
                            ...form,
                            clear_bearer: event.target.checked,
                            bearer_token: "",
                          })
                        }
                        className="h-4 w-4 accent-accent"
                      />
                      Remover autenticação bearer ao salvar
                    </label>
                  ) : null}
                </div>
              </div>

              <div className="grid gap-4 rounded-[7px] border border-rule p-4 sm:grid-cols-2">
                <div>
                  <FieldLabel>Limite para considerar online</FieldLabel>
                  <div className="flex items-center gap-2">
                    <Control
                      type="number"
                      min="30"
                      max="86400"
                      value={form.online_threshold_s}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          online_threshold_s: event.target.value,
                        })
                      }
                      required
                    />
                    <span className="text-[12px] text-quiet">segundos</span>
                  </div>
                </div>
                <div className="grid content-end gap-2 pb-1 text-[12px]">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={form.verify_tls}
                      onChange={(event) =>
                        setForm({ ...form, verify_tls: event.target.checked })
                      }
                      className="h-4 w-4 accent-accent"
                    />
                    Validar certificado TLS
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={form.is_default}
                      onChange={(event) =>
                        setForm({ ...form, is_default: event.target.checked })
                      }
                      className="h-4 w-4 accent-accent"
                    />
                    Usar como servidor padrão
                  </label>
                </div>
              </div>

              <div className="sticky -bottom-5 -mx-5 -mb-5 flex shrink-0 justify-end gap-2 border-t border-rule bg-panel-2 px-5 py-3.5">
                <Btn
                  type="button"
                  variant="ghost"
                  onClick={closeDialog}
                  disabled={Boolean(busyId)}
                >
                  Cancelar
                </Btn>
                <Btn type="submit" disabled={Boolean(busyId)}>
                  {busyId
                    ? "Validando…"
                    : editing === "new"
                      ? "Adicionar servidor"
                      : "Salvar alterações"}
                </Btn>
              </div>
            </form>
        </FloatingDialog>
      ) : null}
    </div>
  );
}
