# Comprehensive Algorithm Comparison Analysis

**Generated:** 2026-01-16 20:13:59

**Total Experiments:** 18
**Successful:** 18
**Failed:** 0
**Note:** Deterministic simulations with fixed traffic patterns (single run per config)

## Overall Performance Comparison

### Travel Times by Algorithm (seconds)

| Algorithm | Time (s) | Configs |
|-----------|----------|---------|
| adaptive_astar | 301.00 | 3 |
| alt | 655.00 | 3 |
| ch | 655.00 | 3 |
| chwrapper | 655.00 | 3 |
| dijkstra | 687.67 | 3 |
| standard_astar | 655.00 | 3 |

## Statistical Comparisons


### HIGH Traffic Conditions


#### Adaptive A* (CRITICAL) vs Baselines

| Baseline Algorithm | Route | Adaptive (s) | Baseline (s) | Difference | Improvement % |
|-------------------|-------|--------------|--------------|------------|---------------|
| standard_astar | Route 1 | 199.00 | 1291.00 | -1092.00s | +84.6% |
| standard_astar | Route 2 | 342.00 | 243.00 | +99.00s | -40.7% |
| standard_astar | Route 3 | 362.00 | 431.00 | -69.00s | +16.0% |
| dijkstra | Route 1 | 199.00 | 1291.00 | -1092.00s | +84.6% |
| dijkstra | Route 2 | 342.00 | 341.00 | +1.00s | -0.3% |
| dijkstra | Route 3 | 362.00 | 431.00 | -69.00s | +16.0% |
| ch | Route 1 | 199.00 | 1291.00 | -1092.00s | +84.6% |
| ch | Route 2 | 342.00 | 243.00 | +99.00s | -40.7% |
| ch | Route 3 | 362.00 | 431.00 | -69.00s | +16.0% |
| chwrapper | Route 1 | 199.00 | 1291.00 | -1092.00s | +84.6% |
| chwrapper | Route 2 | 342.00 | 243.00 | +99.00s | -40.7% |
| chwrapper | Route 3 | 362.00 | 431.00 | -69.00s | +16.0% |
| alt | Route 1 | 199.00 | 1291.00 | -1092.00s | +84.6% |
| alt | Route 2 | 342.00 | 243.00 | +99.00s | -40.7% |
| alt | Route 3 | 362.00 | 431.00 | -69.00s | +16.0% |


## Summary Statistics

**Overall Performance (Deterministic Comparison):**
- Mean improvement: 22.65%
- Median improvement: 16.01%
- Best improvement: 84.59%
- Worst case: -40.74%
- Comparisons: 15 configurations


---

**Notes:**
- Positive improvement % means Adaptive A* is faster
- Results are from deterministic simulations with fixed traffic patterns
- Each configuration ran once (no statistical variance)
