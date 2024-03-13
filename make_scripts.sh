#!/bin/bash
LINT_JOBS=4

function lint_code {
  set -ex
	flake8 --jobs $LINT_JOBS --statistics --show-source "$@"
	pylint --jobs $LINT_JOBS --rcfile=pyproject.toml "$@"
	mypy "$@"
	black --check "$@"
	ruff "$@" --show-source --show-fixes -n || true
	pytest --dead-fixtures --dup-fixtures "$@"
	set +ex
}

function format_code {
  set -e
	autoflake --recursive --in-place --remove-all-unused-imports "$@"
	isort "$@"
	black  "$@"
	unify --in-place --recursive "$@"
	set +e
}

function test_code {
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR
  pytest --verbosity=2 --showlocals --strict-markers "$@" --cov
}
