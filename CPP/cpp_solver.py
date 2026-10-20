"""
=============================================================================
CHINESE POSTMAN PROBLEM (CPP) SOLVER
=============================================================================
Graph Theory Course Assignment - Institut Teknologi Sepuluh Nopember (ITS)

This module provides clean, easy-to-understand solutions for:
1. Undirected Chinese Postman Problem (matching odd-degree vertices)
2. Directed Chinese Postman Problem (balancing in/out-degrees via min-cost flow)
3. Hierholzer's Algorithm for constructing Eulerian circuits
=============================================================================
"""

import heapq
from collections import defaultdict, deque
import networkx as nx


# ---------------------------------------------------------------------------
# HELPER: DIJKSTRA'S SHORTEST PATH ALGORITHM
# ---------------------------------------------------------------------------

def dijkstra(nodes, adj, start_node):
    """
    Finds the shortest path from start_node to all other reachable nodes.
    
    Parameters:
        nodes: Iterable of node identifiers.
        adj: Dictionary mapping node u -> list of (neighbor v, weight, edge_id).
        start_node: The source node.
        
    Returns:
        dist: Dictionary mapping node v -> shortest distance from start_node.
        parent: Dictionary mapping node v -> previous node on shortest path.
        parent_edge: Dictionary mapping node v -> edge_id used to reach v.
    """
    dist = {u: float('inf') for u in nodes}
    parent = {u: None for u in nodes}
    parent_edge = {u: None for u in nodes}
    
    dist[start_node] = 0
    # Priority queue stores tuples of (current_distance, node)
    pq = [(0, start_node)]
    
    while pq:
        current_dist, u = heapq.heappop(pq)
        
        # If we already found a shorter path to u, skip
        if current_dist > dist[u]:
            continue
            
        for v, weight, edge_id in adj.get(u, []):
            new_dist = current_dist + weight
            if new_dist < dist[v]:
                dist[v] = new_dist
                parent[v] = u
                parent_edge[v] = edge_id
                heapq.heappush(pq, (new_dist, v))
                
    return dist, parent, parent_edge


def reconstruct_path_edges(u, v, parent, parent_edge):
    """
    Reconstructs the list of edges along the shortest path from u to v.
    Returns: list of (from_node, to_node, edge_id) or None if unreachable.
    """
    edges = []
    curr = v
    while curr != u:
        p = parent.get(curr)
        if p is None:
            return None
        edges.append((p, curr, parent_edge[curr]))
        curr = p
    edges.reverse()
    return edges


# ---------------------------------------------------------------------------
# 1. UNDIRECTED CHINESE POSTMAN PROBLEM
# ---------------------------------------------------------------------------

