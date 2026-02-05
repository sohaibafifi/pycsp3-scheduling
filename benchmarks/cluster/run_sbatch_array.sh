#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

MANIFEST="${1:-${PROJECT_ROOT}/benchmarks/results/jobs/manifest.tsv}"
TIMEOUT="${TIMEOUT:-300}"
SUITE="${SUITE:-full}"
RESULTS_ROOT="${RESULTS_ROOT:-${PROJECT_ROOT}/benchmarks/results/jobs}"

if [[ -z "${SLURM_ARRAY_TASK_ID:-}" ]]; then
  echo "Error: SLURM_ARRAY_TASK_ID is not set."
  exit 1
fi

if [[ ! -f "${MANIFEST}" ]]; then
  echo "Error: manifest not found: ${MANIFEST}"
  exit 1
fi

LINE="$(sed -n "${SLURM_ARRAY_TASK_ID}p" "${MANIFEST}")"
if [[ -z "${LINE}" ]]; then
  echo "Error: no manifest row for task ${SLURM_ARRAY_TASK_ID}"
  exit 1
fi

IFS=$'\t' read -r MODEL INSTANCE REP_OFFSET <<< "${LINE}"
if [[ -z "${MODEL}" || -z "${INSTANCE}" || -z "${REP_OFFSET}" ]]; then
  echo "Error: invalid manifest row: ${LINE}"
  exit 1
fi

TASK_OUT="${RESULTS_ROOT}/slurm_${SLURM_ARRAY_JOB_ID:-unknown}_${SLURM_ARRAY_TASK_ID}"
mkdir -p "${TASK_OUT}"

cd "${PROJECT_ROOT}"
echo "[SLURM ${SLURM_ARRAY_TASK_ID}] ${MODEL} / ${INSTANCE} (rep=${REP_OFFSET})"

uv run python benchmarks/runner.py \
  --suite="${SUITE}" \
  --model="${MODEL}" \
  --instance="${INSTANCE}" \
  --timeout="${TIMEOUT}" \
  --repetitions=1 \
  --repetition-offset="${REP_OFFSET}" \
  --output="${TASK_OUT}" \
  --no-report
