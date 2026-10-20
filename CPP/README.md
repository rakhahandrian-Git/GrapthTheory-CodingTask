# Task 2: Chinese Postman Problem (CPP) & DLH Surabaya Simulator

## 1. Overview

The Chinese Postman Problem (CPP) finds the shortest closed walk (tour) that traverses every edge of a graph at least once and returns to the starting vertex.

This task provides:
1. `cpp_solver.py`: Modular solver supporting:
   - Undirected graphs (minimum-weight perfect matching on odd-degree vertices).
   - Directed graphs (digraphs balanced via minimum-cost network flow).
   - Hierholzer's algorithm for linear Eulerian circuit extraction.
2. `dlh_simulator.py`: Surabaya dump truck simulator engine loading real OpenStreetMap road networks, filtering Strongly Connected Components (SCC), and generating closed collection routes.
3. `app.py`: Interactive Flask web application with Google Satellite GIS view and a Vis.js Custom Graph Playground.
4. `demo_cpp.py`: Interactive CLI tool for testing and the Week 7 Teaching Assistant (TA) live evaluation.

---

## 2. Prerequisites & Installation

### Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`:
  - `Flask`
  - `networkx`
  - `requests`

### Installation
```bash
pip install -r requirements.txt
```

---

## 3. How to Run

### 1. Interactive Web Application
Start the local server:
```bash
python app.py
```
Open in browser:
```
http://127.0.0.1:5000
```

Modes available:
- **DLH Surabaya Map Simulator**: Select dump truck base location, adjust delivery radius (0.5 km to 3.0 km), calculate optimal CPP tour, and play traversal animation.
- **Custom Graph Playground**: Input arbitrary graphs (undirected or directed), run instant presets, and inspect physics diagrams with step-by-step tour playback.

---

### 2. CLI Tool (TA Live Evaluation)
Run the interactive CLI:
```bash
python demo_cpp.py
```

Shortcut flags:
- **Slide 6 Verification (Cost: 69):**
  ```bash
  python demo_cpp.py --slide6
  ```
- **Directed Graph (Digraph) Demo:**
  ```bash
  python demo_cpp.py --directed
  ```
- **Interactive Custom Graph Input:**
  ```bash
  python demo_cpp.py --custom
  ```

---

## 4. Sample Cases

### Scenario A: Lecture Slide 6 Benchmark
- **Graph:** Vertices `A, B, C, D, E`
- **Edges & Weights:**
  - `(A, D): 2`, `(C, B): 12`, `(B, E): 17`, `(D, E): 18`, `(B, D): 7`, `(A, C): 6`
  - Total original edges cost: $62$
- **Odd Vertices:** `B` (degree 3) and `D` (degree 3)
- **Shortest Path:** Direct edge `(B, D)` with weight 7
- **Duplicated Path:** `(B, D)` (+7)
- **Eulerian Circuit:** `A -> C -> B -> D -> B -> E -> D -> A`
- **Total Tour Cost:** $62 + 7 = 69\text{ meters}$ (Exact match with Slide 6 illustration)

Verification command:
```bash
python demo_cpp.py --slide6
```

---

### Scenario B: Directed Graph Imbalance (Slide 7 DLH Simulator)
- **Graph Type:** Directed Multigraph (Digraph)
- **Condition:** In-degree equals out-degree for all vertices ($d_{\text{in}}(v) = d_{\text{out}}(v)$).
- **Optimization:** Vertices with $d_{\text{in}} > d_{\text{out}}$ (Supply) route flow to vertices with $d_{\text{out}} > d_{\text{in}}$ (Demand) via directed Dijkstra shortest paths and Min-Cost Flow.
- **Tour Extraction:** Directed Hierholzer traversal starting and ending at the depot.

Verification command:
```bash
python demo_cpp.py --directed
```

---

### Scenario C: Custom Graph Live Evaluation
TAs can test arbitrary graphs during the live demo session using either:
1. Terminal input:
   ```bash
   python demo_cpp.py --custom
   ```
2. Web interface: Open `http://127.0.0.1:5000` and switch to the **Custom Graph Playground** tab.

---

## 5. Computational Complexity Analysis

Let $|V|$ = number of vertices, $|E|$ = number of edges, and $k$ = number of unbalanced / odd vertices ($k \ll |V|$):

| Phase | Algorithm | Time Complexity | Space Complexity | Description |
|---|---|---|---|---|
| **Graph Construction** | Adjacency List | $O(\|V\| + \|E\|)$ | $O(\|V\| + \|E\|)$ | Degree counting and graph initialization |
| **Shortest Paths** | Dijkstra (Binary Heap) | $O(k \cdot (\|E\| + \|V\| \log \|V\|))$ | $O(\|V\|)$ | All-pairs paths between unbalanced nodes |
| **Balancing** | MWPM / Min-Cost Flow | $O(k^3)$ (Undirected) / $O(k^2 \log k)$ (Directed) | $O(k^2)$ | Minimum added distance matching |
| **Eulerian Circuit** | Hierholzer's Algorithm | $O(\|E_{\text{total}}\|)$ | $O(\|V\| + \|E_{\text{total}}\|)$ | Linear multigraph edge traversal |
| **Overall Pipeline** | Complete Solver | $O(k \cdot \|E\| + k^3)$ | $O(\|V\| + \|E\|)$ | Polynomial time; solves in $< 20\text{ ms}$ |
