#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM="${ROOT_DIR}/scripts/terraform.sh"
DESTROY_PLAN="${ROOT_DIR}/infra/supportops-destroy.tfplan"
DB_INSTANCE_ID="${DB_INSTANCE_ID:-supportops-dev-postgres}"
CONFIRMATION="${CONFIRM_DESTROY:-}"
CREATE_SNAPSHOT="${CREATE_SNAPSHOT:-true}"

if [[ "$CONFIRMATION" != "I_UNDERSTAND_DATA_WILL_BE_DELETED" ]]; then
  echo "Refusing to destroy." >&2
  echo "Set CONFIRM_DESTROY=I_UNDERSTAND_DATA_WILL_BE_DELETED to continue." >&2
  exit 2
fi

if [[ "$CREATE_SNAPSHOT" == "true" ]]; then
  if aws rds describe-db-instances     --db-instance-identifier "$DB_INSTANCE_ID"     --region "${AWS_REGION:-eu-west-2}" >/dev/null 2>&1; then
    SNAPSHOT_ID="${SNAPSHOT_ID:-${DB_INSTANCE_ID}-pre-destroy-$(date -u +%Y%m%d%H%M%S)}"
    echo "Creating RDS snapshot: $SNAPSHOT_ID"
    aws rds create-db-snapshot       --db-instance-identifier "$DB_INSTANCE_ID"       --db-snapshot-identifier "$SNAPSHOT_ID"       --region "${AWS_REGION:-eu-west-2}" >/dev/null
    aws rds wait db-snapshot-available       --db-snapshot-identifier "$SNAPSHOT_ID"       --region "${AWS_REGION:-eu-west-2}"
    echo "RDS snapshot is available: $SNAPSHOT_ID"
  else
    echo "RDS instance not found; continuing without a snapshot."
  fi
elif [[ "$CREATE_SNAPSHOT" != "false" ]]; then
  echo "CREATE_SNAPSHOT must be true or false." >&2
  exit 2
fi

cd "${ROOT_DIR}/infra"
"$TERRAFORM" init -input=false
"$TERRAFORM" plan -destroy -input=false -out="$DESTROY_PLAN"
echo "Review the destroy plan above."
"$TERRAFORM" apply "$DESTROY_PLAN"
