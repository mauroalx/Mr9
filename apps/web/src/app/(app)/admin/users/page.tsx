"use client";

import { FormEvent, useEffect, useState } from "react";
import { X } from "lucide-react";
import {
  Btn,
  Control,
  FieldLabel,
  PageHead,
  Panel,
  SelectControl,
} from "@/components/ops/primitives";
import { api } from "@/lib/api";
import {
  positionFloatingDialog,
  type FloatingDialogPosition,
} from "@/lib/floating-dialog";
import { FloatingDialog } from "@/components/ops/FloatingDialog";

type Group = { id: string; name: string };
type User = { id: string; email: string; name: string; group_id: string | null; is_active: boolean };
type UserForm = { email: string; name: string; password: string; group_id: string; is_active: boolean };

const EMPTY_FORM: UserForm = {
  email: "",
  name: "",
  password: "",
  group_id: "",
  is_active: true,
};


export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [form, setForm] = useState<UserForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [dialogPosition, setDialogPosition] = useState<FloatingDialogPosition>({
    top: 96,
    left: 24,
  });

  async function refresh() {
    const [u, g] = await Promise.all([
      api<User[]>("/security/users"),
      api<Group[]>("/security/groups"),
    ]);
    setUsers(u);
    setGroups(g);
  }

  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);

  const groupName = (id: string | null) => groups.find((g) => g.id === id)?.name || id || "—";

  function openCreate(anchor: HTMLButtonElement) {
    setEditing(null);
    setForm({ ...EMPTY_FORM, group_id: groups[0]?.id || "" });
    setDialogPosition(positionFloatingDialog(anchor, 460, 680));
    setOpen(true);
  }

  function openManage(user: User, anchor: HTMLButtonElement) {
    setEditing(user);
    setForm({
      email: user.email,
      name: user.name,
      password: "",
      group_id: user.group_id || "",
      is_active: user.is_active,
    });
    setDialogPosition(positionFloatingDialog(anchor, 460, 680));
    setOpen(true);
  }

  function closeDialog() {
    if (busy) return;
    setOpen(false);
    setEditing(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const payload = editing && !form.password
        ? { ...form, password: undefined }
        : form;
      await api(editing ? `/security/users/${editing.id}` : "/security/users", {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify(payload),
      });
      setForm({ ...EMPTY_FORM, group_id: form.group_id });
      setOpen(false);
      setEditing(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-3">
      <PageHead
        title="Usuários"
        subtitle="Super Admin não é listado nem gerenciável aqui"
        actions={
          <Btn size="sm" onClick={(event) => openCreate(event.currentTarget)}>
            Novo usuário
          </Btn>
        }
      />
      {error ? <p className="text-[13px] text-bad">{error}</p> : null}

      <Panel flush>
        <table className="ops-table">
          <thead>
            <tr>
              <th>E-mail</th>
              <th>Nome</th>
              <th>Grupo</th>
              <th>Status</th>
              <th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="tech">{u.email}</td>
                <td>{u.name}</td>
                <td>{groupName(u.group_id)}</td>
                <td className={u.is_active ? "font-semibold text-good" : "text-quiet"}>
                  {u.is_active ? "Ativo" : "Inativo"}
                </td>
                <td className="text-right">
                  <Btn
                    size="sm"
                    variant="outline"
                    onClick={(event) => openManage(u, event.currentTarget)}
                  >
                    Gerenciar
                  </Btn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!users.length ? <p className="p-4 text-[13px] text-quiet">Nenhum usuário no CRUD.</p> : null}
      </Panel>

      {open ? (
        <FloatingDialog
          labelledBy="user-dialog-title"
          onClose={closeDialog}
          position={dialogPosition}
          width={460}
        >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-rule px-5 py-4">
              <div>
                <h2 id="user-dialog-title" className="text-[16px] font-bold">
                  {editing ? "Gerenciar usuário" : "Criar usuário"}
                </h2>
                <p className="mt-0.5 text-[12px] text-quiet">
                  {editing
                    ? "Atualize acesso, grupo ou credenciais deste usuário."
                    : "Crie um acesso vinculado a um grupo de permissões."}
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
            <form className="ops-scroll grid min-h-0 gap-4 overflow-y-auto p-5" onSubmit={onSubmit}>
              <div>
                <FieldLabel>Nome</FieldLabel>
                <Control
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <FieldLabel>E-mail</FieldLabel>
                <Control
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <FieldLabel>{editing ? "Nova senha (opcional)" : "Senha"}</FieldLabel>
                <Control
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required={!editing}
                  minLength={8}
                  placeholder={editing ? "Mantenha vazio para não alterar" : undefined}
                />
              </div>
              <div>
                <FieldLabel>Grupo</FieldLabel>
                <SelectControl
                  value={form.group_id}
                  onChange={(e) => setForm({ ...form, group_id: e.target.value })}
                  required
                >
                  <option value="">Selecione…</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                    </option>
                  ))}
                </SelectControl>
              </div>
              <div>
                <FieldLabel>Status</FieldLabel>
                <SelectControl
                  value={form.is_active ? "active" : "inactive"}
                  onChange={(e) =>
                    setForm({ ...form, is_active: e.target.value === "active" })
                  }
                >
                  <option value="active">Ativo</option>
                  <option value="inactive">Inativo</option>
                </SelectControl>
                {editing && !form.is_active ? (
                  <p className="mt-1.5 text-[12px] text-caution">
                    Usuários inativos não conseguem entrar no sistema.
                  </p>
                ) : null}
              </div>
              <div className="sticky -bottom-5 -mx-5 -mb-5 flex justify-end gap-2 border-t border-rule bg-panel-2 px-5 py-3.5">
                <Btn type="button" variant="ghost" onClick={closeDialog} disabled={busy}>
                  Cancelar
                </Btn>
                <Btn type="submit" disabled={busy}>
                  {busy ? "Salvando…" : editing ? "Salvar alterações" : "Criar"}
                </Btn>
              </div>
            </form>
        </FloatingDialog>
      ) : null}
    </div>
  );
}
