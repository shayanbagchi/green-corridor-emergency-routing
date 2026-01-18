# Comprehensive Algorithm Comparison Analysis

**Generated:** 2026-01-16 11:26:15

**Total Experiments:** 18
**Successful:** 18
**Failed:** 0
**Note:** Deterministic simulations with fixed traffic patterns (single run per config)

## Overall Performance Comparison

### Travel Times by Algorithm (seconds)

| Algorithm | Time (s) | Configs |
|-----------|----------|---------|
| adaptive_astar | 161.67 | 3 |
| alt | 214.67 | 3 |
| ch | 214.67 | 3 |
| chwrapper | 214.67 | 3 |
| dijkstra | 214.67 | 3 |
| standard_astar | 214.67 | 3 |

## Statistical Comparisons


### MODERATE Traffic Conditions


#### Adaptive A* (CRITICAL) vs Baselines

| Baseline Algorithm | Route | Adaptive (s) | Baseline (s) | Difference | Improvement % |
|-------------------|-------|--------------|--------------|------------|---------------|
| standard_astar | Route 1 | 143.00 | 191.00 | -48.00s | +25.1% |
| standard_astar | Route 2 | 186.00 | 223.00 | -37.00s | +16.6% |
| standard_astar | Route 3 | 156.00 | 230.00 | -74.00s | +32.2% |
| dijkstra | Route 1 | 143.00 | 191.00 | -48.00s | +25.1% |
| dijkstra | Route 2 | 186.00 | 223.00 | -37.00s | +16.6% |
| dijkstra | Route 3 | 156.00 | 230.00 | -74.00s | +32.2% |
| ch | Route 1 | 143.00 | 191.00 | -48.00s | +25.1% |
| ch | Route 2 | 186.00 | 223.00 | -37.00s | +16.6% |
| ch | Route 3 | 156.00 | 230.00 | -74.00s | +32.2% |
| chwrapper | Route 1 | 143.00 | 191.00 | -48.00s | +25.1% |
| chwrapper | Route 2 | 186.00 | 223.00 | -37.00s | +16.6% |
| chwrapper | Route 3 | 156.00 | 230.00 | -74.00s | +32.2% |
| alt | Route 1 | 143.00 | 191.00 | -48.00s | +25.1% |
| alt | Route 2 | 186.00 | 223.00 | -37.00s | +16.6% |
| alt | Route 3 | 156.00 | 230.00 | -74.00s | +32.2% |


## Summary Statistics

**Overall Performance (Deterministic Comparison):**
- Mean improvement: 24.63%
- Median improvement: 25.13%
- Best improvement: 32.17%
- Worst case: 16.59%
- Comparisons: 15 configurations


---

**Notes:**
- Positive improvement % means Adaptive A* is faster
- Results are from deterministic simulations with fixed traffic patterns
- Each configuration ran once (no statistical variance)
