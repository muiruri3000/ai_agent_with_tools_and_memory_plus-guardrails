from http.server import BaseHTTPRequestHandler, HTTPServer

from monitoring.exporter import generate_metrics


class MetricsHandler(BaseHTTPRequestHandler):

    metrics = None

    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        output = generate_metrics(self.metrics)

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; version=0.0.4; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(output)),
        )
        self.end_headers()

        self.wfile.write(output)

    def log_message(self, format, *args):
        return


def start_metrics_server(
    metrics,
    host="127.0.0.1",
    port=8000,
):
    MetricsHandler.metrics = metrics

    server = HTTPServer(
        (host, port),
        MetricsHandler,
    )

    print(
        f"📊 Metrics server listening on "
        f"http://{host}:{port}/metrics"
    )

    server.serve_forever()
