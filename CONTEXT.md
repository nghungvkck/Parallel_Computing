# Ngữ cảnh bàn giao dự án

Cập nhật: 08/11/2026. Đọc file này trước khi làm việc để hiểu dự án và các quyết định đã thống nhất. Chỉ mở thêm mã nguồn liên quan đến yêu cầu mới. Đây là ảnh chụp trạng thái; luôn đối chiếu `git status` trước khi sửa, không tự khôi phục hoặc xóa thay đổi của người dùng.

## 1. Mục tiêu và cấu trúc

Dự án khảo sát bài toán đường đi ngắn nhất từ một nguồn (SSSP) trên đồ thị vô hướng có trọng số dương, so sánh thời gian và khả năng tăng tốc của Serial, MPI và CUDA. Bài tham khảo là **High-Performance Parallelization of Dijkstra’s Algorithm Using MPI and CUDA**, Boyang Song, arXiv:2504.03667v1; PDF ở gốc dự án: `2504.03667v1.pdf`.

| File | Vai trò |
|---|---|
| `src/Serial.cpp` | Dijkstra tuần tự, ma trận kề, O(V²). |
| `src/MPI.cpp` | Chia ma trận theo cột, Scatterv phân phối, Allreduce/MINLOC chọn đỉnh toàn cục, Gatherv gom khoảng cách. |
| `src/CUDA.cu` | Thư giãn cạnh lặp đến hội tụ, hai buffer khoảng cách và atomicMin; không chọn đỉnh tuần tự như Serial/MPI. |
| `scripts/generate_benchmarks.py` | Sinh đồ thị có seed và manifest SHA-256; không chạy thuật toán. |
| `scripts/benchmark_sparse.py` | Đo Serial/MPI/CUDA trên cả sparse/dense, xuất CSV và biểu đồ PNG/SVG. |
| `data/README.md`, `data/manifest.csv` | Mô tả, nguồn gốc và thông tin đối chiếu dữ liệu. |
| `RUN.md`, `INSTALL.md` | Lệnh biên dịch/chạy và cài đặt. |
| `output/` | Kết quả benchmark; có thể được người dùng cập nhật giữa các phiên. |

Đầu vào: dòng đầu `n m`, sau đó m dòng `u v w`. Đỉnh đánh số từ 0, nguồn mặc định là 0. Binary nhận `<file> <source>` và in khoảng cách cùng `Execution time: ... seconds`.

Cả ba bản dùng ma trận kề, bộ nhớ O(V²). Một ma trận int32 ở 10.000 đỉnh cần 400 MB, ở 20.000 đỉnh cần 1,6 GB (MB/GB thập phân); MPI còn buffer đóng gói, CUDA có bản sao trên host và GPU.

## 2. Yêu cầu và sở thích đã thống nhất

- MPI đo 1, 2, 4, 8, 12 tiến trình; một biểu đồ chung cho mỗi loại sparse/dense, mỗi cấu hình một màu và có chú thích.
- Dữ liệu chỉ bổ sung đến **20.000 đỉnh**. Người dùng đã bác đề xuất 40.000 đỉnh; không thêm lại nếu chưa được yêu cầu.
- **Cả trục ngang và trục thời gian đều dùng log**, áp dụng Serial/MPI/CUDA và sparse/dense. Ghi mốc ngang theo kích thước test để thấy các điểm nhỏ.
- `RUN.md` cần gọn, theo bố cục Serial → MPI → CUDA như trước. Người dùng không thích phần giải thích dài và vòng lặp tổng hợp test mới ở đầu file. Chi tiết dữ liệu đặt trong `data/README.md`.
- Chưa yêu cầu commit, đổi phạm vi đo hoặc triển khai warm-up trong cùng phiên MPI. Không coi các đề xuất trước đây là yêu cầu đã chấp thuận.

## 3. Bộ dữ liệu hiện tại

