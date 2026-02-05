import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot
} from 'recharts';

function CostChart({ costData, anomalies }) {
  // Merge cost data with anomaly flags
  const chartData = costData.map(day => {
    const isAnomaly = anomalies.some(a => a.date === day.date);
    return {
      ...day,
      isAnomaly,
      // Format date for display (MM/DD)
      displayDate: new Date(day.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    };
  });

  // Get anomaly points for markers
  const anomalyPoints = chartData.filter(d => d.isAnomaly);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{
          background: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '12px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          <p style={{ fontWeight: 600, marginBottom: '8px' }}>{data.date}</p>
          <p style={{ color: '#3b82f6' }}>
            Total: ${data.total_cost.toLocaleString()}
          </p>
          {data.services && (
            <div style={{ marginTop: '8px', fontSize: '0.875rem', color: '#666' }}>
              {Object.entries(data.services).map(([service, cost]) => (
                <p key={service}>
                  {service}: ${cost.toLocaleString()}
                </p>
              ))}
            </div>
          )}
          {data.isAnomaly && (
            <p style={{ color: '#ef4444', marginTop: '8px', fontWeight: 500 }}>
              Anomaly Detected
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-container">
      <h2>Daily Cloud Costs (Last 30 Days)</h2>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="displayDate"
            tick={{ fill: '#666', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#666', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="total_cost"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 0, r: 3 }}
            activeDot={{ r: 6, fill: '#3b82f6' }}
          />
          {/* Anomaly markers */}
          {anomalyPoints.map((point, index) => (
            <ReferenceDot
              key={index}
              x={point.displayDate}
              y={point.total_cost}
              r={8}
              fill="#ef4444"
              stroke="white"
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="legend">
        <div className="legend-item">
          <span className="legend-dot normal"></span>
          <span>Normal Cost</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot anomaly"></span>
          <span>Anomaly</span>
        </div>
      </div>
    </div>
  );
}

export default CostChart;
