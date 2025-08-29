# RocksDB Compaction — End-to-End 분석 보고서 (재작성판)

<style>
.math { font-size: 120%; }
.math-display { font-size: 130%; }
img { 
  max-width: 100%; 
  height: auto; 
  display: block; 
  margin: 10px auto; 
  border: 1px solid #ddd; 
  border-radius: 4px; 
  padding: 5px; 
}
</style>

_Date:_ 2025-08-29  
_Assumptions:_ Leveled compaction, 단일 SSD (실효 R/W BW = **300 MB/s**), 트리거: **L0=20/36**, **PCB=64/256 GB**.  
_Calibration (예시):_ **WAF≈6.2**, **RAFc≈5.2** (실측으로 대체 권장).
_File layout:_ 이 MD와 모든 그림 PNG 및 CSV 파일이 **같은 디렉토리**에 있다고 가정합니다.

---

## 개요 (Executive Summary)

- **안정 put 상한**은 증폭과 장치 예산으로 결정:  
  $$\Large P_{\max} = \min\big( B_{\text{W}}/\mathrm{WAF},\; B_{\text{R}}/\mathrm{RAFc},\; \text{IOPS/CPU} \big)$$
  300 MB/s, WAF≈6.2, RAFc≈5.2 → **`P_max`≈48.4 MB/s**.
- **트리거(백프레셔)**: L0 파일 수·PCB가 임계에 닿으면 수용 계수 A(t)↓ →  
  $$\Large P_{adm}(t) = \min\big( P_{tgt}\cdot A(t),\; P_{\max} \big)$$
- **시간 변동**: 다중 레벨이 동시 활성 → 버스티 I/O·톱니형 처리량. L0/PCB 관리를 통해 꼬리(p99) 감소.
- **튜닝 핵심**: WAF/RAFc↓(파일 크기/병렬/리드어헤드/필터/압축), L0<slowdown·PCB<soft 유지, 컴팩션 BW 보장.

---

## 1. 배경과 원리

### 1.1 LSM & Leveled Compaction

- MemTable → flush → **L0 SST**. L1~Lᵢ는 **정렬/비중복** 유지를 위해 상·하위 레벨 병합(compaction).
- 컴팩션은 **삭제/중복 정리**와 **정렬 유지**를 수행하며, 그만큼 **추가 Read/Write I/O**가 듭니다.

### 1.2 증폭 지표

- **WAF** (Write Amplification):  
  $$\large \mathrm{WAF} = \frac{\text{user} + \text{compaction write}}{\text{user}}$$
- **RAFc** (Compaction Read Amp):  
  $$\large \mathrm{RAFc} = \frac{\text{compaction read}}{\text{user}}$$
  (Leveled에서 대체로 **RAFc≈WAF−1** 이 성립)

### 1.3 안정 상태 상한

- 포그라운드 예약을 제외한 실효 예산 `B_W, B_R`에서:  
  $$\Large \boxed{ P_{\max} = \min\big( B_{\text{W}}/\mathrm{WAF},\; B_{\text{R}}/\mathrm{RAFc},\; \text{IOPS/CPU} \big) }$$
- **예시**(300/300, WAF≈6.2, RAFc≈5.2) → `P_max`≈48.4 MB/s.

**Figure 1.** `P_max` vs WAF (RAFc≈WAF−1)  
<img src="fig1_pmax_vs_waf.png" alt="Figure 1" width="600">

---

## 2. 트리거(백프레셔) 모델

### 2.1 L0 파일 수 S에 대한 수용 함수

$$
\large
g_{\text{L0}}(S) = \begin{cases}
  1, & S \le S_{\text{slow}} \\[2pt]
  \dfrac{S_{\text{stop}}-S}{S_{\text{stop}}-S_{\text{slow}}}, & S_{\text{slow}} < S < S_{\text{stop}} \\[8pt]
  0, & S \ge S_{\text{stop}}
 \end{cases}
$$

**Figure 2.** g_L0(S) with slowdown=20, stop=36  
<img src="fig2_gL0.png" alt="Figure 2" width="600">

### 2.2 PCB(C) (Pending Compaction Bytes)에 대한 수용 함수

$$
\large
g_{\text{PCB}}(C) = \begin{cases}
  1, & C \le C_{\text{soft}} \\[2pt]
  \dfrac{C_{\text{hard}}-C}{C_{\text{hard}}-C_{\text{soft}}}, & C_{\text{soft}} < C < C_{\text{hard}} \\[8pt]
  0, & C \ge C_{\text{hard}}
 \end{cases}
$$

**Figure 3.** g_PCB(C) with soft=64 GB, hard=256 GB  
<img src="fig3_gPCB.png" alt="Figure 3" width="600">

### 2.3 즉시 수용 put

