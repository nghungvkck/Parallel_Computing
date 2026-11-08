# Dữ liệu đo tốc độ

8 đồ thị vô hướng, liên thông, không cạnh trùng/khuyên; trọng số nguyên 1–100, đỉnh nguồn `0`. Đồ thị thưa có `3n` cạnh, đồ thị dày là đồ thị đầy đủ. Đây là dữ liệu tự sinh để khảo sát theo hướng bài báo, không phải dữ liệu gốc của tác giả.

| File | Đỉnh | Cạnh | Một ma trận int32 |
|---|---:|---:|---:|
| sparse_100_300.txt | 100 | 300 | 0,04 MB |
| sparse_1000_3000.txt | 1.000 | 3.000 | 4 MB |
| sparse_2000_6000.txt | 2.000 | 6.000 | 16 MB |
| sparse_5000_15000.txt | 5.000 | 15.000 | 100 MB |
| sparse_10000_30000.txt | 10.000 | 30.000 | 400 MB |
| dense_100_4950.txt | 100 | 4.950 | 0,04 MB |
| dense_1000_499500.txt | 1.000 | 499.500 | 4 MB |
| dense_2000_1999000.txt | 2.000 | 1.999.000 | 16 MB |

MB tính theo 1.000.000 byte; đây chỉ là một ma trận, chưa tính các bản sao và bộ nhớ khác. Dữ liệu không có cạnh trùng nên tránh khác biệt đọc cạnh của bản tuần tự với MPI/CUDA.

## Sinh lại dữ liệu

Tại thư mục gốc dự án:

```bash
python3 scripts/generate_benchmarks.py
```

Chỉ cần Python 3, không cần gói pip. Lệnh ghi lại 8 file dữ liệu và `manifest.csv`, không chạy chương trình đo tốc độ. Manifest chứa seed, kích thước và SHA-256 để đối chiếu dữ liệu.

## Phương pháp đo

- Mỗi file chạy 5 cấu hình: tuần tự, MPI 1/2/4 tiến trình và CUDA.
- Mỗi cấu hình chạy khởi động 1 lần, sau đó đo 5 lần, lấy trung vị.
- Luôn dùng cùng file và nguồn `0`; thời gian lấy từ `Execution time`.
- Tăng tốc = trung vị thời gian tuần tự / trung vị thời gian cấu hình tương ứng.
- Ghi GPU, CPU, RAM, phiên bản compiler và cờ biên dịch khi lập báo cáo.

Lưu ý trước khi đo: MPI hiện chưa tính phân phối/gom dữ liệu trong thời gian báo cáo; CUDA tính cả cấp phát/truyền dữ liệu. Cần thống nhất phạm vi đo khi so sánh với bài báo. Các lần chạy riêng biệt vẫn có thể chịu chi phí khởi tạo CUDA dù có lượt khởi động. `--oversubscribe` giúp chạy đủ tiến trình, nhưng nếu vượt tài nguyên CPU thì kết quả có thể chậm hơn.

Để ghi kết quả sau này, có thể dùng các cột: `file, implementation, processes, run1_s, run2_s, run3_s, run4_s, run5_s, median_s, speedup`.

Script `scripts/benchmark_sparse.py` hỗ trợ `--implementation serial|mpi|cuda`, `--kind sparse|dense`, `--runs` (mặc định 5) và `--processes` (MPI, mặc định 4). Các lệnh chạy nằm trong [RUN.md](../RUN.md).

Mỗi cấu hình chạy khởi động 1 lần, rồi lấy trung vị các lần đo từ `Execution time`. CSV lưu từng lần đo, trung vị, min/max, cấu hình và phạm vi đo. Biểu đồ chỉ hiển thị đường và các điểm trung vị. Kết quả được ghi lại khi chạy cùng thư mục; dùng `--output-dir` để chọn thư mục khác. `--binary` chọn chương trình, `--data-dir` chọn thư mục dữ liệu, `--source` chọn nguồn (mặc định 0).

Đồ thị thưa hiện có `E = 3V`, đồ thị dày có `E = V(V-1)/2`; chưa tách riêng ảnh hưởng của số cạnh và số đỉnh. Với cạnh trùng, MPI/CUDA giữ trọng số nhỏ nhất, Serial giữ trọng số đọc sau. Dữ liệu benchmark hiện không có cạnh trùng.