12 đồ thị tự sinh, vô hướng, liên thông, không cạnh trùng/khuyên, trọng số nguyên 1–100. Đây là dữ liệu cùng kích thước tham khảo bài báo, **không phải dữ liệu gốc của tác giả**; seed, trọng số và cách sinh do dự án lựa chọn.

| File | V | E |
|---|---:|---:|
| `sparse_10_30.txt` | 10 | 30 |
| `sparse_100_300.txt` | 100 | 300 |
| `sparse_1000_3000.txt` | 1.000 | 3.000 |
| `sparse_2000_6000.txt` | 2.000 | 6.000 |
| `sparse_5000_15000.txt` | 5.000 | 15.000 |
| `sparse_10000_30000.txt` | 10.000 | 30.000 |
| `sparse_20000_60000.txt` | 20.000 | 60.000 |
| `dense_10_45.txt` | 10 | 45 |
| `dense_100_4950.txt` | 100 | 4.950 |
| `dense_1000_499500.txt` | 1.000 | 499.500 |
| `dense_2000_1999000.txt` | 2.000 | 1.999.000 |
| `dense_3000_4498500.txt` | 3.000 | 4.498.500 |

Bốn file mới bổ sung: sparse 10/20.000 đỉnh, dense 10 đỉnh và dense đầy đủ 3.000 đỉnh / 4.498.500 cạnh. Tám file cũ giữ nguyên SHA-256. Theo yêu cầu mới nhất, file `dense_2000_1899500.txt` đã được thay bằng file 3.000 đỉnh để không có hai test dense cùng kích thước.

Đã đọc trực tiếp PDF cục bộ, trang 4, mục IV-A, Bảng I–II; bảng dense 2.000 đỉnh ghi **1.899.500 cạnh**, Bảng III trang 5 cũng ghi như vậy. Đồ thị đầy đủ thực tế có **1.999.000 cạnh**. Ban đầu sinh thêm file theo bài báo, nhưng người dùng yêu cầu đổi test dense cuối sang 3.000 đỉnh; hiện chỉ giữ dense đầy đủ ở mọi kích thước, không sinh lại file 1.899.500 cạnh. Sparse 5.000 đỉnh, dense đầy đủ 2.000 và 3.000 đỉnh là các trường hợp mở rộng ngoài bảng. PDF có sparse 40.000 đỉnh nhưng không tạo theo giới hạn người dùng.

Sinh dữ liệu từ gốc dự án:

```bash
python3 scripts/generate_benchmarks.py
```

- Đã sửa đích mặc định từ `data/benchmarks/` thành **`data/`**, khớp script đo.
- Mặc định tạo file còn thiếu, giữ file có sẵn, kiểm tra header và SHA-256 theo manifest cũ, rồi cập nhật manifest. File có sẵn thiếu manifest hoặc không khớp hash sẽ gây lỗi thay vì tự ghi đè.
- `--output-dir <dir>` để sinh vào nơi khác; `--overwrite` để chủ động sinh lại các file trong bộ 12 trường hợp.
- Seed sparse = `42 + V`; dense = `1000042 + V`. Cạnh được ghi theo thứ tự `(u, v)` tăng dần, `u < v`.
- `manifest.csv` chứa tên, loại, V/E, nguồn, seed, bộ nhớ một ma trận, kích thước file và SHA-256. CSV manifest dùng LF. `matrix_mb` làm tròn hai chữ số, nên V=10 hiện `0.00` (thực tế 0,0004 MB).

## 4. Biên dịch và benchmark

Các lệnh đầy đủ ở `RUN.md`; chạy tại gốc dự án:

```bash
g++ -O2 -std=c++17 src/Serial.cpp -o serial
mpic++ -O2 -std=c++17 src/MPI.cpp -o mpi
nvcc -O2 -std=c++17 -ccbin g++-13 -arch=sm_61 src/CUDA.cu -o cuda

python3 scripts/benchmark_sparse.py --implementation serial --kind sparse
python3 scripts/benchmark_sparse.py --implementation serial --kind dense
python3 scripts/benchmark_sparse.py --implementation mpi --kind sparse --processes 1 2 4 8 12
python3 scripts/benchmark_sparse.py --implementation mpi --kind dense --processes 1 2 4 8 12
python3 scripts/benchmark_sparse.py --implementation cuda --kind sparse
python3 scripts/benchmark_sparse.py --implementation cuda --kind dense
```

