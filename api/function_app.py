import json
import os
from datetime import datetime, timedelta, timezone
import azure.functions as func
from pydantic import BaseModel, Field

from mock_data import get_mock_costs
from anomaly_detector import detect_anomalies

app = func.FunctionApp()

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DB_NAME = os.getenv("COSMOS_DB", "costdb")

# Check if Cosmos DB is configured
USE_COSMOS = bool(COSMOS_URL and COSMOS_KEY)

# In-memory storage for mock mode
_mock_events = []


def _client():
    if not USE_COSMOS:
        raise RuntimeError("Cosmos DB not configured - using mock data")
    from azure.cosmos import CosmosClient
    return CosmosClient(COSMOS_URL, credential=COSMOS_KEY)


def _db():
    return _client().get_database_client(DB_NAME)


def add_cors_headers(response: func.HttpResponse) -> func.HttpResponse:
    """Add CORS headers for local development."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


class CostEvent(BaseModel):
    subscriptionId: str = "demo"
    ts: str  # ISO string
    service: str
    resourceGroup: str
    region: str = "unknown"
    costUsd: float = Field(ge=0)
    usageQty: float | None = None
    tags: dict = {}


@app.route(route="events", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def ingest_event(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return add_cors_headers(func.HttpResponse(status_code=204))

    try:
        body = req.get_json()
        ev = CostEvent(**body)
        dt = datetime.fromisoformat(ev.ts.replace("Z", "+00:00"))
        date = dt.date().isoformat()

        doc = {
            "id": f"evt_{ev.ts}_{ev.service}_{ev.resourceGroup}",
            "pk": ev.subscriptionId,
            "ts": ev.ts,
            "date": date,
            "service": ev.service,
            "resourceGroup": ev.resourceGroup,
            "region": ev.region,
            "costUsd": float(ev.costUsd),
            "usageQty": ev.usageQty,
            "tags": ev.tags or {}
        }

        if USE_COSMOS:
            events = _db().get_container_client("events")
            events.upsert_item(doc)
        else:
            # Mock mode: store in memory
            _mock_events.append(doc)

        return add_cors_headers(func.HttpResponse(
            json.dumps({"ok": True, "id": doc["id"], "mode": "cosmos" if USE_COSMOS else "mock"}),
            mimetype="application/json",
            status_code=200
        ))
    except Exception as e:
        return add_cors_headers(func.HttpResponse(
            json.dumps({"ok": False, "error": str(e)}),
            mimetype="application/json",
            status_code=400
        ))


@app.route(route="costs", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def get_costs(req: func.HttpRequest) -> func.HttpResponse:
    """Return daily cost data - from Cosmos or mock data."""
    if req.method == "OPTIONS":
        return add_cors_headers(func.HttpResponse(status_code=204))

    try:
        days = int(req.params.get("days", "30"))
        days = min(max(days, 1), 90)

        if USE_COSMOS:
            # TODO: Query Cosmos for aggregated daily costs
            return add_cors_headers(func.HttpResponse(
                json.dumps({"success": True, "data": [], "mode": "cosmos", "todo": "implement query"}),
                mimetype="application/json"
            ))
        else:
            # Mock mode: use generated data
            cost_data = get_mock_costs(days)
            return add_cors_headers(func.HttpResponse(
                json.dumps({"success": True, "data": cost_data, "mode": "mock"}),
                mimetype="application/json"
            ))
    except Exception as e:
        return add_cors_headers(func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        ))


@app.route(route="summary", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def summary(req: func.HttpRequest) -> func.HttpResponse:
    """Return cost summary statistics."""
    if req.method == "OPTIONS":
        return add_cors_headers(func.HttpResponse(status_code=204))

    try:
        if USE_COSMOS:
            # TODO: Query Cosmos for summary
            return add_cors_headers(func.HttpResponse(
                json.dumps({"success": True, "mode": "cosmos", "todo": "implement query"}),
                mimetype="application/json"
            ))
        else:
            # Mock mode: calculate from mock data
            cost_data = get_mock_costs(30)
            total = sum(d["total_cost"] for d in cost_data)
            avg = total / len(cost_data) if cost_data else 0

            # Service breakdown
            services = {}
            for day in cost_data:
                for svc, cost in day["services"].items():
                    services[svc] = services.get(svc, 0) + cost

            return add_cors_headers(func.HttpResponse(
                json.dumps({
                    "success": True,
                    "mode": "mock",
                    "data": {
                        "total_cost": round(total, 2),
                        "daily_average": round(avg, 2),
                        "days": len(cost_data),
                        "services": {k: round(v, 2) for k, v in services.items()}
                    }
                }),
                mimetype="application/json"
            ))
    except Exception as e:
        return add_cors_headers(func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        ))


@app.route(route="anomalies", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def list_anomalies(req: func.HttpRequest) -> func.HttpResponse:
    """Return detected anomalies."""
    if req.method == "OPTIONS":
        return add_cors_headers(func.HttpResponse(status_code=204))

    try:
        threshold = float(req.params.get("threshold", "2.0"))
        threshold = min(max(threshold, 1.0), 5.0)

        if USE_COSMOS:
            # TODO: Query Cosmos for stored anomalies
            return add_cors_headers(func.HttpResponse(
                json.dumps({"success": True, "data": [], "mode": "cosmos", "todo": "implement query"}),
                mimetype="application/json"
            ))
        else:
            # Mock mode: detect from mock data
            cost_data = get_mock_costs(30)
            anomalies = detect_anomalies(cost_data, threshold)

            return add_cors_headers(func.HttpResponse(
                json.dumps({
                    "success": True,
                    "data": anomalies,
                    "count": len(anomalies),
                    "threshold": threshold,
                    "mode": "mock"
                }),
                mimetype="application/json"
            ))
    except Exception as e:
        return add_cors_headers(func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        ))


@app.route(route="status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Return API status and configuration mode."""
    return add_cors_headers(func.HttpResponse(
        json.dumps({
            "status": "ok",
            "mode": "cosmos" if USE_COSMOS else "mock",
            "cosmos_configured": USE_COSMOS,
            "mock_events_count": len(_mock_events)
        }),
        mimetype="application/json"
    ))


@app.timer_trigger(schedule="0 0 2 * * *", arg_name="mytimer", run_on_startup=False)
def nightly_detector(mytimer: func.TimerRequest) -> None:
    # Will: aggregate yesterday + run MAD detection + write anomalies
    # (Only runs when deployed to Azure with Cosmos configured)
    if not USE_COSMOS:
        return
    pass
