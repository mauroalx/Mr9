"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cx } from "@/lib/cx";

const SECTIONS = [
  { href: "/admin/general", label: "Geral" },
  { href: "/admin/acs-servers", label: "Servidores ACS" },
  { href: "/admin/users", label: "Usuários" },
  { href: "/admin/groups", label: "Grupos" },
  { href: "/admin/appearance", label: "Aparência" },
  { href: "/admin/audit", label: "Auditoria" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
      <aside className="ops-panel h-fit p-2">
        <div className="px-3 py-2 text-[12px] font-semibold uppercase tracking-[0.06em] text-quiet">
          Administração
        </div>
        <nav className="grid gap-0.5">
          {SECTIONS.map((s) => {
            const active = pathname === s.href || pathname.startsWith(s.href + "/");
            return (
              <Link
                key={s.href}
                href={s.href}
                className={cx(
                  "rounded-[5px] border-l-[3px] px-3 py-2 text-[13px] font-medium transition",
                  active ? "border-accent bg-accent-soft text-accent-strong" : "border-transparent text-ink-soft hover:bg-panel-2 hover:text-ink",
                )}
              >
                {s.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="min-w-0">{children}</div>
    </div>
  );
}
