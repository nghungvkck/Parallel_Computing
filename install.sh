#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo 'Cách dùng: bash install.sh [--cpu-only]'
    echo 'Mặc định: cài C++, MPI và CUDA 12.8 trên Ubuntu WSL2 x86_64.'
    echo '--cpu-only: chỉ cài C++ và MPI trên Ubuntu.'
}

cpu_only=false
case "${1:-}" in
    '') ;;
    --cpu-only) cpu_only=true ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 1 ;;
esac
if (( $# > 1 )); then usage >&2; exit 1; fi

if [[ ! -r /etc/os-release ]]; then
    echo 'Script này cần Ubuntu.' >&2
    exit 1
fi
source /etc/os-release
if [[ ${ID:-} != ubuntu ]]; then
    echo 'Script này chỉ hỗ trợ Ubuntu.' >&2
    exit 1
fi
if ! "$cpu_only"; then
    kernel=$(uname -r)
    if [[ ${kernel,,} != *microsoft* || $(uname -m) != x86_64 ]]; then
        echo 'Cài CUDA tự động chỉ hỗ trợ Ubuntu WSL2 x86_64. Dùng --cpu-only để cài C++/MPI.' >&2
        exit 1
    fi
fi

admin=()
if (( EUID != 0 )); then
    if ! command -v sudo >/dev/null; then
        echo 'Cần sudo hoặc chạy bằng tài khoản root.' >&2
        exit 1
    fi
    admin=(sudo)
    sudo -v
fi

echo 'Đang cài trình biên dịch C++ và Open MPI...'
"${admin[@]}" apt-get update
"${admin[@]}" apt-get install -y build-essential openmpi-bin libopenmpi-dev

if ! "$cpu_only"; then
    echo 'Đang cài CUDA Toolkit 12.8 và g++-13 (tương thích nvcc)...'
    echo 'CUDA có thể tải vài GB. Driver NVIDIA trên Windows cần được cài sẵn.'
    "${admin[@]}" apt-get install -y ca-certificates curl g++-13
    # Keep CUDA 12.x for the project's Pascal GPU; never install Linux GPU drivers in WSL.
    # Repository: https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/
    task_tmp=$(mktemp -d)
    trap 'rm -rf -- "$task_tmp"' EXIT
    curl --fail --show-error --location --retry 3 \
        https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb \
        --output "$task_tmp/cuda-keyring.deb"
    "${admin[@]}" dpkg -i "$task_tmp/cuda-keyring.deb"
    "${admin[@]}" apt-get update
    "${admin[@]}" apt-get install -y cuda-toolkit-12-8
    /usr/local/cuda-12.8/bin/nvcc --version
fi

g++ --version
mpirun --version
echo 'Cài xong. Xem lệnh biên dịch/chạy trong readme.md.'
if ! "$cpu_only"; then
    echo 'Để dùng nvcc trong terminal hiện tại, chạy:'
    echo 'export PATH=/usr/local/cuda-12.8/bin:$PATH'
fi
