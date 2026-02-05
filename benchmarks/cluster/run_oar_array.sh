#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DEFAULT_RESULTS_ROOT="${PROJECT_ROOT}/benchmarks/results/jobs"
TASK_ID="${OAR_ARRAY_INDEX:-${OAR_JOB_INDEX:-}}"

MODEL=""
INSTANCE=""
REP_OFFSET=""
TIMEOUT="${TIMEOUT:-300}"
SUITE="${SUITE:-full}"
RESULTS_ROOT="${RESULTS_ROOT:-${DEFAULT_RESULTS_ROOT}}"

# Mode A: manifest file provided as $1 (use array index to select a row).
if [[ -n "${1:-}" && -f "${1}" ]]; then
  MANIFEST="${1}"
  TIMEOUT="${2:-${TIMEOUT}}"
  SUITE="${3:-${SUITE}}"
  RESULTS_ROOT="${4:-${RESULTS_ROOT}}"

  if [[ -z "${TASK_ID}" ]]; then
    echo "Error: OAR_ARRAY_INDEX (or OAR_JOB_INDEX) is not set."
    exit 1
  fi

  LINE="$(sed -n "${TASK_ID}p" "${MANIFEST}")"
  if [[ -z "${LINE}" ]]; then
    echo "Error: no manifest row for task ${TASK_ID}"
    exit 1
  fi

  IFS=$'\t' read -r MODEL INSTANCE REP_OFFSET <<< "${LINE}"

# Mode B: array-param-file passes (model, instance, rep_offset, [timeout], [suite], [results_root]).
else
  MODEL="${1:-}"
  INSTANCE="${2:-}"
  REP_OFFSET="${3:-}"
  TIMEOUT="${4:-${TIMEOUT}}"
  SUITE="${5:-${SUITE}}"
  RESULTS_ROOT="${6:-${RESULTS_ROOT}}"
fi

if [[ -z "${MODEL}" || -z "${INSTANCE}" || -z "${REP_OFFSET}" ]]; then
  echo "Error: missing model/instance/rep_offset parameters."
  exit 1
fi

TASK_OUT="${RESULTS_ROOT}/oar_${OAR_JOB_ID:-unknown}_${TASK_ID:-param}"
mkdir -p "${TASK_OUT}"

cd "${PROJECT_ROOT}"
echo "[OAR ${TASK_ID:-param}] ${MODEL} / ${INSTANCE} (rep=${REP_OFFSET})"

uv run python benchmarks/runner.py \
  --suite="${SUITE}" \
  --model="${MODEL}" \
  --instance="${INSTANCE}" \
  --timeout="${TIMEOUT}" \
  --repetitions=1 \
  --repetition-offset="${REP_OFFSET}" \
  --output="${TASK_OUT}" \
  --no-report
