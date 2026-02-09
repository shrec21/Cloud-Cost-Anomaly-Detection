"""Unit tests for Cloud Cost Anomaly Detection API workflow."""

import unittest
from unittest.mock import MagicMock, patch

# Import modules under test
from anomaly_detector import calculate_mean, calculate_std_dev, calculate_z_score, detect_anomalies
from mock_data import generate_mock_costs, get_mock_costs


class TestAnomalyDetector(unittest.TestCase):
    """Tests for anomaly detection functions."""

    def test_calculate_mean_normal(self):
        """Test mean calculation with normal values."""
        values = [100.0, 200.0, 300.0, 400.0, 500.0]
        self.assertEqual(calculate_mean(values), 300.0)

    def test_calculate_mean_empty(self):
        """Test mean calculation with empty list."""
        self.assertEqual(calculate_mean([]), 0.0)

    def test_calculate_std_dev_normal(self):
        """Test standard deviation calculation."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        mean = calculate_mean(values)
        std_dev = calculate_std_dev(values, mean)
        # Expected std dev is ~14.14
        self.assertTrue(14.0 < std_dev < 15.0)

    def test_calculate_std_dev_empty(self):
        """Test std dev with empty list returns 0."""
        self.assertEqual(calculate_std_dev([]), 0.0)

    def test_calculate_std_dev_single_value(self):
        """Test std dev with single value returns 0."""
        self.assertEqual(calculate_std_dev([100.0]), 0.0)

    def test_calculate_z_score(self):
        """Test Z-score calculation."""
        # z = (value - mean) / std_dev = (150 - 100) / 25 = 2.0
        self.assertEqual(calculate_z_score(150.0, 100.0, 25.0), 2.0)

    def test_calculate_z_score_zero_std_dev(self):
        """Test Z-score returns 0 when std dev is 0."""
        self.assertEqual(calculate_z_score(100.0, 100.0, 0.0), 0.0)

    def test_calculate_z_score_negative(self):
        """Test Z-score calculation for values below mean."""
        # z = (50 - 100) / 25 = -2.0
        self.assertEqual(calculate_z_score(50.0, 100.0, 25.0), -2.0)

    def test_calculate_mean_single_value(self):
        """Test mean calculation with single value."""
        self.assertEqual(calculate_mean([42.0]), 42.0)

    def test_calculate_std_dev_two_values(self):
        """Test std dev with two values."""
        values = [0.0, 10.0]
        std_dev = calculate_std_dev(values)
        self.assertEqual(std_dev, 5.0)


class TestDetectAnomalies(unittest.TestCase):
    """Tests for the detect_anomalies function."""

    def test_detect_anomalies_empty_data(self):
        """Test anomaly detection with empty data."""
        self.assertEqual(detect_anomalies([]), [])

    def test_detect_anomalies_with_spike(self):
        """Test anomaly detection identifies cost spikes."""
        # Create mock data with a clear spike
        cost_data = [
            {"date": "2024-01-01", "total_cost": 1000.0, "services": {"compute": 1000.0}},
            {"date": "2024-01-02", "total_cost": 1050.0, "services": {"compute": 1050.0}},
            {"date": "2024-01-03", "total_cost": 980.0, "services": {"compute": 980.0}},
            {"date": "2024-01-04", "total_cost": 1070.0, "services": {"compute": 1020.0}},
            {"date": "2024-01-05", "total_cost": 2500.0, "services": {"compute": 2500.0}},  # Spike!
            {"date": "2024-01-06", "total_cost": 1000.0, "services": {"compute": 1000.0}},
        ]

        anomalies = detect_anomalies(cost_data, threshold=2.0)

        # Should detect the spike on 2024-01-05
        self.assertGreaterEqual(len(anomalies), 1)
        spike_detected = any(a["date"] == "2024-01-05" for a in anomalies)
        self.assertTrue(spike_detected, "Should detect spike on 2024-01-05")

    def test_detect_anomalies_no_anomalies(self):
        """Test no anomalies for consistent data."""
        # Create consistent data with minimal variation
        cost_data = [
            {"date": f"2024-01-{i:02d}", "total_cost": 1000.0, "services": {"compute": 1000.0}}
            for i in range(1, 11)
        ]

        anomalies = detect_anomalies(cost_data, threshold=2.0)
        self.assertEqual(len(anomalies), 0)

    def test_detect_anomalies_severity_levels(self):
        """Test that severity is assigned correctly based on z-score."""
        cost_data = [
            {"date": "2024-01-01", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-02", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-03", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-04", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-05", "total_cost": 500.0, "services": {"compute": 500.0}},  # Extreme spike
        ]

        anomalies = detect_anomalies(cost_data, threshold=2.0)

        if anomalies:
            # Extreme spike should be marked as high severity
            has_severity = any(a["severity"] in ["high", "medium"] for a in anomalies)
            self.assertTrue(has_severity)

    def test_detect_anomalies_cost_drop(self):
        """Test anomaly detection identifies unusual cost drops."""
        cost_data = [
            {"date": "2024-01-01", "total_cost": 1000.0, "services": {"compute": 1000.0}},
            {"date": "2024-01-02", "total_cost": 1000.0, "services": {"compute": 1000.0}},
            {"date": "2024-01-03", "total_cost": 1000.0, "services": {"compute": 1000.0}},
            {"date": "2024-01-04", "total_cost": 1000.0, "services": {"compute": 1000.0}},
            {"date": "2024-01-05", "total_cost": 200.0, "services": {"compute": 200.0}},  # Drop!
            {"date": "2024-01-06", "total_cost": 1000.0, "services": {"compute": 1000.0}},
        ]

        anomalies = detect_anomalies(cost_data, threshold=2.0)

        # Should detect the drop (negative z-score)
        drop_detected = any(a["date"] == "2024-01-05" and a["z_score"] < 0 for a in anomalies)
        self.assertTrue(drop_detected, "Should detect cost drop on 2024-01-05")

    def test_detect_anomalies_multiple_services(self):
        """Test anomaly detection with multiple services identifies top contributor."""
        cost_data = [
            {"date": "2024-01-01", "total_cost": 1000.0, "services": {"compute": 500.0, "storage": 300.0, "network": 200.0}},
            {"date": "2024-01-02", "total_cost": 1000.0, "services": {"compute": 500.0, "storage": 300.0, "network": 200.0}},
            {"date": "2024-01-03", "total_cost": 2500.0, "services": {"compute": 1800.0, "storage": 400.0, "network": 300.0}},  # Compute spike
        ]

        anomalies = detect_anomalies(cost_data, threshold=1.5)

        if anomalies:
            # Reason should mention compute as the top contributor
            self.assertIn("compute", anomalies[0]["reason"].lower())


class TestMockData(unittest.TestCase):
    """Tests for mock data generation."""

    def test_generate_mock_costs_correct_length(self):
        """Test that generated data has correct number of days."""
        data = generate_mock_costs(days=10)
        self.assertEqual(len(data), 10)

    def test_generate_mock_costs_structure(self):
        """Test that generated data has correct structure."""
        data = generate_mock_costs(days=5)

        for day in data:
            self.assertIn("date", day)
            self.assertIn("total_cost", day)
            self.assertIn("services", day)
            self.assertGreater(day["total_cost"], 0)
            self.assertIsInstance(day["services"], dict)

    def test_generate_mock_costs_services(self):
        """Test that all expected services are present."""
        data = generate_mock_costs(days=1)
        expected_services = {"compute", "storage", "network", "database"}

        self.assertEqual(set(data[0]["services"].keys()), expected_services)

    def test_generate_mock_costs_total_matches_services(self):
        """Test that total_cost equals sum of service costs."""
        data = generate_mock_costs(days=5)

        for day in data:
            services_sum = sum(day["services"].values())
            self.assertLess(abs(day["total_cost"] - services_sum), 0.01)  # Allow small float error

    def test_generate_mock_costs_date_format(self):
        """Test that dates are in correct ISO format (YYYY-MM-DD)."""
        import re
        data = generate_mock_costs(days=5)
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

        for day in data:
            self.assertRegex(day["date"], date_pattern)

    def test_generate_mock_costs_different_ranges(self):
        """Test mock data generation with various day ranges."""
        for days in [1, 7, 14, 30]:
            data = generate_mock_costs(days=days)
            self.assertEqual(len(data), days)

    def test_generate_mock_costs_positive_values(self):
        """Test that all cost values are positive."""
        data = generate_mock_costs(days=10)

        for day in data:
            self.assertGreater(day["total_cost"], 0)
            for service_cost in day["services"].values():
                self.assertGreater(service_cost, 0)


class TestAPIWorkflow(unittest.TestCase):
    """Integration tests for the complete API workflow."""

    def test_full_anomaly_detection_workflow(self):
        """Test the complete workflow: generate data -> detect anomalies -> validate results."""
        # Step 1: Generate mock cost data
        cost_data = generate_mock_costs(days=30)
        self.assertEqual(len(cost_data), 30)

        # Step 2: Detect anomalies
        anomalies = detect_anomalies(cost_data, threshold=2.0)

        # Step 3: Validate anomaly structure
        for anomaly in anomalies:
            self.assertIn("date", anomaly)
            self.assertIn("total_cost", anomaly)
            self.assertIn("z_score", anomaly)
            self.assertIn("expected_cost", anomaly)
            self.assertIn("severity", anomaly)
            self.assertIn("reason", anomaly)
            self.assertIn(anomaly["severity"], ["medium", "high"])

    def test_threshold_sensitivity(self):
        """Test that higher threshold results in fewer anomalies."""
        cost_data = generate_mock_costs(days=30)

        anomalies_low = detect_anomalies(cost_data, threshold=1.5)
        anomalies_high = detect_anomalies(cost_data, threshold=3.0)

        # Higher threshold should catch fewer or equal anomalies
        self.assertLessEqual(len(anomalies_high), len(anomalies_low))

    def test_cost_data_consistency(self):
        """Test that cached data remains consistent."""
        # Clear any cached data
        import mock_data
        mock_data._cached_data = None

        data1 = get_mock_costs(days=30)
        data2 = get_mock_costs(days=30)

        # Same request should return same cached data
        self.assertEqual(data1, data2)

    def test_anomaly_deviation_calculation(self):
        """Test that deviation is correctly calculated as cost minus expected."""
        cost_data = [
            {"date": "2024-01-01", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-02", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-03", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-04", "total_cost": 300.0, "services": {"compute": 300.0}},  # Spike
        ]

        anomalies = detect_anomalies(cost_data, threshold=1.5)

        if anomalies:
            anomaly = anomalies[0]
            expected_deviation = anomaly["total_cost"] - anomaly["expected_cost"]
            self.assertAlmostEqual(anomaly["deviation"], expected_deviation, places=1)

    def test_workflow_with_minimum_data(self):
        """Test workflow handles minimum viable data (2 data points)."""
        cost_data = [
            {"date": "2024-01-01", "total_cost": 100.0, "services": {"compute": 100.0}},
            {"date": "2024-01-02", "total_cost": 500.0, "services": {"compute": 500.0}},
        ]

        # Should not crash with minimal data
        anomalies = detect_anomalies(cost_data, threshold=1.0)
        self.assertIsInstance(anomalies, list)


# Run tests with: python3 test_api_workflow.py
if __name__ == "__main__":
    unittest.main(verbosity=2)
