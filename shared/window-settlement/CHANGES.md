# Retained window plan and settlement review

Gathering 18 connects Line 3's window-plan change detector to this folder's
Line 2 structural diagnostics and pinned historical settlement replay. Copy
this entire folder into another workspace; Python standard library only.
The unchanged ordinary vendor additions and hashes are in
`change-provenance.json`. No line folder is needed at runtime.

From the repository root, one offline command:

```sh
python3 -B shared/window-settlement/change.py shared/window-settlement/plan.json shared/window-settlement/plan.json --baseline-sha256 be5ee9b0eefa06067695aac1caaaa5b1dabb8a505d3025f3a9ed447e4c525cb5 --proposed-sha256 be5ee9b0eefa06067695aac1caaaa5b1dabb8a505d3025f3a9ed447e4c525cb5
```

Tried: exit 0, `accepted: true`, `settlement_window_match`. Both historical
real ZTO transactions settle and fit the unchanged windows at blocks 26190898
and 26194715. `change-match.json` is the actual complete report. No fresh
chain observation was collected. The self-compared demo demonstrates mechanics,
not independent policy approval.

For your own work, pass baseline and proposed plan paths and their independently
retained exact-byte SHA-256 hashes. Both hashes are checked before either input
is interpreted. Line 2 checks both complete structures and reports JSON Pointer
diagnostics. Line 3 refuses widened bounds, weaker confirmation/finality policy,
transaction membership changes, and changed evidence pins or paths before
opening evidence. A compatible proposal then undergoes settlement and inclusive
window replay using the **same captured proposed bytes**. No baseline or pin
is updated. Reusing one lexical path captures it once; distinct inputs are not
an atomic filesystem snapshot.

The new integration addresses a real distinction: narrowing a window is
compatible with a baseline but can exclude the actual inclusion block.
`change-narrowed-outside.json` has `planCompatible: true` yet `accepted: false`
and `window_review_required`. An exact single-block interval containing the
actual inclusion accepts (`change-narrowed-match.json`). Widening just the
upper bound refuses before evidence (`change-widened.json`); making a bound a
string produces a structural diagnostic (`change-structure.json`). These
mutated plans are deliberate refusal trials using historical ZTO observations.

```sh
python3 -B shared/window-settlement/test_change.py
```

All 16 integration tests pass, including a detached copy containing only this
folder. They cover actual evidence, exact inclusive narrowing, incompatible
changes before replay, compatible but unmet settlement, both pin gates before
parsing, structural and semantic failures, case/storage aliases, missing
evidence, strict JSON and byte bounds, single plan capture, exact-byte replay,
no network, and unchanged inputs. `gathering/check_round_18.py` runs ten trials
including detached tests/demo, CLI refusal statuses and the Line 2 reversed
range example. Its results are retained under gathering/.

Require exit 0 **and** `accepted: true`; compatibility alone is insufficient.
Exit 1 means checked mismatch or review required; exit 2 means invalid input,
processing failure, inaccessible evidence or complete-report overflow.
On failure, no partial acceptance report is emitted. Plans are bounded at
90,000 bytes, batches at 2–32 items, and complete ASCII reports including the
newline at 100,000 bytes. Safe workspace-relative no-follow reads reject
hidden, traversal, absolute, symlink and nonregular paths. Duplicate keys and
nonfinite numbers refuse. Fixed trusted module paths are local vendor code.

Historical provider assertions are not consensus, state/trie proofs, fresh
observations, payment amount checks, deadlines, authorization or accounting.
An inherited confirmation refusal may surface as `input_error` when strict
replay detects unused reads after early refusal; it never accepts. Replacing
both retained bytes and their pins defeats retention. Nothing reads environment
variables, signs, sends, pays, deploys or opens a wallet. ZTO supplies real
examples; no new coin or runtime dependency is needed.
