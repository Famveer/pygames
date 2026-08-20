#!/usr/bin/env bash
# Re-renders every Lectures/*/slides/teoria*.qmd deck to revealjs HTML.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail=0
count=0

while IFS= read -r -d '' qmd; do
  echo "==> Rendering ${qmd#"$REPO_ROOT"/}"
  # --execute-daemon 0: force a fresh Jupyter kernel per deck. Rendering many
  # decks back-to-back with the daemon's default kernel reuse (300s keepalive)
  # has been observed to make an unrelated later deck fail intermittently.
  if quarto render "$qmd" --to revealjs --execute-daemon 0; then
    count=$((count + 1))
  else
    echo "!! FAILED: $qmd" >&2
    fail=1
  fi
done < <(find "$REPO_ROOT/Lectures" -type f -name "teoria*.qmd" -print0 | sort -z)

echo
echo "Rendered $count deck(s)."
if [ "$fail" -ne 0 ]; then
  echo "One or more renders failed — see !! FAILED lines above." >&2
  exit 1
fi
