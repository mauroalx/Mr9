from app.services.diagnostic_service import (
    classify_ping_outcome,
    ping_penalty_for_outcome,
    run_router_diagnostic,
)


def test_ping_timeout_zero_penalty():
    assert classify_ping_outcome({"ok": False, "state": "Error_Timeout"}) == "agent_timeout"
    assert ping_penalty_for_outcome("agent_timeout") == 0
    assert ping_penalty_for_outcome("high_latency") == 1


def test_dns_uses_approved_list():
    dev = {
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "LANHostConfigManagement": {"DNSServers": {"_value": "8.8.8.8,1.1.1.1"}},
                    "Hosts": {"Host": {}},
                }
            },
            "DeviceInfo": {"UpTime": {"_value": 100}},
        }
    }
    report = run_router_diagnostic(dev, approved_dns=["1.1.1.1"])
    assert report["penalties"]["dns"] == 1
    ping = [
        {"host": "8.8.8.8", "ok": False, "state": "Error_Timeout", "threshold_ms": 80, "penalty": 0, "failure_kind": "agent_timeout"},
        {"host": "1.1.1.1", "ok": False, "state": "Requested", "threshold_ms": 80, "penalty": 0, "failure_kind": "agent_timeout"},
    ]
    report2 = run_router_diagnostic(dev, approved_dns=["8.8.8.8", "1.1.1.1"], ping_results=ping)
    assert report2["penalties"]["ping"] == 0
    ping_check = next(c for c in report2["checks"] if c["id"] == "ping")
    assert ping_check["status"] == "skipped"
