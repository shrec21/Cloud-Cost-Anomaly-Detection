# Cloud Cost Anomaly Detection

A dashboard for monitoring cloud costs and detecting unusual spending patterns using statistical analysis.

## Features

- **Cost Dashboard** - Visualize daily cloud costs over 30 days
- **Anomaly Detection** - Automatically flags unusual spending spikes using Z-score analysis
- **Service Breakdown** - View costs by service (compute, storage, network, database)
- **Mock/Production Mode** - Works with mock data locally, connects to Cosmos DB when deployed

## Architecture

```
┌─────────────┐      ┌─────────────────┐      ┌──────────────┐
│  React UI   │ ───> │  Azure Functions │ ───> │  Mock Data / │
│  (Port 3000)│ <─── │  API (Port 7071) │ <─── │  Cosmos DB   │
└─────────────┘      └─────────────────┘      └──────────────┘
```

## Quick Start

### 1. Start the API

```bash
cd api
pip install -r requirements.txt
func start
```

API runs at http://localhost:7071

### 2. Start the UI

```bash
cd ui
npm install
npm start
```

UI opens at http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | API status and mode (mock/cosmos) |
| `/api/costs` | GET | Daily cost data (last 30 days) |
| `/api/anomalies` | GET | Detected anomalies |
| `/api/summary` | GET | Cost summary with service breakdown |
| `/api/events` | POST | Ingest a cost event |

## Anomaly Detection

Uses **Z-score method**:
- Calculates mean and standard deviation of daily costs
- Flags days where cost deviates > 2 standard deviations
- Severity: "high" (z > 3) or "medium" (z > 2)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Recharts |
| Backend | Azure Functions (Python) |
| Validation | Pydantic |
| Database | Azure Cosmos DB (optional) |

## Project Structure

```
├── api/
│   ├── function_app.py      # API endpoints
│   ├── mock_data.py         # Mock cost data generator
│   ├── anomaly_detector.py  # Z-score anomaly detection
│   └── requirements.txt     # Python dependencies
├── ui/
│   ├── src/
│   │   ├── App.js           # Main dashboard
│   │   ├── App.css          # Styles
│   │   └── components/
│   │       └── CostChart.js # Cost trend chart
│   └── package.json         # Node dependencies
└── docs/
    ├── architecture.md
    └── sequence-diagram.md
```

## Configuration

For production with Cosmos DB, set environment variables:

```bash
COSMOS_URL=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key
COSMOS_DB=costdb
```

Without these, the API runs in mock mode with generated data.

## License

MIT
