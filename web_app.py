from __future__ import annotations

import hashlib
import html
import inspect
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent.runtime import AquaMindRuntime, RuntimeConfig


APP_TITLE = "AquaMindAI-Agent"
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = (PROJECT_ROOT / "data").resolve()
FRONTEND_ROOT = (PROJECT_ROOT / "frontend").resolve()

# Vercel Functions expose the deployed project as read-only at runtime.
# Use /tmp for temporary uploads, SQLite memory, and audit files there,
# while keeping the existing local paths unchanged for normal development.
IS_VERCEL = bool(os.getenv("VERCEL"))
WRITABLE_ROOT = Path("/tmp/aquamind").resolve() if IS_VERCEL else PROJECT_ROOT

UPLOAD_ROOT = (
    (WRITABLE_ROOT / "uploads").resolve()
    if IS_VERCEL
    else (DATA_ROOT / "uploads").resolve()
)
RUNTIME_ROOT = (
    (WRITABLE_ROOT / ".runtime").resolve()
    if IS_VERCEL
    else (PROJECT_ROOT / ".runtime").resolve()
)
MAX_UPLOAD_BYTES = int(os.getenv("AQUAMIND_MAX_UPLOAD_MB", "10")) * 1024 * 1024

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=APP_TITLE, version="1.0.0")
ACTIVE_RUNS: dict[str, dict[str, Any]] = {}


class InvestigationRequest(BaseModel):
    dataset: str
    user_request: str = Field(min_length=3, max_length=2000)
    plant_id: str = Field(default="RO-TRAIN-01", min_length=1, max_length=120)
    user_name: str = Field(default="Operator", max_length=120)


class SaveRequest(BaseModel):
    task_id: str


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "value") and isinstance(getattr(value, "value"), (str, int, float, bool)):
        return getattr(value, "value")
    if hasattr(value, "to_dict"):
        try:
            return _jsonable(value.to_dict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        try:
            return {k: _jsonable(v) for k, v in vars(value).items() if not k.startswith("_")}
        except Exception:
            pass
    return str(value)


def _safe_filename(name: str) -> str:
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in "._-")
    return cleaned or "uploaded.csv"


def _demo_csv_files() -> list[Path]:
    files: list[Path] = []
    if DATA_ROOT.exists():
        for path in DATA_ROOT.rglob("*.csv"):
            resolved = path.resolve()
            if UPLOAD_ROOT in resolved.parents:
                continue
            files.append(resolved)
    return sorted(files, key=lambda p: p.name.lower())


