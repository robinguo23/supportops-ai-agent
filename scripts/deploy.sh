#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM="${ROOT_DIR}/scripts/terraform.sh"
PLAN_FILE="${ROOT_DIR}/infra/supportops.tfplan"
MODE="${1:-plan}"

cd "${ROOT_DIR}/infra"

case "$MODE" in
  plan)
    "$TERRAFORM" init -input=false
    "$TERRAFORM" fmt -check -recursive
    "$TERRAFORM" validate -no-color
    "$TERRAFORM" plan -input=false -out="$PLAN_FILE"
    echo "Plan saved to $PLAN_FILE"
    ;;
  apply)
    if [[ ! -f "$PLAN_FILE" ]]; then
      echo "No saved plan found. Run: bash scripts/deploy.sh plan" >&2
      exit 1
    fi
    "$TERRAFORM" apply "$PLAN_FILE"
    ;;
  up)
    "$TERRAFORM" init -input=false
    "$TERRAFORM" fmt -check -recursive
    "$TERRAFORM" validate -no-color
    "$TERRAFORM" plan -input=false -out="$PLAN_FILE"
    "$TERRAFORM" apply "$PLAN_FILE"
    ;;
  *)
    echo "Usage: bash scripts/deploy.sh [plan|apply|up]" >&2
    exit 2
    ;;
esac
