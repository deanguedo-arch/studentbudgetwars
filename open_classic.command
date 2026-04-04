#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

ensure_runtime() {
  local python_bin

  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    python_bin="$ROOT_DIR/.venv/bin/python"
  else
    for python_bin in "$(command -v python3 2>/dev/null || true)" "$(command -v python 2>/dev/null || true)"; do
      if [ -n "${python_bin:-}" ] && [ -x "$python_bin" ]; then
        "$python_bin" -m venv "$ROOT_DIR/.venv"
        python_bin="$ROOT_DIR/.venv/bin/python"
        break
      fi
    done
  fi

  if [ ! -x "$ROOT_DIR/.venv/bin/python" ]; then
    echo "Python was not found. Install Python or create a .venv first."
    exit 1
  fi

  python_bin="$ROOT_DIR/.venv/bin/python"
  if ! "$python_bin" - <<'PY' >/dev/null 2>&1; then
import pydantic  # noqa: F401
import eval_type_backport  # noqa: F401
PY
    echo "Bootstrapping Mac runtime dependencies..."
    "$python_bin" -m pip install --upgrade pip setuptools wheel
    "$python_bin" -m pip install pydantic eval-type-backport
  fi
}

ensure_runtime
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
echo "Launching After Grad Classic preview..."
exec "$ROOT_DIR/.venv/bin/python" -m budgetwars.main --mode classic --name PreviewPlayer "$@"