Cờ CUDA trên là cấu hình hiện được ghi trong hướng dẫn; cần đối chiếu GPU/compiler nếu chuyển máy.

- Mặc định 1 warm-up + 5 lượt đo, lấy trung vị từ `Execution time`. `--runs 10` đổi số lượt đo.
- Script tự tìm `sparse_*.txt` hoặc `dense_*.txt` ngay trong `data/`, không tìm đệ quy. Hiện sparse có 7 test, dense có 5 test. Dense có V=10/100/1.000/2.000/3.000, mỗi kích thước một file.
- `--processes` nhận danh sách, loại trùng, mặc định `[4]`; vẫn nhận `--processes 4`.
- Các tùy chọn khác: `--binary`, `--data-dir`, `--source`, `--mpirun`, `--output-dir`.
- Mỗi lượt là subprocess mới, timeout 300 giây; MPI dùng `mpirun --oversubscribe`. Vượt tài nguyên CPU có thể làm chậm kết quả.
- Mỗi thư mục chứa `results.csv`, `time_vs_size.png`, `time_vs_size.svg`. Chạy lại cùng thư mục sẽ ghi đè; dùng `--output-dir` nếu cần giữ kết quả cũ.
- Serial: `output/benchmark_sparse/`, `output/benchmark_dense/`.
- MPI nhiều cấu hình: `output/benchmark_sparse_mpi/`, `output/benchmark_dense_mpi/`; CSV phân biệt bằng `processes`. Một cấu hình dùng hậu tố `_mpi_npN/`.
- CUDA: `output/benchmark_sparse_cuda/`, `output/benchmark_dense_cuda/`.

### Cách vẽ đã sửa

Hàm `plot_results` trong `scripts/benchmark_sparse.py` dùng `set_xscale("log")` và `set_yscale("log")`, đã bỏ giới hạn y bắt đầu ở 0. Mốc x lấy các giá trị thực trong dữ liệu, định dạng có dấu phẩy và xoay 30 độ; lưới cả major/minor. MPI có một ô theo V, mỗi cấu hình một đường; Serial/CUDA có hai ô theo V và E.

Người dùng tưởng thiếu test vì đồ thị tuyến tính dồn điểm 10/100/1.000/2.000 đỉnh vào góc trái. Đã giải thích đủ 7 điểm; hai ô sparse giống hình dạng vì E=3V. Người dùng yêu cầu đổi sang log và thay đổi này đã hoàn thành.

Đã vẽ lại **chỉ biểu đồ Serial sparse hiện có** từ `output/benchmark_sparse/results.csv` bằng hàm `plot_results`, không chạy lại benchmark và không đổi CSV. Đã xem PNG xác nhận thấy đủ 7 điểm. Có thể dùng `runpy.run_path` để gọi hàm vẽ từ CSV; hiện chưa có tùy chọn CLI chỉ vẽ lại. Biểu đồ khác khi chạy benchmark sau sẽ dùng log; không mặc định coi file kết quả cũ đã được vẽ lại. Log yêu cầu giá trị dương; hiện chưa có xử lý riêng cho thời gian 0 do làm tròn.

Trung vị Serial sparse trong CSV tại lần đọc gần nhất:

| V | Trung vị (s) |
|---:|---:|
| 10 | 0.000002 |
| 100 | 0.000047 |
| 1.000 | 0.003544 |
| 2.000 | 0.015158 |
| 5.000 | 0.112622 |
| 10.000 | 0.488024 |
| 20.000 | 2.274610 |

Đây là kết quả người dùng đã chạy, không phải benchmark do Codex chạy trong phiên này; dữ liệu có thể thay đổi.

## 5. Phạm vi đo và vấn đề MPI còn mở

Phạm vi hiện tại (chưa sửa mã C++/CUDA trong các công việc trên):

