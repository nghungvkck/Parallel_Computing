# Hướng dẫn biên dịch và chạy

Chạy các lệnh tại thư mục gốc dự án.

## Serial

### Biên dịch

```bash
g++ -O2 -std=c++17 src/Serial.cpp -o serial
```

### Chạy một đồ thị

```bash
./serial data/sparse_10000_30000.txt 0
./serial data/dense_2000_1999000.txt 0
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
mpirun --oversubscribe -np 4 ./mpi data/dense_2000_1999000.txt 0
```

### Đo và vẽ biểu đồ đồ thị thưa

```bash
python3 scripts/benchmark_sparse.py --implementation mpi --kind sparse --processes 4
```

### Đo và vẽ biểu đồ đồ thị dày

```bash
python3 scripts/benchmark_sparse.py --implementation mpi --kind dense --processes 4
```

## CUDA

### Biên dịch

```bash
nvcc -O2 -std=c++17 -ccbin g++-13 -arch=sm_61 src/CUDA.cu -o cuda
```

### Chạy một đồ thị

```bash
./cuda data/sparse_10000_30000.txt 0
./cuda data/dense_2000_1999000.txt 0
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
python3 scripts/benchmark_sparse.py --implementation mpi --kind sparse --processes 4 --runs 10
python3 scripts/benchmark_sparse.py --implementation cuda --kind sparse --runs 10

python3 scripts/benchmark_sparse.py --implementation serial --kind dense --runs 10
python3 scripts/benchmark_sparse.py --implementation mpi --kind dense --processes 4 --runs 10
python3 scripts/benchmark_sparse.py --implementation cuda --kind dense --runs 10
```

## Kết quả

Mỗi thư mục chứa `results.csv`, `time_vs_size.png` và `time_vs_size.svg`.

| Bản chạy | Đồ thị thưa | Đồ thị dày |
|---|---|---|
| Serial | `output/benchmark_sparse/` | `output/benchmark_dense/` |
| MPI, 4 tiến trình | `output/benchmark_sparse_mpi_np4/` | `output/benchmark_dense_mpi_np4/` |
| CUDA | `output/benchmark_sparse_cuda/` | `output/benchmark_dense_cuda/` |
