#!/bin/sh
# Ensure the output directory is writable (handles bind-mounted volumes
# whose host permissions may not match the container user).
mkdir -p /app/output
chown -R appuser:appuser /app/output 2>/dev/null || true

exec gosu appuser "$@"
