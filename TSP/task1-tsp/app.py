import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
import time
import os

st.set_page_config(page_title="SPPG Delivery Simulator", layout="wide")
st.title("SPPG Delivery Simulator")
st.caption("Surabaya")

@st.cache_resource
def load_local_graph(filepath="surabaya_sppg.graphml"):
    if not os.path.exists(filepath):
        st.error("Graph file 'surabaya_sppg.graphml' not found. Please run the download script first.")
        st.stop()
    G = ox.load_graphml(filepath)
    G_proj = ox.project_graph(G)
    return G, G_proj

G, G_proj = load_local_graph()

st.sidebar.header("Delivery Parameters")
sppg_lat = st.sidebar.number_input("Latitude", value=-7.2819, format="%.4f")
sppg_lon = st.sidebar.number_input("Longitude", value=112.7953, format="%.4f")
radius_km = st.sidebar.slider("Delivery Radius (km)", min_value=0.5, max_value=2.0, value=1.2, step=0.1)
max_schools = st.sidebar.slider("Number of Target Schools", min_value=3, max_value=12, value=6)
solver_type = st.sidebar.radio("TSP Solver Algorithm", ["Exact DP (Held-Karp)", "2-Opt Heuristic", "Both (Benchmark)"])

sppg_node = ox.distance.nearest_nodes(G, sppg_lon, sppg_lat)

candidate_nodes = []
for node, data in G.nodes(data=True):
    if node == sppg_node:
        continue
    dist = ox.distance.great_circle(sppg_lat, sppg_lon, data['y'], data['x']) / 1000.0
    if dist <= radius_km:
        candidate_nodes.append(node)

selected_nodes = [sppg_node] + candidate_nodes[:max_schools]

def compute_distance_matrix(target_nodes):
    n = len(target_nodes)
    dist_matrix = [[0] * n for _ in range(n)]
    path_matrix = [[None] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            try:
                length = nx.shortest_path_length(G_proj, target_nodes[i], target_nodes[j], weight='length')
                path = nx.shortest_path(G_proj, target_nodes[i], target_nodes[j], weight='length')
                dist_matrix[i][j] = length
                path_matrix[i][j] = path
            except nx.NetworkXNoPath:
                dist_matrix[i][j] = float('inf')
                path_matrix[i][j] = []
    return dist_matrix, path_matrix

dist_matrix, path_matrix = compute_distance_matrix(selected_nodes)

def solve_tsp_exact(dist_matrix):
    n = len(dist_matrix)
    memo = {}
    def tsp(mask, u):
        if mask == (1 << n) - 1:
            return dist_matrix[u][0], [u, 0]
        if (mask, u) in memo:
            return memo[(mask, u)]
        min_cost, best_path = float('inf'), []
        for v in range(n):
            if not (mask & (1 << v)):
                cost, path = tsp(mask | (1 << v), v)
                total_cost = dist_matrix[u][v] + cost
                if total_cost < min_cost:
                    min_cost, best_path = total_cost, [u] + path
        memo[(mask, u)] = (min_cost, best_path)
        return min_cost, best_path
    return tsp(1, 0)

def solve_tsp_2opt(dist_matrix):
    n = len(dist_matrix)
    unvisited = set(range(1, n))
    curr, tour = 0, [0]
    while unvisited:
        next_node = min(unvisited, key=lambda x: dist_matrix[curr][x])
        tour.append(next_node)
        unvisited.remove(next_node)
        curr = next_node
    tour.append(0)
    
    def calc_cost(route):
        return sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
    
    improved, best_tour, best_cost = True, tour, calc_cost(tour)
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                new_tour = best_tour[:i] + best_tour[i:j+1][::-1] + best_tour[j+1:]
                new_cost = calc_cost(new_tour)
                if new_cost < best_cost:
                    best_tour, best_cost, improved = new_tour, new_cost, True
                    break
            if improved:
                break
    return best_cost, best_tour

if solver_type == "Exact DP (Held-Karp)":
    t0 = time.time()
    cost, order = solve_tsp_exact(dist_matrix)
    exec_time = time.time() - t0
elif solver_type == "2-Opt Heuristic":
    t0 = time.time()
    cost, order = solve_tsp_2opt(dist_matrix)
    exec_time = time.time() - t0
else:
    t0 = time.time()
    exact_cost, exact_order = solve_tsp_exact(dist_matrix)
    exact_time = time.time() - t0
    
    t0 = time.time()
    opt2_cost, opt2_order = solve_tsp_2opt(dist_matrix)
    opt2_time = time.time() - t0
    
    cost, order, exec_time = exact_cost, exact_order, exact_time

full_route_nodes = []
for idx in range(len(order) - 1):
    u_idx, v_idx = order[idx], order[idx + 1]
    segment_path = path_matrix[u_idx][v_idx]
    if full_route_nodes and segment_path:
        full_route_nodes.extend(segment_path[1:])
    else:
        full_route_nodes.extend(segment_path)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Route Distance", f"{cost / 1000.0:.2f} km")
col2.metric("Est. Travel Time (30 km/h)", f"{(cost / 1000.0) / 30.0 * 60.0:.1f} mins")
col3.metric("Solver Execution Time", f"{exec_time * 1000:.2f} ms")
col4.metric("Target Locations", f"{len(selected_nodes) - 1} Schools")

if solver_type == "Benchmark":
    st.subheader("Results")
    st.dataframe({
        "Algorithm": ["Exact Held-Karp DP", "2-Opt Heuristic"],
        "Route Distance (km)": [f"{exact_cost/1000.0:.3f}", f"{opt2_cost/1000.0:.3f}"],
        "Execution Time (s)": [f"{exact_time:.6f}", f"{opt2_time:.6f}"],
        "Visiting Order": [str(exact_order), str(opt2_order)]
    })

st.subheader("Delivery Sequence")
route_steps = []
for idx_pos, node_idx in enumerate(order):
    if node_idx == 0:
        label = "**SPPG** (Start/End)" if idx_pos == 0 or idx_pos == len(order)-1 else "SPPG"
    else:
        label = f"**Stop #{idx_pos}**: School Node ID `{selected_nodes[node_idx]}`"
    route_steps.append(label)

st.markdown(" ➔ ".join(route_steps))

m = folium.Map(location=[sppg_lat, sppg_lon], zoom_start=14)

folium.Circle(location=[sppg_lat, sppg_lon], radius=radius_km * 1000, color="blue", fill=True, fill_opacity=0.1).add_to(m)

folium.Marker(
    location=[G.nodes[sppg_node]['y'], G.nodes[sppg_node]['x']],
    popup="<b>SPPG</b>",
    icon=folium.Icon(color="red", icon="home")
).add_to(m)

for stop_num, idx in enumerate(order[:-1]):
    if idx == 0:
        continue
    node_id = selected_nodes[idx]
    node_data = G.nodes[node_id]
    folium.Marker(
        location=[node_data['y'], node_data['x']],
        popup=f"Stop #{stop_num}: School Node {node_id}",
        icon=folium.Icon(color="green", icon="info-sign")
    ).add_to(m)

route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in full_route_nodes]
folium.PolyLine(route_coords, color="red", weight=5, opacity=0.8).add_to(m)

st.subheader("Interactive Route Map")
map_data = st_folium(m, width=1100, height=550)

if map_data and map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]
    st.info(f"Picked new SPPG Location from Map Click: Lat {clicked_lat:.4f}, Lon {clicked_lon:.4f}. Update sidebar values to set!")