- Serial: chỉ thuật toán; bỏ đọc đồ thị và in kết quả.
- MPI: MPI_Init, đọc dữ liệu, Bcast, đóng gói, Scatterv và Barrier đầu ngoài vùng đo. Đồng hồ bao quanh `dijkstra_mpi`, gồm khởi tạo dist/visited, Exscan và Allreduce. Báo max thời gian qua rank bằng Reduce; Reduce đó và Gatherv ngoài vùng đo.
- CUDA: tính cấp phát GPU, truyền dữ liệu, kernel, đồng bộ và giải phóng; bỏ đọc đồ thị/in kết quả. Kiểm tra/chọn thiết bị trước đồng hồ.

Warm-up Python chạy subprocess riêng. Mỗi lượt MPI là một `mpirun` mới, nên không giữ trạng thái MPI giữa warm-up và lượt đo. MPI_Init/tạo tiến trình vốn ngoài đồng hồ; thiết lập collective đầu tiên trong thuật toán có thể ảnh hưởng nhưng **chưa được kiểm chứng**.

Trong phiên trước người dùng thấy MPI 12 tiến trình bất thường: dense V=100 median 0.162685 s (min–max 0.025984–0.221976), V=1.000 median 0.008338 s, V=2.000 median 0.018567 s; sparse V=100 median 0.186730 s (0.001670–0.594640). Đây là số liệu lịch sử, file có thể không còn. Chưa xác định nguyên nhân; không kết luận do khởi tạo, CPU hoặc oversubscription khi chưa đo kiểm chứng.

Đã đề xuất warm-up và nhiều lượt thuật toán trong cùng phiên MPI, đặt lại dist/visited giữa lượt, nhưng **chưa triển khai/chưa được yêu cầu triển khai**.

## 6. Đối chiếu bài báo và giới hạn kết luận

Bản HTML cùng phiên bản: <https://arxiv.org/html/2504.03667v1>. Đã đọc HTML ở phiên trước và trích PDF cục bộ trang 4–5 ở phiên bổ sung dữ liệu.

- Bài dùng đồ thị vô hướng nếu không nói khác; mục IV-A có các kích thước được mô tả ở phần dữ liệu trên.
- Mục III-B: chia ma trận theo cột, padding để chia hết cho số tiến trình, rank 0 copy phần mình và Send/Recv cho rank khác. Code dự án dùng chia không đều với Scatterv, không padding.
- Mục III: bỏ chuyển edge list sang ma trận; MPI tính giao tiếp, thuật toán, Gather; CUDA tính bộ nhớ GPU, truyền dữ liệu, kernel; cả hai tính đồng bộ.
- Code hiện bỏ Scatterv/Gatherv khỏi đồng hồ, chưa khớp phạm vi bài báo. Chưa sửa.
- Bài không nói rõ vị trí đồng hồ quanh MPI_Init hoặc quy trình warm-up/nhiều lượt; không suy ra chắc chắn tác giả tính hay loại MPI_Init.
- Mục IV-B/IV-D: đồ thị nhỏ và quá nhiều tiến trình có thể chậm do giao tiếp/đồng bộ. Đây không phải bằng chứng cho nguyên nhân bất thường trên máy hiện tại.
- Máy bài báo là Perlmutter, AMD EPYC 7763 64 lõi và GPU A100; không kỳ vọng thời gian/tăng tốc giống máy cá nhân. Bảng IV dùng 40.000 đỉnh cho strong scaling, nhưng bộ dữ liệu dự án chỉ đến 20.000 theo yêu cầu.

## 7. Kiểm tra đã làm

Các kiểm tra toàn bộ/tái lập dưới đây được thực hiện trước khi đổi dense cuối sang 3.000 đỉnh. Sau khi đổi đã kiểm tra riêng file mới: đủ 4.498.500 cạnh theo thứ tự của đồ thị đầy đủ, đỉnh/trọng số hợp lệ và SHA-256 khớp manifest; 11 file giữ lại vẫn khớp manifest. Chưa chạy benchmark trên test 3.000 đỉnh.

