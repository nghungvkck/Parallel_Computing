#include <cuda_runtime.h>

#include <algorithm>
#include <chrono>
#include <climits>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

constexpr int INF = INT_MAX;

void check_cuda(cudaError_t result) {
    if (result != cudaSuccess)
        throw std::runtime_error(cudaGetErrorString(result));
}

// Free device memory even if a later CUDA operation fails.
struct DeviceBuffer {
    int* data = nullptr;

    explicit DeviceBuffer(size_t bytes) {
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&data), bytes));
    }
    ~DeviceBuffer() { cudaFree(data); }
    DeviceBuffer(const DeviceBuffer&) = delete;
    DeviceBuffer& operator=(const DeviceBuffer&) = delete;
};

std::vector<int> read_graph(const std::string& filename, int& n) {
    std::ifstream file(filename);
    int m;
    if (!(file >> n >> m) || n <= 0 || m < 0)
        throw std::runtime_error("Invalid graph file or graph size.");

    const size_t nodes = static_cast<size_t>(n);
    if (nodes > std::numeric_limits<size_t>::max() / sizeof(int) / nodes)
        throw std::runtime_error("Adjacency matrix is too large.");
    std::vector<int> adj(nodes * nodes, INF);
    for (int i = 0; i < n; ++i)
        adj[static_cast<size_t>(i) * n + i] = 0;

    for (int i = 0; i < m; ++i) {
        int u, v, w;
        if (!(file >> u >> v >> w) || u < 0 || u >= n ||
            v < 0 || v >= n || w < 0 || w == INF)
            throw std::runtime_error("Invalid edge (require 0 <= weight < INT_MAX).");
        // Match the MPI version: keep the smallest parallel-edge weight.
        const size_t uv = static_cast<size_t>(u) * n + v;
        const size_t vu = static_cast<size_t>(v) * n + u;
        adj[uv] = std::min(adj[uv], w);
        adj[vu] = std::min(adj[vu], w);
    }
    return adj;
}

// Paper's CUDA approach: relax edges in parallel until convergence.
// This is iterative relaxation, rather than the serial greedy min selection.
// Read only from current; atomicMin resolves concurrent writes to next.
__global__ void relax_edges(int n, const int* adj, const int* current,
                            int* next, int* changed) {
    const size_t u = static_cast<size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (u >= static_cast<size_t>(n) || current[u] == INF) return;

    const int distance = current[u];
    for (int v = 0; v < n; ++v) {
        const int w = adj[u * n + v];
        if (w == INF || distance > INF - w) continue;
        const int candidate = distance + w;
        if (candidate < atomicMin(&next[v], candidate))
            atomicExch(changed, 1);
    }
}

std::vector<int> dijkstra_cuda(const std::vector<int>& adj, int n, int src) {
    const size_t dist_bytes = static_cast<size_t>(n) * sizeof(int);
    DeviceBuffer d_adj(adj.size() * sizeof(int));
    DeviceBuffer d_first(dist_bytes), d_second(dist_bytes), d_changed(sizeof(int));

    std::vector<int> dist(n, INF);
    dist[src] = 0;
    check_cuda(cudaMemcpy(d_adj.data, adj.data(), adj.size() * sizeof(int),
                          cudaMemcpyHostToDevice));
    check_cuda(cudaMemcpy(d_first.data, dist.data(), dist_bytes, cudaMemcpyHostToDevice));

    int* current = d_first.data;
    int* next = d_second.data;
    constexpr int threads = 256;
    const unsigned int blocks = static_cast<unsigned int>(
        (static_cast<size_t>(n) + threads - 1) / threads);

    // At most n-1 rounds for shortest paths, plus one convergence check.
    for (int round = 0; round < n; ++round) {
        check_cuda(cudaMemcpy(next, current, dist_bytes, cudaMemcpyDeviceToDevice));
        check_cuda(cudaMemset(d_changed.data, 0, sizeof(int)));
        relax_edges<<<blocks, threads>>>(n, d_adj.data, current, next, d_changed.data);
        check_cuda(cudaGetLastError());
        check_cuda(cudaDeviceSynchronize());

        int changed = 0;
        check_cuda(cudaMemcpy(&changed, d_changed.data, sizeof(int), cudaMemcpyDeviceToHost));
        std::swap(current, next);
        if (!changed) break;
    }

    check_cuda(cudaMemcpy(dist.data(), current, dist_bytes, cudaMemcpyDeviceToHost));
    return dist;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: ./cuda <input_file> <source>\n";
        return 1;
    }

    try {
        int n = 0;
        const auto adj = read_graph(argv[1], n);
        size_t parsed = 0;
        const std::string source = argv[2];
        const int src = std::stoi(source, &parsed);
        if (parsed != source.size() || src < 0 || src >= n)
            throw std::runtime_error("Invalid source vertex.");

        int devices = 0;
        check_cuda(cudaGetDeviceCount(&devices));
        if (devices == 0) throw std::runtime_error("No CUDA GPU found.");
        check_cuda(cudaSetDevice(0));
        cudaDeviceProp properties{};
        check_cuda(cudaGetDeviceProperties(&properties, 0));

        // Include device allocation, transfers, kernels, synchronization and cleanup.
        const auto start = std::chrono::steady_clock::now();
        const auto dist = dijkstra_cuda(adj, n, src);
        const double elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();

        std::cout << "Shortest distances from source " << src << ":\n";
        for (int i = 0; i < n; ++i) {
            std::cout << src << " -> " << i << " : ";
            if (dist[i] == INF) std::cout << "INF\n";
            else std::cout << dist[i] << '\n';
        }
        std::cout << "CUDA GPU: " << properties.name << '\n'
                  << std::fixed << std::setprecision(6)
                  << "Execution time: " << elapsed << " seconds\n";
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
