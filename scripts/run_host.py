"""Run Functions and a report-only HTTP server; Ctrl+C stops both children."""

import functools
import signal
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from azure.core.exceptions import ResourceExistsError
from azure.storage.queue import QueueClient
from settings import ROOT, load_environment
from verify_upstream import _wait_for_port


class ReportHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Generated HTML must stay self-contained, even if a model ignores instructions.
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; sandbox allow-popups")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def main():
    values = load_environment()
    for port in [10000, 10001, 10002, 8080, 8082]:
        _wait_for_port(port, timeout=60)
    with QueueClient.from_connection_string(values["AzureWebJobsStorage"], "pr-status-requests") as queue:
        try:
            queue.create_queue()
        except ResourceExistsError:
            pass
    reports = ROOT / ".demo/reports"
    reports.mkdir(parents=True, exist_ok=True)
    index = reports / "index.html"
    if not index.exists():
        index.write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>PR report demo</title><body><h1>PR report demo</h1><p>まだレポートはありません。別ターミナルで <code>./demo submit --wait</code> を実行してください。</p><p>PR データは模擬データです。モデルは実際に呼び出します。</p><a href="report.html">生成済みレポートを開く</a></body></html>')
    server = ThreadingHTTPServer(("0.0.0.0", 8000), functools.partial(ReportHandler, directory=str(reports)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    process = subprocess.Popen(["func", "start", "--port", "7071"], cwd=ROOT / "src", start_new_session=True)

    def shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, shutdown)
    print("DTS dashboard: http://localhost:8082", flush=True)
    print("Generated report: http://localhost:8000/report.html", flush=True)
    print("Wait for the Functions trigger to be indexed, then run ./demo submit --wait in another terminal.", flush=True)
    try:
        while process.poll() is None:
            time.sleep(0.5)
        return process.returncode
    except KeyboardInterrupt:
        return 0
    finally:
        import os
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        server.shutdown()
        server.server_close()
        print("Functions and report server stopped. ./demo stop stops the emulators.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
