"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  Boxes,
  ChevronDown,
  CircleHelp,
  ClipboardList,
  LayoutDashboard,
  Router as RouterIcon,
  Search,
  Server,
  Settings,
  Zap,
} from "lucide-react";
import { api, clearTokens, getAcsServerId, setAcsServerId } from "@/lib/api";
import { cx } from "@/lib/cx";
import { isNavigationActive, operationalNavigation } from "@/lib/navigation";
import { applyAppearance, loadAppearance } from "@/lib/appearance";
import { Mr9Mark } from "@/components/brand/Mr9Mark";

type Server = {
  id: string;
  name: string;
  is_default: boolean;
  credentials_ok?: boolean;
};

type CurrentUser = {
  email: string;
  name: string;
  is_superadmin: boolean;
};

function initials(name: string, email: string): string {
  const source = name.trim() || email.split("@")[0] || "U";
  return source
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function OpsChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [servers, setServers] = useState<Server[]>([]);
  const [acs, setAcs] = useState("");
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [menu, setMenu] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const quickRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    applyAppearance(loadAppearance());
    setAcs(getAcsServerId() || "");
    api<Server[]>("/acs/servers")
      .then((rows) => {
        setServers(rows);
        if (!getAcsServerId() && rows[0]) {
          const selected = rows.find((row) => row.is_default) || rows[0];
          setAcsServerId(selected.id);
          setAcs(selected.id);
        }
      })
      .catch(() => setServers([]));
    api<CurrentUser>("/auth/me")
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null));
  }, []);

  useEffect(() => {
    function close(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setMenu(false);
      if (!quickRef.current?.contains(event.target as Node))
        setQuickOpen(false);
    }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const selectedServer = servers.find((server) => server.id === acs);
  const acsOk = selectedServer?.credentials_ok !== false;
  const userInitials = initials(
    currentUser?.name || "",
    currentUser?.email || "",
  );

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="sticky top-0 z-40 border-b border-rule bg-[#f8fafc] text-[#102a36]">
        <div className="mx-auto flex h-[68px] w-full max-w-[1840px] items-center gap-5 px-4 md:px-5 lg:px-6">
          <Link
            href="/dashboard"
            className="flex shrink-0 items-center gap-2 pr-3 text-accent lg:pr-7"
          >
            <Mr9Mark />
            <span className="text-ink">
              <span className="block text-[17px] font-bold leading-none tracking-[-0.02em]">
                Mr9
              </span>
              <span className="mt-1 hidden text-[12px] font-medium text-quiet sm:block">
                ACS Control
              </span>
            </span>
          </Link>
          <div className="hidden h-7 w-px bg-rule lg:block" />
          <label className="hidden min-w-[220px] lg:block">
            <span className="block text-[12px] text-quiet">
              Ambiente · Produção
            </span>
            <span className="mt-0.5 flex items-center gap-2">
              <i
                className={cx(
                  "h-2 w-2 rounded-full",
                  acsOk ? "bg-good" : "bg-bad",
                )}
              />
              <select
                className="max-w-[190px] bg-transparent text-[13px] font-semibold outline-none"
                value={acs}
                onChange={(event) => {
                  setAcs(event.target.value);
                  setAcsServerId(event.target.value || null);
                  router.refresh();
                }}
              >
                {servers.map((server) => (
                  <option key={server.id} value={server.id}>
                    {server.name}
                  </option>
                ))}
                {!servers.length ? (
                  <option value="">Sem ACS configurado</option>
                ) : null}
              </select>
            </span>
          </label>
          <label className="ml-auto hidden h-10 w-[360px] items-center gap-2.5 rounded-[6px] border border-rule bg-white px-3 text-quiet transition focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/15 md:flex">
            <Search size={16} />
            <input
              className="w-full bg-transparent text-[13px] text-ink outline-none placeholder:text-quiet"
              placeholder="Buscar serial, IP, MAC ou PPPoE"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  const value = event.currentTarget.value.trim();
                  router.push(
                    value
                      ? `/devices?q=${encodeURIComponent(value)}`
                      : "/devices",
                  );
                }
              }}
            />
            <kbd className="rounded border border-rule bg-[#f8fafc] px-1.5 py-0.5 text-[12px]">
              /
            </kbd>
          </label>
          <div className="relative hidden sm:block" ref={quickRef}>
            <button
              className="flex h-10 items-center gap-2 rounded-[6px] border border-rule bg-white px-3 text-[13px] font-semibold transition hover:bg-panel-2 focus-visible:outline-accent"
              onClick={() => setQuickOpen((open) => !open)}
              aria-expanded={quickOpen}
            >
              <Zap size={15} className="text-accent" />
              Ação rápida
            </button>
            {quickOpen ? (
              <div className="absolute right-0 top-12 z-50 w-[360px] rounded-[8px] border border-rule bg-white p-4 shadow-xl">
                <div className="border-b border-rule pb-3">
                  <h2 className="text-[15px] font-bold">Ação rápida</h2>
                  <p className="mt-0.5 text-[12px] text-quiet">
                    Acesso aos módulos operacionais do Mr9.
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-3">
                  {[
                    {
                      href: "/dashboard",
                      label: "Dashboard",
                      icon: LayoutDashboard,
                      tone: "text-signal bg-signal-soft",
                    },
                    {
                      href: "/devices",
                      label: "Dispositivos",
                      icon: RouterIcon,
                      tone: "text-accent bg-accent-soft",
                    },
                    {
                      href: "/tasks",
                      label: "Tarefas",
                      icon: ClipboardList,
                      tone: "text-caution bg-caution-soft",
                    },
                    {
                      href: "/firmwares",
                      label: "Firmwares",
                      icon: Boxes,
                      tone: "text-signal bg-signal-soft",
                    },
                    {
                      href: "/admin/acs-servers",
                      label: "Servidores",
                      icon: Server,
                      tone: "text-ink-soft bg-panel-2",
                    },
                    {
                      href: "/admin/general",
                      label: "Administração",
                      icon: Settings,
                      tone: "text-ink-soft bg-panel-2",
                    },
                  ].map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setQuickOpen(false)}
                        className="group flex min-h-24 flex-col items-center justify-center gap-2 rounded-[7px] border border-transparent px-2 py-3 text-center text-[12px] font-bold transition hover:border-rule hover:bg-panel-2"
                      >
                        <span
                          className={cx(
                            "grid h-10 w-10 place-items-center rounded-[7px]",
                            item.tone,
                          )}
                        >
                          <Icon size={19} />
                        </span>
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ) : null}
          </div>
          <div className="relative" ref={menuRef}>
            <button
              className="flex h-11 items-center gap-2.5 rounded-[7px] border border-rule bg-white px-2.5 pr-3 text-left transition hover:border-[#b9c8d0] hover:bg-panel-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/25"
              onClick={() => setMenu((open) => !open)}
              aria-expanded={menu}
              aria-haspopup="menu"
            >
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-[6px] bg-accent-soft text-[11px] font-bold text-accent-strong">
                {userInitials}
              </span>
              <span className="hidden min-w-0 sm:block">
                <span className="block max-w-28 truncate text-[13px] font-semibold leading-4 text-ink">
                  {currentUser?.name || "Minha conta"}
                </span>
                <span className="block text-[11px] leading-4 text-quiet">
                  {currentUser?.is_superadmin ? "Super Admin" : "Usuário"}
                </span>
              </span>
              <ChevronDown
                size={13}
                className={cx(
                  "text-quiet transition-transform",
                  menu && "rotate-180",
                )}
              />
            </button>
            {menu ? (
              <div
                className="absolute right-0 top-12 z-50 w-64 overflow-hidden rounded-[7px] border border-rule bg-white py-1 shadow-panel"
                role="menu"
              >
                <div className="border-b border-rule px-3 py-2.5">
                  <p className="truncate text-[13px] font-semibold">
                    {currentUser?.name || "Minha conta"}
                  </p>
                  <p className="mt-0.5 truncate text-[12px] text-quiet">
                    {currentUser?.email || "Sessão autenticada"}
                  </p>
                </div>
                {[
                  ["/admin/general", "Administração"],
                  ["/admin/acs-servers", "Servidores ACS"],
                  ["/admin/users", "Usuários"],
                  ["/admin/groups", "Grupos"],
                ].map(([href, label]) => (
                  <Link
                    key={href}
                    href={href}
                    className="block px-3 py-2 text-[13px] hover:bg-panel-2"
                    onClick={() => setMenu(false)}
                    role="menuitem"
                  >
                    {label}
                  </Link>
                ))}
                <button
                  className="block w-full border-t border-rule px-3 py-2 text-left text-[13px] text-bad hover:bg-bad-soft"
                  onClick={() => {
                    clearTokens();
                    router.push("/login");
                  }}
                  role="menuitem"
                >
                  Sair
                </button>
              </div>
            ) : null}
          </div>
        </div>
        <div className="h-[48px] overflow-x-auto border-t border-rule bg-[#eef3f5]">
          <div className="mx-auto flex h-full w-full max-w-[1840px] items-stretch px-4 md:px-5 lg:px-6">
            <nav className="flex min-w-max items-stretch">
              {operationalNavigation.map((item) => {
                const active = isNavigationActive(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cx(
                      "relative flex items-center border-x px-4 text-[13px] font-semibold transition focus-visible:z-10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent",
                      active
                        ? "border-[#cfe3e1] bg-accent-soft/65 text-accent-strong"
                        : "border-transparent text-[#405965] hover:bg-[#e4ebee] hover:text-ink",
                    )}
                  >
                    {item.label}
                    {active ? (
                      <span className="absolute inset-x-3 bottom-0 h-[3px] rounded-t bg-accent" />
                    ) : null}
                  </Link>
                );
              })}
            </nav>
            <div className="ml-auto hidden items-center gap-5 text-[12px] font-medium text-[#405965] 2xl:flex">
              <span className="flex items-center gap-1.5">
                <CircleHelp size={14} />
                Documentação
              </span>
              <Link href="/admin/general" className="flex items-center gap-1.5">
                <Settings size={14} />
                Administração
              </Link>
            </div>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1840px] px-4 py-4 md:px-5 md:py-5 lg:px-6 lg:py-6">
        {children}
      </main>
    </div>
  );
}
