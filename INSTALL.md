# Hướng dẫn cài đặt

[README chính](readme.md) · [Hướng dẫn chạy](RUN.md)

## Cài C++, MPI và CUDA

Sau khi clone, mở terminal tại thư mục dự án trên Ubuntu WSL2 x86_64:

```bash
# Tự cài C++, MPI và CUDA 12.8 (cần mạng, mật khẩu sudo và vài GB dung lượng)
bash install.sh
export PATH=/usr/local/cuda-12.8/bin:$PATH

# Nếu chỉ cần bản tuần tự và MPI:
# bash install.sh --cpu-only
```

CUDA cần GPU NVIDIA và driver cài sẵn trên Windows. Danh sách công cụ nằm trong [requirement.txt](requirement.txt).

## Công cụ đo thời gian và vẽ biểu đồ

Script benchmark cần Python 3 và Matplotlib. Cài trên Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-matplotlib
```

## Biên dịch

Chạy tại thư mục gốc dự án:

```bash
g++ -O2 -std=c++17 src/Serial.cpp -o serial
mpic++ -O2 -std=c++17 src/MPI.cpp -o mpi
nvcc -O2 -std=c++17 -ccbin g++-13 -arch=sm_61 src/CUDA.cu -o cuda
```

Cờ `sm_61` dành cho Quadro P3200 với CUDA Toolkit 12.x. Biên dịch lại bản tương ứng sau khi sửa mã nguồn.

Xem [hướng dẫn chạy](RUN.md) để chạy từng bản và đo toàn bộ đồ thị thưa/dày.
