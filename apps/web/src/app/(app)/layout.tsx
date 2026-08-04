"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { OpsChrome } from "@/components/chrome/OpsChrome";
import { api, getToken } from "@/lib/api";

type SetupStatus = { installed: boolean };

export default function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api<SetupStatus>("/setup/status", { auth: false })
      .then((s) => {
        if (!s.installed) router.replace("/setup");
        else setReady(true);
      })
      .catch(() => setReady(true));
  }, [router]);

  if (!ready) {
    return (
      <div className="grid min-h-screen place-items-center bg-canvas text-[13px] text-quiet">Carregando…</div>
    );
  }

  return <OpsChrome>{children}</OpsChrome>;
}
