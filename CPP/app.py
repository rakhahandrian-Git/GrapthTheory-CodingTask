"""
=============================================================================
DLH SURABAYA - DUMP TRUCK CPP ROUTE SIMULATOR (WEB APPLICATION)
=============================================================================
Flask Backend providing the interactive map and Chinese Postman Problem solver.
=============================================================================
"""

import os
import time
from flask import Flask, render_template, request, jsonify
from dlh_simulator import DLHSimulator
from cpp_solver import solve_undirected_cpp, solve_directed_cpp

app = Flask(__name__)

# Initialize simulator with Surabaya road network
simulator = DLHSimulator("surabaya_roads.json")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """
    API endpoint to run DLH Simulator on user-selected location and radius.
    """
    try:
        data = request.get_json() or {}
        lat = float(data.get("lat", -7.280))
        lon = float(data.get("lon", 112.795))
        radius_km = float(data.get("radius_km", 1.0))
        speed_kmh = float(data.get("speed_kmh", 25.0))

        # Restrict radius to reasonable bounds
        radius_km = max(0.3, min(radius_km, 4.0))

        result = simulator.simulate(lat, lon, radius_km, speed_kmh)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/slide6", methods=["GET"])
def slide6_benchmark():
    """
    API endpoint returning solution for the Slide 6 benchmark example.
    """
    nodes = ['A', 'B', 'C', 'D', 'E']
    edges = [
        ('A', 'D', 2),
        ('C', 'B', 12),
        ('B', 'E', 17),
        ('D', 'E', 18),
        ('B', 'D', 7),
        ('A', 'C', 6)
    ]
    res = solve_undirected_cpp(nodes, edges, start_node='A')
    return jsonify({
        "success": True,
        "nodes": nodes,
        "edges": [{"u": u, "v": v, "w": w} for u, v, w in edges],
        "result": res
    })


@app.route("/api/solve-custom", methods=["POST"])
def solve_custom():
    """
    Solves Chinese Postman Problem for any custom graph (directed or undirected).
    """
    try:
        data = request.get_json() or {}
        is_directed = bool(data.get("is_directed", False))
        edges_raw = data.get("edges", [])
        start_node = data.get("start_node", None)

        edges = []
        nodes_set = set()
        for idx, e in enumerate(edges_raw):
            if isinstance(e, dict):
                u = str(e.get("u", "")).strip()
                v = str(e.get("v", "")).strip()
                w = float(e.get("weight", 1.0))
                name = str(e.get("name", f"e_{u}_{v}")).strip()
            elif isinstance(e, (list, tuple)):
                u = str(e[0]).strip()
                v = str(e[1]).strip()
                w = float(e[2])
                name = str(e[3]) if len(e) > 3 else f"e_{u}_{v}"
            else:
                continue
            if u and v:
                edges.append((u, v, w, name))
                nodes_set.add(u)
                nodes_set.add(v)

        nodes = sorted(list(nodes_set))
        if not nodes:
            return jsonify({"success": False, "error": "No valid edges found in graph input."}), 400

        if not start_node or start_node not in nodes_set:
            start_node = nodes[0]

        t0 = time.perf_counter()
        if is_directed:
            res = solve_directed_cpp(nodes, edges, start_node=start_node)
        else:
            res = solve_undirected_cpp(nodes, edges, start_node=start_node)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return jsonify({
            "success": True,
            "is_directed": is_directed,
            "nodes": nodes,
            "edges": [{"u": u, "v": v, "weight": w, "name": name} for u, v, w, name in edges],
            "result": res,
            "elapsed_ms": round(elapsed_ms, 3)
        })
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print(" [DLH SURABAYA SIMULATOR] Starting Web Server...")
    print(" Open your browser and navigate to: http://127.0.0.1:5000")
    print("=" * 65 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
