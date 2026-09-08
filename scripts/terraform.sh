#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TF_VERSION="${TF_VERSION:-1.9.8}"

if command -v terraform >/dev/null 2>&1; then
  exec terraform "$@"
fi

TF_BIN_DIR="${ROOT_DIR}/.terraform-bin"
TF_BINARY="${TF_BIN_DIR}/terraform"

if [[ ! -x "$TF_BINARY" ]]; then
  case "$(uname -m)" in
    x86_64) TF_ARCH="amd64" ;;
    aarch64|arm64) TF_ARCH="arm64" ;;
    *)
      echo "Unsupported architecture: $(uname -m)" >&2
      exit 1
      ;;
  esac

  command -v curl >/dev/null 2>&1 || {
    echo "curl is required to bootstrap Terraform." >&2
    exit 1
  }
  command -v unzip >/dev/null 2>&1 || {
    echo "unzip is required to bootstrap Terraform." >&2
    exit 1
  }

  mkdir -p "$TF_BIN_DIR"
  archive="/tmp/terraform-${TF_VERSION}-${TF_ARCH}.zip"

  curl --fail --silent --show-error --location     --output "$archive"     "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_${TF_ARCH}.zip"

  unzip -o "$archive" terraform -d "$TF_BIN_DIR" >/dev/null
fi

exec "$TF_BINARY" "$@"
