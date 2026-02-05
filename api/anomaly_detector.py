"""Anomaly detection using Z-score method."""

import math
from typing import Optional


def calculate_mean(values: list[float]) -> float:
    """Calculate the arithmetic mean of a list of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_std_dev(values: list[float], mean: Optional[float] = None) -> float:
    """Calculate the standard deviation of a list of values."""
    if not values or len(values) < 2:
        return 0.0

    if mean is None:
        mean = calculate_mean(values)

    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
    """Calculate the Z-score for a value given mean and standard deviation."""
    if std_dev == 0:
        return 0.0
    return (value - mean) / std_dev


def detect_anomalies(cost_data: list[dict], threshold: float = 2.0) -> list[dict]:
    """Detect anomalies in cost data using Z-score method.

    Args:
        cost_data: List of daily cost records with 'date' and 'total_cost' fields.
        threshold: Z-score threshold for flagging anomalies (default: 2.0 std devs).

    Returns:
        List of anomaly records with date, cost, z_score, and reason.
    """
    if not cost_data:
        return []

    # Extract total costs
    costs = [day["total_cost"] for day in cost_data]

    # Calculate statistics
    mean = calculate_mean(costs)
    std_dev = calculate_std_dev(costs, mean)

    anomalies = []

    for day in cost_data:
        cost = day["total_cost"]
        z_score = calculate_z_score(cost, mean, std_dev)

        if abs(z_score) > threshold:
            # Determine which service contributed most to the anomaly
            services = day.get("services", {})
            max_service = max(services.items(), key=lambda x: x[1])[0] if services else "unknown"

            anomalies.append({
                "date": day["date"],
                "total_cost": cost,
                "z_score": round(z_score, 2),
                "expected_cost": round(mean, 2),
                "deviation": round(cost - mean, 2),
                "severity": "high" if abs(z_score) > 3 else "medium",
                "reason": f"Unusual spike in {max_service} costs"
            })

    return anomalies
