"use client";

import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import { Btn, Control, FieldLabel, PageHead, Panel } from "@/components/ops/primitives";
import { api } from "@/lib/api";
import { cx } from "@/lib/cx";
import {
  positionFloatingDialog,
  type FloatingDialogPosition,
} from "@/lib/floating-dialog";
import { FloatingDialog } from "@/components/ops/FloatingDialog";
import { permissionsByModule } from "@/lib/permissions-meta";

type Group = { id: string; name: string; permissions: string[] };

const DEFAULT_PERMISSIONS = ["acs.access", "dashboard.view"];

export default function AdminGroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [editing, setEditing] = useState<Group | "new" | null>(null);
  const [name, setName] = useState("");
  const [perms, setPerms] = useState<string[]>(DEFAULT_PERMISSIONS);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [dialogPosition, setDialogPosition] =
    useState<FloatingDialogPosition>({ top: 96, left: 24 });
  const modules = permissionsByModule();

  async function refresh() {
    setGroups(await api<Group[]>("/security/groups"));
  }

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);

  function openNew(anchor: HTMLElement) {
    setName("");
    setPerms(DEFAULT_PERMISSIONS);
    setDialogPosition(positionFloatingDialog(anchor, 680, 760));
    setEditing("new");
  }

  function openEdit(group: Group, anchor: HTMLElement) {
    setName(group.name);
    setPerms(group.permissions);
    setDialogPosition(positionFloatingDialog(anchor, 680, 760));
    setEditing(group);
  }

  function closeDialog() {
    if (busy) return;
    setEditing(null);
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!editing) return;
    setError(null);
    setMsg(null);
    setBusy(true);
    try {
      await api(
        editing === "new"
          ? "/security/groups"
          : `/security/groups/${editing.id}`,
        {
          method: editing === "new" ? "POST" : "PATCH",
          body: JSON.stringify({ name: name.trim(), permissions: perms }),
        },
      );
      setMsg(editing === "new" ? "Grupo criado." : "Grupo atualizado.");
      setEditing(null);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar.");
    } finally {
      setBusy(false);
    }
  }

  function toggle(permission: string, checked: boolean) {
    setPerms((current) =>
      checked
        ? [...new Set([...current, permission])]
        : current.filter((item) => item !== permission),
    );
  }

  function toggleModule(permissionIds: string[], checked: boolean) {
    setPerms((current) =>
      checked
        ? [...new Set([...current, ...permissionIds])]
        : current.filter((item) => !permissionIds.includes(item)),
    );
  }

  return (
    <div className="grid gap-3">
      <PageHead
        title="Grupos"
        subtitle="Perfis de acesso atribuídos aos usuários do Mr9"
        actions={
          <Btn onClick={(event) => openNew(event.currentTarget)}>
            <Plus size={15} />
            Novo grupo
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
              <th>Escopo de acesso</th>
              <th>Permissões</th>
              <th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((group) => {
              const moduleLabels = modules
                .filter((module) =>
                  module.items.some((item) =>
                    group.permissions.includes(item.id),
                  ),
                )
                .map((module) => module.label);
              return (
                <tr key={group.id}>
                  <td className="font-semibold">{group.name}</td>
                  <td>
                    <div className="flex flex-wrap gap-1.5">
                      {moduleLabels.map((label) => (
                        <span
                          key={label}
                          className="rounded-full border border-rule bg-panel-2 px-2 py-0.5 text-[11px] font-medium text-ink-soft"
                        >
                          {label}
                        </span>
                      ))}
                      {!moduleLabels.length ? (
                        <span className="text-[12px] text-quiet">
                          Sem acesso configurado
                        </span>
                      ) : null}
                    </div>
                  </td>
                  <td className="text-[12px] text-ink-soft">
                    {group.permissions.length}{" "}
                    {group.permissions.length === 1 ? "permissão" : "permissões"}
                  </td>
                  <td className="text-right">
                    <Btn
                      size="sm"
                      variant="outline"
                      onClick={(event) => openEdit(group, event.currentTarget)}
                    >
                      Gerenciar
                    </Btn>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!groups.length ? (
          <p className="p-4 text-[13px] text-quiet">
            Nenhum grupo cadastrado. Super Admin não depende de um grupo.
          </p>
        ) : null}
      </Panel>

      {editing ? (
        <FloatingDialog
          labelledBy="group-dialog-title"
          onClose={closeDialog}
          position={dialogPosition}
          width={680}
        >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-rule px-5 py-4">
              <div>
                <h2 id="group-dialog-title" className="text-[17px] font-bold">
                  {editing === "new" ? "Criar grupo" : "Gerenciar grupo"}
                </h2>
                <p className="mt-0.5 text-[12px] text-quiet">
                  Defina o que os usuários vinculados poderão consultar ou alterar.
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
              <div>
                <FieldLabel>Nome do grupo</FieldLabel>
                <Control
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Ex.: Operação NOC"
                  required
                />
              </div>

              <div className="grid gap-3">
                {modules.map((module) => {
                  const permissionIds = module.items.map((item) => item.id);
                  const selected = permissionIds.filter((id) =>
                    perms.includes(id),
                  ).length;
                  return (
                    <section
                      key={module.id}
                      className="overflow-hidden rounded-[7px] border border-rule"
                    >
                      <label className="flex cursor-pointer items-center justify-between gap-3 bg-panel-2 px-3 py-2.5">
                        <span>
                          <span className="block text-[13px] font-bold">
                            {module.label}
                          </span>
                          <span className="text-[11px] text-quiet">
                            {selected} de {permissionIds.length} selecionadas
                          </span>
                        </span>
                        <input
                          type="checkbox"
                          checked={selected === permissionIds.length}
                          ref={(element) => {
                            if (element)
                              element.indeterminate =
                                selected > 0 && selected < permissionIds.length;
                          }}
                          onChange={(event) =>
                            toggleModule(permissionIds, event.target.checked)
                          }
                          className="h-4 w-4 accent-accent"
                        />
                      </label>
                      <div className="grid gap-px bg-[#edf2f4] sm:grid-cols-2">
                        {module.items.map((permission, index) => (
                          <label
                            key={permission.id}
                            className={cx(
                              "flex cursor-pointer gap-2 bg-panel px-3 py-2.5 transition hover:bg-panel-2",
                              perms.includes(permission.id) &&
                                "bg-accent-soft/55",
                              module.items.length % 2 === 1 &&
                                index === module.items.length - 1 &&
                                "sm:col-span-2",
                            )}
                          >
                            <input
                              type="checkbox"
                              checked={perms.includes(permission.id)}
                              onChange={(event) =>
                                toggle(permission.id, event.target.checked)
                              }
                              className="mt-0.5 h-4 w-4 shrink-0 accent-accent"
                            />
                            <span>
                              <span className="block text-[12.5px] font-semibold">
                                {permission.label}
                              </span>
                              <span className="mt-0.5 block text-[11px] leading-snug text-quiet">
                                {permission.description}
                              </span>
                            </span>
                          </label>
                        ))}
                      </div>
                    </section>
                  );
                })}
              </div>

              <div className="sticky -bottom-5 -mx-5 -mb-5 flex shrink-0 items-center justify-between gap-3 border-t border-rule bg-panel-2 px-5 py-3.5">
                <span className="text-[12px] text-quiet">
                  {perms.length} selecionadas
                </span>
                <div className="flex gap-2">
                  <Btn
                    type="button"
                    variant="ghost"
                    onClick={closeDialog}
                    disabled={busy}
                  >
                    Cancelar
                  </Btn>
                  <Btn type="submit" disabled={busy || !name.trim()}>
                    {busy
                      ? "Salvando…"
                      : editing === "new"
                        ? "Criar grupo"
                        : "Salvar alterações"}
                  </Btn>
                </div>
              </div>
            </form>
        </FloatingDialog>
      ) : null}
    </div>
  );
}
