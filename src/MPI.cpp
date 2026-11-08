
#include <mpi.h>
#include <iostream>
#include <vector>
#include <fstream>
#include <climits>
#include <iomanip>
#include <algorithm>

using namespace std;

const int INF = INT_MAX;

bool read_graph(const string& filename, int& n, vector<int>& adj) {
    ifstream file(filename);
    if (!file) return false;

    int m;
    if (!(file >> n >> m) || n <= 0 || m < 0) return false;

    adj.assign(n * n, INF);

    for (int i = 0; i < n; i++)
        adj[i * n + i] = 0;

    for (int i = 0; i < m; i++) {
        int u, v, w;

        if (!(file >> u >> v >> w)) return false;
        if (u < 0 || u >= n || v < 0 || v >= n || w < 0)
            return false;

        adj[u * n + v] = min(adj[u * n + v], w);
        adj[v * n + u] = min(adj[v * n + u], w);
    }

    return true;
}

void dijkstra_mpi(
    int n,
    int src,
    int rank,
    int local_n,
    const vector<int>& local_adj,
    vector<int>& dist,
    vector<bool>& visited
) {
    dist.assign(local_n, INF);
    visited.assign(local_n, false);

    int start = 0;
    MPI_Exscan(&local_n, &start, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);

    if (rank == 0) start = 0;

    if (src >= start && src < start + local_n)
        dist[src - start] = 0;

    while (true) {
        int local_pair[2] = {INF, INT_MAX};
        int global_pair[2];

        // Find local minimum
        for (int j = 0; j < local_n; j++) {
            if (!visited[j] && dist[j] < local_pair[0]) {
                local_pair[0] = dist[j];
                local_pair[1] = start + j;
            }
        }

        // Find global minimum
        MPI_Allreduce(
            local_pair,
            global_pair,
            1,
            MPI_2INT,
            MPI_MINLOC,
            MPI_COMM_WORLD
        );

        int min_dist = global_pair[0];
        int u = global_pair[1];

        if (min_dist == INF) break;

        // Mark selected vertex as visited
        if (u >= start && u < start + local_n)
            visited[u - start] = true;

        // Relax local vertices
        for (int j = 0; j < local_n; j++) {
            if (visited[j]) continue;

            int w = local_adj[u * local_n + j];

            if (w == INF || min_dist > INF - w)
                continue;

            if (min_dist + w < dist[j])
                dist[j] = min_dist + w;
        }
    }
}

int main(int argc, char* argv[]) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc < 3) {
        if (rank == 0)
            cout << "Usage: mpirun -np <processes> ./MPI <input_file> <source>\n";

        MPI_Finalize();
        return 1;
    }

    int n = 0;
    int src = stoi(argv[2]);
    int valid = 1;

    vector<int> adj;

    if (rank == 0) {
        valid = read_graph(argv[1], n, adj);
    }

    MPI_Bcast(&valid, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (!valid) {
        if (rank == 0)
            cout << "Error reading graph file!\n";

        MPI_Finalize();
        return 1;
    }

    MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (src < 0 || src >= n) {
        if (rank == 0)
            cout << "Invalid source vertex!\n";

        MPI_Finalize();
        return 1;
    }

    // Divide vertices among processes
    vector<int> counts(size);
    vector<int> displs(size);
    vector<int> sendcounts(size);
    vector<int> senddispls(size);

    int base = n / size;
    int remainder = n % size;
    int offset = 0;

    for (int p = 0; p < size; p++) {
        counts[p] = base + (p < remainder ? 1 : 0);
        displs[p] = offset;

        sendcounts[p] = n * counts[p];
        senddispls[p] = n * offset;

        offset += counts[p];
    }

    int local_n = counts[rank];

    // Pack adjacency matrix by column blocks
    vector<int> packed;

    if (rank == 0) {
        packed.resize(n * n);

        for (int p = 0; p < size; p++) {
            int block_start = displs[p];

            for (int i = 0; i < n; i++) {
                for (int j = 0; j < counts[p]; j++) {
                    packed[senddispls[p] + i * counts[p] + j] =
                        adj[i * n + block_start + j];
                }
            }
        }
    }

    vector<int> local_adj(n * local_n);

    MPI_Scatterv(
        rank == 0 ? packed.data() : nullptr,
        sendcounts.data(),
        senddispls.data(),
        MPI_INT,
        local_adj.data(),
        n * local_n,
        MPI_INT,
        0,
        MPI_COMM_WORLD
    );

    vector<int> dist;
    vector<bool> visited;

    MPI_Barrier(MPI_COMM_WORLD);
    double start_time = MPI_Wtime();

    dijkstra_mpi(
        n, src, rank, local_n,
        local_adj, dist, visited
    );

    double local_time = MPI_Wtime() - start_time;
    double execution_time = 0;

    MPI_Reduce(
        &local_time,
        &execution_time,
        1,
        MPI_DOUBLE,
        MPI_MAX,
        0,
        MPI_COMM_WORLD
    );

    // Gather distances
    vector<int> global_dist;

    if (rank == 0)
        global_dist.resize(n);

    MPI_Gatherv(
        dist.data(),
        local_n,
        MPI_INT,
        rank == 0 ? global_dist.data() : nullptr,
        counts.data(),
        displs.data(),
        MPI_INT,
        0,
        MPI_COMM_WORLD
    );

    if (rank == 0) {
        cout << "Shortest distances from source " << src << ":\n";

        for (int i = 0; i < n; i++) {
            cout << src << " -> " << i << " : ";

            if (global_dist[i] == INF)
                cout << "INF\n";
            else
                cout << global_dist[i] << '\n';
        }

        cout << fixed << setprecision(6);
        cout << "MPI processes: " << size << '\n';
        cout << "Execution time: " << execution_time << " seconds\n";
    }

    MPI_Finalize();
    return 0;
}
