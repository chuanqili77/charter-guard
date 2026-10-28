# DEPLOY.md — Deployment

## Canonical deployment (Stable Studionet)

- Network: Stable Studionet, chain 61999, RPC
  `https://studio.genlayer.com/api`.
- Contract: `contracts/charter_guard.py`, class `CharterGuard`.
- Contract SHA-256 (deployed source, verified unchanged after
  deployment):
  `9b4e8476148a119789c207e0a2a26a9a04beef16f7c6c323b82109b4f016a2bc`
- Contract address: `0x77b8E8289a51eb9DCB8Dd6b9f000F4E31e0b8A82`
- Explorer:
  https://explorer-studio.genlayer.com/address/0x77b8E8289a51eb9DCB8Dd6b9f000F4E31e0b8A82
- Deploy transaction:
  `0x6bcc0b812d4ef302ed5ea7dba7126054b270da138480c28d01f92d0f80aeeb3f`
  (FINALIZED, status 7, `tx_execution_succeeded`).
- Deployed with the `gltest` CLI path from the reproducible
  environment (see TESTING.md). Studio-UI deployment was not
  performed.

## Demo chamber record on the canonical contract

Both demo proposals cite the same fictional charter text (the
"Meridian Collective" charter), so the chamber record shows one
compliant and one violating proposal side by side.

| Proposal | File tx | Rule tx | Result |
| --- | --- | --- | --- |
| `demo-grants-q4` | `0xcff195a120cddad2ad042a245508afef3d21dedd6d5626aa817e122e4d885eb0` | `0x13fad14a5da34d2d802bb54908249985ced036eccce2b108e1e6f3249f9e` | RULED / COMPLIANT / compliant |
| `demo-audit-80k` | `0x086f733ff4465ddcc2d214805e90a2c5d78ba50faaf03538ba8c70683f8f9981` | `0x1d2afeaa8371058162e7d97a7f07c6e2ac11c275a0c070a406070a4ec438f5c0` | RULED / VIOLATION / spending_limit |

All five transactions FINALIZED, status 7, `tx_execution_succeeded`
verified one by one. The filer of both demo proposals is the gltest
auto-generated test account
`0x43450A2b0251bbe12dad08aF4de369111dF78893`. Full records and
summaries are in `evidence/EVIDENCE.md` and
`evidence/studionet_assess.json`.

Design note: the violation proposal was deliberately designed to
break exactly one hard rule (the Article 1 spending cap), so the
ruling category is unambiguous; a proposal breaking several rules
at once would risk validators disagreeing on which category to
report.

## Frontend write verification

The frontend's contract-call layer was exercised from Node with a
throwaway generated genlayer-js account (discarded after the run),
filing proposal `node-verify-mvrkq9fh`:

- Transaction:
  `0xbc3806e1aa4bab8fe377c3e6fdd145bf595343c98e44a499e8b968351ef0d8e0`
  (receipt status 7).
- Read back: `FILED`, filer
  `0x183F9fD82EdaE4Beb019De23Ca6Fce70F7e809ae`.
- Script: `frontend/scripts/verify-frontend-call.mjs`.

The canonical contract therefore holds 3 proposals (2 RULED + 1
FILED). Browser MetaMask writes were not executed by the author;
the same code path was verified with the throwaway account above.

## Demo site

- Source: `frontend/` (Vite + vanilla JS + genlayer-js 1.1.8).
- Contract address injected via `VITE_CONTRACT_ADDRESS` in
  `frontend/.env` before build; the built bundle was verified to
  contain the canonical address.
- Published on GitHub Pages (gh-pages branch, dist output only):
  https://chuanqili77.github.io/charter-guard/ (HTTP 200 verified).

## Reproduce the deployment

From the project root, with the reproducible environment:

```
.venv-repro/bin/gltest --network studionet tests_integration -v -s
```

The integration test deploys a fresh instance, files the two demo
proposals, rules on both, and writes `evidence/studionet_assess.json`.
It asserts only closed-set membership for verdicts and categories;
the actual demo verdicts on the canonical instance are recorded in
evidence, not forced by the test.
