#!/usr/bin/env python3
# Generate all figures (fig1..fig8) into out/
import yaml, os
from compaction_analysis.config import load_cfg
from compaction_analysis.plot import fig1_pmax_vs_waf, fig2_gL0, fig3_gPCB, fig4_5_timeseries, fig6_8_triggers

def main():
    cfg = load_cfg("config.yaml")
    out = cfg.output.out_dir
    os.makedirs(out, exist_ok=True)

    # fig1
    fig1_pmax_vs_waf(cfg.device.B_W, cfg.device.B_R, cfg.amp.WAF, cfg.amp.RAFc,
                     dpi=cfg.output.dpi, out_path=f"{out}/fig1_pmax_vs_waf.png")
    # fig2
    fig2_gL0(cfg.triggers.L0_slow, cfg.triggers.L0_stop, dpi=cfg.output.dpi,
             out_path=f"{out}/fig2_gL0.png")
    # fig3
    fig3_gPCB(cfg.triggers.PCB_soft_GB, cfg.triggers.PCB_hard_GB, dpi=cfg.output.dpi,
              out_path=f"{out}/fig3_gPCB.png")
    # fig4 & fig5
    fig4_5_timeseries(cfg.device.B_W, cfg.device.B_R, cfg.workload.P_tgt,
                      cfg.amp.WAF, cfg.amp.RAFc, cfg.triggers.L0_slow, cfg.triggers.L0_stop,
                      cfg.triggers.PCB_soft_GB, cfg.triggers.PCB_hard_GB,
                      series_cfg={'S': vars(cfg.series.S), 'C': vars(cfg.series.C)},
                      dpi=cfg.output.dpi, out_dir=out)
    # fig6..8
    fig6_8_triggers(cfg.device.B_W, cfg.device.B_R, cfg.workload.P_tgt,
                    cfg.amp.WAF, cfg.amp.RAFc, cfg.triggers.PCB_soft_GB, cfg.triggers.PCB_hard_GB,
                    dpi=cfg.output.dpi, out_dir=out)

    print(f"Figures saved to {out}/")

if __name__ == "__main__":
    main()
