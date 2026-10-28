# Evidence — CharterGuard on Stable Studionet

All transactions below are FINALIZED, status 7, with
`tx_execution_succeeded` verified one by one. No transaction was
resent: every hash below is a first send. The Studionet
integration run passed on its first attempt (282.15 s, 0 failed
attempts, no gateway errors, no retries).

## Canonical contract

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
  (FINALIZED, status 7).
- Deployed with the `gltest` CLI path from the reproducible
  environment (see TESTING.md). Studio-UI deployment was not
  performed.

## The demo charter

Both demo proposals cite the same fictional charter text (the
"Meridian Collective" charter), written for this demo so the
chamber record shows one compliant and one violating proposal
side by side:

> Article 1 - Spending: no single proposal may allocate more than
> 50,000 GEN from the treasury in one quarter. Article 2 -
> Procedure: every proposal must be discussed for at least 7 days
> and receive votes from at least 60% of voting members before
> execution. Article 3 - Self-dealing: no proposal may direct
> treasury funds to its own author or to an entity the author
> controls. Article 4 - Membership: only members in good standing
> may author proposals; suspended members may not author proposals.

## Demo chamber record

| Proposal | File tx | Rule tx | Result |
| --- | --- | --- | --- |
| `demo-grants-q4` | `0xcff195a120cddad2ad042a245508afef3d21dedd6d5626aa817e122e4d885eb0` | `0x13fad14a5da34d2d802bb54908249985ced036eccce2b108e1e6f3249f9e` | RULED / COMPLIANT / compliant |
| `demo-audit-80k` | `0x086f733ff4465ddcc2d214805e90a2c5d78ba50faaf03538ba8c70683f8f9981` | `0x1d2afeaa8371058162e7d97a7f07c6e2ac11c275a0c070a406070a4ec438f5c0` | RULED / VIOLATION / spending_limit |

All five transactions FINALIZED, status 7. The filer of both demo
proposals is the gltest auto-generated test account
`0x43450A2b0251bbe12dad08aF4de369111dF78893`.

### demo-grants-q4 — COMPLIANT / compliant

Proposal: allocate 20,000 GEN for the Q4 community grants round,
discussed 10 days, 72% of voting members voted, author receives
nothing. Validator summary: "The proposal allocates 20,000 GEN
(under the 50,000 GEN quarterly limit), was discussed for 10 days
(exceeding the 7-day minimum), and received votes from 72% of
voting members (exceeding the 60% threshold). It also complies
with self-dealing restrictions as the author receives no funds."
The summary checks every article explicitly — observable proof
the validators compared the proposal against the charter text,
not merely its headline.

### demo-audit-80k — VIOLATION / spending_limit

Proposal: allocate 80,000 GEN to an independent auditor, discussed
10 days, 71% participation, author receives nothing. Validator
summary: "Checked Article 1 spending, Article 2 procedure,
Article 3 self-dealing, and Article 4 membership. The proposal
violates Article 1 because it allocates 80,000 GEN, exceeding the
50,000 GEN single-proposal quarterly cap." The violation proposal
was deliberately designed to break exactly one hard rule, so the
category is unambiguous; a proposal breaking several rules at once
would risk validators disagreeing on which category to report.

## Design notes recorded honestly

- Neither demo proposal files a source URL. The charter and
  proposal texts are the primary evidence by design, and sources
  are optional. On-chain source fetching during a ruling is
  therefore covered by the stand-in suite (partial fetch,
  all-sources-failed still rules on texts, unreachable key fact →
  `UNCLEAR` / `source_unreachable`), not by a chain demo.
- Verdict/category combinations observed live: `COMPLIANT` /
  `compliant` and `VIOLATION` / `spending_limit` only. All other
  combinations (`process_violation`, `self_dealing`,
  `values_conflict`, `insufficient_evidence`, `ambiguous_text`,
  `source_unreachable`, `UNCLEAR` variants) are covered by the
  stand-in suite and the strict parser, not observed on-chain, and
  are not claimed as live-verified.
- No Appeal was sent for any transaction. No personal wallet or
  key was used anywhere in this evidence.

## Machine-readable record

`evidence/studionet_assess.json` — deploy receipt, rule receipts,
and full ruled records for both demo proposals, written by the
integration test itself.
