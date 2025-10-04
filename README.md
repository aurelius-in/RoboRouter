# RoboRouter

Enterprise-grade, on-prem multi-agent 3D point-cloud perception and explainable autonomy stack. See `docs/` and `README.md` sections for setup and architecture as the project evolves.

Getting started
----------------
Prereqs: Docker with NVIDIA runtime. Then:

1. Copy env file and bring services up:
   - `cp infra/compose/.env.example infra/compose/.env`
   - `cd infra/compose && docker compose up --build`

2. Check health:
   - API: `http://localhost:8000/health`
   - Ray dashboard: `http://localhost:8265`
   - MinIO: `http://localhost:9001`

3. Smoke test:
   - `python -m scripts.smoke_run`

Ingest
------
- POST `/ingest` with `{source_uri, crs, sensor_meta}` to ingest and QA a scan.
- For now, if PDAL is not installed in the API image, the pipeline stubs out and creates an empty output artifact to exercise the flow end-to-end.

*RoboRouter turns raw 3D point clouds into explainable maps, metrics, and safe routes—bridging perception and autonomy through agentic AI.*


**Explainable Multi-Agent System for 3D Point Cloud Intelligence and Autonomous Navigation**

RoboRouter is an on-prem, GPU-accelerated, multi-agent AI platform that transforms raw LiDAR and 3D point cloud data into actionable spatial intelligence for robotics, construction, utilities, and manufacturing environments.  
It handles full-stack 3D perception — registration, filtering, segmentation, modeling, change detection — and can extend into self-driving mode through explainable navigation maps and cost-aware routing.

---

## 🚀 Overview
RoboRouter brings together two worlds:  
- **3D Point Cloud ML Pipelines** – cleaning, aligning, labeling, and modeling spatial data.  
- **Agentic AI Orchestration** – specialized agents that plan, execute, and verify each step with full traceability.  

Every output — whether it’s a mesh, report, or navigation path — comes with confidence scores, residual heatmaps, and a signed audit trail.

---

## 🧠 Key Capabilities

### 3D Perception
- **Ingestion & QA**: Reads LAS/LAZ/PLY/E57, validates coordinate frames, and filters noise with PDAL and Open3D.  
- **Registration**: Global (FGR/TEASER++) + local ICP (point-to-plane) alignment with per-tile RMSE and inlier ratio.  
- **Segmentation**: Classifies terrain, walls, poles, vegetation, machinery using KPConv or PointTransformer.  
- **Modeling**: Builds meshes via Poisson Surface Reconstruction or Instant-NGP, exports glTF/OBJ.  
- **Change Detection**: Voxel-based and learned differencing with displacement vectors and semantic deltas.  

### Navigation & Autonomy
- **Map Generation**: Converts registered clouds to occupancy grids and ESDF costmaps for safe routing.  
- **Path Planning**: A*/D* global planner + TEB local planner for smooth, explainable motion.  
- **Safety Guardian**: Monitors confidence, slope, clearance, and ODD limits; pauses or re-plans when needed.  
- **Explainable Autonomy**: Every “go” or “stop” decision links back to the point-level evidence that caused it.

### Agentic Architecture
Each stage runs as its own agent orchestrated by LangGraph and Ray:
| Agent | Purpose |
|-------|----------|
| Ingestor | Watch folders, pull scans, validate metadata |
| QA / Calibration | Filter, denoise, compute completeness metrics |
| Registration | Align scans and compute residual heatmaps |
| Segmentation | Label classes and uncertainties |
| Modeling | Generate meshes and glTF artifacts |
| Change Detection | Compute temporal differences |
| XAI / Provenance | Build “why” overlays and signed reports |
| Policy / Export | Apply OPA rules, export Potree tiles, costmaps |
| Navigation | Plan safe paths using explainable costmaps |
| Guardian | Enforce safety policies and trigger human review |

---

