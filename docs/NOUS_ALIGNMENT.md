# Nous Alignment Plan — ASEAN Grid ↔ Nous Research (DisTrO / Psyche)

## Part A — Technical Architecture

> **ASEAN Grid ↔ Nous Research (DisTrO / Psyche) — Technical Alignment**
> This document maps *where* and *how* the ASEAN Grid prototype aligns with — and
> extends — Nous Research's open distributed-training stack. It is a technical
> reference, not a claim of using Nous code directly. We align on **design**, and
> credit the source openly.
>
> *เอกสารนี้ระบุจุดที่ ASEAN Grid วางแนวสถาปัตยกรรมตาม (และต่อยอดจาก) ชุด open-source
> ด้าน distributed training ของ Nous Research — เป็นการอ้างอิงดีไซน์ ไม่ใช่การอ้างว่าใช้
> โค้ดของ Nous โดยตรง*

---

## 1. What we reference (สิ่งที่อ้างอิง)

| Project | What it is | Where |
|---|---|---|
| **DisTrO** | Family of low-latency distributed optimizers that cut inter-GPU communication by **3–4 orders of magnitude** (DCT compression + sign-only quantization) | github.com/NousResearch/DisTrO |
| **DeMo** | Standalone PyTorch optimizer (drop-in `torch.optim.SGD` subclass). Use as-is — the only required change is disabling DDP's native gradient all-reduce | github.com/bloc97/DeMo |
| **Psyche Network** | Infrastructure for internet-distributed training: `run-manager` binary + Docker, **Training / Witnessing / Verifying** roles, Solana coordinator for trust & rewards | github.com/PsycheFoundation/psyche |

---

## 2. Current ASEAN Grid architecture (architecture จริงของเรา)

| Module | File | Responsibility |
|---|---|---|
| Arbitrage Engine | `core/arbitrage.py` | Scan 7 revenue channels → pick best (Smart Yield Balancer: 15% switch threshold + overhead guard) |
| Scheduler | `core/scheduler.py` | Assign workloads to nodes by tariff × country × trust |
| Channels | `core/channels.py` | 7 channels behind one `ComputeChannel` interface (Vast.ai live API, RunPod GraphQL, Akash REST) |
| Sandbox | `core/sandbox.py` | One-click Docker isolation: create → `verify_isolation` → run → destroy (network=none, seccomp, no-new-privileges) |
| AI Hooks | `ai/strategy_hooks.py` | 5 pluggable decision points (`predict_best_channel`, `predict_price_curve`, `score_node_trust`, `forecast_demand`, `route_workload`) |
| Workload types | `core/models.py` | `AI_TRAINING`, `AI_INFERENCE`, `RENDERING`, `MINING`, `SIMULATION`, `CLOUD_GAMING` |

---

## 3. Alignment map (จุดวางตาม — จริงต่อจริง)

| Nous concept | ASEAN Grid counterpart | Status |
|---|---|---|
| **DeMo optimizer** (drop-in, disable all-reduce) | The missing engine for `AI_TRAINING` workload — currently a stub. Adopting DeMo lets grid nodes co-train models across home GPUs | 🔜 Phase 1 (design) |
| **DisTrO DCT compression** (`distro.rs`) | Gradient-sync protocol between grid nodes when a training job spans multiple nodes | 🔜 Phase 1 (design) |
| **Witnessing / Verifying roles** | Maps to `score_node_trust` hook + `NodeStatus.STAKED` (collateral) — anti-fraud at the work level, not just payment level | ✅ concept mapped → extend |
| **`run-manager` + Docker** | `DockerSandboxOrchestrator` — containerized job distribution is already the same pattern | ✅ aligned |
| **Coordinator (on-chain trust)** | `GenesisLedger` (append-only hash chain) — Phase 3 target to move trust/rewards on-chain | 🔜 Phase 3 |

---

## 4. The gap we fill (จุดที่เราไปก่อน)

**Psyche is training-first; ASEAN Grid is inference-first.**

- Psyche's roadmap explicitly lists *"accessible inference / RL"* as **stage 2** — still ahead.
- ASEAN Grid starts at **inference + rendering + flexible workloads** (the 6 `WorkloadType`s) with a **prepaid API-key monetization matrix** and live channel arbitrage — the demand side Psyche has not built yet.
- We are complementary, not competing: the DisTrO optimizer is the piece we adopt *for* the training workloads we list; the inference/arbitrage layer is ours.

This is the honest, defensible framing for the open-source community: **"ASEAN Grid adopts DisTrO for its training path and extends the Nous ethos to the inference/demand side."**

---

## 5. Phase plan (แผนดำเนินการตามลำดับ)

- **Phase 0 (now)** — This alignment doc + adopt DeMo as the documented optimizer for `AI_TRAINING` (spec, no runtime dependency yet).
- **Phase 1** — Proof: run DeMo on a rented GPU (Vast.ai) to validate the drop-in path on a small model; document results + a reproducible script in the repo.
- **Phase 2** — Wire DeMo into the `AI_TRAINING` workload path behind the existing `SandboxOrchestrator`; add a `verify_isolation`-gated training job type.
- **Phase 3** — Move trust/rewards on-chain (Solana coordinator pattern) while keeping the 75/20/5 split as the points→payout conversion rule.

---

*AGPL-3.0. Credit: DisTrO / DeMo / Psyche © Nous Research & contributors — referenced under their respective licenses.*


---

## Part B — Payment & Trust Layer

