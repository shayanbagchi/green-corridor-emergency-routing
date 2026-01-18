# Comprehensive Algorithm Comparison Analysis

**Generated:** 2026-01-16 11:26:08

**Total Experiments:** 18
**Successful:** 18
**Failed:** 0
**Note:** Deterministic simulations with fixed traffic patterns (single run per config)

## Overall Performance Comparison

### Travel Times by Algorithm (seconds)

| Algorithm | Time (s) | Configs |
|-----------|----------|---------|
| adaptive_astar | 158.00 | 3 |
| alt | 216.00 | 3 |
| ch | 216.00 | 3 |
| chwrapper | 216.00 | 3 |
| dijkstra | 215.67 | 3 |
| standard_astar | 216.00 | 3 |

## Statistical Comparisons


### LOW Traffic Conditions


#### Adaptive A* (CRITICAL) vs Baselines

| Baseline Algorithm | Route | Adaptive (s) | Baseline (s) | Difference | Improvement % |
|-------------------|-------|--------------|--------------|------------|---------------|
| standard_astar | Route 1 | 143.00 | 251.00 | -108.00s | +43.0% |
| standard_astar | Route 2 | 177.00 | 197.00 | -20.00s | +10.2% |
| standard_astar | Route 3 | 154.00 | 200.00 | -46.00s | +23.0% |
| dijkstra | Route 1 | 143.00 | 251.00 | -108.00s | +43.0% |
| dijkstra | Route 2 | 177.00 | 196.00 | -19.00s | +9.7% |
| dijkstra | Route 3 | 154.00 | 200.00 | -46.00s | +23.0% |
| ch | Route 1 | 143.00 | 251.00 | -108.00s | +43.0% |
| ch | Route 2 | 177.00 | 197.00 | -20.00s | +10.2% |
| ch | Route 3 | 154.00 | 200.00 | -46.00s | +23.0% |
| chwrapper | Route 1 | 143.00 | 251.00 | -108.00s | +43.0% |
| chwrapper | Route 2 | 177.00 | 197.00 | -20.00s | +10.2% |
| chwrapper | Route 3 | 154.00 | 200.00 | -46.00s | +23.0% |
| alt | Route 1 | 143.00 | 251.00 | -108.00s | +43.0% |
| alt | Route 2 | 177.00 | 197.00 | -20.00s | +10.2% |
| alt | Route 3 | 154.00 | 200.00 | -46.00s | +23.0% |


## Summary Statistics

**Overall Performance (Deterministic Comparison):**
- Mean improvement: 25.36%
- Median improvement: 23.00%
- Best improvement: 43.03%
- Worst case: 9.69%
- Comparisons: 15 configurations


---

**Notes:**
- Positive improvement % means Adaptive A* is faster
- Results are from deterministic simulations with fixed traffic patterns
- Each configuration ran once (no statistical variance)
