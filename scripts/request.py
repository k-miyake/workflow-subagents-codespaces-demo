"""Submit a base64 queue message and optionally wait for a NEW report Blob."""

import argparse
import json
import re
import time
from pathlib import Path

from azure.core import MatchConditions
from azure.core.exceptions import ResourceExistsError, ResourceModifiedError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient, TextBase64EncodePolicy
from settings import ROOT, read_values
from verify_upstream import validate_report


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object.")
    for key in ["report_title", "report_blob"]:
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise ValueError(f"{key} must be a non-empty string.")
    if not request["report_blob"].endswith(".html"):
        raise ValueError("report_blob must end with .html.")
    prs = request.get("pull_requests")
    if not isinstance(prs, list) or not 1 <= len(prs) <= 10:
        raise ValueError("Use 1 to 10 pull requests for this demo.")
    seen = set()
    for pr in prs:
        url = pr.get("url", "") if isinstance(pr, dict) else ""
        if not isinstance(url, str) or not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+/pull/[1-9]\d*", url):
            raise ValueError("Each entry needs a canonical GitHub PR URL.")
        if url in seen:
            raise ValueError("Duplicate PR URLs are not allowed.")
        seen.add(url)
    if len(json.dumps(request).encode()) > 45000:
        raise ValueError("Request is too large for a base64 Storage Queue message.")


def wait_for_report(blob, request, previous_etag, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            properties = blob.get_blob_properties()
            etag = str(properties.etag)
            if etag != previous_etag:
                content = blob.download_blob(etag=etag, match_condition=MatchConditions.IfNotModified).readall()
                validate_report(content, request)
                return etag, content
        except (ResourceNotFoundError, ResourceModifiedError):
            pass
        time.sleep(2)
    raise RuntimeError("Timed out waiting for a new report. Inspect DTS (8082), the Functions log, and pr-status-requests-poison. The request may still be running.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=ROOT / "requests/demo.json")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    request = json.loads(args.file.read_text())
    validate_request(request)
    values = read_values()
    connection = values["AzureWebJobsStorage"]
    container = values["PR_STATUS_REPORT_CONTAINER"]
    with BlobServiceClient.from_connection_string(connection) as service:
        blob = service.get_blob_client(container, request["report_blob"])
        try:
            previous_etag = str(blob.get_blob_properties().etag)
        except ResourceNotFoundError:
            previous_etag = None
        with QueueClient.from_connection_string(connection, "pr-status-requests", message_encode_policy=TextBase64EncodePolicy()) as queue:
            try:
                queue.create_queue()
            except ResourceExistsError:
                pass
            message = queue.send_message(json.dumps(request, ensure_ascii=False))
        receipt = {"message_id": message.id, "report_blob": request["report_blob"], "previous_etag": previous_etag}
        state = ROOT / ".demo"
        state.mkdir(exist_ok=True)
        (state / "last-request.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"Submitted {len(request['pull_requests'])} synthetic PRs. Queue message: {message.id}", flush=True)
        if args.wait:
            print("Waiting for a NEW Blob version. Follow the workflow in DTS on port 8082.", flush=True)
            etag, content = wait_for_report(blob, request, previous_etag, args.timeout)
            report = state / "reports/report.html"
            report.parent.mkdir(exist_ok=True)
            report.write_bytes(content)
            receipt["etag"] = etag
            receipt["validated"] = True
            print(f"PASS: HTML and all PR URLs validated. ETag changed: {previous_etag} -> {etag}")
            print("Open http://localhost:8000/report.html (Ports tab: 8000).")
        (state / "last-request.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
