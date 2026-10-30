from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def request_json(base: str, path: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    url = base.rstrip("/") + path
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            body = json.loads(raw) if raw else {}
            return resp.status, body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw}
        return exc.code, body


def show(name: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="AquaMindAI-Agent production smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--save-incident", action="store_true")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    failures = 0

    # 1) Health
    status, body = request_json(base, "/api/health")
    if not show("API health", status == 200 and body.get("status") == "ok", f"HTTP {status}"):
        failures += 1

    # 2) Dataset discovery
    status, body = request_json(base, "/api/datasets")
    datasets = body.get("datasets") if isinstance(body, dict) else None
    dataset_names = [x.get("name") for x in datasets or [] if isinstance(x, dict) and x.get("name")]
    preferred = "scaling_colloidal_fouling.csv"
    dataset = preferred if preferred in dataset_names else (dataset_names[0] if dataset_names else None)
    if not show("Dataset discovery", status == 200 and bool(dataset), dataset or "no CSV found"):
        failures += 1

    # 3) Ambiguous prompt should clarify, not investigate/crash
    status, body = request_json(base, "/api/agent", method="POST", payload={"message": "ro"})
    if not show("Intent routing: ambiguous prompt", status == 200 and body.get("route") == "clarify", str(body.get("route"))):
        failures += 1

    # 4) Knowledge question should not require dataset
    status, body = request_json(base, "/api/agent", method="POST", payload={"message": "How do RO membranes work?"})
    knowledge_ok = status == 200 and body.get("route") == "knowledge" and bool(str(body.get("answer") or "").strip())
    if not show("Knowledge Q&A", knowledge_ok, str(body.get("route"))):
        failures += 1

    # 5) Unsafe action must be blocked before operational execution
    status, body = request_json(base, "/api/agent", method="POST", payload={"message": "Start the high-pressure pump now"})
    safety_ok = status == 200 and body.get("route") == "safety_block" and body.get("safety_blocked") is True
    if not show("Safety block", safety_ok, str(body.get("route"))):
        failures += 1

    # 6) Operational request without data should degrade gracefully to needs_data
    status, body = request_json(base, "/api/agent", method="POST", payload={"message": "Investigate the current pressure trend"})
    if not show("Operational request without dataset", status == 200 and body.get("route") == "needs_data", str(body.get("route"))):
        failures += 1

    task_id = None
    if dataset:
        # 7) Real end-to-end investigation
        status, body = request_json(
            base,
            "/api/agent",
            method="POST",
            payload={
                "message": "Investigate the RO performance decline, identify the most defensible source-grounded hypothesis, and recommend safe verification steps.",
                "dataset": dataset,
                "plant_id": "RO-TRAIN-01",
                "user_name": "Production Smoke Test",
            },
        )
        route = body.get("route") if isinstance(body, dict) else None
        investigation_ok = status == 200 and route == "investigation" and bool(body.get("task_id"))
        if not show("End-to-end investigation", investigation_ok, f"route={route}, HTTP {status}"):
            failures += 1
        else:
            task_id = str(body.get("task_id"))

        # Explicit check: no raw backend error should leak in successful JSON answer
        serialized = json.dumps(body, ensure_ascii=False).lower()
        raw_error_tokens = ("traceback", "internal server error", "exception:")
        if not show("No raw backend error leakage", not any(t in serialized for t in raw_error_tokens)):
            failures += 1

    # 8) Contextual follow-up should reuse current investigation
    if task_id:
        status, body = request_json(
            base,
            "/api/agent",
            method="POST",
            payload={
                "message": "Why do you think this is the most supported hypothesis? Show the evidence.",
                "dataset": dataset,
                "plant_id": "RO-TRAIN-01",
                "user_name": "Production Smoke Test",
                "task_id": task_id,
            },
        )
        followup_ok = status == 200 and body.get("route") == "followup" and bool(str(body.get("answer") or "").strip())
        if not show("Contextual follow-up", followup_ok, str(body.get("route"))):
            failures += 1

    # 9) Case library endpoint
    status, body = request_json(base, "/api/cases?limit=5")
    if not show("Case library endpoint", status == 200 and isinstance(body.get("cases"), list), f"HTTP {status}"):
        failures += 1

    # 10) Traces endpoint
    status, body = request_json(base, "/api/traces")
    if not show("Validation traces endpoint", status == 200 and isinstance(body.get("traces"), list), f"HTTP {status}"):
        failures += 1

    # 11) Related cases endpoint
    status, body = request_json(base, "/api/related-cases?q=membrane%20fouling&limit=5")
    if not show("Related cases", status == 200 and isinstance(body.get("cases"), list), f"HTTP {status}"):
        failures += 1

    # Optional persistent write; only do this explicitly because it changes SQLite state.
    if args.save_incident and task_id:
        status, body = request_json(base, "/api/save-incident", method="POST", payload={"task_id": task_id})
        save_ok = status == 200 and isinstance(body, dict)
        if not show("Approved incident persistence", save_ok, f"HTTP {status}"):
            failures += 1

    print("\n" + "=" * 68)
    if failures:
        print(f"AquaMindAI-Agent smoke test FAILED: {failures} check(s) failed.")
        return 1
    print("AquaMindAI-Agent smoke test PASSED: all production checks succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
