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
- `fig1_pmax_vs_waf.png` — steady-state bound vs WAF (RAFc≈WAF−1)
- `fig2_gL0.png` — g_L0(S)
- `fig3_gPCB.png` — g_PCB(C)
- `fig4_Padm_timeseries.png` — P_adm(t) = min(P_tgt·A(t), P_max)
- `fig5_acceptance_timeseries.png` — g_L0, g_PCB, A(t), A*
- `fig6_trigger_aggressive.png` — Accepted Put (12/24)
- `fig7_trigger_default.png` — Accepted Put (20/36)
- `fig8_trigger_lenient.png` — Accepted Put (32/64)

### Deriving WAF/RAFc from stats (Δ-window method)
For a window Δt (e.g., 5 s):
- ΔU: user ingest bytes (from app layer or db_bench interval)
- ΔC_w: compaction write bytes (diff of counters)
- ΔC_r: compaction read bytes (diff of counters)

```text
WAF  = (ΔU + ΔC_w) / ΔU
RAFc =  ΔC_r / ΔU
P_max = min(B_W / WAF, B_R / RAFc)
A*(t) = P_max / P_tgt
P_adm(t) = min(P_tgt * A(t), P_max), where A(t)=g_L0(S(t))*g_PCB(C(t))
```

### License
MIT
