# Node Agent v0.5 — Real Job Pipeline (Design)

> Status: **APPROVED** (2026-08-24) · extends v0 (register + heartbeat), no rewrite.
> Phase map: v0 (report) → **v0.5 (run jobs)** → v1 (Docker sandbox + billing + trust).

## 1. Goal (end state)

Customer submits a job in the Portal → job enters the queue → a gamer node
pulls it → runs it → returns the result → the customer sees **status + result**.

## 2. Job lifecycle

```
queued → assigned → running → ✅ done / ❌ failed
```

- `queued`    — job created, waiting for a node
- `assigned`  — scheduler matched a live node
- `running`   — node confirmed it started
- `done`      — node returned a result
- `failed`    — node crashed / job timed out → auto-requeue (retry)

## 3. New pieces (4 — extend existing, no rewrite)

| Piece | What it does |
|---|---|
| 1. `core/db.py` | add a `jobs` table (alongside the existing `nodes` table) |
| 2. API (`app.py`) | `POST /jobs` create · `GET /jobs/{id}` status · `POST /jobs/{id}/result` return result · `GET /jobs/next` node polls for work |
| 3. scheduler | pick a node — v0.5: first live matching node; v1: `tariff × country × trust` |
| 4. `node_agent.py` v0.5 | add loop: poll job → run task → post result (v0 only sent heartbeats) |

## 4. v0.5 task: DEMO compute

The node receives a payload → runs a simulated task (5–30 s hash calc / sleep)
→ returns a result (text + elapsed time + GPU used) → customer sees `✅ done`
with the result. This proves the full loop before wiring real AI (v1).

## 5. No dead-end (built in from day one)

- **Node dies mid-job** → job timeout → back to `queued` → another node retries
  (jobs are never stuck).
- **Result format** → text/JSON now; a `file_url` field is reserved so object
  storage (S3) can be added later without a schema change.
- **Task type** → demo task now; Docker + DeMo real jobs in v1 behind the same
  executor interface (no rewrite).
- **Scheduler** → simple now; trust/tariff scoring in v1 (no rewrite).

## 6. Decisions (approved with Tay, 2026-08-24)

1. First job = **simulated DEMO** (prove the loop before AI).
2. Result = **text/JSON** (files deferred to v1).
3. Node runs **in-agent** (Docker sandbox deferred to v1 — v0.5 only runs our
   own simulated task, never customer code, so it is safe without isolation).