def solve_undirected_cpp(nodes, edges, start_node=None):
    """
    Solves the Chinese Postman Problem on an undirected graph.
    
    Algorithm Steps:
    1. Calculate degree of every vertex.
    2. Identify vertices with odd degrees (by Handshaking Lemma, count is even).
    3. If no odd vertices, graph is Eulerian -> find circuit directly.
    4. If odd vertices exist, compute shortest path between all pairs of odd vertices.
    5. Find minimum-weight perfect matching among odd vertices.
    6. Duplicate the edges on the shortest paths corresponding to the matching.
    7. All vertices now have even degrees! Run Hierholzer's Algorithm to find
       the optimal closed Eulerian circuit traversing every edge.
       
    Parameters:
        nodes: List of node names (e.g. ['A', 'B', 'C', 'D', 'E'])
        edges: List of tuples (u, v, weight) or (u, v, weight, name/id)
        start_node: Optional starting vertex for the circuit.
        
    Returns:
        dict containing:
            'circuit': List of node names in traversal order
            'total_cost': Total distance of the tour
            'original_cost': Sum of original edge weights
            'added_cost': Extra distance from duplicated edges
            'odd_nodes': List of odd-degree vertices
            'matching_pairs': Pairs of odd vertices matched
    """
    # Step 1: Build graph and count degrees
    adj = defaultdict(list)
    edge_info = {}
    degree = {u: 0 for u in nodes}
    total_original_cost = 0
    
    for idx, edge in enumerate(edges):
        u, v, w = edge[0], edge[1], edge[2]
        eid = edge[3] if len(edge) > 3 else f"e_{idx}_{u}_{v}"
        adj[u].append((v, w, eid))
        adj[v].append((u, w, eid))
        edge_info[eid] = (u, v, w)
        degree[u] += 1
        degree[v] += 1
        total_original_cost += w
        
    if start_node is None:
        start_node = nodes[0]

    # Step 2: Find odd-degree vertices
    odd_nodes = [u for u in nodes if degree[u] % 2 != 0]

    # Step 3: Compute shortest paths between all pairs of odd vertices
    sp_dist = {}
    sp_edges = {}
    for u in odd_nodes:
        dist, parent, p_edge = dijkstra(nodes, adj, u)
        for v in odd_nodes:
            if u != v:
                sp_dist[(u, v)] = dist[v]
                sp_edges[(u, v)] = reconstruct_path_edges(u, v, parent, p_edge)

    # Step 4: Minimum Weight Perfect Matching on odd vertices
    # Since odd_nodes count is usually small (2, 4, 6, etc.), recursion with memoization is fast & exact.
    memo = {}
    def min_matching(remaining):
        rem_tuple = tuple(sorted(remaining))
        if not remaining:
            return 0, []
        if rem_tuple in memo:
            return memo[rem_tuple]
            
        first = remaining[0]
        best_cost = float('inf')
        best_pairs = []
        
        for i in range(1, len(remaining)):
            other = remaining[i]
            pair_cost = sp_dist.get((first, other), float('inf'))
            rest = [remaining[j] for j in range(1, len(remaining)) if j != i]
            sub_cost, sub_pairs = min_matching(rest)
            
            if pair_cost + sub_cost < best_cost:
                best_cost = pair_cost + sub_cost
                best_pairs = [(first, other)] + sub_pairs
                
        memo[rem_tuple] = (best_cost, best_pairs)
        return memo[rem_tuple]

    added_cost, matching_pairs = min_matching(odd_nodes)
    
    # Step 5: Duplicate edges to form an Eulerian multigraph
    # multi_adj stores list of (neighbor, weight, unique_edge_id)
    multi_adj = defaultdict(list)
    # Add original edges
    for eid, (u, v, w) in edge_info.items():
        multi_adj[u].append((v, w, eid))
        multi_adj[v].append((u, w, eid))
        
    # Add duplicated edges along matching paths
    dup_id = 0
    duplicated_edge_list = []
    for u, v in matching_pairs:
        path = sp_edges.get((u, v), [])
        for pu, pv, peid in path:
            pw = edge_info[peid][2]
            new_eid = f"dup_{dup_id}_{peid}"
            dup_id += 1
            multi_adj[pu].append((pv, pw, new_eid))
            multi_adj[pv].append((pu, pw, new_eid))
            duplicated_edge_list.append((pu, pv, pw, new_eid))

    # Step 6: Hierholzer's Algorithm for undirected multigraph
    used_edges = defaultdict(int)
    local_adj = {u: list(multi_adj[u]) for u in multi_adj}
    
    stack = [start_node]
    circuit = []
    
    while stack:
        curr = stack[-1]
        found_edge = False
        while local_adj[curr]:
            nxt, w, eid = local_adj[curr].pop()
            if used_edges[eid] < 1:
                used_edges[eid] += 1
                stack.append(nxt)
                found_edge = True
                break
        if not found_edge:
            circuit.append(stack.pop())
            
    circuit.reverse()
    
    return {
        'circuit': circuit,
        'total_cost': total_original_cost + added_cost,
        'original_cost': total_original_cost,
        'added_cost': added_cost,
        'odd_nodes': odd_nodes,
        'matching_pairs': matching_pairs,
        'degrees': degree,
        'duplicated_edges': [{'u': u, 'v': v, 'weight': w, 'id': eid} for u, v, w, eid in duplicated_edge_list]
    }


# ---------------------------------------------------------------------------
# 2. DIRECTED CHINESE POSTMAN PROBLEM (DIGRAPH)
# ---------------------------------------------------------------------------

