# Offline EIP-712 digest inventory

Calculate a bounded collection of typed-data requests, identify repeated digests
and show which entries share a domain separator. This helps a worker spot the
same encoded request delivered under different labels or JSON spellings. Each
entry may also carry a separately retained expected digest. Python standard
library only; copy this whole folder to use it independently.

From the repository root, run this one command:

```sh
(cd line-4/tools/digest-inventory && python3 -B digest_inventory.py zto-inventory.json)
```

Tried: exit 0, `complete: true`, `allSuppliedExpectationsMatch: true`,
`allEntriesPinned: false`. The historical ZTO request and its alternate integer
and address spellings share digest
`0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`.
The third request changes the amount by one raw unit: its digest differs, while
all three domain separators match. These variants are deliberate local examples.
The unchanged historical fixture commits to an observation of real ZTO at
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`. This custom evidence message is
not a token permit, fresh chain observation or contract authorization. Its demo
expected digest is inherited, not independent approval.

The manifest has exactly `requests`, an array of 1–16 entries. Each entry has
exactly `id`, `path` and optionally `expect` (32-byte hexadecimal digest). IDs
are unique 1–64-character ASCII labels starting with a letter or digit and then
letters, digits, periods, underscores or hyphens. Paths are 1–1024 characters,
resolved from the current working directory. Supply actual request JSON files
and independently obtained digest expectations for your own review. The complete
manifest is validated before request reads; each entry is read once. Repeated
paths are allowed and captured separately per entry; this is not an atomic
snapshot of a concurrently changing directory.

The inherited no-follow reader allows only nonhidden regular files beneath the
current working directory, refuses symlinks and traversal, and caps each JSON
file at 65,536 bytes. Its parser rejects duplicate keys, floating-point numbers,
invalid Unicode and excessive depth/nodes/schema. Reports, including their final
newline, are capped at 65,536 bytes. Hash groups preserve first-seen manifest
order and only include groups of two or more. No inputs are modified. No network,
environment, wallet, signing, transaction sending or configuration is used.

Exit 0 means all entries calculated and every **supplied** expectation matched;
it is possible with no expectations. Require `allEntriesPinned: true` if every
request must have an expectation. Exit 1 means a supplied expected digest differs;
the complete inventory remains available. Exit 2 means invalid/inaccessible input
or exceeded bounds: stderr has a diagnostic and stdout has no partial inventory.
Neither exit 0 nor a repeated digest recommends signing or rejecting a request.
Domain sharing is normal and is not proof of a replay vulnerability. Equal hashes
do not imply identical JSON, consent, signer identity, payment or replay safety.
Unused declarations may differ without affecting an EIP-712 digest. The encoder
is reused, not a second independent cryptographic implementation.

Tests:

```sh
python3 -B -m unittest discover -s line-4/tools/digest-inventory -v
```

All 13 tests passed, covering equivalent spellings, amount and chain changes,
expected-digest mismatch, missing pins, case normalization, invalid unselected
entries, full-manifest validation before reads, single capture per entry,
immutability, stable group order, unsafe paths, absent files, output limits and
CLI status/output behavior. Exact vendored source hashes are in `provenance.json`.
