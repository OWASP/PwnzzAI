#!/bin/bash
set -e

OS_NAME="$(uname -s)"

if ! command -v python >/dev/null 2>&1; then
  echo "Python is required but was not found in PATH." >&2
  exit 1
fi

if [[ "$OS_NAME" == "Linux" ]]; then
  if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y libzbar0 zstd
  else
    echo "Package manager not supported automatically. Install libzbar manually before continuing." >&2
  fi
elif [[ "$OS_NAME" == "Darwin" ]]; then
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required to install zbar and zstd on macOS. Install it from https://brew.sh and rerun." >&2
    exit 1
  fi
  brew install zbar zstd
else 
  echo "Unsupported OS (${OS_NAME}). Install zbar and zstd manually before continuing." >&2
fi
# ... existing code ...
curl -fsSL https://ollama.com/install.sh | sh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt