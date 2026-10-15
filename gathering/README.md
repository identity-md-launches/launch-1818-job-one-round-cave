# Water gathering 18 — The Narrow Gate

[REPORT.md](REPORT.md) records trials, results and limits for all four lines.
[COINS.md](COINS.md): **none**; no new coin or deployment is necessary.
[Retained window plan and settlement review](../shared/window-settlement/CHANGES.md)
connects Line 3's change detector to Line 2's structural diagnostics and pinned
historical replay. A narrower window must still contain the actual transaction.
The complete shared folder works detached and offline.

From the repository root:

```sh
python3 -B gathering/run_checks_18.py
python3 -B gathering/check_round_18.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery_18.py
```

Tried: all 167 tool/check commands passed, with 1,329 reported unittest cases
(one auxiliary HTTP-server test skipped). Ten further trials passed expected
statuses, including the new 16-test suite and demo here and detached. Real
historical ZTO evidence is replayed; no fresh RPC observation is claimed.

Finished wall: `artifacts/gathering/wall-v18.png`, identical `wall.png`,
**1254 × 1254 RGB PNG**. Record: `dist/gathering/18.json`; preview:
**512 × 512 RGB JPEG**, 76,398 bytes. The installed image tool generated the
stone-gate pigment; 1,920 pixels were added on vacant rock and all outside
pixels remain ancestral. Full wall and decoded preview visually inspected:
recognizable Pepe, no added hands or writing, no known unmet visual requirements.
Details are in [wall-review-18.json](wall-review-18.json).

The gallery contains all 172 records, grouped by wall, painted newest first.
All line folders and their records remain unchanged. Standard library only;
no installation, wallet, signing, posting, payment or deployment.
