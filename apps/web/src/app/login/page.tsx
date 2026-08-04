"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, setTokens } from "@/lib/api";
import { Mr9Mark } from "@/components/brand/Mr9Mark";
import { Btn, Control, FieldLabel } from "@/components/ops/primitives";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const tokens = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email, password }),
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-canvas px-4">
      <div className="w-full max-w-[420px] rounded-[8px] border border-rule bg-white p-7 shadow-panel">
        <div className="mb-6 flex items-center gap-3">
          <Mr9Mark className="h-9 w-9 text-accent" />
          <div>
            <div className="text-[20px] font-bold tracking-tight text-ink">Mr9</div>
            <div className="text-[13px] text-quiet">Acesso à operação ACS</div>
          </div>
        </div>
        <form className="grid gap-3" onSubmit={onSubmit}>
          <label className="grid gap-1">
            <FieldLabel>
              E-mail
            </FieldLabel>
            <Control
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
            />
          </label>
          <label className="grid gap-1">
            <FieldLabel>
              Senha
            </FieldLabel>
            <Control
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="current-password"
            />
          </label>
          {error ? <p className="rounded-[5px] border border-bad/20 bg-bad-soft px-3 py-2 text-[13px] text-bad">{error}</p> : null}
          <Btn type="submit" disabled={loading} className="mt-1 w-full">
            {loading ? "Entrando…" : "Entrar"}
          </Btn>
        </form>
        <p className="mt-5 text-center text-[12px] text-quiet">
          <Link href="/setup" className="font-semibold text-accent hover:underline">
            Instalação
          </Link>
        </p>
      </div>
    </main>
  );
}
