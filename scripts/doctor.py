"""Check prerequisites; does not make a model inference request."""

import importlib.metadata
import shutil
import subprocess
import sys

from settings import read_values, validate


def main():
    failures = []
    if sys.version_info < (3, 13):
        failures.append("Python 3.13+ is required.")
    for name in ["func", "docker", "az"]:
        if not shutil.which(name):
            failures.append(f"Missing command: {name}")
        else:
            print(f"OK command: {name}")
    for package in ["azurefunctions-agents-runtime", "azure-storage-queue", "azure-storage-blob"]:
        try:
            print(f"OK package: {package} {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            failures.append(f"Missing package: {package}; run ./demo setup")
    try:
        validate(read_values())
        print("OK provider settings (connectivity and access are checked by ./demo verify)")
    except ValueError as exc:
        failures.append(str(exc))
    for command in [["docker", "info"], ["docker", "compose", "version"]]:
        if shutil.which(command[0]):
            try:
                result = subprocess.run(command, capture_output=True, timeout=20)
                if result.returncode:
                    failures.append(f"Failed: {' '.join(command)}; confirm Docker is ready")
            except subprocess.TimeoutExpired:
                failures.append(f"Timed out: {' '.join(command)}")
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    print("Model authentication: use az login --use-device-code, or an Azure OpenAI Codespaces secret.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
