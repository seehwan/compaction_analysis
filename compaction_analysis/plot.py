import numpy as np
import matplotlib.pyplot as plt
from .model import pmax, g_L0, g_PCB, synth_series, synth_series_C_GB

# NOTE: Use matplotlib only, one chart per figure, no explicit color settings.

def fig1_pmax_vs_waf(B_W, B_R, WAF, RAFc, dpi=140, out_path=None):
    waf_grid = np.linspace(2.0, 20.0, 300)
    rafc_grid = np.maximum(waf_grid - 1.0, 0.5)
    pmax_w = B_W / waf_grid
    pmax_r = B_R / rafc_grid
    pmax_grid = np.minimum(pmax_w, pmax_r)
    P_max = pmax(B_W, B_R, WAF, RAFc)

    plt.figure(figsize=(8,4.5))
    plt.plot(waf_grid, pmax_w, label="B_W / WAF")
    plt.plot(waf_grid, pmax_r, label="B_R / RAFc (≈WAF-1)")
    plt.plot(waf_grid, pmax_grid, label="P_max = min(·)")
    plt.axvline(WAF, linestyle="--", label=f"WAF={WAF}")
    plt.axhline(P_max, linestyle=":", label=f"P_max@WAF={P_max:.1f} MB/s")
    plt.title("Steady-state P_max vs WAF (B_W=B_R device)")
    plt.xlabel("WAF"); plt.ylabel("MB/s"); plt.legend(loc="best"); plt.tight_layout()
    if out_path: plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()

def fig2_gL0(S_slow, S_stop, dpi=140, out_path=None):
    S = np.linspace(0, 60, 600)
    gL0_vals = g_L0(S, S_slow, S_stop)
    plt.figure(figsize=(8,4.5))
    plt.plot(S, gL0_vals, label="g_L0(S)")
    plt.axvline(S_slow, linestyle="--", label="slowdown")
    plt.axvline(S_stop, linestyle="--", label="stop")
    plt.title("L0 Trigger Acceptance g_L0(S)")
    plt.xlabel("L0 file count S"); plt.ylabel("accept factor"); plt.legend(loc="best"); plt.tight_layout()
    if out_path: plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()

def fig3_gPCB(soft_GB, hard_GB, dpi=140, out_path=None):
    C_GB = np.linspace(0, 300, 600)
    C_MB = C_GB * 1024.0
    gPCB_vals = g_PCB(C_MB, soft_GB*1024.0, hard_GB*1024.0)
    plt.figure(figsize=(8,4.5))
    plt.plot(C_GB, gPCB_vals, label="g_PCB(C)")
    plt.axvline(soft_GB, linestyle="--", label="soft")
    plt.axvline(hard_GB, linestyle="--", label="hard")
    plt.title("PCB Trigger Acceptance g_PCB(C)")
    plt.xlabel("Pending compaction bytes C (GB)"); plt.ylabel("accept factor"); plt.legend(loc="best"); plt.tight_layout()
    if out_path: plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()

def fig4_5_timeseries(B_W, B_R, P_tgt, WAF, RAFc, S_slow, S_stop, soft_GB, hard_GB, series_cfg, dpi=140, out_dir=None):
    # Build time series
    T = 220.0; dt = 0.2
    t = np.arange(0, T+dt, dt)
    S_t = synth_series(t, **series_cfg['S'])
    C_t_MB = synth_series_C_GB(t, **series_cfg['C'])
    P_max = pmax(B_W, B_R, WAF, RAFc)
    A_star = P_max / P_tgt

    gL0_t = g_L0(S_t, S_slow, S_stop)
    gPCB_t = g_PCB(C_t_MB, soft_GB*1024.0, hard_GB*1024.0)
    A_t = gL0_t * gPCB_t
    Padm_raw = P_tgt * A_t
    Padm = np.minimum(Padm_raw, P_max)

    # fig4
    plt.figure(figsize=(9,4.8))
    plt.plot(t, Padm_raw, label="P_tgt · A(t)")
    plt.plot(t, Padm, label="P_adm(t) = min(P_tgt·A, P_max)")
    plt.axhline(P_max, linestyle="--", label=f"P_max ≈ {P_max:.1f} MB/s")
    plt.title("Instantaneous Admitted Put P_adm(t)")
    plt.xlabel("time (s)"); plt.ylabel("MB/s"); plt.legend(loc="best"); plt.tight_layout()
    if out_dir: plt.savefig(f"{out_dir}/fig4_Padm_timeseries.png", dpi=dpi, bbox_inches="tight")
    plt.close()

    # fig5
    plt.figure(figsize=(9,4.8))
    plt.plot(t, gL0_t, label="g_L0(S(t))")
    plt.plot(t, gPCB_t, label="g_PCB(C(t))")
    plt.plot(t, A_t, label="A(t) = g_L0·g_PCB")
    plt.axhline(A_star, linestyle="--", label=f"A* = P_max/P_tgt ≈ {A_star:.3f}")
    plt.title("Trigger Acceptance Factors Over Time")
    plt.xlabel("time (s)"); plt.ylabel("factor (0..1)"); plt.legend(loc="best"); plt.tight_layout()
    if out_dir: plt.savefig(f"{out_dir}/fig5_acceptance_timeseries.png", dpi=dpi, bbox_inches="tight")
    plt.close()

def fig6_8_triggers(B_W, B_R, P_tgt, WAF, RAFc, soft_GB, hard_GB, dpi=140, out_dir=None):
    P_max = pmax(B_W, B_R, WAF, RAFc)
    # time base
    T = 220.0; dt = 0.2
    t = np.arange(0, T+dt, dt)

    def run_scn(slo, stp):
        S_t = np.clip(8 + 0.16*t + 3*np.sin(0.12*t), 0, max(stp-1, 10))
        C_t_MB = np.clip(1024*(0.50*t + 6*np.sin(0.03*t)), 0, 140*1024)
        gL0 = g_L0(S_t, slo, stp); gPCB = g_PCB(C_t_MB, soft_GB*1024.0, hard_GB*1024.0)
        A = gL0 * gPCB
        return np.minimum(P_tgt * A, P_max)

    for (slo, stp, fn, title) in [
        (12, 24, "fig6_trigger_aggressive.png", "Aggressive (12/24)"),
        (20, 36, "fig7_trigger_default.png", "Default-ish (20/36)"),
        (32, 64, "fig8_trigger_lenient.png", "Lenient (32/64)"),
    ]:
        y = run_scn(slo, stp)
        plt.figure(figsize=(9,4.8))
        plt.plot(t, y, label="P_adm(t)")
        plt.axhline(P_max, linestyle="--", label=f"P_max ≈ {P_max:.1f}")
        plt.title(f"Accepted Put vs Time — {title}")
        plt.xlabel("time (s)"); plt.ylabel("MB/s"); plt.legend(loc="best"); plt.tight_layout()
        if out_dir: plt.savefig(f"{out_dir}/{fn}", dpi=dpi, bbox_inches="tight")
        plt.close()
