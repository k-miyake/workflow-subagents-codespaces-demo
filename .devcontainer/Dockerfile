# Python 1-3.13-bookworm. Digest-only syntax also works with the Codespaces CLI.
FROM mcr.microsoft.com/devcontainers/python@sha256:0aa711e570b306c02946cdda67587ce8c65978dbb65691341cbcfd4854dfcfff

# Microsoft package feed; Core Tools v4 (Python 3.13 support).
# The pinned base includes an unused Yarn apt feed with an expired/missing key.
# Remove that feed; keep signature verification for every feed we actually use.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -o /tmp/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends azure-functions-core-tools-4 \
    && rm -rf /var/lib/apt/lists/*
