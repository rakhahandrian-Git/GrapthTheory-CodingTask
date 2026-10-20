"""
=============================================================================
DLH SIMULATOR - CHINESE POSTMAN PROBLEM FOR GARBAGE COLLECTION
=============================================================================
Task 2 Requirements (Slide 7):
1. Road network of Surabaya from OSM treated as a Digraph.
2. Interactive capability: pick dump truck base & adjust radius x km.
3. Efficient CPP route starting and ending at dump truck base, visiting every
   trunk, primary, secondary, and tertiary road within radius x km.
4. Output: Route overlay, street traversal order, distance, travel time, execution time.
=============================================================================
"""

import json
import math
import os
import time
from collections import defaultdict
import networkx as nx
from cpp_solver import solve_directed_cpp


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Computes great-circle distance between two GPS points in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class DLHSimulator:
    def __init__(self, dataset_path="surabaya_roads.json"):
        self.dataset_path = dataset_path
        self.nodes = {}
        self.ways = []
        self.load_dataset()

    def load_dataset(self):
        """Loads Surabaya road network dataset."""
        if not os.path.exists(self.dataset_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(script_dir, self.dataset_path)
            if os.path.exists(alt_path):
                self.dataset_path = alt_path
            else:
                raise FileNotFoundError(f"Dataset {self.dataset_path} not found!")
            
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.nodes = {int(k): (v[0], v[1]) for k, v in data.get("nodes", {}).items()}
        self.ways = data.get("ways", [])
        print(f"[DLHSimulator] Loaded {len(self.ways)} ways and {len(self.nodes)} nodes from {self.dataset_path}")

    def find_closest_node(self, lat, lon):
        """Finds the nearest road network node to a given lat/lon."""
        best_node = None
        min_d = float('inf')
        for nid, (nlat, nlon) in self.nodes.items():
            d = haversine_distance(lat, lon, nlat, nlon)
            if d < min_d:
                min_d = d
                best_node = nid
        return best_node, min_d

    def simulate(self, base_lat, base_lon, radius_km, truck_speed_kmh=25.0):
        """
        Runs the full DLH Simulator pipeline:
        1. Identifies the closest road node to the dump truck base.
        2. Filters trunk, primary, secondary, tertiary roads within radius_km.
        3. Extracts the connected road component containing the base.
        4. Solves Directed CPP (Digraph) using min-cost flow & Hierholzer.
        5. Computes traversal order, distances, travel time, and route coordinates.
        """
        start_time = time.perf_counter()
        radius_m = radius_km * 1000.0

        # Step 1: Find closest node to base
        closest_node, base_to_road_dist = self.find_closest_node(base_lat, base_lon)
        if closest_node is None:
            return {"error": "No road network nodes found."}

        # Step 2: Filter roads within radius
        target_types = {
            "trunk", "primary", "secondary", "tertiary",
            "trunk_link", "primary_link", "secondary_link", "tertiary_link"
        }
        
        edges = []
        node_coords = {}
        
        for way in self.ways:
            hw = way.get("highway", "")
            if hw not in target_types:
                continue
                
            w_nodes = [nid for nid in way.get("nodes", []) if nid in self.nodes]
            if len(w_nodes) < 2:
                continue
                
            # Keep way if any node falls within radius of base
            in_radius = any(haversine_distance(base_lat, base_lon, self.nodes[nid][0], self.nodes[nid][1]) <= radius_m for nid in w_nodes)
            if not in_radius:
                continue
                
            w_name = way.get("name") or f"Jalan {hw.replace('_', ' ').title()}"
            is_oneway = way.get("oneway", False)
            
            for i in range(len(w_nodes) - 1):
                u, v = w_nodes[i], w_nodes[i+1]
                u_lat, u_lon = self.nodes[u]
                v_lat, v_lon = self.nodes[v]
                seg_dist = haversine_distance(u_lat, u_lon, v_lat, v_lon)
                
                # Directed edge u -> v
                eid_fwd = f"w_{way['id']}_{u}_{v}"
                edges.append((u, v, seg_dist, eid_fwd, w_name))
                node_coords[u] = (u_lat, u_lon)
                node_coords[v] = (v_lat, v_lon)
                
                # If two-way street, add v -> u
                if not is_oneway:
                    eid_rev = f"w_{way['id']}_{v}_{u}_rev"
                    edges.append((v, u, seg_dist, eid_rev, w_name))

        if not edges:
            return {
                "error": f"No trunk, primary, secondary, or tertiary roads found within {radius_km} km of the selected location."
            }

        # Step 3: Handle connectivity
        # "If a road segment not connected to the graph where the dump truck base located, you may ignore it"
        G = nx.DiGraph()
        for u, v, w, eid, name in edges:
            G.add_edge(u, v, weight=w, id=eid, name=name)

        sccs = list(nx.strongly_connected_components(G))
        base_scc = None
        for scc in sccs:
            if closest_node in scc:
                base_scc = scc
                break

        # Fallback if closest_node was in an isolated segment: pick largest reachable component
        if not base_scc or len(base_scc) < 2:
            base_scc = max(sccs, key=len)
            closest_node = list(base_scc)[0]

        subG = G.subgraph(base_scc).copy()
        filtered_edges = [
            (u, v, data['weight'], data['id'], data['name'])
            for u, v, data in subG.edges(data=True)
        ]
        
        filtered_nodes = list(subG.nodes())

        # Step 4: Solve Directed Chinese Postman Problem
        cpp_result = solve_directed_cpp(filtered_nodes, filtered_edges, start_node=closest_node)
        
        solver_exec_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 5: Format metrics and traversal list
        total_dist_m = cpp_result['total_cost']
        total_dist_km = total_dist_m / 1000.0
        orig_dist_km = cpp_result['original_cost'] / 1000.0
        dup_dist_km = cpp_result['added_cost'] / 1000.0
        
        travel_time_hours = total_dist_km / truck_speed_kmh
        travel_time_min = travel_time_hours * 60.0

        # Reconstruct route GPS coordinates and street traversal sequence
        route_coords = []
        traversal_order = []
        
        circuit_nodes = cpp_result['circuit']
        circuit_edges = cpp_result.get('circuit_edges', [])
        
        # Coordinates path for map polyline
        for nid in circuit_nodes:
            if nid in self.nodes:
                route_coords.append([self.nodes[nid][0], self.nodes[nid][1]])
                
        # Group sequential segments by street name for readable presentation
        step_idx = 1
        for u, v, w, eid, name in circuit_edges:
            is_revisit = "(Revisit)" in name or "dup_" in str(eid)
            clean_name = name.replace(" (Revisit)", "")
            traversal_order.append({
                "step": step_idx,
                "street": clean_name,
                "distance_m": round(w, 1),
                "is_revisit": is_revisit,
                "from_node": u,
                "to_node": v
            })
            step_idx += 1

        # Collect network road lines for background display
        network_lines = []
        for u, v, data in subG.edges(data=True):
            if u in self.nodes and v in self.nodes:
                network_lines.append({
                    "coords": [
                        [self.nodes[u][0], self.nodes[u][1]],
                        [self.nodes[v][0], self.nodes[v][1]]
                    ],
                    "name": data.get("name", "Road")
                })

        return {
            "success": True,
            "base_location": {"lat": base_lat, "lon": base_lon},
            "nearest_node": {
                "id": closest_node,
                "lat": self.nodes[closest_node][0],
                "lon": self.nodes[closest_node][1],
                "dist_to_base_m": round(base_to_road_dist, 1)
            },
            "radius_km": radius_km,
            "metrics": {
                "total_distance_km": round(total_dist_km, 2),
                "original_distance_km": round(orig_dist_km, 2),
                "duplicated_distance_km": round(dup_dist_km, 2),
                "estimated_time_minutes": round(travel_time_min, 1),
                "estimated_speed_kmh": truck_speed_kmh,
                "solver_time_ms": round(solver_exec_ms, 2),
                "road_segments_count": len(filtered_edges),
                "total_traversals": len(circuit_edges),
                "unique_nodes_count": len(filtered_nodes)
            },
            "route_coords": route_coords,
            "network_lines": network_lines,
            "traversal_order": traversal_order
        }