> **ASEAN Grid `RevenueSplit` v2 ← Psyche `solana-treasurer` / `coordinator` / `mining-pool`**
> We keep **EVM (Solidity)** and the **75/20/5 split** as the payout *conversion rule*,
> but adopt Psyche's **points-based, permissionless-claim, collateral** design.
> This is a design migration, not a rewrite — and it stays on Ethereum-family chains.
>
> *เราคง **EVM (Solidity)** และ **สัดส่วน 75/20/5** เป็นกติกาการแปลงค่า แต่ยืมดีไซน์
> **points / permissionless-claim / collateral** ของ Psyche มาใช้ — เป็นการปรับดีไซน์ ไม่ใช่รื้อใหม่*

---

## 1. Current `RevenueSplit` (Solidity / EVM)

- Fixed **75/20/5** (basis points 7500 / 2000 / 500), `BPS = 10000`
- **Push model** — `owner` calls `batchPayout(nodes[], amounts[])` (off-chain computed)
- Dev pool 5% via `verifyDeveloper` + `claimDeveloperReward`
- Safety: CEI pattern, `batchProcessed` replay-guard, remainder → developer pool

**Weakness (from the decentralized-trust lens):** nodes must *trust the owner* to pay
correctly — the exact trust assumption Psyche eliminates.

---

## 2. What Psyche does (on Solana)

| Component | Behavior |
|---|---|
| **Coordinator** | Counts each client's **earned points** on-chain during a run |
| **Participant** | `{ claimed_collateral_amount, claimed_earned_points }` — tracks what's already paid |
| **`participant_claim`** | **Permissionless** — a client claims its own points: `unclaimed = earned − claimed`, then `1 point → 1 collateral` |
| **Treasurer** | Escrow that converts points → reward token at a fixed rate |
| **Mining Pool** | Users pool funds to collectively buy compute |
| **Collateral** | Clients stake before joining (anti-fraud at the economic layer) |

---

## 3. RevenueSplit v2 — the migration (ยืมดีไซน์ 3 ข้อ)

1. **Points-based (Pull model)** — replace `owner.batchPayout` with **per-epoch points**
   counted by the (off-chain → future on-chain) coordinator. Each epoch holds a node pool
   equal to **75%** of that epoch's revenue; nodes convert `earned_points` → payout
   proportionally (`nodePoolUsd / totalPoints × unclaimedPoints`).
2. **Permissionless claim** — a node calls `claim(epoch)` itself. No owner in the loop.
   The 75/20/5 split survives as the **pool ratio**, not as an owner-managed payment.
3. **Collateral / staking** — a node must be `STAKED` (deposit `$GRID`) before the
   coordinator assigns work — aligning `core/models.py: NodeStatus.STAKED` with the
   on-chain economic layer.

---

## 4. Interface sketch (Solidity v2, conceptual)

```solidity
// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.24;

contract RevenueSplitV2 {
    uint256 public constant NODE_SHARE = 7500;      // 75%  (retained as pool ratio)
    uint256 public constant PLATFORM_SHARE = 2000;  // 20%
    uint256 public constant DEVELOPER_SHARE = 500;  // 5%

    struct Epoch {
        uint256 index;
        uint256 totalPoints;                     // coordinator-issued points this epoch
        uint256 nodePoolUsd;                     // 75% of epoch revenue (funded at settle)
        mapping(address => uint256) earnedPoints; // per-node earned points
        mapping(address => uint256) claimedPoints; // replay guard (per node)
    }
    mapping(uint256 => Epoch) public epochs;

    // Coordinator (authorized off-chain oracle → future on-chain) records work
    function recordWork(uint256 epochIdx, address node, uint256 points) external onlyCoordinator {
        epochs[epochIdx].earnedPoints[node] += points;
        epochs[epochIdx].totalPoints += points;
    }

    // Permissionless: any node claims its own share — no owner in the loop
    function claim(uint256 epochIdx) external {
        Epoch storage e = epochs[epochIdx];
        uint256 unclaimed = e.earnedPoints[msg.sender] - e.claimedPoints[msg.sender];
        require(unclaimed > 0, "RevenueSplitV2: nothing to claim");
        uint256 payout = unclaimed * e.nodePoolUsd / e.totalPoints; // CEI: state first
        e.claimedPoints[msg.sender] = e.earnedPoints[msg.sender];
        (bool ok, ) = msg.sender.call{value: payout}("");
        require(ok, "RevenueSplitV2: claim failed");
    }

    // 20% platform / 5% dev pool — settled at epoch close (kept from v1)
    function settleEpoch(uint256 epochIdx) external onlyOwner { /* fund nodePoolUsd + split */ }
}
```

*Conceptual only — final contract follows v1's CEI discipline and the repo's test-first flow.*

---

## 5. What stays / what changes (สรุป)

| Aspect | v1 (now) | v2 (aligned) |
|---|---|---|
| Chain | EVM / Solidity | ✅ EVM / Solidity (unchanged) |
| Split ratio | 75/20/5 fixed | ✅ 75/20/5 (now a *pool ratio*) |
| Payout direction | **Push** (owner `batchPayout`) | **Pull** (node `claim`) |
| Work accounting | off-chain, owner-computed | points (coordinator → oracle → on-chain) |
| Anti-fraud | `batchProcessed` replay guard | **collateral/stake** + `claimedPoints` |
| Dev pool | owner-verified | retained (v1 logic) |

---

## 6. Phase plan (payment layer)

- **Phase 0 (now)** — this doc + keep v1 contract as-is (it already enforces 75/20/5 safely).
- **Phase 1** — implement `RevenueSplitV2` points/claim in Solidity + unit tests alongside v1.
- **Phase 2** — wire the coordinator (Python, off-chain) to record points per workload.
- **Phase 3** — evaluate Solana coordinator/treasurer for on-chain trust when scale justifies it.

---

*AGPL-3.0. Credit: Psyche `solana-treasurer` / `coordinator` design © Nous Research & contributors — referenced for design, re-implemented on EVM.*
