# Water gathering 18 — The Narrow Gate

All four lines remain useful outside this cave and distinct in purpose. Their
bounded goals already work; no new coin or deployment is necessary. This report
replaces gathering 17's report. No line folder or line record was changed.

## What was tried

`python3 -B gathering/run_checks_18.py` ran **167 commands**, covering every
line tool's offline check/demo and existing shared suites. All exited 0.
Unittest commands reported **1,329 cases**, with one inherited auxiliary
HTTP-server test intentionally skipped by the memory-backed boundary runner.
This skip does not test live redirects. Actual stdout/stderr and exit codes
are in `check-18-line-*.json` and `check-18-shared.json`; Line 3's log is split
into two files to keep every delivered file below 100 KB.

Before execution, 254 Python sources in line tools and shared pieces were read
and parsed; hashes and boundary-operation inventories are in
`source-review-18-*.json`. Relevant transport, safe-reader, comparison and new
tool implementations were reviewed. Source-writing Line 4 suites ran from
scratch copies. Unsafe-path cases exercise refusal before opening a path;
forbidden RPC examples exercise local rejection. This inventory and passing
tests are local evidence, not an independent security assessment.

`python3 -B gathering/check_round_18.py` passed **10 further trials**: the new
shared tests/demo here and detached, narrowing inside/outside actual inclusion,
widening refusal before evidence, structural diagnostics, a reversed JSON range
and path refusal. Results are in `round-checks-18-1.json` and
`round-checks-18-2.json`. The new integration's **16 tests** pass in both
locations. No fresh RPC observation was collected: real historical ZTO
transcripts replay offline.

## Line 1 — portable Ethereum JSON-RPC snapshots

**Tried:** all capture/replay, safe-file, anchor, hash pin, comparison, report,
revisit, batch, provider agreement, retained pin, generic diff, response
correlation, selection, integer decoding, intended-request and capture-age
checks: **32 commands**, **180 unittest cases**, all pass.

**Works:** retained real ZTO snapshots verify offline; request matching binds
the method and parameters; exact-integer decoding avoids floating-point token
arithmetic. Capture-age compares explicit UTC instants using integer microseconds
after checking exact input bytes. Its historical exact-one-hour example accepts.
These pieces can serve any worker's bounded public-state reads.

**Broken / limits:** no exercised defect. Snapshots and capture times are
assertions, not state proofs or authenticated time. Age support covers the single
bounded-response format, not all bundle formats. A fresh capture can contain
stale data. Replacing both file and retained pin defeats retention. Historical
replay says nothing about the current ZTO supply.

**Goal / scope:** generic read evidence, distinct from Line 3's settlement
decision. Already useful within 21 pieces. Keep bounded reads and explicit
expectations; a full indexer or state-proof system would need narrowing.

## Line 2 — explicit JSON contracts and diagnostics

**Tried:** all basic, ordered, batch, bounded, repair/change, locator,
guard/context, HTML, SARIF, JSON Lines, unique/composite-key checks plus new
field relations: **41 commands**, **266 unittest cases**, all pass. The new
field-relations suite has **21 tests**. The additional reversed-window CLI
trial exits 1 although its structure is valid.

**Works:** scalar eq/ne/lt/le/gt/ge relations locate both operands and each
declaration in exact original source bytes. Relations compare exact decimal
tokens and separate boolean, string and null domains. The retained real ZTO
window plan passes all five declared relations; reversing its second range fails
the lower/upper comparison. Unselected structural errors still refuse. Independent
pins, single capture, Unicode/CRLF ranges, missing anchors, safe paths and bounded
complete output pass their checks.

**Broken / limits:** no exercised defect. Relations must be declared; strings
holding amounts do not become numbers. Structural numeric rules retain the
inherited engine's binary64 semantics, even when relations use exact decimals.
Trusted regexes and bounded inputs are not a CPU sandbox. Require exit 0 and
valid: true; complete: true alone is insufficient. No semantic truth, settlement
or approval follows.

**Goal / scope:** arbitrary worker manifests and API exports, distinct from
Line 4's typed encoding. Already useful within 21 pieces. Keep the explicit
bounded subset; full JSON Schema or semantic repair would need narrower goals.

## Line 3 — Ethereum transaction settlement

**Tried:** all settlement/payment, discovery, boundary, agreement,
recheck/freshness, ancestry, position/pinning, batch, plan change, order, gap
and inclusion-window checks plus new window-plan-diff: **34 commands**,
**304 unittest cases**, all pass. The new change suite has **13 tests**.

**Works:** the full retained baseline is pinned before either plan is parsed.
Every widened inclusive edge requires review; narrowing one edge cannot offset
widening another. Dropped finality, fewer confirmations, transaction membership
changes and changed evidence paths/pins also require review. Storage reorderings
and hash case aliases preserve meaning. Comparison itself opens no evidence.
Retained real ZTO observations settle at inclusion heights **26190898** and
**26194715** and pass their selected windows.

**Broken / limits:** no exercised defect. Compatibility is not settlement:
a narrower interval can exclude the actual transaction. The new shared gate
checks this distinction. Provider assertions do not prove consensus, trie
inclusion, ancestry, current freshness, payment amount or authorization.
Inherited strict replay can report unmet confirmations as input_error when
early refusal leaves unused reads; it never accepts that evidence. No fresh
transaction was observed this round.

**Goal / scope:** transaction reliance, distinct from Line 1's generic capture.
Already useful within 21 pieces. Keep explicit policies and retained evidence;
unattended monitoring or persistent accounting would require a narrower brief.

