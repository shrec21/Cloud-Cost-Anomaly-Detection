import React, { useState, useEffect } from 'react';
import CostChart from './components/CostChart';
import './App.css';

function App() {
  const [costData, setCostData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch cost data and anomalies in parallel
        const API_BASE = 'https://cloud-cost-anomaly-api.azurewebsites.net';
        const [costsResponse, anomaliesResponse] = await Promise.all([
          fetch(`${API_BASE}/api/costs`),
          fetch(`${API_BASE}/api/anomalies`)
        ]);

        if (!costsResponse.ok || !anomaliesResponse.ok) {
          throw new Error('Failed to fetch data from API');
        }

        const costsJson = await costsResponse.json();
        const anomaliesJson = await anomaliesResponse.json();

        if (costsJson.success) {
          setCostData(costsJson.data);
        }
        if (anomaliesJson.success) {
          setAnomalies(anomaliesJson.data);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // Calculate summary stats
  const totalSpend = costData.reduce((sum, day) => sum + day.total_cost, 0);
  const avgDaily = costData.length > 0 ? totalSpend / costData.length : 0;

  return (
    <div className="app">
      <header className="header">
        <h1>Cloud Cost Anomaly Dashboard</h1>
        <p>Monitor and detect unusual spending patterns</p>
      </header>

      {error && (
        <div className="error">
          Error: {error}. Please try again later.
        </div>
      )}

      <div className="summary-cards">
        <div className="card">
          <h3>Total Spend (30 days)</h3>
          <div className="value">
            {loading ? '...' : `$${totalSpend.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
          </div>
        </div>
        <div className="card">
          <h3>Daily Average</h3>
          <div className="value">
            {loading ? '...' : `$${avgDaily.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
          </div>
        </div>
        <div className="card anomaly">
          <h3>Anomalies Detected</h3>
          <div className="value">
            {loading ? '...' : anomalies.length}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading cost data...</div>
      ) : (
        <CostChart costData={costData} anomalies={anomalies} />
      )}
    </div>
  );
}

export default App;
