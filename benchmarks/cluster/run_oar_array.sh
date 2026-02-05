#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

MANIFEST="${1:-${PROJECT_ROOT}/benchmarks/results/jobs/manifest.tsv}"
TIMEOUT="${TIMEOUT:-300}"
SUITE="${SUITE:-full}"
RESULTS_ROOT="${RESULTS_ROOT:-${PROJECT_ROOT}/benchmarks/results/jobs}"
TASK_ID="${OAR_ARRAY_INDEX:-${OAR_JOB_INDEX:-}}"

if [[ -z "${TASK_ID}" ]]; then
  echo "Error: OAR_ARRAY_INDEX (or OAR_JOB_INDEX) is not set."
  exit 1
fi

if [[ ! -f "${MANIFEST}" ]]; then
  echo "Error: manifest not found: ${MANIFEST}"
  exit 1
fi

LINE="$(sed -n "${TASK_ID}p" "${MANIFEST}")"
if [[ -z "${LINE}" ]]; then
  echo "Error: no manifest row for task ${TASK_ID}"
  exit 1
fi

IFS=$'\t' read -r MODEL INSTANCE REP_OFFSET <<< "${LINE}"
if [[ -z "${MODEL}" || -z "${INSTANCE}" || -z "${REP_OFFSET}" ]]; then
  echo "Error: invalid manifest row: ${LINE}"
  exit 1
fi

TASK_OUT="${RESULTS_ROOT}/oar_${OAR_JOB_ID:-unknown}_${TASK_ID}"
mkdir -p "${TASK_OUT}"

cd "${PROJECT_ROOT}"
echo "[OAR ${TASK_ID}] ${MODEL} / ${INSTANCE} (rep=${REP_OFFSET})"

uv run python benchmarks/runner.py \
  --suite="${SUITE}" \
  --model="${MODEL}" \
  --instance="${INSTANCE}" \
  --timeout="${TIMEOUT}" \
  --repetitions=1 \
  --repetition-offset="${REP_OFFSET}" \
  --output="${TASK_OUT}" \
  --no-report