- **합성 수용 계수**: $\large A(t)=g_{\text{L0}}(S(t))\cdot g_{\text{PCB}}(C(t))$
- **즉시 수용**: $\Large \boxed{ P_{adm}(t) = \min\big( P_{tgt}A(t),\; P_{\max} \big) }$
- **임계치**: $\large A^* = P_{\max}/P_{tgt}$. A(t)≥A* → WAF 지배(=`P_max`), A(t)<A* → 트리거 지배.

---

## 3. 시간 변동과 임계 A\*

**Figure 4.** `P_adm(t) = min(P_tgt·A(t), P_max)`  
<img src="fig4_Padm_timeseries.png" alt="Figure 4" width="800">

**Figure 5.** Acceptance factors over time: g_L0, g_PCB, A(t), A\*  
<img src="fig5_acceptance_timeseries.png" alt="Figure 5" width="800">

- 초반엔 $A(t)\approx1$이라도 **P_max**로 클립.
- 시간이 지나 L0/PCB가 임계에 접근하면 A(t)↓ → A\* 아래로 내려가는 동안 **P_adm(t) < P_max**.

---

## 4. WAF/RAFc 유도(실측) 절차

**Δt**(권장 5s) 구간에서 RocksDB 통계를 차분해 계산합니다.

- **ΔU (user bytes)**: 앱 레벨에서 put/ingest payload 합(또는 `db_bench` interval ingest).
- **ΔC_w**: compaction write bytes 차분
- **ΔC_r**: compaction read bytes 차분

\[
\mathrm{WAF} = (\Delta U + \Delta C_w)/\Delta U,\qquad
\mathrm{RAFc} = \Delta C_r/\Delta U
\]

> 참고: RocksDB 내부 `bytes_written`에는 flush/compaction도 섞일 수 있으니 **앱 계층에서 ΔU 계측**이 가장 정확합니다.

산출한 **WAF/RAFc**를 상한식과 트리거 모델에 대입해 **P_max**, **A\***, **P_adm(t)**를 갱신합니다.

---

## 5. 트리거 민감도 비교 (Aggressive vs Default vs Lenient)

- **Aggressive (12/24)**: 꼬리 제어↑, 감속 빠름
- **Default-ish (20/36)**: 균형형(권장 시작점)
- **Lenient (32/64)**: 수용↑ 가능, PCB/꼬리 리스크↑

**Figure 6.** Accepted put — Aggressive (12/24)  
<img src="fig6_trigger_aggressive.png" alt="Figure 6" width="700">

**Figure 7.** Accepted put — Default-ish (20/36)  
<img src="fig7_trigger_default.png" alt="Figure 7" width="700">

**Figure 8.** Accepted put — Lenient (32/64)  
<img src="fig8_trigger_lenient.png" alt="Figure 8" width="700">

> 원자료: [trigger scenarios timeseries CSV](final_trigger_scenarios_timeseries.csv)

---

## 6. 튜닝 가이드 (300 MB/s 기준)

- **균형 시작**: slowdown/stop=20/36, PCB soft/hard=64/256GB, max_background_jobs=6, max_subcompactions=2,  
  target_file_size_base=128MB, level_compaction_dynamic_level_bytes=true,  
  bytes_per_sync=1MB, wal_bytes_per_sync=1MB, partition_filters=true,  
  pin_l0_filter_and_index_blocks_in_cache=true, compaction_readahead_size=2–8MB
- **지연 우선**: 12/24 + rate_limiter.auto_tuned=true (컴팩션 BW 보장)
- **처리량 우선**: 32/64 + 파일 크기/병렬 상향(PCB·꼬리 모니터링 필수)

**목표 역산** (필요 장치 예산):  
$$\large B_{\text{W}} \ge P_{\text{target}}\cdot \mathrm{WAF},\; B_{\text{R}} \ge P_{\text{target}}\cdot \mathrm{RAFc}$$

---

## 7. 검증 전략과 한계

- Δ(5s)로 **WAF/RAFc 실측** → **P_max** 갱신 → L0/PCB, 레벨별 Rd/Wr, stall micros와 **형상** 대조.
- Universal/FIFO, 압축률, WAL on/off, 캐시/DirectIO, IOPS/CPU 병목 등은 동역학을 바꿀 수 있음 → **현장 캘리브레이션 필수**.

---

## 8. 결론

- **안정 put**은 **증폭(WAF/RAFc)**과 **장치 예산**으로 결정되며, **트리거**가 즉시 수용을 더 낮춥니다.
- 300 MB/s·WAF≈6.2·RAFc≈5.2의 예시에서 **P_max≈48.4 MB/s**, 트리거로 더 낮아질 수 있습니다.
- 운용 시 **WAF/RAFc 실측**과 **트리거 관리**(L0<slowdown, PCB<soft)가 핵심입니다.

---

### 부록: 데이터 파일

- Formula time series: [final_formula_timeseries.csv](final_formula_timeseries.csv)
- Trigger scenarios: [final_trigger_scenarios_timeseries.csv](final_trigger_scenarios_timeseries.csv) · [summary](final_trigger_scenarios_summary.csv)
