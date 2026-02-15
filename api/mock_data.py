"""Mock cost data generator for Cloud Cost Anomaly Detection."""

import random
from datetime import datetime, timedelta


def generate_mock_costs(days: int = 30) -> list[dict]:
    """Generate mock daily cost data for the specified number of days.

    Args:
        days: Number of days of historical data to generate.

    Returns:
        List of daily cost records with service breakdown.
    """
    data = []
    base_date = datetime.now() - timedelta(days=days) 

    # Base costs for each service (will vary slightly each day)
    base_costs = {
        "compute": 600.0,
        "storage": 300.0,
        "network": 200.0,
        "database": 250.0
    }

    for i in range(days):
        current_date = base_date + timedelta(days=i)

        # Generate daily costs with some random variation
        services = {}
        for service, base_cost in base_costs.items():
            # Normal variation: +/- 15%
            variation = random.uniform(-0.15, 0.15)
            services[service] = round(base_cost * (1 + variation), 2)

        # Inject some anomalies (roughly 10% of days)
        if random.random() < 0.1:
            # Pick a random service to spike
            spike_service = random.choice(list(services.keys()))
            # Spike it by 50-100%
            spike_factor = random.uniform(1.5, 2.0)
            services[spike_service] = round(services[spike_service] * spike_factor, 2)

        total_cost = round(sum(services.values()), 2)

        data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "total_cost": total_cost,
            "services": services
        })

    return data


# Cache the generated data so it's consistent within a session
_cached_data = None


def get_mock_costs(days: int = 30) -> list[dict]:
    """Get mock cost data, using cached data if available.

    Args:
        days: Number of days of historical data.

    Returns:
        List of daily cost records.
    """
    global _cached_data
    if _cached_data is None or len(_cached_data) != days:
        _cached_data = generate_mock_costs(days)
    return _cached_data
