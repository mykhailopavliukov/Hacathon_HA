#!/bin/sh
# Enable the shared git hooks in .githooks/ for this clone.
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
chmod +x .githooks/* 2>/dev/null || true
echo "Git hooks enabled (core.hooksPath=.githooks)."
