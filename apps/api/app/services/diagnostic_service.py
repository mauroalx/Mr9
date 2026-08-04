from __future__ import annotations

from typing import Any

from app.cpe.extract import extract_dhcp_lan, extract_hosts
from app.cpe.params import Cap
from app.cpe.profiles import candidates_for
from app.cpe.tree import leaf, param_at


def _score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def classify_ping_outcome(raw: dict[str, Any], *, threshold_ms: int | None = None) -> str:
    state = str(raw.get("state") or "").strip()
    if raw.get("ok"):
        avg = raw.get("average_ms")
        if threshold_ms is not None and isinstance(avg, int) and avg > int(threshold_ms):
            return "high_latency"
        return "ok"
    if state in {"Error_Timeout", "Requested", "None"}:
        return "agent_timeout"
    if state in {"Error_Stale", "Error_StaleResult"}:
        return "stale"
    if state == "Error_CannotResolveHostName" or state == "Complete":
        return "icmp_fail"
    if state.startswith("Error"):
        return "cpe_error"
    if not state or raw.get("supported") is False:
        return "unsupported"
    return "agent_timeout"


def ping_penalty_for_outcome(kind: str) -> int:
    return 1 if kind in {"icmp_fail", "cpe_error", "high_latency"} else 0


def run_router_diagnostic(
    dev: dict[str, Any],
    *,
    approved_dns: list[str] | None = None,
    ping_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Diagnóstico leve: lê inventário via extract/catálogo CPE (sem dig hardcoded)."""
    approved = set(approved_dns or [])
    dhcp = extract_dhcp_lan(dev) or {}
    raw_dns = dhcp.get("dnsServers") or ""
    dns_servers: list[str] = []
    if isinstance(raw_dns, str):
        dns_servers = [s.strip() for s in raw_dns.split(",") if s.strip()]

    invalid_dns = [s for s in dns_servers if approved and s not in approved]
    dns_penalty = 1 if invalid_dns else 0

    hosts = extract_hosts(dev)
    host_count = len(hosts)
    host_penalty = 1 if host_count > 10 else (2 if host_count > 20 else 0)

    uptime = None
    for path in candidates_for(dev, Cap.DEVICE_UPTIME):
        uptime = leaf(param_at(dev, path))
        if uptime is not None:
            break
    try:
        uptime_s = int(uptime) if uptime is not None else 0
    except (TypeError, ValueError):
        uptime_s = 0
    uptime_penalty = 1 if uptime_s > 86_400 else 0

    ping_rows = list(ping_results or [])
    for row in ping_rows:
        if not row.get("failure_kind"):
            kind = classify_ping_outcome(row, threshold_ms=row.get("threshold_ms"))
            row["failure_kind"] = kind
            row.setdefault("penalty", ping_penalty_for_outcome(kind))
    ping_penalty = sum(int(r.get("penalty") or 0) for r in ping_rows)
    transport_only = (
        bool(ping_rows)
        and ping_penalty == 0
        and not any(r.get("ok") for r in ping_rows)
        and all(str(r.get("failure_kind") or "") in {"agent_timeout", "stale", "unsupported", "transport"} for r in ping_rows)
    )

    penalties = {
        "dns": dns_penalty,
        "hosts": host_penalty,
        "uptime": uptime_penalty,
        "ping": ping_penalty,
    }
    total = sum(penalties.values())
    score = max(0, min(100, 100 - total * 7))
    tips: list[str] = []
    if invalid_dns:
        tips.append(f"DNS fora do padrão configurado: {', '.join(invalid_dns)}.")
    if host_penalty:
        tips.append(f"Há {host_count} clientes ativos — acima de 10 pode degradar o Wi‑Fi.")
    if uptime_penalty:
        tips.append("CPE ligado há mais de 1 dia — considere reiniciar.")
    if transport_only:
        tips.append("Pings não concluíram via ACS (timeout/agente). Não contabilizado como falha do roteador.")

    checks = [
        {
            "id": "dns",
            "title": "DNS",
            "status": "ok" if dns_penalty == 0 else "warn",
            "penalty": dns_penalty,
            "summary": "DNS OK." if not invalid_dns else f"{len(invalid_dns)} DNS fora do padrão.",
            "details": {"servers": dns_servers, "invalid": invalid_dns, "approved": sorted(approved)},
        },
        {
            "id": "hosts",
            "title": "Clientes na rede",
            "status": "ok" if host_penalty == 0 else "warn",
            "penalty": host_penalty,
            "summary": f"{host_count} cliente(s) ativo(s).",
            "details": {"count": host_count},
        },
        {
            "id": "uptime",
            "title": "Uptime",
            "status": "ok" if uptime_penalty == 0 else "warn",
            "penalty": uptime_penalty,
            "summary": f"Uptime {uptime_s}s.",
            "details": {"uptime_s": uptime_s},
        },
        {
            "id": "ping",
            "title": "Latência (ping do roteador)",
            "status": "skipped" if not ping_rows or transport_only else ("ok" if ping_penalty == 0 else "warn"),
            "penalty": ping_penalty,
            "summary": (
                "Ping não executado."
                if not ping_rows
                else (
                    "Ping não concluiu via ACS (timeout/agente). Não contabilizado como falha do roteador."
                    if transport_only
                    else ("Latência dentro do esperado." if ping_penalty == 0 else "Latência alta ou ping com falha no CPE.")
                )
            ),
            "details": {"results": ping_rows, "transport_only": transport_only},
        },
    ]
    return {
        "score": score,
        "grade": _score_to_grade(score),
        "penalties": penalties,
        "checks": checks,
        "tips": tips,
    }
