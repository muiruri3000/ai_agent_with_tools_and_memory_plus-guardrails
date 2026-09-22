import threading
import unittest
from http.client import HTTPConnection
from socket import socket
from time import sleep

from monitoring.metrics import Metrics
from monitoring.server import start_metrics_server


def get_free_port():
    with socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(host, port, attempts=20):
    for _ in range(attempts):
        try:
            connection = HTTPConnection(
                host,
                port,
                timeout=0.2,
            )
            connection.connect()
            connection.close()
            return
        except ConnectionRefusedError:
            sleep(0.05)

    raise RuntimeError(
        f"Metrics server did not become ready on {host}:{port}"
    )


class TestMetricsServer(unittest.TestCase):

    def start_test_server(self, metrics):
        port = get_free_port()

        thread = threading.Thread(
            target=start_metrics_server,
            args=(metrics, "127.0.0.1", port),
            daemon=True,
        )

        thread.start()

        wait_for_server(
            "127.0.0.1",
            port,
        )

        return port

    def test_metrics_endpoint(self):
        metrics = Metrics()
        metrics.increment("agent_requests", 3)

        port = self.start_test_server(metrics)

        connection = HTTPConnection(
            "127.0.0.1",
            port,
            timeout=2,
        )

        connection.request("GET", "/metrics")

        response = connection.getresponse()
        body = response.read().decode("utf-8")

        connection.close()

        self.assertEqual(response.status, 200)

        self.assertIn(
            "atlas_agent_requests_total",
            body,
        )

        self.assertIn(
            "atlas_agent_requests_total 3.0",
            body,
        )

    def test_unknown_endpoint_returns_404(self):
        metrics = Metrics()

        port = self.start_test_server(metrics)

        connection = HTTPConnection(
            "127.0.0.1",
            port,
            timeout=2,
        )

        connection.request("GET", "/unknown")

        response = connection.getresponse()
        response.read()

        connection.close()

        self.assertEqual(response.status, 404)


if __name__ == "__main__":
    unittest.main()