## 🔍 Explainability
RoboRouter was designed to be auditable by default:
- **Residual Maps:** show registration errors in color.  
- **Entropy Overlays:** visualize model uncertainty.  
- **Attention Maps:** highlight features that drove decisions.  
- **Per-Step Metrics:** RMSE, inlier ratio, mIoU, clearance, deviation.  
- **Immutable Audit Logs:** hash-signed records of every agent action and parameter.  

A human can always trace *why* a path was chosen or a region was flagged.

---

## 🏗️ Architecture

```

LiDAR / Drone / Robot  →  Ingestor Agent  →  Registration → Segmentation
↓
Modeling & Change Detection
↓
XAI + Policy Export + Navigation
↓
Potree / Web 3D Viewer + Report + API

````

- **Backend:** Python 3.11, CUDA 12.x, PyTorch 2.x, Ray, LangGraph, FastAPI  
- **3D Stack:** Open3D, PDAL, MinkowskiEngine, Kaolin, PyTorch3D  
- **Storage:** MinIO (S3), Postgres + PostGIS, Redis  
- **Frontend:** React + Vite + TypeScript, Three.js/Potree viewer  
- **Ops:** Docker + NVIDIA runtime, Kubernetes, MLflow, DVC, OPA policies  

---

## ⚙️ Quick Start

```bash
# Clone the repo
git clone https://github.com/aurelius-in/RoboRouter.git
cd RoboRouter

# Launch the full stack (API, Ray, MinIO, Postgres, UI)
docker compose up

# Optional: fetch small test dataset
bash scripts/fetch_samples.sh

# Open the UI
http://localhost:5173
````

1. Load a sample scene.
2. Run the pipeline (Ingest → Register → Segment → Model).
3. View overlays (Residuals, Segmentation, Uncertainty, Change).
4. Export the explainable report and navigation map.

---

## 🧩 Example Use Cases

### 🏗️ Construction / AEC

Register weekly site scans to BIM baselines, measure volumes, detect progress and hazards.

### ⚡ Utilities / Telco

Segment poles, wires, vegetation; compute clearances and encroachment risks.

### 🏭 Manufacturing / QA

Align parts to CAD, compute deviations, generate pass/fail heatmaps.

### 🤖 Robotics / Autonomous Systems

Generate costmaps and explainable routes for drones or rovers navigating cluttered or dynamic environments.

---

## 📊 Reports & Outputs

* **Interactive 3D viewer** (Potree / Three.js)
* **HTML/PDF report** with metrics, overlays, and “why” sentences
* **glTF / OBJ meshes**
* **Costmaps and routes** for navigation systems
* **OPA-validated exports** for policy compliance

---

## 🔐 Security & Compliance

* Air-gapped by default — no external data calls.
* Policy-as-Code using **Open Policy Agent (OPA)**.
* Signed audit logs for each agent action.
* Configurable data retention and redaction policies.

---

## 🧭 Future Roadmap

* Multi-robot coordination via shared spatial memory.
* Integration with ROS 2 Nav2 and MoveIt 2.
* Live streaming mode for real-time perception and routing.
* Edge deployment templates for NVIDIA Jetson and Orin.

---

## 📁 Repository Layout

```
RoboRouter/
 ├─ agents/             # Individual agent modules
 ├─ apps/
 │   ├─ api/            # FastAPI service
 │   └─ web/            # React UI
 ├─ data/               # DVC-tracked sample data
 ├─ models/             # ML checkpoints and configs
 ├─ scripts/            # Setup and utility scripts
 ├─ infra/              # Docker & K8s manifests
 ├─ tests/              # Unit & integration tests
 └─ docs/               # Architecture & usage docs
```

---

## 🤝 Author

**Oliver A. Ellison, MS SD**
Principal AI Engineer & Architect – RAIN (Reliable AI Network, Inc.)
- Portfolio: [ReliableAINetwork.com](https://reliableainetwork.com)

---

## 🧩 License

Copyright © 2025 Reliable AI Network, Inc.
All rights reserved. For portfolio and evaluation use only.
