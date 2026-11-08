#include <iostream>
#include <vector>
#include <chrono>
#include <fstream>
#include <climits>
#include <iomanip>

using namespace std;

const int INF = INT_MAX;
vector<vector<int>> read_graph(const string& filename, int& n){
    ifstream file(filename);

    int m ;
    file >> n >> m;
    vector<vector<int>> adj(n, vector<int>(n, INF));

    for ( int i = 0; i <n ; i++){
        adj[i][i] = 0;
    }

    for (int i = 0; i < m; i++) {
        int u, v, w;
        file >> u >> v >> w;
        adj[u][v] = w;
        adj[v][u] = w; // Assuming undirected graph
    }
    return adj;
}

vector<int> dijkstra(const vector<vector<int>>& adj, int src){
    int n = adj.size();

    vector<int> dist(n, INF);
    vector<bool> visited(n, false);
    dist[src] = 0;

    for ( int i =0; i < n; i++){
        int u  =  -1;
        int min_dist = INF;

        for ( int v = 0; v < n; v++){
            if (!visited[v] && dist[v] < min_dist){
                min_dist = dist[v];
                u = v;
            }
        }

        if (u == -1) break; // All reachable vertices are visited
        visited[u] = true;

        for ( int v = 0 ; v < n; v++){
            if (!visited[v] && adj[u][v] != INF && 
                dist[u] <= INF - adj[u][v] && 
                dist[u] + adj[u][v] < dist[v]) {

                dist[v] = dist[u] + adj[u][v];
            }
        }
    }
    return dist;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cout << "Usage: ./serial <input_file> <source>\n";
        return 1;
    }

    int n;
    auto adj = read_graph(argv[1], n);
    int src = stoi(argv[2]);

    auto start = chrono::high_resolution_clock::now();
    auto dist = dijkstra(adj, src);
    auto end = chrono::high_resolution_clock::now();
    double elapsed = chrono::duration<double>(end - start).count();

    cout << "Shortest distances from source " << src << ":\n";

    for (int i = 0; i < n; i++) {
        cout << src << " -> " << i << " : ";

        if (dist[i] == INF)
            cout << "INF\n";
        else
            cout << dist[i] << '\n';
    }

    cout << fixed << setprecision(6);
    cout << "Execution time: " << elapsed << " seconds\n";

    return 0;
}