"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearTokens, getAcsServerId, setAcsServerId } from "@/lib/api";
import { AcsSwitcher } from "@/components/AcsSwitcher";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/devices", label: "Dispositivos" },
  { href: "/firmwares", label: "Firmwares" },
  { href: "/security/groups", label: "Grupos" },
  { href: "/security/users", label: "Usuários" },
  { href: "/settings", label: "Settings" },
];

type Server = { id: string; name: string; is_default: boolean };

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [servers, setServers] = useState<Server[]>([]);
  const [acsId, setAcsId] = useState<string>("");

  useEffect(() => {
    setAcsId(getAcsServerId() || "");
    api<Server[]>("/acs/servers")
      .then((rows) => {
        setServers(rows);
        if (!getAcsServerId() && rows[0]) {
          const pref = rows.find((r) => r.is_default) || rows[0];
          setAcsServerId(pref.id);
          setAcsId(pref.id);
        }
      })
      .catch(() => undefined);
  }, []);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          Mr<span>9</span>
        </div>
        <p style={{ margin: 0, fontSize: 12, opacity: 0.75 }}>micro-ACS · fiber control</p>
        <nav className="nav">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className={pathname.startsWith(item.href) ? "active" : ""}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div style={{ marginTop: "auto", fontSize: 11, opacity: 0.55 }}>v0.1.0-mvp</div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div>
            <strong>Operação ACS</strong>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>NBI apenas via backend Mr9</div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <AcsSwitcher
              servers={servers}
              value={acsId}
              onChange={(id) => {
                setAcsServerId(id || null);
                setAcsId(id);
                router.refresh();
              }}
            />
            <button
              className="btn secondary"
              type="button"
              onClick={() => {
                clearTokens();
                router.push("/login");
              }}
            >
              Sair
            </button>
          </div>
        </header>
        <div className="content">{children}</div>
      </div>
    </div>
  );
}