def _resolve_dataset(name: str) -> Path:
    candidate = (DATA_ROOT / name).resolve()
    if DATA_ROOT == candidate or DATA_ROOT in candidate.parents:
        if candidate.exists() and candidate.suffix.lower() == ".csv":
            return candidate
    for path in _demo_csv_files():
        if path.name == Path(name).name:
            return path
    upload_candidate = (UPLOAD_ROOT / Path(name).name).resolve()
    if UPLOAD_ROOT in upload_candidate.parents and upload_candidate.exists():
        return upload_candidate
    raise HTTPException(status_code=404, detail="Dataset not found")


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean environment flag safely."""

    raw = os.getenv(name)

    if raw is None:
        return default

    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_positive_float(name: str, default: float) -> float:
    """Read a positive finite float or safely use the default."""

    raw = os.getenv(name)

    if raw is None or not raw.strip():
        return default

    try:
        value = float(raw)
    except ValueError:
        return default

    if not math.isfinite(value) or value <= 0:
        return default

    return value


def _runtime_config(dataset_path: Path) -> RuntimeConfig:
    signature = inspect.signature(RuntimeConfig)
    values: dict[str, Any] = {}

    resolved_dataset = dataset_path.resolve()
    allowed_root = DATA_ROOT
    if IS_VERCEL and (resolved_dataset == UPLOAD_ROOT or UPLOAD_ROOT in resolved_dataset.parents):
        allowed_root = UPLOAD_ROOT

    llm_requested = _env_flag(
        "AQUAMIND_LLM_ENABLED",
        False,
    )
    gemini_key_available = bool(
        os.getenv("GEMINI_API_KEY", "").strip()
    )
    llm_model = (
        os.getenv(
            "AQUAMIND_LLM_MODEL",
            "gemini-3.5-flash-lite",
        ).strip()
        or "gemini-3.5-flash-lite"
    )

    candidates: dict[str, Any] = {
        "dataset_path": dataset_path,
        "allowed_data_root": allowed_root,
        "allowed_root": allowed_root,
        "memory_path": RUNTIME_ROOT / "aquamind_memory.db",
        "memory_db_path": RUNTIME_ROOT / "aquamind_memory.db",
        "db_path": RUNTIME_ROOT / "aquamind_memory.db",
        "audit_path": RUNTIME_ROOT / "aquamind_audit.jsonl",
        "audit_log_path": RUNTIME_ROOT / "aquamind_audit.jsonl",
        "llm_enabled": llm_requested and gemini_key_available,
        "llm_model": llm_model,
        "budget_cap_usd": _env_positive_float(
            "AQUAMIND_TASK_BUDGET_USD",
            0.10,
        ),
    }
    for name, parameter in signature.parameters.items():
        if name in candidates:
            values[name] = candidates[name]
            continue
        if parameter.default is not inspect.Parameter.empty:
            continue
        lowered = name.lower()
        if "dataset" in lowered and "path" in lowered:
            values[name] = dataset_path
        elif "allowed" in lowered and ("root" in lowered or "path" in lowered):
            values[name] = allowed_root
        elif "memory" in lowered and ("path" in lowered or "db" in lowered):
            values[name] = RUNTIME_ROOT / "aquamind_memory.db"
        elif "audit" in lowered and "path" in lowered:
            values[name] = RUNTIME_ROOT / "aquamind_audit.jsonl"
        else:
            raise RuntimeError(f"Unsupported required RuntimeConfig parameter: {name!r}")
    return RuntimeConfig(**values)


def _build_runtime(dataset_path: Path) -> AquaMindRuntime:
    config = _runtime_config(dataset_path)
    parameters = inspect.signature(AquaMindRuntime).parameters
    if "config" in parameters:
        return AquaMindRuntime(config=config)
    return AquaMindRuntime(config)


def _call_runtime(runtime: AquaMindRuntime, *, request: str, plant_id: str, task_id: str) -> dict[str, Any]:
    signature = inspect.signature(runtime.run)
    kwargs: dict[str, Any] = {}
    aliases = {
        "user_request": request,
        "request": request,
        "query": request,
        "prompt": request,
        "plant_id": plant_id,
        "plant": plant_id,
        "task_id": task_id,
    }
    for name, parameter in signature.parameters.items():
        if name in aliases:
            kwargs[name] = aliases[name]
            continue
        if parameter.default is inspect.Parameter.empty:
            raise RuntimeError(f"Unsupported required AquaMindRuntime.run() parameter: {name!r}")
    result = runtime.run(**kwargs)
    if not isinstance(result, dict):
        raise RuntimeError("AquaMindRuntime.run() returned a non-dictionary result")
    return result


def _find_column(df: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    normalized_aliases = tuple(_normalize_key(a) for a in aliases)
    for column in df.columns:
        key = _normalize_key(str(column))
        if key in normalized_aliases:
            return str(column)
    for alias in normalized_aliases:
        for column in df.columns:
            key = _normalize_key(str(column))
            if alias and (alias in key or key in alias):
                return str(column)
    return None


def _numeric_series(df: pd.DataFrame, aliases: Iterable[str]) -> pd.Series:
    column = _find_column(df, aliases)
    if column is None:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[column], errors="coerce").dropna()


def _metric_delta(series: pd.Series) -> float | None:
    series = pd.to_numeric(series, errors="coerce").dropna()
    if len(series) < 2:
        return None
    baseline_count = max(1, min(len(series) // 3, 30))
    baseline = float(series.iloc[:baseline_count].mean())
    latest = float(series.iloc[-1])
    if baseline == 0:
        return None
    return ((latest - baseline) / abs(baseline)) * 100.0


def _metric_payload(df: pd.DataFrame, aliases: Iterable[str], label: str, unit: str, decimals: int = 1) -> dict[str, Any]:
    series = _numeric_series(df, aliases)
    latest = float(series.iloc[-1]) if not series.empty else None
    return {
        "label": label,
        "unit": unit,
        "value": round(latest, decimals) if latest is not None and math.isfinite(latest) else None,
        "delta_pct": round(_metric_delta(series), 1) if _metric_delta(series) is not None else None,
        "spark": [round(float(x), 4) for x in series.tail(28).tolist()],
    }


def _dataset_summary(path: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    metrics = {
        "feed_pressure": _metric_payload(df, ("feed_pressure", "feed pressure", "feed_pressure_bar"), "Feed Pressure", "bar"),
        "differential_pressure": _metric_payload(df, ("differential_pressure", "pressure_drop", "dp", "delta_p"), "Differential Pressure (ΔP)", "bar"),
        "permeate_flow": _metric_payload(df, ("permeate_flow", "permeate flow", "product_flow"), "Permeate Flow", "m³/h"),
        "recovery": _metric_payload(df, ("recovery", "recovery_pct", "recovery_percent"), "Recovery", "%"),
        "salt_rejection": _metric_payload(df, ("salt_rejection", "tds_rejection", "rejection_pct"), "Salt Rejection", "%"),
        "sec": _metric_payload(df, ("specific_energy_consumption", "sec", "energy_kwh_m3"), "Specific Energy Consumption", "kWh/m³"),
    }
    flow_series = _numeric_series(df, ("permeate_flow", "permeate flow", "product_flow"))
    if flow_series.empty:
        flow_series = _numeric_series(df, ("feed_pressure", "feed pressure", "feed_pressure_bar"))
    labels: list[str] = []
    time_col = _find_column(df, ("timestamp", "datetime", "date", "time"))
    if time_col:
        parsed = pd.to_datetime(df[time_col], errors="coerce")
        for value in parsed.tail(len(flow_series)):
            labels.append(value.strftime("%b %d") if not pd.isna(value) else "")
    if not labels:
        labels = [str(i + 1) for i in range(len(flow_series))]
    baseline = float(flow_series.iloc[: max(1, min(len(flow_series)//3, 30))].mean()) if not flow_series.empty else None
    return {
        "filename": path.name,
        "row_count": int(len(df)),
        "metrics": metrics,
        "trend": {
            "labels": labels[-90:],
            "values": [round(float(x), 4) for x in flow_series.tail(90).tolist()],
            "baseline": baseline,
        },
    }


def _latest_observation(state: Any, source: str) -> dict[str, Any] | None:
    observations = getattr(state, "observations", []) if state is not None else []
    for obs in reversed(observations):
        if isinstance(obs, dict) and obs.get("source") == source:
            content = obs.get("content")
            if isinstance(content, dict):
                return content
    return None


def _simplify_result(result: dict[str, Any], dataset_path: Path, task_id: str) -> dict[str, Any]:
    state = result.get("state")
    report = result.get("report") if isinstance(result.get("report"), dict) else {}
    diagnosis = _latest_observation(state, "diagnose_issue") or {}
    primary = diagnosis.get("primary_hypothesis") if isinstance(diagnosis.get("primary_hypothesis"), dict) else {}
    anomaly = _latest_observation(state, "detect_anomalies") or {}
    validation = _latest_observation(state, "validate_sensor_data") or {}

    recommendations = report.get("recommendations")
    if not isinstance(recommendations, list):
        recommendations = primary.get("verification_steps") if isinstance(primary.get("verification_steps"), list) else []

    evidence = primary.get("evidence") if isinstance(primary.get("evidence"), list) else []
    if not evidence and isinstance(report.get("evidence"), list):
        evidence = report.get("evidence")

    source_ids: list[str] = []
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key == "source_id" and isinstance(child, str):
                    source_ids.append(child)
                elif key == "source_ids" and isinstance(child, list):
                    source_ids.extend(str(x) for x in child if isinstance(x, str))
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
    walk(diagnosis)
    source_ids = list(dict.fromkeys(source_ids))

    trace = result.get("react_trace") if isinstance(result.get("react_trace"), list) else []
    activity: list[dict[str, Any]] = []
    for item in trace:
        if not isinstance(item, dict):
            continue
        action = item.get("action") or item.get("tool") or item.get("step") or item.get("event") or "Agent step"
        summary = item.get("decision_summary") or item.get("summary") or item.get("status") or ""
        activity.append({"action": str(action), "summary": str(summary)})

    final_answer = getattr(state, "final_answer", None) if state is not None else None
    termination_reason = getattr(state, "termination_reason", None) if state is not None else None
    if hasattr(termination_reason, "value"):
        termination_reason = termination_reason.value

    return {
        "task_id": task_id,
        "dataset": _dataset_summary(dataset_path),
        "final_answer": final_answer or report.get("executive_summary") or report.get("conclusion") or "Investigation completed.",
        "termination_reason": termination_reason,
        "report": _jsonable(report),
        "diagnosis": {
            "status": diagnosis.get("diagnosis_status"),
            "conclusion": diagnosis.get("conclusion"),
            "id": primary.get("id") or primary.get("label") or "Awaiting investigation",
            "severity": primary.get("severity") or "unknown",
            "confidence": primary.get("confidence"),
            "evidence": _jsonable(evidence),
            "verification_steps": _jsonable(recommendations),
            "source_ids": source_ids,
        },
        "anomaly": _jsonable(anomaly),
        "validation": _jsonable(validation),
        "activity": activity,
        "safety_assessment": _jsonable(result.get("safety_assessment")),
        "audit_integrity": _jsonable(result.get("audit_integrity")),
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "app": APP_TITLE}


@app.get("/api/datasets")
def datasets() -> dict[str, Any]:
    items = [{"name": p.name, "path": str(p.relative_to(DATA_ROOT))} for p in _demo_csv_files()]
    return {"datasets": items}


@app.get("/api/dataset/{dataset_name}")
def dataset_summary(dataset_name: str) -> dict[str, Any]:
    path = _resolve_dataset(dataset_name)
    return _dataset_summary(path)


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    payload = await file.read()
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="CSV exceeds upload limit")
    digest = hashlib.sha256(payload).hexdigest()[:12]
    destination = UPLOAD_ROOT / f"{digest}-{_safe_filename(file.filename)}"
    destination.write_bytes(payload)
    return {"name": destination.name, "summary": _dataset_summary(destination)}


@app.post("/api/investigate")
def investigate(payload: InvestigationRequest) -> dict[str, Any]:
    dataset_path = _resolve_dataset(payload.dataset)
    task_id = (
        "ops-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + hashlib.sha1(f"{payload.plant_id}|{payload.user_request}|{dataset_path}".encode()).hexdigest()[:8]
    )
    try:
        runtime = _build_runtime(dataset_path)
        result = _call_runtime(runtime, request=payload.user_request, plant_id=payload.plant_id, task_id=task_id)
    except Exception as exc:
        error_id = hashlib.sha1(f"{type(exc).__name__}|{exc}".encode()).hexdigest()[:8].upper()
        raise HTTPException(status_code=500, detail=f"Investigation failed. Reference: {error_id}") from exc

    ACTIVE_RUNS[task_id] = {"runtime": runtime, "result": result, "dataset_path": dataset_path}
    return _simplify_result(result, dataset_path, task_id)


@app.post("/api/save-incident")
def save_incident(payload: SaveRequest) -> dict[str, Any]:
    run = ACTIVE_RUNS.get(payload.task_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation session is no longer active")
    runtime: AquaMindRuntime = run["runtime"]
    result: dict[str, Any] = run["result"]
    state = result.get("state")
    if state is None:
        raise HTTPException(status_code=400, detail="No investigation state available")
    saved = runtime.save_incident(state, approved=True)
    return _jsonable(saved)


@app.get("/api/traces")
def traces() -> dict[str, Any]:
    trace_root = PROJECT_ROOT / "traces"
    items = []
    if trace_root.exists():
        for path in sorted(trace_root.glob("*.jsonl")):
            items.append({"name": path.name, "size": path.stat().st_size})
    return {"traces": items}


@app.get("/api/cases")
def cases(limit: int = 50) -> dict[str, Any]:
    path = PROJECT_ROOT / "knowledge" / "case_library.json"
    if not path.exists():
        return {"cases": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Case library could not be read") from exc
    items = data.get("cases", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        items = []
    safe_limit = max(1, min(int(limit), 200))
    return {"cases": [_jsonable(item) for item in items[:safe_limit]]}


@app.get("/api/trace/{trace_name}")
def trace_preview(trace_name: str) -> dict[str, Any]:
    safe_name = Path(trace_name).name
    if safe_name != trace_name or not safe_name.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="Invalid trace name")
    path = (PROJECT_ROOT / "traces" / safe_name).resolve()
    trace_root = (PROJECT_ROOT / "traces").resolve()
    if trace_root not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Trace not found")
    text = path.read_text(encoding="utf-8", errors="replace")
    return {"name": safe_name, "preview": text[:20000], "truncated": len(text) > 20000}


@app.get("/api/system-info")
def system_info() -> dict[str, Any]:
    knowledge_root = PROJECT_ROOT / "knowledge"
    def count_items(filename: str, key: str) -> int | None:
        path = knowledge_root / filename
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get(key), list):
                return len(data[key])
        except Exception:
            return None
        return None
    return {
        "sources": count_items("source_registry.json", "sources"),
        "cases": count_items("case_library.json", "cases"),
        "rules": count_items("diagnostic_rules.json", "rules"),
        "evidence_terms": count_items("evidence_vocabulary.json", "terms"),
    }


app.mount("/assets", StaticFiles(directory=FRONTEND_ROOT), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_ROOT / "index.html", headers={"Cache-Control": "no-store, max-age=0"})


# ---------------------------------------------------------------------------
# Investor-ready universal agent layer
# ---------------------------------------------------------------------------
class AgentRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2400)
    dataset: str | None = None
    plant_id: str = Field(default="RO-TRAIN-01", min_length=1, max_length=120)
    user_name: str = Field(default="Operator", max_length=120)
    task_id: str | None = None


def _words(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", str(text).lower())
        if len(token) > 2
    }


def _read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{k} {_flatten_text(v)}" for k, v in value.items())
    if isinstance(value, list):
        return " ".join(_flatten_text(v) for v in value)
    return str(value or "")


def _score_text(query: str, text: str) -> float:
    q = _words(query)
    if not q:
        return 0.0
    hay = str(text).lower()
    score = sum(2.0 for token in q if token in hay)
    phrase = str(query).strip().lower()
    if phrase and phrase in hay:
        score += 5.0
    return score


def _knowledge_search(query: str, limit: int = 6) -> dict[str, Any]:
    knowledge_root = PROJECT_ROOT / "knowledge"
    case_data = _read_json_file(knowledge_root / "case_library.json")
    source_data = _read_json_file(knowledge_root / "source_registry.json")

    raw_cases = case_data.get("cases", []) if isinstance(case_data, dict) else []
    raw_sources = source_data.get("sources", []) if isinstance(source_data, dict) else []
    if not isinstance(raw_cases, list):
        raw_cases = []
    if not isinstance(raw_sources, list):
        raw_sources = []

    scored_cases = []
    for case in raw_cases:
        if not isinstance(case, dict):
            continue
        score = _score_text(query, _flatten_text(case))
        if score > 0:
            scored_cases.append((score, case))
    scored_cases.sort(key=lambda x: x[0], reverse=True)

    source_by_id: dict[str, dict[str, Any]] = {}
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        sid = str(source.get("source_id") or source.get("id") or "").strip()
        if sid:
            source_by_id[sid] = source

    picked_cases = [case for _, case in scored_cases[:limit]]
    source_ids: list[str] = []
    for case in picked_cases:
        ids = case.get("source_ids")
        if isinstance(ids, list):
            source_ids.extend(str(x) for x in ids if isinstance(x, str))
    source_ids = list(dict.fromkeys(source_ids))

    scored_sources = []
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        sid = str(source.get("source_id") or source.get("id") or "")
        score = _score_text(query, _flatten_text(source))
        if sid in source_ids:
            score += 8.0
        if score > 0:
            scored_sources.append((score, source))
    scored_sources.sort(key=lambda x: x[0], reverse=True)

    sources = [source for _, source in scored_sources[:limit]]
    return {
        "cases": [_jsonable(c) for c in picked_cases],
        "sources": [_jsonable(s) for s in sources],
    }


def _source_label(source: dict[str, Any]) -> str:
    return str(
        source.get("source_id")
        or source.get("id")
        or source.get("title")
        or "Source"
    )


def _gemini_answer(question: str, evidence: dict[str, Any], *, context: dict[str, Any] | None = None) -> str | None:
    if not os.getenv("GEMINI_API_KEY"):
        return None
    try:
        from google import genai
    except Exception:
        return None

    compact = {
        "question": question,
        "knowledge_cases": evidence.get("cases", [])[:5],
        "knowledge_sources": evidence.get("sources", [])[:5],
        "investigation_context": context or {},
    }
    system = (
        "You are AquaMindAI-Agent, an industrial reverse-osmosis desalination "
        "operations intelligence agent. Answer the operator's question using only "
        "the supplied grounded evidence and investigation context. Be concise, "
        "technical, practical, and explicit about uncertainty. Treat diagnoses as "
        "hypotheses requiring verification. Never authorize physical plant control, "
        "setpoint changes, valve/pump actuation, dosing, shutdown, or cleaning. "
        "When useful, cite source IDs in square brackets. Do not reveal chain-of-thought."
    )
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=os.getenv("AQUAMIND_LLM_MODEL", "gemini-3.5-flash-lite"),
            contents=json.dumps(compact, ensure_ascii=False),
            config={
                "system_instruction": system,
                "temperature": 0.15,
                "max_output_tokens": 700,
            },
        )
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
    except Exception:
        return None
    return None


_RO_PRIMER = {
    "membrane": (
        "Reverse-osmosis membranes are semi-permeable barriers. A high-pressure pump "
        "raises feed-water pressure above the osmotic pressure, driving water through "
        "the membrane while most dissolved salts and many contaminants remain in the "
        "concentrate stream. Operators therefore watch pressure, permeate flow, salt "
        "rejection, recovery, differential pressure and specific energy together—not "
        "as isolated measurements."
    ),
    "recovery": (
        "Recovery is the fraction of feed flow converted to permeate. Increasing recovery "
        "can improve water production but also increases concentration at the membrane "
        "surface, so it must be evaluated together with scaling risk, pressure, rejection "
        "and site-specific design limits."
    ),
    "rejection": (
        "Salt rejection describes how effectively the RO membrane prevents dissolved salts "
        "from passing into permeate. A meaningful change should be interpreted with normalized "
        "operating conditions, conductivity/TDS data, pressure and temperature rather than "
        "from a single raw value alone."
    ),
}


def _fallback_knowledge_answer(question: str, evidence: dict[str, Any]) -> str:
    q = question.lower()
    if "column" in q and ("data" in q or "csv" in q):
        return (
            "For a useful RO investigation, include a timestamp plus the measurements available from your train. "
            "Commonly useful fields are feed pressure, permeate flow, feed/concentrate flow, feed and permeate "
            "conductivity or TDS, and—when available—differential pressure, temperature and specific energy. "
            "AquaMind validates the uploaded CSV first and will report missing or unusable evidence instead of inventing values."
        )
    primer = None
    if "membrane" in q or "reverse osmosis" in q or " ro " in f" {q} ":
        primer = _RO_PRIMER["membrane"]
    elif "recovery" in q:
        primer = _RO_PRIMER["recovery"]
    elif "rejection" in q or "salt" in q:
        primer = _RO_PRIMER["rejection"]

    cases = evidence.get("cases") or []
    sources = evidence.get("sources") or []
    parts: list[str] = []
    if primer:
        parts.append(primer)
    if cases:
        case = cases[0]
        basis = case.get("reasoning_basis")
        if isinstance(basis, list) and basis:
            parts.append("Operationally, the knowledge base highlights: " + "; ".join(str(x) for x in basis[:3]) + ".")
        patterns = case.get("observed_patterns")
        if isinstance(patterns, list) and patterns:
            parts.append("Relevant patterns include " + ", ".join(str(x) for x in patterns[:4]) + ".")
    if sources:
        parts.append("Grounding: " + ", ".join(f"[{_source_label(s)}]" for s in sources[:4]) + ".")
    if not parts:
        parts.append(
            "I can answer desalination operations questions, but I do not have enough grounded "
            "project evidence for that exact topic yet. Ask about RO membranes, recovery, rejection, "
            "fouling, integrity, operating trends, or load plant data for an investigation."
        )
    return " ".join(parts)


def _is_unsafe_request(message: str) -> tuple[bool, str]:
    text = message.strip().lower()
    injection = any(x in text for x in (
        "ignore previous", "reveal hidden", "reveal system", "bypass safety",
        "disable safety", "override policy", "ignore safety", "circumvent"
    ))
    if injection:
        return True, "The request attempts to override AquaMind's safety boundary. I can analyze the situation and recommend verification steps, but I will not bypass policy or expose hidden instructions."

    # Explanatory questions about equipment are allowed; direct actuation commands are not.
    direct_patterns = (
        r"\b(open|close)\s+(the\s+)?[^.]{0,30}valve\b",
        r"\b(start|stop|restart|trip)\s+(the\s+)?[^.]{0,30}pump\b",
        r"\b(change|set|override|raise|lower)\s+(the\s+)?[^.]{0,30}(setpoint|set point)\b",
        r"\b(shutdown|shut down)\s+(the\s+)?(plant|train|system)\b",
        r"\b(dose|inject)\s+[^.]{0,30}(chemical|antiscalant|biocide|acid|caustic)\b",
        r"\b(run|start|trigger)\s+(a\s+)?(cip|cleaning cycle)\b",
    )
    if any(re.search(pattern, text) for pattern in direct_patterns):
        return True, "AquaMind can analyze and recommend, but it does not directly actuate pumps, valves, setpoints, dosing, shutdowns, or cleaning cycles. I can evaluate the evidence and prepare a verification plan for an authorized operator."
    return False, ""


def _route_intent(message: str, task_id: str | None) -> str:
    text = message.strip().lower()
    tokens = [t for t in re.findall(r"[a-z0-9_]+", text) if t]

    if task_id and any(x in text for x in (
        "why", "evidence", "source", "what next", "next step", "recommend",
        "verification", "explain", "conclusion", "hypothesis", "compare",
        "how confident", "confidence", "show me"
    )):
        return "followup"

    # Extremely short or underspecified prompts should never start an expensive
    # plant investigation. Ask the operator what they want instead.
    if len(tokens) <= 2 and text in {
        "ro", "help", "hello", "hi", "hey", "start", "investigate",
        "membrane", "plant", "data", "problem", "issue"
    }:
        return "clarify"

    knowledge_openers = (
        "what is", "what are", "how does", "how do", "how ", "explain",
        "define", "tell me about", "why does", "why is a"
    )
    investigation_context = any(x in text for x in (
        "this plant", "our plant", "this train", "train 1", "ro-train",
        "this data", "dataset", "current", "today", "last week", "decline",
        "increased", "decreased", "abnormal", "anomaly", "trend", "investigate",
        "analyze", "analyse"
    ))
    if text.startswith(knowledge_openers) and not investigation_context:
        return "knowledge"

    operational = any(x in text for x in (
        "investigate", "analyze", "analyse", "decline", "increase", "decrease",
        "abnormal", "anomaly", "trend", "pressure", "permeate flow", "conductivity",
        "recovery", "sec", "fouling", "integrity", "plant data", "dataset",
        "performance", "train 1", "ro-train"
    ))
    if not operational and any(x in text for x in ("membrane", "osmosis", "desalination", "pretreatment", "antiscalant")):
        return "knowledge"
    return "investigation"


def _smart_suggestions(route: str, result: dict[str, Any] | None = None) -> list[str]:
    if route == "clarify":
        return [
            "Investigate current plant performance",
            "Explain an RO concept",
            "Review a recent anomaly",
        ]
    if route == "degraded":
        return [
            "Retry the investigation",
            "Show me the plant data summary",
            "Answer using grounded knowledge only",
        ]
    if route == "knowledge":
        return [
            "What operating signals indicate membrane fouling?",
            "How do recovery and salt rejection interact?",
            "When should an RO trend trigger an investigation?",
        ]
    if route == "safety_block":
        return [
            "Analyze the risk without changing plant controls",
            "What should an operator verify before acting?",
            "Show the evidence behind the safety block",
        ]
    diagnosis = (result or {}).get("diagnosis") or {}
    label = str(diagnosis.get("id") or "the hypothesis").replace("_", " ")
    return [
        "Show the strongest supporting evidence",
        "What should be verified next?",
        f"Explain why {label} is more likely than alternatives",
    ]


def _followup_answer(question: str, simplified: dict[str, Any]) -> str:
    diagnosis = simplified.get("diagnosis") or {}
    evidence = diagnosis.get("evidence") or []
    sources = diagnosis.get("source_ids") or []
    steps = diagnosis.get("verification_steps") or []
    q = question.lower()
    if "source" in q:
        if sources:
            return "The current hypothesis is grounded in these project source IDs: " + ", ".join(f"[{x}]" for x in sources[:8]) + "."
        return "The current result did not expose additional source IDs. I would keep the hypothesis verification-required rather than overstate certainty."
    if "evidence" in q or "why" in q or "explain" in q or "confidence" in q:
        lines = [evidenceText for evidenceText in [
            str(x.get("description") or x.get("statement") or x.get("metric") or x.get("reason") or x)
            if isinstance(x, dict) else str(x)
            for x in evidence[:5]
        ] if evidenceText]
        answer = diagnosis.get("conclusion") or simplified.get("final_answer") or "The hypothesis is based on the observed operating pattern."
        if lines:
            answer += " Strongest evidence: " + "; ".join(lines) + "."
        if sources:
            answer += " Grounding: " + ", ".join(f"[{x}]" for x in sources[:6]) + "."
        answer += " This remains a source-grounded heuristic hypothesis, not a calibrated probability."
        return answer
    if "next" in q or "recommend" in q or "verification" in q:
        if steps:
            return "Recommended verification sequence: " + " ".join(f"{i+1}) {str(x)}" for i, x in enumerate(steps[:5]))
        return "No additional verification steps were returned. Review data quality, normalized performance, pretreatment history and recent maintenance before taking physical action."
    return (
        simplified.get("final_answer")
        or diagnosis.get("conclusion")
        or "I can explain the evidence, sources, verification plan, or alternatives from the current investigation."
    )


def _data_quality_notice(simplified: dict[str, Any]) -> str | None:
    validation = simplified.get("validation") or {}
    quality = validation.get("quality_score")
    removed = validation.get("removed_row_count")
    recovery = validation.get("recovery_actions")
    if isinstance(quality, (int, float)) and quality < 0.9:
        return f"Data quality is {quality:.0%}; interpret the diagnosis cautiously."
    if isinstance(removed, int) and removed > 0:
        return f"Validation removed {removed} unusable row(s) before analysis."
    if isinstance(recovery, list) and recovery:
        return "Recoverable data-quality issues were corrected before analysis."
    return None


def _proactive_insights(dataset: dict[str, Any]) -> list[str]:
    metrics = dataset.get("metrics") or {}
    insights: list[tuple[float, str]] = []
    for key, m in metrics.items():
        if not isinstance(m, dict):
            continue
        delta = m.get("delta_pct")
        if not isinstance(delta, (int, float)):
            continue
        if abs(delta) >= 5:
            direction = "increased" if delta > 0 else "decreased"
            insights.append((abs(float(delta)), f"{m.get('label', key)} {direction} {abs(float(delta)):.1f}% from the initial baseline."))
    insights.sort(reverse=True, key=lambda x: x[0])
    return [text for _, text in insights[:3]]


def _related_cases(query: str, limit: int = 5) -> list[dict[str, Any]]:
    path = PROJECT_ROOT / "knowledge" / "case_library.json"
    data = _read_json_file(path)
    items = data.get("cases", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        return []
    scored = []
    for case in items:
        if isinstance(case, dict):
            score = _score_text(query, _flatten_text(case))
            if score > 0:
                scored.append((score, case))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [_jsonable(c) for _, c in scored[:limit]]


@app.post("/api/agent")
def universal_agent(payload: AgentRequest) -> dict[str, Any]:
    unsafe, safety_message = _is_unsafe_request(payload.message)
    if unsafe:
        return {
            "route": "safety_block",
            "answer": safety_message,
            "suggestions": _smart_suggestions("safety_block"),
            "safety_blocked": True,
        }

    route = _route_intent(payload.message, payload.task_id)

    if route == "clarify":
        return {
            "route": "clarify",
            "answer": (
                "I can help with RO operations. Tell me what you want to do: investigate current "
                "plant performance, explain an RO concept, review an anomaly, compare operating "
                "trends, or search previous incidents."
            ),
            "suggestions": _smart_suggestions("clarify"),
        }

    if route == "followup" and payload.task_id in ACTIVE_RUNS:
        run = ACTIVE_RUNS[payload.task_id]
        dataset_path = run.get("dataset_path")
        if isinstance(dataset_path, Path):
            simplified = _simplify_result(run["result"], dataset_path, payload.task_id)
            evidence = _knowledge_search(payload.message, 5)
            answer = _gemini_answer(payload.message, evidence, context=simplified) or _followup_answer(payload.message, simplified)
            return {
                "route": "followup",
                "answer": answer,
                "task_id": payload.task_id,
                "suggestions": _smart_suggestions("followup", simplified),
                "sources": evidence.get("sources", []),
            }

    if route == "knowledge":
        evidence = _knowledge_search(payload.message, 6)
        answer = _gemini_answer(payload.message, evidence) or _fallback_knowledge_answer(payload.message, evidence)
        return {
            "route": "knowledge",
            "answer": answer,
            "sources": evidence.get("sources", []),
            "related_cases": evidence.get("cases", [])[:4],
            "suggestions": _smart_suggestions("knowledge"),
        }

    if not payload.dataset:
        return {
            "route": "needs_data",
            "answer": "This looks like an operational investigation. Select or upload plant CSV data and I can validate it, calculate RO KPIs, detect anomalies, search grounded knowledge and incident memory, then produce a verification-oriented diagnosis.",
            "suggestions": ["Open Plant Data", "What data columns do you need?"],
        }

    try:
        result = investigate(
            InvestigationRequest(
                dataset=payload.dataset,
                user_request=payload.message,
                plant_id=payload.plant_id,
                user_name=payload.user_name,
            )
        )
    except HTTPException as exc:
        reference = str(exc.detail)
        return {
            "route": "degraded",
            "answer": (
                "I could not complete the full plant investigation safely. The workspace is still "
                "available, and I have not fabricated a diagnosis. You can retry, review the plant "
                "data summary, or ask a grounded RO knowledge question instead."
            ),
            "reference": reference,
            "suggestions": _smart_suggestions("degraded"),
        }
    except Exception as exc:
        error_id = hashlib.sha1(f"{type(exc).__name__}|{exc}".encode()).hexdigest()[:8].upper()
        return {
            "route": "degraded",
            "answer": (
                "The analytical runtime is temporarily unavailable. I stopped safely without "
                "inventing a result. You can retry or continue with grounded knowledge while the "
                "runtime recovers."
            ),
            "reference": error_id,
            "suggestions": _smart_suggestions("degraded"),
        }
    result["route"] = "investigation"
    result["suggestions"] = _smart_suggestions("investigation", result)
    result["data_quality_notice"] = _data_quality_notice(result)
    result["proactive_insights"] = _proactive_insights(result.get("dataset") or {})
    query = " ".join([
        str((result.get("diagnosis") or {}).get("id") or ""),
        payload.message,
    ])
    result["related_cases"] = _related_cases(query, 5)
    return result


@app.get("/api/related-cases")
def related_cases(q: str, limit: int = 5) -> dict[str, Any]:
    safe_limit = max(1, min(int(limit), 20))
    return {"cases": _related_cases(q, safe_limit)}


@app.get("/api/investigation/{task_id}")
def investigation_snapshot(task_id: str) -> dict[str, Any]:
    run = ACTIVE_RUNS.get(task_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation session is no longer active")
    dataset_path = run.get("dataset_path")
    if not isinstance(dataset_path, Path):
        raise HTTPException(status_code=500, detail="Investigation dataset is unavailable")
    return _simplify_result(run["result"], dataset_path, task_id)


@app.get("/api/demo-scenario")
def demo_scenario() -> dict[str, Any]:
    preferred = "scaling_colloidal_fouling.csv"
    names = [p.name for p in _demo_csv_files()]
    dataset = preferred if preferred in names else (names[0] if names else None)
    return {
        "dataset": dataset,
        "plant_id": "RO-TRAIN-01",
        "prompt": "Investigate the RO performance decline, identify the most defensible source-grounded hypothesis, explain the evidence, and recommend safe verification steps.",
        "title": "Membrane performance degradation",
    }
