from __future__ import annotations
import yaml
from dataclasses import dataclass

@dataclass
class Device:
    B_W: float
    B_R: float

@dataclass
class Workload:
    P_tgt: float

@dataclass
class Amplification:
    WAF: float
    RAFc: float

@dataclass
class Triggers:
    L0_slow: int
    L0_stop: int
    PCB_soft_GB: float
    PCB_hard_GB: float

@dataclass
class SeriesParams:
    s0: float; s_gain: float; s_amp: float; s_freq: float; s_clip: float

@dataclass
class SeriesCParams:
    c0: float; c_gain: float; c_amp: float; c_freq: float; c_clip_GB: float

@dataclass
class SeriesCfg:
    S: SeriesParams
    C: SeriesCParams

@dataclass
class OutputCfg:
    out_dir: str
    dpi: int

@dataclass
class Cfg:
    device: Device
    workload: Workload
    amp: Amplification
    triggers: Triggers
    series: SeriesCfg
    output: OutputCfg

def load_cfg(path: str) -> Cfg:
    with open(path, 'r') as f:
        d = yaml.safe_load(f)
    dev = Device(**d['device'])
    wl  = Workload(**d['workload'])
    amp = Amplification(**d['amp'])
    trg = Triggers(**d['triggers'])
    ser = SeriesCfg(S=SeriesParams(**d['series']['S']), C=SeriesCParams(**d['series']['C']))
    out = OutputCfg(**d['output'])
    return Cfg(device=dev, workload=wl, amp=amp, triggers=trg, series=ser, output=out)
