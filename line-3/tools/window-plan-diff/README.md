# Window plan change review

Detect widening of an Ethereum inclusion window or weakening of settlement
expectations against an independently retained, exact-byte baseline SHA-256.
Python 3.9+ standard library; offline, read-only. Run from the repository root:

```sh
python3 -B line-3/tools/window-plan-diff/window_diff.py --demo
```

Tried locally: the unchanged inherited plan for two historical real ZTO
transactions returns `planCompatible: true`, `plan_unchanged_or_stricter`, exit 0.
Thirteen focused tests pass. Widening either inclusive block bound returns
`plan_review_required`, exit 1. This round collects no fresh chain observation.

For your own settlement-window version-1 plans:

```sh
python3 -B line-3/tools/window-plan-diff/window_diff.py --baseline your/baseline.json --proposed your/proposed.json --baseline-sha256 YOUR_INDEPENDENTLY_RETAINED_64_HEX_SHA256
```

The entire baseline is pinned before parsing either document. Both full plans
must validate, including unique normalized transaction identities and exactly
one ordered uint64 block window per transaction. A lower `notBeforeBlock` or
higher `notAfterBlock` widens the allowed interval and requires review. Narrowing
is compatible, including an exact single-block interval. Every edge is assessed
separately: tightening one edge cannot compensate for widening another. Changes
are reported in normalized transaction-hash order, including later failures.
Window and batch storage reordering and transaction hash case do not weaken
expectations. Formatting changes are visible in the two exact input hashes.

The unchanged settlement-plan-diff engine also detects added/removed transactions,
changed evidence pins or paths, lower confirmations, and dropped finality.
Those changes require review; stronger settlement policy is compatible. Added
or removed windows follow transaction membership and are reflected in the batch
comparison. Neither `planCompatible` nor a narrower interval asserts settlement:
**run settlement-window on the proposed plan separately after review**. A narrow
window can exclude the actual transaction, and stricter policies can require
new evidence. This tool never opens referenced evidence or makes RPC requests.
It emits no settlement `accepted` field and does not update the baseline or pin.

Exit 0 means unchanged or stricter expectations; exit 1 means a baseline pin
mismatch or a change needing review; exit 2 means invalid input/path/size. Require
exit 0 and top-level `planCompatible: true`. Input files are at most 90,000 bytes;
output including its newline is at most 100,000 ASCII bytes. The inherited strict
JSON parser rejects duplicate keys and nonfinite numbers; safe workspace-relative
reads refuse hidden components, traversal, symlinks and nonregular files.
Retain the baseline pin independently: replacing both defeats this boundary.
The bundled pin is a usage example, not independent approval. No current
freshness, chain proof, payment amount or authorization follows.

Tests:

```sh
python3 -B -m unittest discover -s line-3/tools/window-plan-diff -p 'test_*.py' -v
```

Reuses unchanged sibling settlement-window and settlement-plan-diff modules,
transitively settlement-batch, pinned-position, tx-position, payment-witness and
settlement-check. The demo needs settlement-window/demo-plan.json and its hash.
All dependencies are ordinary repository files; no installation is required.
