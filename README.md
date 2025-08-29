# compaction_analysis

Reproducible plotting toolkit for **RocksDB compaction** analysis.

- Pure **matplotlib** (no seaborn), **one chart per figure**, default colors.
- Generates the figures used in the end-to-end report: **fig1 ~ fig8**.
- Parameterized via `config.yaml` (device BW, WAF/RAFc, triggers, time-series shape).
- Outputs saved into `out/`.

## Quickstart

```bash
# Python 3.9+
python3 -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)

# Install the package in development mode
pip install -e .

# Render all figures into out/
python scripts/plot_all.py

# Optional: trigger sensitivity variants into out/
python scripts/trigger_sensitivity.py
```

### Config
All tunables live in `config.yaml`:
- `device.B_W`, `device.B_R`: effective write/read MB/s (after reservations)
- `workload.P_tgt`: target put (MB/s)
- `amp.WAF`, `amp.RAFc`: amplification (use **measured** values from stats)
- `triggers.L0_slow`, `triggers.L0_stop`: file-count thresholds
- `triggers.PCB_soft_GB`, `triggers.PCB_hard_GB`: pending-compaction-bytes thresholds
- `series`: simple synthetic shapes for L0 files/PCB vs time (for illustrative time-series)

### Figures
- `fig1_pmax_vs_waf.png` — steady-state bound vs WAF (RAFc ≈ WAF−1)
- `fig2_gL0.png` — g<sub>L0</sub>(S)
- `fig3_gPCB.png` — g<sub>PCB</sub>(C)
- `fig4_Padm_timeseries.png` — P<sub>adm</sub>(t) = min(P<sub>tgt</sub>·A(t), P<sub>max</sub>)
- `fig5_acceptance_timeseries.png` — g<sub>L0</sub>, g<sub>PCB</sub>, A(t), A*
- `fig6_trigger_aggressive.png` — Accepted Put (12/24)
- `fig7_trigger_default.png` — Accepted Put (20/36)
- `fig8_trigger_lenient.png` — Accepted Put (32/64)

### Deriving WAF/RAFc from stats (Δ-window method)
For a window Δt (e.g., 5 s):
- ΔU: user ingest bytes (from app layer or db_bench interval)
- ΔC<sub>w</sub>: compaction write bytes (diff of counters)
- ΔC<sub>r</sub>: compaction read bytes (diff of counters)

**Formulas:**

WAF = (ΔU + ΔC<sub>w</sub>) / ΔU

RAFc = ΔC<sub>r</sub> / ΔU

P<sub>max</sub> = min(B<sub>W</sub> / WAF, B<sub>R</sub> / RAFc)

A*(t) = P<sub>max</sub> / P<sub>tgt</sub>

P<sub>adm</sub>(t) = min(P<sub>tgt</sub> × A(t), P<sub>max</sub>), where A(t) = g<sub>L0</sub>(S(t)) × g<sub>PCB</sub>(C(t))

### License
MIT