- Đã kiểm tra cả 12 file: header, số dòng/cạnh, đỉnh hợp lệ, trọng số 1–100, không cạnh trùng/khuyên, thứ tự cạnh và liên thông bằng union-find.
- Đối chiếu SHA-256 xác nhận 8 file gốc không đổi.
- Sinh lại toàn bộ ở `/tmp/ttss-data-verify` và đối chiếu manifest xác nhận cả 12 file tái lập đúng. Chạy lại generator mặc định xác nhận giữ nguyên cả 12 file.
- Phiên trước đã mô phỏng subprocess MPI để kiểm tra đủ cấu hình 1/2/4/8/12, warm-up/lượt đo, CSV chung và chú thích. Không coi mô phỏng là kiểm chứng hiệu năng/tính đúng thuật toán.
- Đã gọi hàm vẽ bằng CSV Serial sparse thật và xem PNG log có đủ 7 điểm; không chạy benchmark thật trong phiên bổ sung dữ liệu/vẽ log.
- `git diff --check -- scripts/benchmark_sparse.py RUN.md` đã qua sau đổi log. Kiểm tra toàn repo có lỗi whitespace ở CSV kết quả dùng CRLF và SVG do Matplotlib sinh; không nhầm với lỗi mã nguồn hay tự sửa dữ liệu người dùng chỉ để dọn diff.

## 8. Trạng thái workspace và lưu ý cho phiên sau

Tại lần `git status` gần nhất trước cập nhật file này:

- Modified: `RUN.md`, `data/README.md`, `data/manifest.csv`, `scripts/benchmark_sparse.py`, `scripts/generate_benchmarks.py`, cùng CSV/PNG/SVG của `output/benchmark_sparse/`.
- Untracked: `CONTEXT.md` và 4 file dữ liệu mới liệt kê ở phần 3.
- Git báo deleted CSV/PNG/SVG tại `output/benchmark_dense/`, `output/benchmark_dense_mpi_np4/`, `output/benchmark_sparse_mpi_np4/`. Không phải thao tác xóa do Codex thực hiện trong công việc này; không tự khôi phục. Đối chiếu trạng thái thực tế ở phiên sau.
- Chưa commit. Không thay đổi mã nguồn C++/CUDA trong chuỗi công việc này.

Các giới hạn đã biết: Serial thiếu kiểm tra file/đỉnh nguồn/đầu vào. Nếu cạnh trùng, Serial giữ trọng số cuối còn MPI/CUDA giữ nhỏ nhất; bộ dữ liệu hiện không có cạnh trùng. Phạm vi đo giữa MPI/CUDA chưa thống nhất. Log chưa xử lý riêng median bằng 0. Không tự mở rộng phạm vi sửa nếu người dùng chưa yêu cầu.

Môi trường làm việc gần nhất: `/mnt/d/hoc_tren_truong/ttss` (trước đây đường dẫn hiển thị `/mnt/d/Hoc_tren_truong/TTSS`); dùng cwd của phiên hiện tại. Hướng dẫn người dùng tham chiếu `/home/nghung/.codex/RTK.md`: **mọi lệnh shell phải có tiền tố `rtk`**, dùng `rtk proxy ...` khi cần đầu ra nguyên bản.

Matplotlib có thể không ghi được cache trong home; dùng `MPLCONFIGDIR=/tmp/ttss-mpl` và `XDG_CACHE_HOME=/tmp/ttss-cache`. Tránh tạo/thay đổi pyc ngoài ý muốn; có thể dùng `runpy.run_path` hoặc `PYTHONDONTWRITEBYTECODE=1`.

Máy ban đầu thiếu pdftotext và thư viện PDF. Đã cài pypdf tạm vào `/tmp/ttss-pdf-reader` để đọc PDF bằng `sys.path.insert(0, ...)`, không thêm dependency dự án. Các thư mục `/tmp` có thể mất ở phiên sau; không phụ thuộc vào chúng.
