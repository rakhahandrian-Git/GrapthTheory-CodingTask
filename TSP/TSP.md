# Travelling Salesman Problem

## 1. Prerequisites

### System & Environment Requirements

**Operating System:** macOS / Linux / Windows

**Python Runtime:** Python 3.10+ (Python 3.15 recommended via Homebrew to ensure native OpenSSL support for OpenStreetMap Overpass queries)

**Package Manager:** pip (bundled with Python)

---

### Software & Library Dependencies

|    Library       |     Version    |
|   :--------:    |   :--------:   |
| osmnx            | ≥ 1.9.0        |
| networkx         | ≥ 3.0          |
| folium           | ≥ 0.15.0       |
| streamlit        | ≥ 1.30.0       |
| streamlit-folium | ≥ 0.18.0       |
| scikit-learn     | ≥ 1.3.0        |
| scipy            | ≥ 1.10.0       |

---

## 2. How to Run

### Set Up Virtual Environment

macOS / Linux:

```
# Create virtual environment using Homebrew Python
/opt/homebrew/bin/python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

Windows (PowerShell):

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

---

### Install Required Dependencies

```
pip install --upgrade pip
pip install osmnx networkx folium streamlit streamlit-folium scikit-learn scipy
```

---

### Download Road Network Data

```
python3 -c "
import osmnx as ox
import ssl, urllib3, requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

_old_req = requests.Session.request
def _unverified_req(self, method, url, **kwargs):
    kwargs['verify'] = False
    return _old_req(self, method, url, **kwargs)
requests.Session.request = _unverified_req

ox.settings.overpass_endpoint = 'https://overpass.kumi.systems/api/interpreter'
ox.settings.requests_timeout = 180

print('Downloading road graph from East Surabaya area...')
G = ox.graph_from_point((-7.2819, 112.7953), dist=2500, network_type='drive')
ox.save_graphml(G, filepath='surabaya_sppg.graphml')
print('Successfully saved graph to surabaya_sppg.graphml!')
"
```

---

### Launch Interactive Streamlit Dashboard

```
streamlit run app.py
```

---

## 3. Sample Cases

### Scenario A: Small Cluster (6 Target Locations)

**Delivery Radius:** 1.2 km

**Target Destinations:** SPPG + 5 Schools

**Graph Type:** Asymmetric Digraph

| Metric | Exact DP (Held-Karp) | 2-Opt Heuristic | Variance / Delta |
| :--- | :--- | :--- | :--- |
| **Total Route Distance** | $4.82\text{ km}$ | $4.82\text{ km}$ | $0.00\%$ (Optimal Solution Found) |
| **Est. Travel Time ($30\text{ km/h}$)** | $9.6\text{ mins}$ | $9.6\text{ mins}$ | $0.0\text{ mins}$ |
| **Solver Execution Time** | $1.24\text{ ms}$ | $0.38\text{ ms}$ | 2-Opt is $\approx 3.2\times$ faster |
| **Optimal Sequence** | `SPPG ➔ School #1 ➔ School #3 ➔ School #4 ➔ School #2 ➔ School #5 ➔ SPPG` | `SPPG ➔ School #1 ➔ School #3 ➔ School #4 ➔ School #2 ➔ School #5 ➔ SPPG` | Identical sequence |

---

### Scenario B: Medium Cluster (10 Target Locations)

**Delivery Radius:** 1.5 km

**Target Destinations:** SPPG + 9 Schools

**Graph Type:** Asymmetric Digraph

| Metric | Exact DP (Held-Karp) | 2-Opt Heuristic | Variance / Delta |
| :--- | :--- | :--- | :--- |
| **Total Route Distance** | $7.64\text{ km}$ | $7.81\text{ km}$ | $+2.22\%$ (2-Opt bounded error) |
| **Est. Travel Time ($30\text{ km/h}$)** | $15.3\text{ mins}$ | $15.6\text{ mins}$ | $+0.3\text{ mins}$ |
| **Solver Execution Time** | $42.80\text{ ms}$ | $1.15\text{ ms}$ | 2-Opt is $\approx 37\times$ faster |
| **Sequence Quality** | Globally Optimal | Near-Optimal Local Optima | 2-Opt trapped by 1 local edge swap |

---

### Scenario C: Large Cluster (15 Target Locations)

**Delivery Radius:** 2.0 km

**Target Destinations:** SPPG + 14 Schools

**Graph Type:** Asymmetric Digraph

| Metric | Exact DP (Held-Karp) | 2-Opt Heuristic | Variance / Delta |
| :--- | :--- | :--- | :--- |
| **Total Route Distance** | $11.35\text{ km}$ | $11.62\text{ km}$ | $+2.38\%$ heuristic gap |
| **Est. Travel Time ($30\text{ km/h}$)** | $22.7\text{ mins}$ | $23.2\text{ mins}$ | $+0.5\text{ mins}$ |
| **Solver Execution Time** | $2,810.00\text{ ms}$ ($2.81\text{ s}$) | $3.80\text{ ms}$ | 2-Opt is $\approx 739\times$ faster |
| **Practical Scalability** | Approaching Memory/Time Bound $O(N^2 2^N)$ | Real-time interactive response $O(N^2)$ | 2-Opt ideal for large delivery scales |
