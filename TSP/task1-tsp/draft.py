import osmnx as ox
import networkx as nx
import folium
import time

class SPPGSimulator:
    def __init__(self, sppg_coords=(-7.2819, 112.7953), dist_meters=2500):
        print(f"Downloading road network within {dist_meters}m of SPPG {sppg_coords}...")
        self.G = ox.graph_from_point(sppg_coords, dist=dist_meters, network_type='drive')
        self.G_proj = ox.project_graph(self.G)
        print("Road network loaded successfully!")

    def get_nodes_in_radius(self, center_lat, center_lon, radius_km):
        center_node = ox.distance.nearest_nodes(self.G, center_lon, center_lat)
        candidate_nodes = [center_node]
        
        for node, data in self.G.nodes(data=True):
            if node == center_node:
                continue
            dist = ox.distance.great_circle(center_lat, center_lon, data['y'], data['x']) / 1000.0
            if dist <= radius_km:
                candidate_nodes.append(node)
                
        return center_node, candidate_nodes

    def compute_distance_matrix(self, target_nodes):
        n = len(target_nodes)
        dist_matrix = [[0] * n for _ in range(n)]
        path_matrix = [[None] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                try:
                    length = nx.shortest_path_length(self.G_proj, target_nodes[i], target_nodes[j], weight='length')
                    path = nx.shortest_path(self.G_proj, target_nodes[i], target_nodes[j], weight='length')
                    dist_matrix[i][j] = length
                    path_matrix[i][j] = path
                except nx.NetworkXNoPath:
                    dist_matrix[i][j] = float('inf')
                    path_matrix[i][j] = []

        return dist_matrix, path_matrix

    def solve_tsp_exact(self, dist_matrix):
        n = len(dist_matrix)
        memo = {}

        def tsp(mask, u):
            if mask == (1 << n) - 1:
                return dist_matrix[u][0], [u, 0]
            
            if (mask, u) in memo:
                return memo[(mask, u)]

            min_cost = float('inf')
            best_path = []

            for v in range(n):
                if not (mask & (1 << v)):
                    cost, path = tsp(mask | (1 << v), v)
                    total_cost = dist_matrix[u][v] + cost
                    if total_cost < min_cost:
                        min_cost = total_cost
                        best_path = [u] + path

            memo[(mask, u)] = (min_cost, best_path)
            return min_cost, best_path

        return tsp(1, 0)

    def solve_tsp_2opt(self, dist_matrix):
        """Solves Asymmetric TSP using Nearest Neighbor + 2-Opt Local Search."""
        n = len(dist_matrix)
        
        unvisited = set(range(1, n))
        curr = 0
        tour = [0]
        while unvisited:
            next_node = min(unvisited, key=lambda x: dist_matrix[curr][x])
            tour.append(next_node)
            unvisited.remove(next_node)
            curr = next_node
        tour.append(0)  # Return to SPPG

        def calc_cost(route):
            return sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))

        improved = True
        best_tour = tour
        best_cost = calc_cost(best_tour)

        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    new_tour = best_tour[:i] + best_tour[i:j+1][::-1] + best_tour[j+1:]
                    new_cost = calc_cost(new_tour)
                    if new_cost < best_cost:
                        best_tour = new_tour
                        best_cost = new_cost
                        improved = True
                        break
                if improved:
                    break

        return best_cost, best_tour

    def run_simulation(self, sppg_coords, radius_km, max_schools=6):
        start_time = time.time()
        sppg_lat, sppg_lon = sppg_coords
        
        center_node, candidate_nodes = self.get_nodes_in_radius(sppg_lat, sppg_lon, radius_km)
        selected_nodes = candidate_nodes[:max_schools]
        print(f"Selected SPPG + {len(selected_nodes)-1} target locations within {radius_km} km radius.")

        dist_matrix, path_matrix = self.compute_distance_matrix(selected_nodes)

        t0 = time.time()
        exact_cost, exact_order = self.solve_tsp_exact(dist_matrix)
        exact_time = time.time() - t0

        t0 = time.time()
        opt2_cost, opt2_order = self.solve_tsp_2opt(dist_matrix)
        opt2_time = time.time() - t0

        order_indices = exact_order
        full_route_nodes = []
        for idx in range(len(order_indices) - 1):
            u_idx = order_indices[idx]
            v_idx = order_indices[idx + 1]
            segment_path = path_matrix[u_idx][v_idx]
            if full_route_nodes and segment_path:
                full_route_nodes.extend(segment_path[1:])
            else:
                full_route_nodes.extend(segment_path)

        m = folium.Map(location=[sppg_lat, sppg_lon], zoom_start=14)

        folium.Circle(
            location=[sppg_lat, sppg_lon],
            radius=radius_km * 1000,
            color="blue",
            fill=True,
            fill_opacity=0.1,
            popup=f"Delivery Radius: {radius_km} km"
        ).add_to(m)

        folium.Marker(
            location=[sppg_lat, sppg_lon],
            popup="<b>SPPG (Central Kitchen)</b>",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(m)

        for stop_num, idx in enumerate(order_indices[:-1]):
            if idx == 0:
                continue
            node_id = selected_nodes[idx]
            node_data = self.G.nodes[node_id]
            folium.Marker(
                location=[node_data['y'], node_data['x']],
                popup=f"Stop #{stop_num}: School Node {node_id}",
                icon=folium.Icon(color="green", icon="info-sign")
            ).add_to(m)

        route_coords = [(self.G.nodes[n]['y'], self.G.nodes[n]['x']) for n in full_route_nodes]
        folium.PolyLine(route_coords, color="red", weight=4, opacity=0.8).add_to(m)

        m.save("map.html")
        total_time = time.time() - start_time

        print("\n" + "="*60)
        print("          SPPG SIMULATOR BENCHMARK COMPARISON         ")
        print("="*60)
        print(f"Exact DP (Held-Karp) Order  : {exact_order}")
        print(f"Exact DP Route Cost         : {exact_cost / 1000.0:.3f} km")
        print(f"Exact DP Execution Time     : {exact_time:.6f} seconds")
        print("-" * 60)
        print(f"2-Opt Heuristic Order       : {opt2_order}")
        print(f"2-Opt Route Cost            : {opt2_cost / 1000.0:.3f} km")
        print(f"2-Opt Execution Time        : {opt2_time:.6f} seconds")
        print("="*60)
        print(f"Total Program Runtime       : {total_time:.2f} seconds")
        print("Interactive map saved to    : map.html")
        print("="*60)

if __name__ == "__main__":
    its_sppg_coords = (-7.2819, 112.7953)
    radius = 1.2

    simulator = SPPGSimulator(sppg_coords=its_sppg_coords, dist_meters=2500)
    simulator.run_simulation(sppg_coords=its_sppg_coords, radius_km=radius, max_schools=6)
    