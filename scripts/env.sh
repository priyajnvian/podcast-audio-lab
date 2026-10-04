# Source this from the repo root before any pip install or model run:
#   source scripts/env.sh
# Keeps every download and cache (model weights, pip, torch hub) inside the repo's
# .cache/, so nothing lands in your home folder.
# The root is taken from the working directory on purpose: deriving it from
# BASH_SOURCE silently breaks under zsh, where it's empty. In the original lab
# that resolved to the parent folder and leaked 1.3 GB of caches there.
if [ ! -f "$(pwd)/scripts/env.sh" ]; then
  echo "env.sh: run from the repo root (currently in $(pwd))" >&2
  return 1 2>/dev/null || exit 1
fi
LAB="$(pwd)"
export PIP_CACHE_DIR="$LAB/.cache/pip"
export HF_HOME="$LAB/.cache/huggingface"
export TORCH_HOME="$LAB/.cache/torch"
export XDG_CACHE_HOME="$LAB/.cache"
export MPLCONFIGDIR="$LAB/.cache/matplotlib"
export NUMBA_CACHE_DIR="$LAB/.cache/numba"
export TMPDIR="$LAB/.cache/tmp"
mkdir -p "$TMPDIR"
