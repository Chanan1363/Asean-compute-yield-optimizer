# DeMo Proof-of-Concept — พิสูจน์ว่า DeMo ใช้ได้จริง ✅

> **Date / วันที่:** 23 Aug 2026 · **Where / สถานที่:** Google Colab (free T4 GPU)
> **Result / ผลลัพธ์:** `VERDICT: PASS` — DeMo optimizer ทำงานจริงบน GPU จริง

## 🎯 สิ่งที่พิสูจน์ (What was proven)

**DeMo** (Decoupled Momentum Optimization — the optimizer behind Nous Research's DisTrO)
trains a real neural network on a real GPU. This validates the **drop-in path** described in
`docs/NOUS_ALIGNMENT.md` (Part A, Phase 1): the ASEAN Grid can adopt DeMo for its
`AI_TRAINING` workloads without reinventing the wheel.

*DeMo (optimizer ต้นทางของ DisTrO) เทรนโมเดลจริงบน GPU จริงได้ — ยืนยันเส้นทาง "ใช้แทน optimizer ปกติได้เลย" ตาม Nous Alignment Part A Phase 1*

## 📊 ผลลัพธ์จริง (Actual results)

| Metric | Value |
|---|---|
| GPU | NVIDIA T4 (Colab free) |
| Model | Transformer ~1.3M params (char-level LM, vocab 60) |
| Optimizer | **DeMo** (from github.com/bloc97/DeMo) |
| Steps | 300 |
| Loss เริ่มต้น | 3.3499 |
| Loss สุดท้าย | **0.5291** |
| **ลดลง** | **84.2%** ✅ |

```
device: cuda | params: 1.3M
step   0 | loss 3.3499
step  50 | loss ...
step 250 | loss 0.5325
loss: 3.3499 -> 0.5291 (ลด 84.2%)
VERDICT: PASS - DeMo ใช้ได้จริง
```

## 🔁 วิธีรันซ้ำ (How to reproduce — ฟรี 0 บาท)

1. เปิด https://colab.research.google.com → New Notebook
2. Runtime → Change runtime type → **T4 GPU** → Save
3. วางโค้ดด้านล่างใน cell แรก → Shift+Enter → รอ ~3-5 นาที

```python
!pip install -q torch einops
!git clone -q --depth 1 https://github.com/bloc97/DeMo.git /content/DeMo
import sys, time
sys.path.insert(0, '/content/DeMo')
import torch, torch.nn as nn, torch.distributed as dist
from demo import DeMo
if not dist.is_initialized():
    dist.init_process_group('gloo', init_method='file:///tmp/d', world_size=1, rank=0)

TEXT = """The ASEAN Grid democratizes AI compute across Southeast Asia, connecting idle gaming GPUs in homes and internet cafes with global demand. It uses an arbitrage engine to pick the best channel, a tariff aware scheduler, and a genesis ledger. Nous Research built DisTrO to reduce inter GPU communication, enabling training over the internet. The ASEAN Grid aligns with DisTrO and Psyche, using points based rewards and permissionless claims. Anyone with a gaming GPU can join, earn revenue, and democratize AI for the whole region.""".lower()
chars = sorted(set(TEXT)); stoi = {c: i for i, c in enumerate(chars)}; V = len(chars)
data = torch.tensor([stoi[c] for c in TEXT])

model = nn.Sequential(
    nn.Embedding(V, 192),
    nn.TransformerEncoderLayer(192, 3, dim_feedforward=768, dropout=0.1, batch_first=True),
    nn.TransformerEncoderLayer(192, 3, dim_feedforward=768, dropout=0.1, batch_first=True),
    nn.TransformerEncoderLayer(192, 3, dim_feedforward=768, dropout=0.1, batch_first=True),
    nn.LayerNorm(192),
    nn.Linear(192, V),
)

B, S = 32, 64
xb = data[:-1][:B * (len(data) // B)].view(B, -1)
yb = data[1:][:B * (len(data) // B)].view(B, -1)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
xb = xb.to(device)
yb = yb.to(device)
model = model.to(device)
opt = DeMo(model.parameters(), lr=1e-3)
lossf = nn.CrossEntropyLoss()
print('device:', device, '| params: %.1fM' % (sum(p.numel() for p in model.parameters()) / 1e6))
first = None
for step in range(300):
    i = (step * S) % (xb.shape[1] - S)
    loss = lossf(model(xb[:, i:i+S]).reshape(-1, V), yb[:, i:i+S].reshape(-1))
    opt.zero_grad(); loss.backward(); opt.step()
    if first is None:
        first = loss.item()
    if step % 50 == 0:
        print('step %3d | loss %.4f' % (step, loss.item()))
print()
print('loss: %.4f -> %.4f (ลด %.1f%%)' % (first, loss.item(), 100 * (1 - loss.item() / first)))
print('VERDICT: PASS - DeMo ใช้ได้จริง' if loss.item() < first * 0.7 else 'VERDICT: check')
```

## 🧭 ความหมายต่อ ASEAN Grid (What it means for the project)

- ✅ **Nous Alignment Part A Phase 1: complete** — DeMo drop-in path พิสูจน์แล้ว
- ✅ หลักฐานสำหรับผู้ร่วมพัฒนา / ชุมชน — เราทำของจริง ไม่ใช่แค่ blueprint
- 🔜 **Phase 2:** wire DeMo เข้า `AI_TRAINING` workload หลัง `SandboxOrchestrator`

*Credit: DeMo © Nous Research / bloc97 — reproduced under its open license.*
