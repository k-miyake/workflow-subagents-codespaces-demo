import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import request
import settings
from _fake_pr_data import scenario_index
from azure.core.exceptions import ResourceNotFoundError
from verify_upstream import validate_report


@pytest.fixture
def payload():
    return json.loads((settings.ROOT / "requests/demo.json").read_text())


def test_demo_covers_all_three_scenarios(payload):
    request.validate_request(payload)
    assert {scenario_index(pr["url"]) for pr in payload["pull_requests"]} == {0, 1, 2}


@pytest.mark.parametrize("bad", [[], {}, {"report_title": "x", "report_blob": "x.html", "pull_requests": []}])
def test_invalid_request_is_rejected(bad):
    with pytest.raises(ValueError):
        request.validate_request(bad)


def test_duplicate_pr_is_rejected(payload):
    payload["pull_requests"].append(payload["pull_requests"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        request.validate_request(payload)


def test_oversized_queue_message_is_rejected(payload):
    payload["report_title"] = "あ" * 50000
    with pytest.raises(ValueError, match="too large"):
        request.validate_request(payload)


def test_credentials_never_written(tmp_path):
    values = json.loads(settings.TEMPLATE.read_text())["Values"]
    values.update(AZURE_OPENAI_API_KEY="test-secret", AZURE_CLIENT_SECRET="test-secret")
    path = tmp_path / "local.settings.json"
    settings.write_values(values, path)
    assert "test-secret" not in path.read_text()
    assert path.stat().st_mode & 0o777 == 0o600


def test_environment_overrides_saved_settings(monkeypatch):
    monkeypatch.setenv("FOUNDRY_MODEL", "my-deployment")
    assert settings.read_values()["FOUNDRY_MODEL"] == "my-deployment"


def test_rejects_resource_endpoint_instead_of_project():
    with pytest.raises(ValueError, match="/api/projects"):
        settings.validate({"AZURE_FUNCTIONS_AGENTS_PROVIDER": "foundry", "FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com", "FOUNDRY_MODEL": "test"})


def test_azure_openai_is_explicit():
    settings.validate({"AZURE_FUNCTIONS_AGENTS_PROVIDER": "azure_openai", "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com", "AZURE_OPENAI_DEPLOYMENT": "test"})


def test_old_report_does_not_count_as_new_success(payload, monkeypatch):
    blob = Mock()
    blob.get_blob_properties.side_effect = [ResourceNotFoundError("missing"), SimpleNamespace(etag="old"), SimpleNamespace(etag="new")]
    content = ("<html>" + " ".join(pr["url"] for pr in payload["pull_requests"]) + "</html>").encode()
    blob.download_blob.return_value.readall.return_value = content
    monkeypatch.setattr(request.time, "sleep", lambda _: None)
    etag, result = request.wait_for_report(blob, payload, "old", 10)
    assert etag == "new" and result == content
    assert blob.get_blob_properties.call_count == 3
    blob.download_blob.assert_called_once()
    assert blob.download_blob.call_args.kwargs["etag"] == "new"


def test_missing_pr_link_fails_report_validation(payload):
    with pytest.raises(RuntimeError, match="missing pull-request URL"):
        validate_report(b"<html>Missing PR links</html>", payload)


def test_incomplete_html_fails_report_validation(payload):
    with pytest.raises(RuntimeError, match="complete HTML"):
        validate_report(b"Still generating", payload)
