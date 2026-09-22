from prometheus_client import (
    CollectorRegistry,
    generate_latest,
)

from prometheus_client.core import (
    CounterMetricFamily,
    GaugeMetricFamily,
)


class AtlasMetricsCollector:
    """
    Prometheus collector that exposes Atlas Metrics snapshots.

    The existing Metrics class remains the source of truth.
    This collector only translates those metrics into
    Prometheus exposition format.
    """

    def __init__(self, metrics):
        self.metrics = metrics

    def collect(self):
        snapshot = self.metrics.snapshot()

        yield GaugeMetricFamily(
            "atlas_uptime_seconds",
            "Time Atlas has been running in seconds.",
            value=snapshot["uptime_seconds"],
        )

        counters = snapshot["counters"]

        for metric_name, value in counters.items():
            yield CounterMetricFamily(
                f"atlas_{metric_name}_total",
                f"Total number of Atlas {metric_name} events.",
                value=value,
            )

        tools = snapshot["tools"]

        tool_calls = CounterMetricFamily(
            "atlas_tool_calls_total",
            "Total number of tool executions.",
            labels=["tool"],
        )

        tool_successes = CounterMetricFamily(
            "atlas_tool_successes_total",
            "Total number of successful tool executions.",
            labels=["tool"],
        )

        tool_failures = CounterMetricFamily(
            "atlas_tool_failures_total",
            "Total number of failed tool executions.",
            labels=["tool"],
        )

        tool_duration_total = CounterMetricFamily(
            "atlas_tool_duration_seconds_total",
            "Total execution time spent in each tool.",
            labels=["tool"],
        )

        tool_duration_average = GaugeMetricFamily(
            "atlas_tool_duration_seconds_average",
            "Average execution time of each tool.",
            labels=["tool"],
        )

        for tool, data in tools.items():
            calls = data["calls"]
            successes = data["successes"]
            failures = data["failures"]
            average_duration = data["average_duration_seconds"]

            duration_total = (
                average_duration * calls
            )

            tool_calls.add_metric(
                [tool],
                calls,
            )

            tool_successes.add_metric(
                [tool],
                successes,
            )

            tool_failures.add_metric(
                [tool],
                failures,
            )

            tool_duration_total.add_metric(
                [tool],
                duration_total,
            )

            tool_duration_average.add_metric(
                [tool],
                average_duration,
            )

        yield tool_calls
        yield tool_successes
        yield tool_failures
        yield tool_duration_total
        yield tool_duration_average


def create_registry(metrics):
    """
    Create an isolated Prometheus registry containing
    Atlas metrics only.
    """
    registry = CollectorRegistry()

    registry.register(
        AtlasMetricsCollector(metrics)
    )

    return registry


def generate_metrics(metrics):
    """
    Generate Prometheus exposition text for Atlas metrics.
    """
    registry = create_registry(metrics)

    return generate_latest(registry)
