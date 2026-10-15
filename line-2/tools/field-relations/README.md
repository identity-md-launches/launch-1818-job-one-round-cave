# Offline JSON field relations

Check relationships between fields in one JSON document, alongside an explicit
structural contract. A range can have valid integer fields and still be reversed;
a manifest can have valid identifiers that disagree. This tool locates both
operands and the selected relation in their exact original source bytes.

Run this from the repository root (Python 3.10+, standard library only):

```sh
python3 -B line-2/tools/field-relations/check.py line-2/tools/field-relations/window.contract.json line-2/tools/field-relations/window-plan.json line-2/tools/field-relations/window.relations.json
```

Tried locally: **exit 0**, structural validity and all **five relations pass**.
The document is an exact copy of the retained `shared/window-settlement/plan.json`:
two historical ZTO transaction policies with block windows. The comparisons
require each lower block bound to be at most its upper bound, each window's
transaction hash to match the corresponding policy, and the hashes to differ.
The original file hash is recorded in `provenance.json`.

Replace `window-plan.json` in that command with `reversed-window.json` to see a
rejection (**exit 1**). Its second lower bound was deliberately moved past its
upper bound. Structure still passes, but relation index 2 fails at
`/windows/1/notBeforeBlock` and `/windows/1/notAfterBlock`. Both original tokens
and the relation declaration have source ranges. Actual complete outputs are
`window.result.json` and `reversed.result.json`. This modified fixture is a
rejection demonstration, not evidence of an actual failed settlement.

## Writing a plan

The caller supplies all three file paths. The plan contains only `relations`,
an array of 1–64 objects, each with exactly these three string fields:

```json
{"relations": [{"left": "/minimum", "op": "le", "right": "/maximum"}]}
```

Pointers use RFC 6901 escaping (`~0` for tilde, `~1` for slash); the empty string
selects the root. Array indexes use canonical decimal spelling. Pointers are at
most 1,024 characters. Identical pointers and repeated relations are permitted.
No wildcards, expressions, external references, path discovery or implicit
relations are supported. The example contract deliberately describes two
items; use your own explicit contract and relations for a different document.

- `eq` and `ne` compare scalar values. Numbers compare by their exact original
  decimal tokens, so `1` equals `1.0`; binary64 rounding never decides a relation.
  Boolean, number, string and null are separate types. Strings compare decoded
  JSON code points exactly, without normalization or case folding.
- `lt`, `le`, `gt`, `ge` require two numbers and compare their exact decimal
  values. Numeric strings, booleans and null do not become numbers. In particular,
  a token amount encoded as a string is not numerically ordered by this tool.
- Missing operands, objects and arrays always reject, including with `ne`.
  Each missing operand names its nearest existing ancestor as an anchor, never
  inventing a source token for the absent value.

Every relation is evaluated, even when structure fails. Acceptance requires
**both** full structural validity and every relation passing; an invalid field
outside the selected pointers still rejects. Reports contain all structural
diagnostics plus both operands and the declaration for every relation, whether
it passed or failed. `complete: true` means evaluation finished, not acceptance.
Require exit 0 **and** top-level `valid: true`.

Source ranges are zero-based, end-exclusive UTF-8 byte offsets and Unicode
character offsets, plus one-based lines and code-point columns. CRLF and original
escape spelling are preserved. All output is ASCII JSON with escaped control
characters. The complete serialized report including its newline must fit
100,000 bytes; overflow emits no partial stdout report and exits 2.

## Input identity and boundaries

Optional `--contract-sha256 HASH`, `--document-sha256 HASH` and
`--plan-sha256 HASH` compare separately retained lowercase exact-byte hashes
before parsing the corresponding captured source. They pin whitespace too.
The plan is validated before reading the contract; the contract is prepared
before reading the document. Each distinct input path is captured once, even
when reused for multiple roles; parsing, hashes and ranges use those bytes.
Hashes identify bytes; they do not authenticate an author or approve a policy.

Each input must be a visible relative regular file inside the current workspace,
at most 1,000,000 bytes. The inherited no-follow reader refuses absolute, hidden,
parent, symlink, directory and special-file paths. Inputs never choose additional
files to read: `evidence` strings in the demo remain inert strings.
Exit 2 means an invalid plan/contract, malformed source, boundary/pin failure or
output overflow. Inputs are never changed. Nothing contacts the network,
reads environment variables, opens a wallet, signs or sends anything.

This extends the existing bounded contract subset, not full JSON Schema.
Structural numeric rules retain the ancestor engine's semantics, including
binary64 floats. The inherited parser rejects nonfinite floats (including
`1e309`), duplicate keys and malformed JSON before comparison; Python's integer
and Decimal implementation limits also apply. Trusted regular expressions and
bounded bytes are not a CPU sandbox. Passing describes supplied data only:
no settlement, payment, block inclusion, current chain truth, balance, consent
or authorization is established. No new coin or dependency is needed.

## Checks and portability

```sh
python3 -B line-2/tools/field-relations/test_check.py
```

All **21 tests passed**, covering every operator, decimal rounding and underflow,
type distinctions, root/escaped/array pointers, Unicode/CRLF exact spans, missing
anchors, invalid unselected fields, invalid plans and read ordering, malformed
sources, independent pins, single capture, no-follow paths, unchanged inputs,
complete-output bounds including empty stdout on CLI overflow, saved ZTO plans
and CLI exit codes. The inherited JSON Lines uniqueness (19 tests) and source
locator (16 tests) suites passed separately: **56 tests total**.

Keep the unchanged `jsonl-unique`, `jsonl-contract`, `source-locator`,
`rule-locator`, `bounded-contract` and `json-contract` sibling folders alongside
this folder. Their ordinary committed sources supply comparison helpers,
source indexing, structural validation, safe reads and bounded serialization.
Run within the workspace that contains those folders. POSIX no-follow file
support is required. No installation, submodule or runtime download is used.
