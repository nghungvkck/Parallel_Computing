# Dữ liệu đo tốc độ

12 đồ thị vô hướng, liên thông, không cạnh trùng/khuyên; trọng số nguyên 1–100, đỉnh nguồn `0`. Đồ thị thưa có `3n` cạnh; đồ thị dày là đồ thị đầy đủ. Đây là dữ liệu tự sinh theo kích thước bài báo, không phải dữ liệu gốc của tác giả. Trọng số, seed và cách sinh là lựa chọn của dự án.

| File | Đỉnh | Cạnh | Một ma trận int32 |
|---|---:|---:|---:|
| sparse_10_30.txt | 10 | 30 | 0,0004 MB |
| sparse_100_300.txt | 100 | 300 | 0,04 MB |
| sparse_1000_3000.txt | 1.000 | 3.000 | 4 MB |
| sparse_2000_6000.txt | 2.000 | 6.000 | 16 MB |
| sparse_5000_15000.txt | 5.000 | 15.000 | 100 MB |
| sparse_10000_30000.txt | 10.000 | 30.000 | 400 MB |
| sparse_20000_60000.txt | 20.000 | 60.000 | 1.600 MB |
| dense_10_45.txt | 10 | 45 | 0,0004 MB |
| dense_100_4950.txt | 100 | 4.950 | 0,04 MB |
| dense_1000_499500.txt | 1.000 | 499.500 | 4 MB |
| dense_2000_1999000.txt | 2.000 | 1.999.000 | 16 MB |
| dense_3000_4498500.txt | 3.000 | 4.498.500 | 36 MB |

MB tính theo 1.000.000 byte; đây chỉ là một ma trận, chưa tính các bản sao và bộ nhớ khác. Dữ liệu không có cạnh trùng nên tránh khác biệt đọc cạnh của bản tuần tự với MPI/CUDA.

## Đối chiếu bài báo

Đã đối chiếu trực tiếp [PDF của dự án](../2504.03667v1.pdf), trang 4, mục IV-A, Bảng I–II; có thể xem [bản HTML cùng phiên bản](https://arxiv.org/html/2504.03667v1#S4.SS1).

- Bổ sung 4 file: sparse `(V, E)` = `(10, 30)`, `(20000, 60000)`; dense `(10, 45)`, `(3000, 4498500)`. Giữ nguyên 8 file cũ.
- Bảng I và III ghi dense 2.000 đỉnh có **1.899.500 cạnh**, trong khi đồ thị đầy đủ có **1.999.000 cạnh**. Ban đầu có thêm file theo con số trong bài báo; theo yêu cầu mới, đã thay file đó bằng dense đầy đủ **3.000 đỉnh / 4.498.500 cạnh** để mỗi kích thước dense chỉ có một test.
- Sparse 5.000 đỉnh, dense đầy đủ 2.000 và 3.000 đỉnh là các trường hợp mở rộng đã có của dự án. Không sinh trường hợp 40.000 đỉnh trong bài báo; bộ dữ liệu hiện giới hạn tối đa 20.000 đỉnh theo yêu cầu.
- Test 10 đỉnh giúp khảo sát chi phí song song ở quy mô nhỏ và MPI 12 tiến trình nhiều hơn số đỉnh. Test sparse 20.000 đỉnh phục vụ khảo sát tăng kích thước; một ma trận int32 cần 1,6 GB, chưa tính buffer MPI hay bản sao GPU.

## Sinh lại dữ liệu

Tại thư mục gốc dự án:

```bash
python3 scripts/generate_benchmarks.py
```

Chỉ cần Python 3, không cần gói pip. Lệnh tạo file còn thiếu trực tiếp trong `data/`, giữ nguyên file có sẵn và kiểm tra SHA-256 với manifest cũ, rồi cập nhật `manifest.csv`; không chạy benchmark. Manifest chứa seed, kích thước và SHA-256. Seed là `42 + V` cho sparse, `1000042 + V` cho dense. `matrix_mb` làm tròn hai chữ số thập phân nên test 10 đỉnh hiện `0.00`.

Dùng `--output-dir /tmp/ttss-data` để sinh vào thư mục khác; thêm `--overwrite` nếu chủ động muốn sinh lại và ghi đè các file trong bộ 12 trường hợp.

## Phương pháp đo

- Mỗi file chạy 7 cấu hình: tuần tự, MPI 1/2/4/8/12 tiến trình và CUDA.
- Mỗi cấu hình chạy khởi động 1 lần, sau đó đo 5 lần, lấy trung vị.
- Luôn dùng cùng file và nguồn `0`; thời gian lấy từ `Execution time`.
- Tăng tốc = trung vị thời gian tuần tự / trung vị thời gian cấu hình tương ứng.
- Ghi GPU, CPU, RAM, phiên bản compiler và cờ biên dịch khi lập báo cáo.

Lưu ý trước khi đo: MPI hiện chưa tính phân phối/gom dữ liệu trong thời gian báo cáo; CUDA tính cả cấp phát/truyền dữ liệu. Cần thống nhất phạm vi đo khi so sánh với bài báo. Các lần chạy riêng biệt vẫn có thể chịu chi phí khởi tạo CUDA dù có lượt khởi động. `--oversubscribe` giúp chạy đủ tiến trình, nhưng nếu vượt tài nguyên CPU thì kết quả có thể chậm hơn.

Để ghi kết quả sau này, có thể dùng các cột: `file, implementation, processes, run1_s, run2_s, run3_s, run4_s, run5_s, median_s, speedup`.

Script `scripts/benchmark_sparse.py` hỗ trợ `--implementation serial|mpi|cuda`, `--kind sparse|dense`, `--runs` (mặc định 5) và `--processes` (MPI, mặc định 4; dùng `--processes 1 2 4 8 12` để đo đủ năm cấu hình). Các lệnh chạy nằm trong [RUN.md](../RUN.md).

Mỗi cấu hình chạy khởi động 1 lần, rồi lấy trung vị các lần đo từ `Execution time`. CSV lưu từng lần đo, trung vị, min/max, cấu hình và phạm vi đo. Biểu đồ chỉ hiển thị đường và các điểm trung vị. Kết quả được ghi lại khi chạy cùng thư mục; dùng `--output-dir` để chọn thư mục khác. `--binary` chọn chương trình, `--data-dir` chọn thư mục dữ liệu, `--source` chọn nguồn (mặc định 0).

Đồ thị thưa có `E = 3V`; đồ thị dày có `E = V(V-1)/2`. Dense có 5 kích thước riêng biệt: 10, 100, 1.000, 2.000 và 3.000 đỉnh. Với cạnh trùng, MPI/CUDA giữ trọng số nhỏ nhất, Serial giữ trọng số đọc sau. Dữ liệu benchmark hiện không có cạnh trùng.
