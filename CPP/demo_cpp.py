"""
=============================================================================
CHINESE POSTMAN PROBLEM (CPP) - INTERACTIVE CLI & DEMO
=============================================================================
Graph Theory Course Assignment - Institut Teknologi Sepuluh Nopember (ITS)

Use this script to:
1. Demonstrate the Slide 6 benchmark case (Cost = 69) step-by-step.
2. Demonstrate a Directed CPP Digraph with degree balancing.
3. Test custom graph inputs live with Teaching Assistants (TAs).
=============================================================================
"""

import sys
import time
from cpp_solver import solve_undirected_cpp, solve_directed_cpp


def print_banner(title):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)


def run_slide_6_demo():
    print_banner("Task 2: Slide 6 Benchmark Verification")
    print("Graph Specification from Assignment Slide 6:")
    print("  Nodes: A, B, C, D, E")
    print("  Edges:")
    print("    - A to D : 2")
    print("    - C to B : 12")
    print("    - B to E : 17")
    print("    - D to E : 18")
    print("    - B to D : 7")
    print("    - A to C : 6")
    print("-" * 70)
    
    nodes = ['A', 'B', 'C', 'D', 'E']
    edges = [
        ('A', 'D', 2),
        ('C', 'B', 12),
        ('B', 'E', 17),
        ('D', 'E', 18),
        ('B', 'D', 7),
        ('A', 'C', 6)
    ]
    
    t0 = time.perf_counter()
    res = solve_undirected_cpp(nodes, edges, start_node='A')
    t_elapsed = (time.perf_counter() - t0) * 1000

    print("Step 1: Calculate Degrees of Each Node")
    for u, deg in res['degrees'].items():
        parity = "ODD  <-- Needs Pairing!" if deg % 2 != 0 else "EVEN"
        print(f"  Node {u}: degree = {deg} ({parity})")
        
    print(f"\nStep 2: Identify Odd-Degree Vertices")
    print(f"  Odd vertices found: {res['odd_nodes']}")
    
    print(f"\nStep 3: Minimum Weight Perfect Matching")
    print(f"  Matched pairs: {res['matching_pairs']}")
    print(f"  Added duplicate cost: {res['added_cost']}")
    
    print(f"\nStep 4: Hierholzer Eulerian Circuit")
    tour_str = " -> ".join(res['circuit'])
    print(f"  Closed Tour: {tour_str}")
    
    print("\nSummary of Results:")
    print(f"  Original Edges Cost : {res['original_cost']}")
    print(f"  Duplicated Paths    : +{res['added_cost']}")
    print(f"  Total Tour Cost     : {res['total_cost']} (Expected: 69)")
    print(f"  Execution Time      : {t_elapsed:.3f} ms")
    if res['total_cost'] == 69:
        print("  Status              : [SUCCESS] Exact match with Slide 6 illustration!")
    print("=" * 70)


def run_directed_demo():
    print_banner("Directed CPP (Digraph) Demonstration")
    print("Sample Digraph with one-way streets:")
    print("  Nodes: 1, 2, 3")
    print("  Directed Edges:")
    print("    - 1 -> 2 (weight: 10)")
    print("    - 2 -> 3 (weight: 10)")
    print("    - 3 -> 1 (weight: 10)")
    print("    - 1 -> 3 (weight: 5)")
    print("-" * 70)

    nodes = ['1', '2', '3']
    edges = [
        ('1', '2', 10, 'e12', 'Street 1-2'),
        ('2', '3', 10, 'e23', 'Street 2-3'),
        ('3', '1', 10, 'e31', 'Street 3-1'),
        ('1', '3', 5,  'e13', 'Shortcut 1-3')
    ]
    
    t0 = time.perf_counter()
    res = solve_directed_cpp(nodes, edges, start_node='1')
    t_elapsed = (time.perf_counter() - t0) * 1000

    print("Step 1: In-Degree vs Out-Degree Analysis")
    print(f"  Supply nodes (excess incoming, needs outgoing path) : {res['supply_nodes']}")
    print(f"  Demand nodes (excess outgoing, needs incoming path) : {res['demand_nodes']}")
    
    print("\nStep 2: Balance Degrees via Min-Cost Flow / Matching")
    print(f"  Original graph cost : {res['original_cost']}")
    print(f"  Duplication cost    : +{res['added_cost']}")
    print(f"  Total CPP route cost: {res['total_cost']}")
    
    print("\nStep 3: Directed Eulerian Circuit")
    print(f"  Closed Tour: {' -> '.join(res['circuit'])}")
    print(f"  Execution Time: {t_elapsed:.3f} ms")
    print("=" * 70)


def run_custom_interactive():
    print_banner("Custom Graph Solver (For TA Live Demo)")
    print("Choose graph type:")
    print("  1. Undirected Graph")
    print("  2. Directed Graph (Digraph)")
    choice = input("Enter choice (1 or 2): ").strip()
    
    is_directed = (choice == '2')
    print("\nEnter node identifiers separated by spaces (e.g. A B C D E):")
    nodes_line = input("Nodes: ").strip()
    nodes = nodes_line.split() if nodes_line else ['A', 'B', 'C']
    
    print("\nEnter edges one per line in the format: u v weight")
    print("When finished entering edges, enter an empty line.")
    edges = []
    idx = 1
    while True:
        line = input(f"Edge {idx}: ").strip()
        if not line:
            break
        parts = line.split()
        if len(parts) >= 3:
            u, v, w = parts[0], parts[1], float(parts[2])
            edges.append((u, v, w))
            idx += 1
        else:
            print("Invalid format. Please enter: u v weight")
            
    if not edges:
        print("No edges entered. Aborting.")
        return
        
    start_node = input(f"Enter start node (default: {nodes[0]}): ").strip()
    if not start_node or start_node not in nodes:
        start_node = nodes[0]
        
    print("\nSolving Chinese Postman Problem...")
    t0 = time.perf_counter()
    if is_directed:
        res = solve_directed_cpp(nodes, edges, start_node=start_node)
    else:
        res = solve_undirected_cpp(nodes, edges, start_node=start_node)
    elapsed = (time.perf_counter() - t0) * 1000
    
    print("\n" + "=" * 40)
    print("RESULT:")
    print(f"Eulerian Tour: {' -> '.join(res['circuit'])}")
    print(f"Original Edge Sum: {res['original_cost']}")
    print(f"Added Length: {res['added_cost']}")
    print(f"Total Closed Tour Cost: {res['total_cost']}")
    print(f"Computation Time: {elapsed:.3f} ms")
    print("=" * 40)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--slide6', '-s']:
            run_slide_6_demo()
            return
        elif arg in ['--directed', '-d']:
            run_directed_demo()
            return
        elif arg in ['--custom', '-c']:
            run_custom_interactive()
            return

    while True:
        print_banner("CHINESE POSTMAN PROBLEM (CPP) SOLVER")
        print("1. Run Slide 6 Benchmark Test (Cost: 69)")
        print("2. Run Directed Graph (Digraph) Example")
        print("3. Input Custom Graph (TA Live Demo Mode)")
        print("4. Exit")
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == '1':
            run_slide_6_demo()
        elif choice == '2':
            run_directed_demo()
        elif choice == '3':
            run_custom_interactive()
        elif choice == '4':
            print("Exiting. Good luck with the submission!")
            break
        else:
            print("Invalid choice, please select 1-4.")


if __name__ == '__main__':
    main()
