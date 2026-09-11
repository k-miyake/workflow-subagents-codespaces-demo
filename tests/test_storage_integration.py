"""Opt-in local Azurite check; test HTML is a fixture, never a model result."""

import json
import os
import uuid

import pytest
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient, TextBase64DecodePolicy, TextBase64EncodePolicy
from report_publisher import publish_pr_status_report
from settings import ROOT, TEMPLATE
from verify_upstream import validate_report


@pytest.mark.skipif(os.environ.get("RUN_AZURITE_TEST") != "1", reason="Requires running local Azurite")
def test_queue_encoding_and_blob_overwrite(monkeypatch):
    connection = json.loads(TEMPLATE.read_text())["Values"]["AzureWebJobsStorage"]
    name = "demo-test-" + uuid.uuid4().hex[:12]
    payload = json.loads((ROOT / "requests/demo.json").read_text())
    monkeypatch.setenv("AzureWebJobsStorage", connection)
    monkeypatch.setenv("PR_STATUS_REPORT_CONTAINER", name)
    queue = QueueClient.from_connection_string(connection, name, message_encode_policy=TextBase64EncodePolicy(), message_decode_policy=TextBase64DecodePolicy())
    service = BlobServiceClient.from_connection_string(connection)
    container = service.get_container_client(name)
    queue.create_queue()
    container.create_container()
    try:
        queue.send_message(json.dumps(payload, ensure_ascii=False))
        message = next(iter(queue.receive_messages()))
        assert json.loads(message.content) == payload
        queue.delete_message(message)
        links = "".join(f'<a href="{pr["url"]}">fixture</a>' for pr in payload["pull_requests"])
        html = f"<!doctype html><html><body>TEST FIXTURE — NOT MODEL OUTPUT {links}</body></html>"
        args = {"html": html, "blob_name": payload["report_blob"]}
        result = publish_pr_status_report(args)
        assert result["blob_name"] == payload["report_blob"]
        blob = container.get_blob_client(payload["report_blob"])
        first_etag = blob.get_blob_properties().etag
        validate_report(blob.download_blob().readall(), payload)
        publish_pr_status_report(args)
        assert blob.get_blob_properties().etag != first_etag
        assert [b.name for b in container.list_blobs()] == [payload["report_blob"]]
        assert blob.get_blob_properties().content_settings.content_type == "text/html; charset=utf-8"
    finally:
        queue.delete_queue()
        container.delete_container()
        queue.close()
        service.close()
