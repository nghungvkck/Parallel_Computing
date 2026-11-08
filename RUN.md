# Hướng dẫn biên dịch và chạy

Chạy các lệnh tại thư mục gốc dự án.

## Chuẩn bị dữ liệu

```bash
python3 scripts/generate_benchmarks.py
```

Các lệnh benchmark tự chạy cả test mới, tối đa 20.000 đỉnh. Chi tiết dữ liệu xem [data/README.md](data/README.md).

## Serial

### Biên dịch

```bash
g++ -O2 -std=c++17 src/Serial.cpp -o serial
```

### Chạy một đồ thị

```bash
./serial data/sparse_10000_30000.txt 0
./serial data/dense_3000_4498500.txt 0
```

### Đo và vẽ biểu đồ đồ thị thưa

```bash
python3 scripts/benchmark_sparse.py --implementation serial --kind sparse
```

### Đo và vẽ biểu đồ đồ thị dày

```bash
python3 scripts/benchmark_sparse.py --implementation serial --kind dense
```

## MPI

### Biên dịch

```bash
mpic++ -O2 -std=c++17 src/MPI.cpp -o mpi
```

### Chạy một đồ thị với 4 tiến trình

```bash
mpirun --oversubscribe -np 4 ./mpi data/sparse_10000_30000.txt 0
mpirun --oversubscribe -np 4 ./mpi data/dense_3000_4498500.txt 0
```

### Đo và vẽ biểu đồ đồ thị thưa

```bash
python3 scripts/benchmark_sparse.py --implementation mpi --kind sparse --processes 1 2 4 8 12
```

### Đo và vẽ biểu đồ đồ thị dày

```bash
python3 scripts/benchmark_sparse.py --implementation mpi --kind dense --processes 1 2 4 8 12
```

### Chạy MPI với 1, 2, 4, 8 và 12 tiến trình

```bash
for p in 1 2 4 8 12; do
    mpirun --oversubscribe -np "$p" ./mpi data/sparse_10000_30000.txt 0
done

for p in 1 2 4 8 12; do
    mpirun --oversubscribe -np "$p" ./mpi data/dense_3000_4498500.txt 0
done
```

### Đo và vẽ biểu đồ toàn bộ đồ thị với 1, 2, 4, 8 và 12 tiến trình

```bash
python3 scripts/benchmark_sparse.py --implementation mpi --kind sparse --processes 1 2 4 8 12
python3 scripts/benchmark_sparse.py --implementation mpi --kind dense --processes 1 2 4 8 12
```

### Kiểm tra CPU WSL và chạy theo số CPU khả dụng

```bash
nproc
lscpu
mpirun --oversubscribe -np "$(nproc)" ./mpi data/sparse_10000_30000.txt 0
```

## CUDA

### Biên dịch

```bash
nvcc -O2 -std=c++17 -ccbin g++-13 -arch=sm_61 src/CUDA.cu -o cuda
```

### Chạy một đồ thị

```bash
./cuda data/sparse_10000_30000.txt 0
./cuda data/dense_3000_4498500.txt 0
```

### Đo và vẽ biểu đồ đồ thị thưa

```bash
python3 scripts/benchmark_sparse.py --implementation cuda --kind sparse
```

### Đo và vẽ biểu đồ đồ thị dày

```bash
python3 scripts/benchmark_sparse.py --implementation cuda --kind dense
```

## Đo 10 lần cho mỗi đồ thị

```bash
python3 scripts/benchmark_sparse.py --implementation serial --kind sparse --runs 10
python3 scripts/benchmark_sparse.py --implementation cuda --kind sparse --runs 10

python3 scripts/benchmark_sparse.py --implementation serial --kind dense --runs 10
python3 scripts/benchmark_sparse.py --implementation cuda --kind dense --runs 10

python3 scripts/benchmark_sparse.py --implementation mpi --kind sparse --processes 1 2 4 8 12 --runs 10
python3 scripts/benchmark_sparse.py --implementation mpi --kind dense --processes 1 2 4 8 12 --runs 10
```

## Kết quả

Mỗi thư mục chứa `results.csv`, `time_vs_size.png` và `time_vs_size.svg`.

| Bản chạy | Đồ thị thưa | Đồ thị dày |
|---|---|---|
| Serial | `output/benchmark_sparse/` | `output/benchmark_dense/` |
| MPI, 1/2/4/8/12 tiến trình | `output/benchmark_sparse_mpi/` | `output/benchmark_dense_mpi/` |
| CUDA | `output/benchmark_sparse_cuda/` | `output/benchmark_dense_cuda/` |

Các biểu đồ dùng thang log cho cả trục ngang và trục thời gian, với mốc ngang theo từng kích thước test.

Với MPI, mỗi loại đồ thị có một biểu đồ chung: trục ngang là số đỉnh, trục dọc là thời gian trung vị. Năm đường tương ứng 1, 2, 4, 8 và 12 tiến trình có màu khác nhau và chú thích. CSV chung phân biệt các cấu hình bằng cột `processes`.
