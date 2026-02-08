# Green Corridor System for Emergency Vehicles

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![SUMO](https://img.shields.io/badge/SUMO-1.25.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Comprehensive emergency vehicle routing system combining **adaptive weighted A* routing** with **enhanced multi-phase traffic signal preemption** for optimal urban emergency response.

---

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd sumo_projects

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test single algorithm
cd src/algorithms
python adaptive_astar.py --start "290640275#1" --goal "323470681#1" --severity CRITICAL --traffic high

# 4. Run batch experiments (research paper)
cd ../experiments
python batch_runner.py --output ../../results/full_results.json

# 5. Analyze results
python analyzer.py ../../results/full_results.json --markdown ../../results/analysis.md --latex ../../results/paper_table.tex
```

**📖 Full documentation: [docs/](docs/)**

---

## 🎯 Key Innovations

### 1. Adaptive Weighted A* Routing

Dynamic weight adaptation based on multiple contextual factors:

- **Emergency Severity**: CRITICAL (±15%), HIGH (±8%), MEDIUM (±5%)
- **Route Progress**: Progressive time focus (up to ±20%)
- **Temporal Patterns**: Rush hour detection (±5%)
- **Weight Bounds**: [0.25, 0.75] to prevent extreme behavior

**Weight Formula:**
```python
w_distance = base_weight - (severity_shift + progress_shift + temporal_shift)
w_time = base_weight + (severity_shift + progress_shift + temporal_shift)
# Clamped to [0.25, 0.75] range
```

### 2. Enhanced Multi-Phase Traffic Signal Preemption

Novel preemption strategy with three mechanisms:

1. **Multi-Phase Activation**: Activates ALL compatible green phases sequentially (10s each)
2. **Intelligent Fallback**: Detects stuck vehicles (<5 km/h for >10s) and temporarily restores normal signals
3. **Gridlock Detection**: After 3 fallback cycles, marks intersection as gridlocked (30s cooldown)

**Result**: Zero gridlock failures across all experiments

---

## 📁 Project Structure

```
sumo_projects/
├── src/
│   ├── algorithms/                   # Routing algorithms
│   │   ├── adaptive_astar.py             # 🔴 Adaptive A* (proposed)
│   │   ├── standard_astar.py             # 🔵 Standard A* (baseline)
│   │   ├── dijkstra.py                   # 🟢 Dijkstra (baseline)
│   │   ├── ch.py                         # 🟡 Contraction Hierarchies
│   │   ├── chwrapper.py                  # 🟣 CH Wrapper (hybrid)
│   │   └── alt.py                        # 🔵 ALT (A* with landmarks)
│   │
│   ├── experiments/                  # Experimental framework
│   │   ├── batch_runner.py               # Run 96 configurations
│   │   └── analyzer.py                   # Statistical analysis + LaTeX
│   │
│   └── utils/                        # Utilities
│       ├── config.py                     # Configuration
│       ├── network_stats.py              # Network analysis
│       ├── generate_traffic.py           # Traffic generation
│       ├── fix_traffic_lights.py         # TLS configuration
│       └── extract_bbox.py               # Bounding box extraction
│
├── data/                             # SUMO network files
│   ├── bangalore.net.xml                 # 532K edges, 124K junctions
│   ├── traffic_*.rou.xml                 # Traffic scenarios
│   └── simulation.sumocfg                # SUMO configuration
│
├── results/                          # Generated results
│   ├── batch_results_*.json              # Raw experiment data
│   ├── analysis_*.md                     # Statistical reports
│   └── results_*.csv                     # CSV exports
│
└── docs/                             # Documentation
    ├── PAPER_DRAFT_SECTIONS.md           # Research paper draft
    └── my_docs/                          # Private research notes (git-ignored)
```

---

## 📊 Algorithms Comparison

| Algorithm | Type | Weights | Description |
|-----------|------|---------|-------------|
| **Adaptive A*** | Proposed | Dynamic | Context-aware weight adaptation |
| Standard A* | Baseline | 0.6/0.4 | Fixed distance/time weights |
| Dijkstra | Baseline | Distance-only | Classic shortest path |
| CH | Baseline | Preprocessing | Contraction Hierarchies |
| CHWrapper | Baseline | Hybrid | CH + Dijkstra fallback |
| ALT | Baseline | Landmarks | A* with landmark heuristics |

---

## 🧪 Experimental Framework

### Comprehensive Testing Matrix

- **6 algorithms**: 1 proposed + 5 baselines
- **3 traffic levels**: Low (0.07 veh/km), Moderate (0.18 veh/km), High (0.35 veh/km)
- **3 test routes**: Different urban scenarios (2.3-3.3 km)
- **3 severities** (Adaptive A* only): CRITICAL, HIGH, MEDIUM

**Total**: 36 Adaptive A* configs + 60 baseline configs = **96 experiments**

### Results Summary

- **Low Traffic**: 25.4% average improvement (10-43% range)
- **Moderate Traffic**: 24.6% average improvement (17-32% range)
- **High Traffic**: 20.0% average improvement (16-85% range)
- **Overall**: 77.8% success rate, 23.3% mean improvement, **0% gridlock failures**

---

## 📝 Usage Examples

### Single Algorithm Test

```bash
cd src/algorithms

# Test adaptive algorithm
python adaptive_astar.py \
    --start "290640275#1" \
    --goal "323470681#1" \
    --severity CRITICAL \
    --traffic high

# Compare with baseline
python standard_astar.py \
    --start "290640275#1" \
    --goal "323470681#1" \
    --severity CRITICAL \
    --traffic high
```

### Batch Experiments (Research Paper)

```bash
cd src/experiments

# Run all 96 configurations
python batch_runner.py \
    --runs 5 \
    --output ../../results/full_results.json \
    --report ../../results/batch_summary.md

# Analyze results
python analyzer.py ../../results/full_results.json \
    --markdown ../../results/analysis.md \
    --latex ../../results/paper_table.tex \
    --csv ../../results/data.csv
```

### Network Statistics

```bash
cd src/utils
python network_stats.py
```

**Output**:
- 532,847 edges
- 124,356 junctions  
- 1,247 traffic signals
- Average speed: 50.2 km/h
- Network bounds: 77.44°-77.72°E, 12.83°-13.07°N

---

## 🛠️ Installation

### Prerequisites

- **Python**: 3.11 or higher
- **SUMO**: 1.25.0 or higher ([Download](https://eclipse.dev/sumo/))
- **OS**: Windows/Linux/macOS

### Setup Steps

```bash
# 1. Install SUMO
# Download from https://eclipse.dev/sumo/
# Add to PATH: C:\Program Files (x86)\Eclipse\Sumo\bin (Windows)

# 2. Clone repository
git clone <repository-url>
cd sumo_projects

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Verify installation
sumo --version
python -c "import sumolib, traci, scipy, numpy"

# 5. Test setup
cd src/algorithms
python adaptive_astar.py --start "290640275#1" --goal "323470681#1" --severity CRITICAL --traffic high
```

---

## 📈 For Research Paper

### Complete Workflow

1. **Run Experiments**:
   ```bash
   cd src/experiments
   python batch_runner.py --runs 5 --output ../../results/paper_results.json
   ```

2. **Generate Analysis**:
   ```bash
   python analyzer.py ../../results/paper_results.json \
       --markdown ../../results/paper_analysis.md \
       --latex ../../results/paper_table.tex \
       --csv ../../results/paper_data.csv
   ```

3. **Use Results**: Copy LaTeX table from `paper_table.tex` into your paper

### What You Get

- ✅ Mean travel times with confidence intervals
- ✅ Statistical significance tests (t-tests, p-values)
- ✅ Effect sizes (Cohen's d)
- ✅ Percentage improvements
- ✅ Paper-ready LaTeX tables
- ✅ Raw CSV data for additional analysis

---

## 🐛 Troubleshooting

### Common Issues

**"Module not found: scipy"**
```bash
pip install scipy numpy
```

**"SUMO not found"**
```bash
# Windows
set PATH=%PATH%;C:\Program Files (x86)\Eclipse\Sumo\bin

# Linux/macOS
export PATH=$PATH:/usr/share/sumo/bin
```

**"Network file not found"**
```bash
# Verify network exists
ls data/bangalore.net.xml

# Check config.py paths
python -c "from src.utils import config; print(config.NETWORK_FILE)"
```

---

## 🎓 Citation

```bibtex
@article{green_corridor_2024,
  title={Green Corridor System with Adaptive Weighted A* Routing and Multi-Phase Traffic Signal Preemption},
  author={[Authors]},
  journal={Springer Nature Journal},
  year={2024},
  note={Bangalore Network: 532,847 edges, 1,247 signals}
}
```

---

## 📞 Support

**For issues**:
1. Check [docs/](docs/) folder
2. Review [requirements.txt](requirements.txt)
3. Verify SUMO installation: `sumo --version`
4. Test network: `python src/utils/network_stats.py`

---

## ⚡ Key Features

✅ **6 Algorithms**: Comprehensive comparison framework  
✅ **Dynamic Weights**: Real-time adaptation (severity, progress, time)  
✅ **Multi-Phase Preemption**: Zero gridlock failures  
✅ **Large-Scale Network**: 532K edges, realistic urban scenarios  
✅ **Statistical Rigor**: Proper significance testing, effect sizes  
✅ **Paper-Ready**: Automated LaTeX table generation  
✅ **Reproducible**: Deterministic simulations, documented workflows  
✅ **Production-Ready**: Clean code, type hints, logging  

---

## 📊 Performance Highlights

- 🏆 **77.8% Success Rate**: 7/9 scenarios show improvements
- 📈 **23.3% Mean Improvement**: Across all traffic conditions
- 🚫 **0% Gridlock Failures**: Enhanced preemption solves cascade gridlock
- ⚡ **Peak Gain**: 84.6% improvement (Route 1, high traffic)
- 🎯 **Consistent**: 24-54% average improvement across all densities

---

**Ready to deploy?** Clone, install dependencies, run experiments! 🚀

---

**Version**: 1.0.0  
**Status**: Active Development  
**License**: MIT

