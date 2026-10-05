# Adversarial verification

Run after consolidation, before the report. The verifier's job is to disprove Critical and Major findings. A finding that survives an honest attempt to break it is worth the reader's time.

## Batching

- Verify only Critical and Major findings. Minor and Nit keep `verdict: null`.
- One verifier per batch of Critical/Major findings, grouped by file or module, batches of a handful. Launch the batches in ONE parallel call.
- Every Agent call sets `model: sonnet`. Never leave it inherited.
- No subagent tool: run the same prompt yourself as a final pass, one finding at a time.

## Verifier prompt

```
You are an adversarial verifier. For each finding below, try to prove it WRONG.

Scope: the diff base...HEAD plus the files it touches. Read the cited code and its callers. Do not modify any file.

For each finding:
1. Read the cited lines and the surrounding function.
2. Look for the reason the finding is false: a guard upstream, a caller that never passes that input, a framework default that handles it, a test that already covers it, a misread of the diff.
3. If a targeted read-only check settles it, run it (a single test file, a type check, a grep, a REPL one-liner). Never run anything that writes, installs, migrates, or touches the network.
4. Re-derive the severity from the real impact, not the finding's wording.

Return ONLY a JSON array, one object per finding:
{"id": "<finding id>", "verdict": "CONFIRMED|PLAUSIBLE|REJECTED", "severity": "Critical|Major|Minor|Nit", "reason": "<one sentence, with file:line evidence>"}

Findings:
<finding JSON objects>
```

## Verdicts

| Verdict | Meaning |
|---------|---------|
| CONFIRMED | The verifier traced the failure path or reproduced it. |
| PLAUSIBLE | No counter-evidence found, but the path could not be fully traced or reproduced. |
| REJECTED | Concrete evidence shows the finding is wrong (guard, unreachable input, misread). |

`severity` in the verdict is the corrected severity. It may go up or down.

## Applying verdicts

- REJECTED: drop the finding from the report and the statistics. List nothing about it.
- Write each result back into the matching finding in `<scratch>/findings/*.json` (`verdict`, corrected `severity`, `reason`), then re-run `merge_findings.py`. It drops REJECTED findings and renders `Verification: <VERDICT> (<reason>)` on the rest.
- CONFIRMED or PLAUSIBLE: keep the finding with the corrected severity.
- A corrected severity that falls to Minor or Nit leaves the verification line in place and moves the finding to that bucket.
- A missing or malformed verifier result for a finding counts as PLAUSIBLE with reason "verifier returned no result". Do not drop on silence.

## User-evidence exception

If the user said they observed the bug (a repro, a log, a screenshot, "this crashes for me"), the finding keeps its severity and is never REJECTED. The verifier still runs. If it disagrees, record that in the line: `Verification: PLAUSIBLE (user-observed; verifier could not reproduce: <reason>)`.
