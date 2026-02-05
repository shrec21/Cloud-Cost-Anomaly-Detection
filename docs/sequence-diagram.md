# Cloud Cost Anomaly Detection - Sequence Diagram

## System Flow

```
┌──────────┐          ┌──────────────┐          ┌─────────────┐          ┌──────────────┐
│  Browser │          │   React UI   │          │  Azure Func │          │ Mock/Cosmos  │
│          │          │ (localhost:  │          │    API      │          │    Data      │
│          │          │    3000)     │          │ (port 7071) │          │              │
└────┬─────┘          └──────┬───────┘          └──────┬──────┘          └──────┬───────┘
     │                       │                         │                        │
     │  Open localhost:3000  │                         │                        │
     │──────────────────────>│                         │                        │
     │                       │                         │                        │
     │                       │  GET /api/costs         │                        │
     │                       │────────────────────────>│                        │
     │                       │                         │                        │
     │                       │                         │  get_mock_costs(30)    │
     │                       │                         │───────────────────────>│
     │                       │                         │                        │
     │                       │                         │  [30 days cost data]   │
     │                       │                         │<───────────────────────│
     │                       │                         │                        │
     │                       │  {success, data, mode}  │                        │
     │                       │<────────────────────────│                        │
     │                       │                         │                        │
     │                       │  GET /api/anomalies     │                        │
     │                       │────────────────────────>│                        │
     │                       │                         │                        │
     │                       │                         │  detect_anomalies()    │
     │                       │                         │───────────────────────>│
     │                       │                         │                        │
     │                       │                         │  Z-score analysis      │
     │                       │                         │  (threshold > 2.0)     │
     │                       │                         │<───────────────────────│
     │                       │                         │                        │
     │                       │  {anomalies[], count}   │                        │
     │                       │<────────────────────────│                        │
     │                       │                         │                        │
     │   Render Dashboard    │                         │                        │
     │   - Summary Cards     │                         │                        │
     │   - Cost Line Chart   │                         │                        │
     │   - Anomaly Markers   │                         │                        │
     │<──────────────────────│                         │                        │
     │                       │                         │                        │
     │                       │                         │                        │
     │         ═══════════════ POST Event Flow ═══════════════                  │
     │                       │                         │                        │
     │                       │  POST /api/events       │                        │
     │                       │  {ts, service, cost...} │                        │
     │                       │────────────────────────>│                        │
     │                       │                         │                        │
     │                       │                         │  Validate (Pydantic)   │
     │                       │                         │───────┐                │
     │                       │                         │       │                │
     │                       │                         │<──────┘                │
     │                       │                         │                        │
     │                       │                         │  Store event           │
     │                       │                         │───────────────────────>│
     │                       │                         │   (memory or Cosmos)   │
     │                       │                         │<───────────────────────│
     │                       │                         │                        │
     │                       │  {ok: true, id, mode}   │                        │
     │                       │<────────────────────────│                        │
     │                       │                         │                        │
```

## Component Summary

| Component | Role |
|-----------|------|
| **React UI** | Dashboard with charts, fetches data on load |
| **Azure Functions API** | REST endpoints, CORS enabled |
| **mock_data.py** | Generates 30 days of fake cost data |
| **anomaly_detector.py** | Z-score detection (flags > 2 std devs) |
| **Cosmos DB** | Optional - used when credentials configured |

## Data Flow

1. UI loads → parallel fetch `/api/costs` + `/api/anomalies`
2. API checks `USE_COSMOS` flag → uses mock data if false
3. Anomaly detection runs Z-score analysis on cost data
4. UI renders chart with red markers on anomaly dates

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Returns API status and mode (mock/cosmos) |
| `/api/costs` | GET | Returns daily cost data (last 30 days) |
| `/api/anomalies` | GET | Returns detected anomalies |
| `/api/summary` | GET | Returns cost summary with service breakdown |
| `/api/events` | POST | Ingest a new cost event |

## Anomaly Detection Algorithm

Uses **Z-score method**:
- Calculate mean and standard deviation of daily costs
- Flag days where `|z-score| > threshold` (default: 2.0)
- Severity: "high" if z-score > 3, otherwise "medium"

```
z-score = (value - mean) / std_deviation
```
