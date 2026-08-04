"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api, getToken } from "@/lib/api";

type SetupStatus = { installed: boolean };

export default function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api<SetupStatus>("/setup/status", { auth: false })
      .then((s) => {
        if (!s.installed) router.replace("/setup");
      })
      .catch(() => undefined);
  }, [router]);

  return <AppShell>{children}</AppShell>;
}
