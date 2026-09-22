import unittest

from prometheus_client.parser import text_string_to_metric_families

from monitoring.exporter import generate_metrics
from monitoring.metrics import Metrics


class TestAtlasMetricsExporter(unittest.TestCase):

    def test_empty_metrics_export(self):
        metrics = Metrics()

        output = generate_metrics(metrics)

        self.assertIn(
            "atlas_uptime_seconds",
            output.decode("utf-8"),
        )

    def test_counter_is_exported(self):
        metrics = Metrics()

        metrics.increment(
            "agent_requests",
            3,
        )

        output = generate_metrics(metrics).decode(
            "utf-8"
        )

        self.assertIn(
            "atlas_agent_requests_total",
            output,
        )

        self.assertIn(
            "atlas_agent_requests_total 3.0",
            output,
        )

    def test_tool_metrics_are_exported(self):
        metrics = Metrics()

        metrics.record_tool_execution(
            "get_customers",
            success=True,
            duration_seconds=0.25,
        )

        metrics.record_tool_execution(
            "get_customers",
            success=False,
            duration_seconds=0.50,
        )

        output = generate_metrics(metrics).decode(
            "utf-8"
        )

        self.assertIn(
            'atlas_tool_calls_total{tool="get_customers"} 2.0',
            output,
        )

        self.assertIn(
            'atlas_tool_successes_total{tool="get_customers"} 1.0',
            output,
        )

        self.assertIn(
            'atlas_tool_failures_total{tool="get_customers"} 1.0',
            output,
        )

        self.assertIn(
            'atlas_tool_duration_seconds_average{tool="get_customers"} 0.375',
            output,
        )

    def test_export_is_valid_prometheus_format(self):
        metrics = Metrics()

        metrics.increment(
            "agent_requests",
            5,
        )

        metrics.record_tool_execution(
            "web_search",
            success=True,
            duration_seconds=1.2,
        )

        output = generate_metrics(metrics).decode(
            "utf-8"
        )

        families = list(
            text_string_to_metric_families(output)
        )

        metric_names = {
            family.name
            for family in families
        }

        self.assertIn(
            "atlas_uptime_seconds",
            metric_names,
        )

        self.assertIn(
            "atlas_agent_requests",
            metric_names,
        )

        self.assertIn(
            "atlas_tool_calls",
            metric_names,
        )


if __name__ == "__main__":
    unittest.main()
