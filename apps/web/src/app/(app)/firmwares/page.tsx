"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Btn,
  Control,
  FieldLabel,
  MetricCell,
  PageHead,
  Panel,
  PanelTitle,
} from "@/components/ops/primitives";
import { API_BASE, api, getAcsServerId, getToken } from "@/lib/api";
import { cx } from "@/lib/cx";
import { formatDateTime } from "@/lib/format";

type Fw = {
  id: string;
  filename: string;
  product_class: string;
  version: string;
  size_bytes: number;
  sha256: string;
  created_at?: string;
};

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FirmwaresPage() {
  const [items, setItems] = useState<Fw[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [productClass, setProductClass] = useState("");
  const [version, setVersion] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [detail, setDetail] = useState<Fw | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function load() {
    const res = await api<{ items: Fw[] }>("/acs/firmwares");
    setItems(res.items);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  const kpis = useMemo(() => {
    const models = new Set(items.map((i) => i.product_class).filter(Boolean));
    const bytes = items.reduce((a, i) => a + (i.size_bytes || 0), 0);
    return { count: items.length, models: models.size, bytes };
  }, [items]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }, []);

  function upload() {
    if (!file || !productClass.trim()) {
      setError("Informe produto/modelo e selecione o arquivo.");
      return;
    }
    setError(null);
    setMsg(null);
    setProgress(0);

    const fd = new FormData();
    fd.set("product_class", productClass.trim());
    fd.set("version", version.trim());
    fd.set("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/acs/firmwares`);
    const token = getToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    const acs = getAcsServerId();
    if (acs) xhr.setRequestHeader("X-Acs-Server-Id", acs);

    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable) setProgress(Math.round((ev.loaded / ev.total) * 100));
    };
    xhr.onload = async () => {
      setProgress(null);
      if (xhr.status >= 200 && xhr.status < 300) {
        setMsg("Firmware enviado.");
        setFile(null);
        setVersion("");
        if (inputRef.current) inputRef.current.value = "";
        try {
          await load();
        } catch (e) {
          setError(e instanceof Error ? e.message : "Erro ao recarregar");
        }
      } else {
        let detail = xhr.responseText;
        try {
          const body = JSON.parse(xhr.responseText);
          detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
        } catch {
          /* keep text */
        }
        setError(detail || `HTTP ${xhr.status}`);
      }
    };
    xhr.onerror = () => {
      setProgress(null);
      setError("Falha de rede no upload");
    };
    xhr.send(fd);
  }

  return (
    <div className="grid gap-3">
      <PageHead
        title="Firmwares"
        subtitle="Catálogo local de imagens — empurrar via GenieACS fica a cargo do provedor"
      />

      {error ? <p className="text-[13px] text-bad">{error}</p> : null}
      {msg ? <p className="text-[13px] text-good">{msg}</p> : null}

      <Panel flush className="overflow-hidden">
        <div className="grid grid-cols-2 divide-x divide-rule md:grid-cols-3">
          <MetricCell label="Imagens" value={kpis.count} />
          <MetricCell label="Modelos" value={kpis.models} />
          <MetricCell label="Armazenado" value={formatBytes(kpis.bytes)} />
        </div>
      </Panel>

      <Panel>
        <PanelTitle title="Upload" hint="Arraste o binário ou escolha o arquivo" />
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <FieldLabel>Product class / modelo</FieldLabel>
            <Control
              value={productClass}
              onChange={(e) => setProductClass(e.target.value)}
              placeholder="ex.: EG8145V5"
              required
            />
          </div>
          <div>
            <FieldLabel>Versão</FieldLabel>
            <Control value={version} onChange={(e) => setVersion(e.target.value)} placeholder="opcional" />
          </div>
        </div>

        <div
          className={cx(
            "mt-3 flex min-h-[120px] flex-col items-center justify-center gap-2 rounded-[2px] border border-dashed px-4 py-6 text-center",
            dragging ? "border-accent bg-accent-soft" : "border-rule bg-panel-2",
          )}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <p className="text-[13px] font-semibold text-ink">
            {file ? file.name : "Solte o firmware aqui"}
          </p>
          <p className="text-[12px] text-quiet">
            {file ? formatBytes(file.size) : "ou clique para selecionar"}
          </p>
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <Btn size="sm" variant="outline" onClick={() => inputRef.current?.click()}>
            Escolher arquivo
          </Btn>
        </div>

        {progress != null ? (
          <div className="mt-3">
            <div className="mb-1 flex justify-between text-[11px] font-bold text-quiet">
              <span>Enviando…</span>
              <span className="tech">{progress}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-[2px] bg-panel-2">
              <div className="h-full bg-accent transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
        ) : null}

        <div className="mt-3 flex justify-end">
          <Btn disabled={progress != null} onClick={upload}>
            Enviar
          </Btn>
        </div>
      </Panel>

      <Panel flush>
        <table className="ops-table">
          <thead>
            <tr>
              <th>Arquivo</th>
              <th>Modelo</th>
              <th>Versão</th>
              <th>Tamanho</th>
              <th>Criado</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((f) => (
              <tr key={f.id} className="cursor-pointer" onClick={() => setDetail(f)}>
                <td className="tech">{f.filename}</td>
                <td>{f.product_class}</td>
                <td className="tech">{f.version || "—"}</td>
                <td className="tech">{formatBytes(f.size_bytes)}</td>
                <td className="tech">{formatDateTime(f.created_at)}</td>
                <td>
                  <Btn
                    size="sm"
                    variant="ghost"
                    onClick={async (e) => {
                      e.stopPropagation();
                      setError(null);
                      try {
                        await api(`/acs/firmwares/${f.id}`, { method: "DELETE" });
                        if (detail?.id === f.id) setDetail(null);
                        await load();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Erro");
                      }
                    }}
                  >
                    Remover
                  </Btn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length ? <p className="p-4 text-[13px] text-quiet">Nenhuma imagem no catálogo.</p> : null}
      </Panel>

      {detail ? (
        <div className="fixed inset-0 z-50 flex justify-end">
          <button
            type="button"
            className="absolute inset-0 bg-black/35"
            aria-label="Fechar"
            onClick={() => setDetail(null)}
          />
          <div className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-rule bg-panel">
            <div className="border-b border-rule px-4 py-3">
              <h2 className="text-[15px] font-semibold">Detalhe do firmware</h2>
              <p className="tech text-[11px] text-quiet">{detail.filename}</p>
            </div>
            <dl className="grid gap-2 p-4 text-[13px]">
              <Row k="Modelo" v={detail.product_class} />
              <Row k="Versão" v={detail.version || "—"} tech />
              <Row k="Tamanho" v={formatBytes(detail.size_bytes)} tech />
              <Row k="SHA-256" v={detail.sha256} tech />
              <Row k="Criado" v={formatDateTime(detail.created_at)} />
              <Row k="ID" v={detail.id} tech />
            </dl>
            <div className="mt-auto flex justify-end gap-2 border-t border-rule px-4 py-3">
              <Btn variant="ghost" onClick={() => setDetail(null)}>
                Fechar
              </Btn>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Row({ k, v, tech }: { k: string; v: string; tech?: boolean }) {
  return (
    <div className="border-b border-rule/70 py-1.5">
      <dt className="text-[11px] font-bold text-quiet">{k}</dt>
      <dd className={cx("mt-0.5 break-all font-medium", tech && "tech")}>{v}</dd>
    </div>
  );
}
