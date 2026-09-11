"""Provider settings without persisting API keys or other credentials."""

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "src/local.settings.json"
TEMPLATE = ROOT / "src/local.settings.template.json"
PROVIDERS = {
    "foundry": ("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL"),
    "azure_openai": ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"),
}
PUBLIC_KEYS = {"AZURE_FUNCTIONS_AGENTS_PROVIDER", "AZURE_OPENAI_API_VERSION"}
PUBLIC_KEYS.update(key for pair in PROVIDERS.values() for key in pair)


def read_values(path=SETTINGS):
    data = json.loads((path if path.exists() else TEMPLATE).read_text())
    values = data["Values"].copy()
    if values.get("AzureWebJobsStorage", "").strip().lower() == "usedevelopmentstorage=true":
        # Python Storage SDKs do not expand the Functions shorthand.
        values["AzureWebJobsStorage"] = json.loads(TEMPLATE.read_text())["Values"]["AzureWebJobsStorage"]
    # Codespaces environment takes precedence, consistent with our launch environment.
    for key in PUBLIC_KEYS:
        if os.environ.get(key, "").strip():
            values[key] = os.environ[key].strip()
    return values


def validate(values):
    provider = values.get("AZURE_FUNCTIONS_AGENTS_PROVIDER", "foundry")
    if provider not in PROVIDERS:
        raise ValueError("Provider must be foundry or azure_openai.")
    endpoint_key, model_key = PROVIDERS[provider]
    endpoint = values.get(endpoint_key, "")
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"Set a valid HTTPS {endpoint_key} using ./demo configure.")
    if provider == "foundry" and "/api/projects/" not in parsed.path:
        raise ValueError("Use the Foundry project endpoint containing /api/projects/<project>.")
    if not values.get(model_key, "").strip():
        raise ValueError(f"Set {model_key} to your existing model deployment name.")


def write_values(values, path=SETTINGS):
    # Only known, non-secret values are written. Credentials stay in az login / environment.
    allowed = set(json.loads(TEMPLATE.read_text())["Values"]) | PUBLIC_KEYS
    data = {"IsEncrypted": False, "Values": {k: v for k, v in values.items() if k in allowed}}
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
    path.chmod(0o600)


def load_environment():
    values = read_values()
    validate(values)
    os.environ.update({k: str(v) for k, v in values.items()})
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["init", "configure"])
    parser.add_argument("--provider", choices=list(PROVIDERS))
    parser.add_argument("--endpoint")
    parser.add_argument("--model")
    args = parser.parse_args()
    if args.action == "init":
        if not SETTINGS.exists():
            write_values(read_values())
        print("Local settings ready. Next: ./demo configure")
        return
    values = read_values()
    provider = args.provider or values.get("AZURE_FUNCTIONS_AGENTS_PROVIDER", "foundry")
    endpoint_key, model_key = PROVIDERS[provider]
    values["AZURE_FUNCTIONS_AGENTS_PROVIDER"] = provider
    for key, supplied in [(endpoint_key, args.endpoint), (model_key, args.model)]:
        current = values.get(key, "")
        values[key] = supplied if supplied is not None else (input(f"{key} [{current}]: ").strip() or current)
    validate(values)
    write_values(values)
    print(f"Saved {provider} configuration. Credentials were not written to disk.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, EOFError) as exc:
        raise SystemExit(str(exc)) from exc