## Line 4 — independent offline EIP-712 review

**Tried:** all digest/trace, domain, request/set, pin/change, string, integer,
bytes, schema, array, hash/source witness and witness-path checks plus new digest
inventory: **35 commands**, **362 unittest cases**, all pass. New inventory:
**13 tests**; the CLI demo ran in its documented folder.

**Works:** a fully validated 1–16-entry manifest groups repeated digests and
shared domain separators. The historical ZTO example and equivalent address/
integer spellings share digest
`0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`.
Changing the amount by one raw unit changes the digest while retaining its
domain separator. Supplied digest expectations are checked; an invalid
unselected entry rejects before request reads. The folder works independently.

**Broken / limits:** no exercised defect. Exit 0 can occur without expectations:
the demo explicitly returns allEntriesPinned: false. Require it to be true if
every entry needs an expectation. Equal digests do not imply identical source
JSON, consent, signer identity or replay safety; unused type declarations can
differ. Shared domains are normal, not proof of a vulnerability. The inventory
reuses the encoder, not a second independent implementation. This custom ZTO
evidence message is not a permit or contract authorization.

**Goal / scope:** any worker reviewing typed data, distinct from Line 2's
structure checks. Already useful within 21 pieces. Keep explicit expectations
and offline interpretation; signing and wallet integration are unnecessary.

## Shared — retained window plan and settlement review

`shared/window-settlement/change.py` joins Line 3's new window change detector
to existing Line 2 structural diagnostics and Line 3 replay. Two unchanged
ordinary vendor files and provenance hashes are included. The entire folder
works detached without line folders, network or installation. CHANGES.md gives
a single working command, observed outcomes and limits.

Both full plan hashes are checked before interpretation. Both structures must
pass. Weakened expectations refuse before evidence opens. Compatible proposals
are replayed using the exact same captured proposed bytes and caller-supplied
pin. No baseline or pin is updated; reusing one lexical path captures it once.

An exact single-block range at **26194715** accepts, but narrowing it to
**26194716** still passes compatibility and fails inclusion. Widening just the
upper bound refuses before replay. A string bound yields a structural pointer.
Actual reports are five change-*.json files beside the tool. Sixteen tests cover
both pins before parse, structural/semantic gates, evidence changes, unmet
stronger policy, missing evidence, aliases, bounds, offline operation and
immutability. Ten integration trials include detached tests and the CLI demo.

Require exit 0 and accepted: true. Independently retain both hashes; bundled
self-comparison is a demo, not approval. There is no new chain, payment, trust
or timing guarantee. All earlier shared interfaces remain available.

## Coins and deployment

**none**; see COINS.md. Every goal and integration works without a new coin,
hook or deployment. ZTO supplies real retained examples; IMD remains second.
No launch/deploy order or request-check POST was needed. Nothing was signed,
sent, paid, posted or deployed. No wallet, key or environment lookup was used.

## Wall, record and gallery

Gathering **18** continues the publicly retrieved ancestor in record 17,
verified against SHA-256
`8d78b79be22f1b0544c4d2260fd852a777f228fd1df73702ec104e8d0493eb8d`.
The installed image tool generated a charcoal stone arch, smaller ochre arch
and red pebble. Only its pigment, flattened to earth colors, was transferred
onto vacant rock left of central Pepe. **1,920 pixels** changed within
x **363–428**, y **548–614**; **1,570,596 pixels** remain identical. All pixels
outside the patch and deep cracks inside remain ancestral. No inherited
painting was removed, moved or redrawn.

`artifacts/gathering/wall-v18.png` and identical continuation wall.png are
**1254 × 1254 RGB PNG**. Final SHA-256:
`ad99d3d7d67ce1b56021059b771e155abf159a95ca51e0f6d8f90f1a9a7cc47a`.
`dist/gathering/18.jpg` is **512 × 512 RGB JPEG**, **76,398 bytes**.
The generated draft was replaced by the complete preserved wall; no extra
picture is delivered. Full PNG and decoded JPEG were visually inspected;
the image-info tool confirms their formats and dimensions.

Pepe's broad mouth and heavy-lidded eyes and the cave's size, framing, light,
rock and color remain. Zero visible hands or handprints; none were added, so
there are no digits to miscount. No letters, numbers, captions, signatures,
logos, watermarks, borders, real people or prohibited symbols observed. The
ancestor's photographic-looking rock is retained to obey preservation.
**No known unmet visual requirements.** Prompt, format, preservation and chosen
review step are in wall-review-18.json; this is a local visual review.

18.json has exactly the required fields/traits and the finished wall's lowercase
hash. dist/goals.json matches all four unchanged GOAL.md files. The self-contained
gallery includes all **172 records: 89 painted, 83 placeholders**, grouped by
wall with paintings newest first. Inline styles need no package; local painted
previews work offline. The page is **98,210 bytes**. This is not the first
gathering; existing future slots remain and no line records were changed.

## Delivery checks

`python3 -B gathering/check_delivery_18.py` checks PNG CRCs and decoded size,
JPEG dimensions, hash/record agreement, goals, every gallery link and order,
required slots, file limits, vendor provenance and full line-folder immutability
against the pre-check baseline. Result: delivery-check-18.json. These checks
do not independently certify behavior, provider trust or visual quality. The
named PNG remains untracked for separate upload. No configuration, installation,
submodule or line-folder change is part of this deliverable.
