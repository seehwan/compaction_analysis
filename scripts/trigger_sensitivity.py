#!/usr/bin/env python3
# Render only the trigger sensitivity figures (fig6..8)
import os
from compaction_analysis.config import load_cfg
from compaction_analysis.plot import fig6_8_triggers

def main():
    cfg = load_cfg("config.yaml")
    out = cfg.output.out_dir
    os.makedirs(out, exist_ok=True)
    fig6_8_triggers(cfg.device.B_W, cfg.device.B_R, cfg.workload.P_tgt,
                    cfg.amp.WAF, cfg.amp.RAFc, cfg.triggers.PCB_soft_GB, cfg.triggers.PCB_hard_GB,
                    dpi=cfg.output.dpi, out_dir=out)
    print(f"Trigger sensitivity figs saved to {out}/")

if __name__ == "__main__":
    main()
