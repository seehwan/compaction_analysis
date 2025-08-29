from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class ModelInputs:
    B_W: float
    B_R: float
    P_tgt: float
    WAF: float
    RAFc: float
    L0_slow: int
    L0_stop: int
    PCB_soft_GB: float
    PCB_hard_GB: float

def pmax(B_W: float, B_R: float, WAF: float, RAFc: float) -> float:
    return min(B_W / WAF, B_R / RAFc)

def g_L0(S: np.ndarray, S_slow: int, S_stop: int) -> np.ndarray:
    g = np.ones_like(S, dtype=float)
    mid = (S > S_slow) & (S < S_stop)
    g[mid] = (S_stop - S[mid]) / (S_stop - S_slow)
    g[S >= S_stop] = 0.0
    return g

def g_PCB(C_MB: np.ndarray, soft_MB: float, hard_MB: float) -> np.ndarray:
    g = np.ones_like(C_MB, dtype=float)
    mid = (C_MB > soft_MB) & (C_MB < hard_MB)
    g[mid] = (hard_MB - C_MB[mid]) / (hard_MB - soft_MB)
    g[C_MB >= hard_MB] = 0.0
    return g

def synth_series(t: np.ndarray, s0: float, s_gain: float, s_amp: float, s_freq: float, s_clip: float):
    S = s0 + s_gain * t + s_amp * np.sin(s_freq * t)
    return np.clip(S, 0.0, s_clip)

def synth_series_C_GB(t: np.ndarray, c0: float, c_gain: float, c_amp: float, c_freq: float, c_clip_GB: float):
    C = c0 + c_gain * t + c_amp * np.sin(c_freq * t)
    C = np.clip(C, 0.0, c_clip_GB)
    return C * 1024.0  # MB
