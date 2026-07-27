# Dependency Shapes

Load when a project's dependency structure isn't a plain sequential chain. Each shape is a
building block, real plans compose several of these.

## Sequential Chain
`A → B → C → D`: each task blocks the next. Use for strict ordering (e.g. schema before code).
```
TaskUpdate: { taskId: "B", addBlockedBy: ["A"] }
TaskUpdate: { taskId: "C", addBlockedBy: ["B"] }
```

## Parallel Split → Converge
`A → (B ‖ C ‖ D) → E`: B/C/D are independent once A finishes; E waits for all three.
```
TaskUpdate: { taskId: "B", addBlockedBy: ["A"] }
TaskUpdate: { taskId: "C", addBlockedBy: ["A"] }
TaskUpdate: { taskId: "D", addBlockedBy: ["A"] }
TaskUpdate: { taskId: "E", addBlockedBy: ["B", "C", "D"] }
```

## Diamond (single convergence pair)
```
    A
   / \
  B   C
   \ /
    D
```
`D` needs both `B` and `C`: `TaskUpdate: { taskId: "D", addBlockedBy: ["B", "C"] }`

## Staged Rollout (time-gated)
`A → B → wait → C → wait → D`: each stage blocks on the prior *and* a monitoring/soak task.
Record the wait duration in the task description, not a special field: no tool models "wait N days" natively.
```
TaskUpdate: { taskId: "monitor-10pct", addBlockedBy: ["deploy-10pct"] }
TaskUpdate: { taskId: "deploy-50pct", addBlockedBy: ["monitor-10pct"] }
```

## Multi-Team Fan-Out / Fan-In
```
       A (contract)
      /|\
     B C D   (backend / frontend / mobile, parallel)
      \|/
       E (integration)
```
Same pattern as Parallel Split → Converge; label tasks by team in the subject so the graph reads
clearly (`"Backend: implement API"`, `"Frontend: build UI"`).
