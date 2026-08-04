"use client";

import { FormEvent, useEffect, useState } from "react";
import { API_BASE, getToken, getAcsServerId } from "@/lib/api";
import { api } from "@/lib/api";

type Fw = {
  id: string;
  filename: string;
  product_class: string;
  version: string;
  size_bytes: number;
  sha256: string;
  created_at?: string;
};

export default function FirmwaresPage() {
  const [items, setItems] = useState<Fw[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [productClass, setProductClass] = useState("");
  const [version, setVersion] = useState("");
  const [file, setFile] = useState<File | null>(null);

  async function load() {
    const res = await api<{ items: Fw[] }>("/acs/firmwares");
    setItems(res.items);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    const fd = new FormData();
    fd.set("product_class", productClass);
    fd.set("version", version);
    fd.set("file", file);
    const headers: HeadersInit = {};
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const acs = getAcsServerId();
    if (acs) headers["X-Acs-Server-Id"] = acs;
    const res = await fetch(`${API_BASE}/acs/firmwares`, { method: "POST", headers, body: fd });
    if (!res.ok) {
      setError(await res.text());
      return;
    }
    setFile(null);
    await load();
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div>
        <h1 style={{ margin: 0 }}>Firmwares</h1>
        <p style={{ color: "var(--muted)" }}>Catálogo local (upload) — empurrar via GenieACS fica para o provedor</p>
      </div>
      {error ? <p style={{ color: "var(--crit)" }}>{error}</p> : null}
      <form className="panel" onSubmit={onUpload} style={{ display: "grid", gap: 8, maxWidth: 480 }}>
        <input className="input" placeholder="ProductClass" value={productClass} onChange={(e) => setProductClass(e.target.value)} required />
        <input className="input" placeholder="Versão" value={version} onChange={(e) => setVersion(e.target.value)} />
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} required />
        <button className="btn" type="submit">
          Upload
        </button>
      </form>
      <div className="panel" style={{ padding: 0 }}>
        <table className="table">
          <thead>
            <tr>
              <th>Arquivo</th>
              <th>Modelo</th>
              <th>Versão</th>
              <th>Size</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((f) => (
              <tr key={f.id}>
                <td className="mono">{f.filename}</td>
                <td>{f.product_class}</td>
                <td className="mono">{f.version}</td>
                <td className="mono">{f.size_bytes}</td>
                <td>
                  <button
                    className="btn secondary"
                    type="button"
                    onClick={async () => {
                      await api(`/acs/firmwares/${f.id}`, { method: "DELETE" });
                      await load();
                    }}
                  >
                    Remover
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
