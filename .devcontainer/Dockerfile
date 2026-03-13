# Devcontainer: uv and just on PATH for cloud agents (Cursor, Codespaces, etc.)
# Matches CI tooling so agents can run CI-parity checks without bootstrapping.

FROM mcr.microsoft.com/devcontainers/python:3.11

# uv: copy from official image so it's on PATH for all users
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# just: official install script to /usr/local/bin (curl is in the base image)
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Verify both are on PATH
RUN uv --version && just --version