def solve_directed_cpp(nodes, edges, start_node=None):
    """
    Solves the Chinese Postman Problem on a strongly connected directed graph (Digraph).
    
    Algorithm Steps:
    1. Calculate in-degree and out-degree for each vertex.
    2. Compute delta = in_degree - out_degree for each vertex:
       - If delta > 0: Excess incoming edges (supply node, needs outgoing path).
       - If delta < 0: Excess outgoing edges (demand node, needs incoming path).
    3. If all vertices are balanced (delta == 0), graph is Eulerian.
    4. If unbalanced vertices exist, compute shortest directed paths from
       supply nodes (delta > 0) to demand nodes (delta < 0).
    5. Formulate as a Minimum-Cost Flow / Transportation Problem to find the optimal
       number of paths to send from each supply to each demand node with minimum cost.
    6. Duplicate the edges along the chosen shortest paths in the multigraph.
    7. All vertices now have in_degree == out_degree! Run Hierholzer's Algorithm
       for directed graphs to find the closed Eulerian circuit.
       
    Parameters:
        nodes: List of node identifiers
        edges: List of tuples (u, v, weight, name/id) representing directed edges u -> v.
        start_node: Optional starting node for the tour.
        
    Returns:
        dict containing:
            'circuit': List of nodes in traversal order
            'circuit_edges': List of (u, v, weight, edge_id, name) traversed
            'total_cost': Total route distance
            'original_cost': Sum of original edge weights
            'added_cost': Cost of duplicated road segments
            'supply_nodes': Dict of nodes with surplus in-degree
            'demand_nodes': Dict of nodes with surplus out-degree
    """
    in_deg = defaultdict(int)
    out_deg = defaultdict(int)
    adj = defaultdict(list)
    edge_dict = {}
    total_original_cost = 0
    
    all_nodes = set(nodes)
    for edge in edges:
        u, v, w = edge[0], edge[1], edge[2]
        eid = edge[3] if len(edge) > 3 else f"e_{u}_{v}"
        name = edge[4] if len(edge) > 4 else "Road"
        
        all_nodes.add(u)
        all_nodes.add(v)
        out_deg[u] += 1
        in_deg[v] += 1
        adj[u].append((v, w, eid))
        edge_dict[eid] = (u, v, w, name)
        total_original_cost += w
        
    all_nodes = list(all_nodes)
    if start_node is None:
        start_node = all_nodes[0]

    # Step 2: Identify supply and demand nodes
    # supply: in_degree > out_degree (needs to send out flow to balance)
    # demand: out_degree > in_degree (needs to receive in flow to balance)
    supply_nodes = {}
    demand_nodes = {}
    for u in all_nodes:
        diff = in_deg[u] - out_deg[u]
        if diff > 0:
            supply_nodes[u] = diff
        elif diff < 0:
            demand_nodes[u] = -diff

    # Step 3: Compute shortest paths from each supply node to all demand nodes
    sp_dist = {}
    sp_edges = {}
    
    for s in supply_nodes:
        dist, parent, p_edge = dijkstra(all_nodes, adj, s)
        for t in demand_nodes:
            if dist[t] < float('inf'):
                sp_dist[(s, t)] = dist[t]
                sp_edges[(s, t)] = reconstruct_path_edges(s, t, parent, p_edge)

    # Step 4: Min-Cost Flow to match supply to demand
    added_cost = 0
    duplicated_edges = []
    
    if supply_nodes and demand_nodes:
        flow_g = nx.DiGraph()
        # In NetworkX: demand < 0 is supply, demand > 0 is demand
        for s, amount in supply_nodes.items():
            flow_g.add_node(f"s_{s}", demand=-amount)
        for t, amount in demand_nodes.items():
            flow_g.add_node(f"t_{t}", demand=amount)
            
        for s in supply_nodes:
            for t in demand_nodes:
                if (s, t) in sp_dist:
                    cost_val = int(round(sp_dist[(s, t)] * 1000))
                    flow_g.add_edge(f"s_{s}", f"t_{t}", weight=cost_val, capacity=min(supply_nodes[s], demand_nodes[t]))
                    
        flow_dict = nx.min_cost_flow(flow_g)
        
        # Step 5: Duplicate shortest path edges based on flow solution
        dup_count = 0
        for s in supply_nodes:
            for t in demand_nodes:
                amount = flow_dict.get(f"s_{s}", {}).get(f"t_{t}", 0)
                if amount > 0:
                    added_cost += amount * sp_dist[(s, t)]
                    for _ in range(amount):
                        for pu, pv, peid in sp_edges[(s, t)]:
                            pw, pname = edge_dict[peid][2], edge_dict[peid][3]
                            new_eid = f"dup_{dup_count}_{peid}"
                            dup_count += 1
                            duplicated_edges.append((pu, pv, pw, new_eid, f"{pname} (Revisit)"))

    # Step 6: Construct directed Eulerian multigraph
    multi_adj = defaultdict(list)
    # Original edges
    for edge in edges:
        u, v, w = edge[0], edge[1], edge[2]
        eid = edge[3] if len(edge) > 3 else f"e_{u}_{v}"
        name = edge[4] if len(edge) > 4 else "Road"
        multi_adj[u].append((v, w, eid, name))
        
    # Duplicated edges
    for u, v, w, eid, name in duplicated_edges:
        multi_adj[u].append((v, w, eid, name))

    # Step 7: Hierholzer's Algorithm for directed multigraph
    # Copy adjacency lists
    curr_adj = {u: list(neighbors) for u, neighbors in multi_adj.items()}
    
    # If chosen start_node has no outgoing edges in multi_adj, pick one that does
    if start_node not in curr_adj or not curr_adj[start_node]:
        for candidate in curr_adj:
            if curr_adj[candidate]:
                start_node = candidate
                break

    stack = [start_node]
    circuit = []
    circuit_edges = []
    edge_stack = []

    while stack:
        curr = stack[-1]
        if curr_adj.get(curr):
            nxt_v, w, eid, name = curr_adj[curr].pop()
            stack.append(nxt_v)
            edge_stack.append((curr, nxt_v, w, eid, name))
        else:
            circuit.append(stack.pop())
            if edge_stack:
                circuit_edges.append(edge_stack.pop())

    circuit.reverse()
    circuit_edges.reverse()

    return {
        'circuit': circuit,
        'circuit_edges': circuit_edges,
        'total_cost': total_original_cost + added_cost,
        'original_cost': total_original_cost,
        'added_cost': added_cost,
        'supply_nodes': supply_nodes,
        'demand_nodes': demand_nodes,
        'in_degrees': dict(in_deg),
        'out_degrees': dict(out_deg),
        'duplicated_edges': [{'u': u, 'v': v, 'weight': w, 'id': eid, 'name': name} for u, v, w, eid, name in duplicated_edges],
        'start_node': start_node
    }
