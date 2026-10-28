# CharterGuard — DAO Charter Compliance Adjudication

A DAO charter is a promise a DAO makes to itself: spending caps,
proposal procedure, quorum rules, a ban on self-dealing, membership
rules. But a charter written in plain language cannot enforce
itself, and today compliance is usually judged by whoever runs the
vote — or by a committee whose members are also the proposal's
beneficiaries. The argument is settled by an interested party, and
the losing side has no neutral record to point at.

CharterGuard moves that argument to a place neither side controls.
Anyone files a governance proposal together with the charter text
it must comply with, plus up to three optional public sources for
any real-time fact the compliance question depends on (a treasury
balance, a token price, a membership registry). GenLayer validators
compare the proposal against the charter article by article,
fetching those sources live when a fact needs checking, and must
agree exactly on the verdict and the reason category before the
decision is stored. The decision becomes shared on-chain state
instead of one more forum thread.

## Verdicts

- **COMPLIANT** — the proposal complies with every applicable
  charter rule.
- **VIOLATION** — the proposal violates at least one hard charter
  rule.
- **UNCLEAR** — the texts cannot settle compliance, or a key fact
  cannot be checked.

Reason categories (closed list): `compliant`, `spending_limit`,
`process_violation`, `self_dealing`, `values_conflict`,
`insufficient_evidence`, `ambiguous_text`, `source_unreachable`.

Lifecycle: `FILED` → `RULED`. A ruling is terminal; an amended
proposal is filed as a new record.

## Contract

`contracts/charter_guard.py` — class `CharterGuard`, 6 methods
(4 view / 2 write):

| Method | Type | Purpose |
| --- | --- | --- |
| `file_proposal(proposal_id, title, proposal_text, charter_text, source_url_1, source_url_2, source_url_3)` | write | File a proposal with 0–3 sources |
| `rule_proposal(proposal_id)` | write | Run validator consensus and store the ruling |
| `get_proposal(proposal_id)` | view | Full record JSON, or `""` when missing |
| `get_status(proposal_id)` | view | `FILED`, `RULED`, or `NOT_FOUND` |
| `get_proposal_count()` | view | Number of proposals, as a string |
| `get_proposal_id(index)` | view | Proposal id by creation order, or `""` |

Bounds: id ≤ 64 chars `[A-Za-z0-9_-]`; title 1–128; proposal text
10–2000; charter text 10–3000; each source URL ≤ 500 chars,
`https://` only. Sources are optional: the charter and proposal
texts are themselves the primary evidence. Empty strings mean
"source absent" for any source slot.

See [MECHANISM.md](MECHANISM.md) for the consensus design,
[TESTING.md](TESTING.md) for the test suites, and
[DEPLOY.md](DEPLOY.md) for deployment. On-chain evidence lives in
[evidence/EVIDENCE.md](evidence/EVIDENCE.md).

## Why GenLayer, not a backend check

Whether a proposal complies with a charter is a judgement call
over natural language, and the facts it may depend on live on the
open web, outside any ordinary contract's reach. A single backend
LLM call is one opinion, and it never touches the charter the same
way twice. CharterGuard puts the whole job through validator
consensus: each validator compares the filed texts, fetches any
filed sources live when a fact needs checking, and must agree
exactly on verdict and category. The proposer does not grade their
own proposal, and neither does the committee that benefits from it.

## Try it

1. Open the demo site (link in DEPLOY.md) and connect MetaMask.
   Switch to Stable Studionet (chain 61999) when prompted.
2. The chamber record lists the two demo proposals: one the
   charter permits, one it forbids, both judged against the same
   charter text.
3. File your own proposal: paste the proposal text and the charter
   text exactly as written, and add sources only when a compliance
   question depends on a live fact.
4. Rule on it and watch the verdict land on-chain.

## Sustained use

CharterGuard is built to keep being useful after the demo. Every
DAO already has a charter, and every proposal is the same shape: a
text, a charter, an optional fact check. New DAOs need no contract
change, only new filings. The chamber record is permanent, so a
pattern of violations by one author — or of proposals that keep
testing the same article — becomes visible to every member, not
just to whoever happened to read the forum that week. That is the
point: a charter only binds when breaking it leaves a public,
consensus-backed record.

## Honest limits

- CharterGuard rules; it does not execute. No funds move through
  this contract, and a ruling here is not an execution instruction.
- The ruling judges the filed charter and proposal texts, plus the
  filed sources, only. It does not audit a treasury, verify that a
  source document itself is genuine, or detect a forged source page:
  a forged page would fool any reader, including validators.
- Fetched page text is truncated to 6000 characters per source, so
  very long pages are judged on their opening sections. Filers
  should link the specific page that carries the fact.
- If no sources are filed, the ruling is made on the texts alone.
  If every filed source fails to load, the ruling still proceeds
  on the texts, but a compliance question whose key fact then
  cannot be checked is `UNCLEAR` / `source_unreachable` or
  `insufficient_evidence`, never a guess.
- The demo chamber's two proposals share one charter by design, to
  show one compliant and one violating proposal side by side. Live
  rulings on other proposals depend on what their own charters say.
- On-chain source fetching during a ruling is covered by the
  stand-in suite, not by a chain demo: the demo proposals file no
  sources, because the charter and proposal texts are the primary
  evidence (see evidence for what was observed live).
- Studio-UI deployment was not performed; deployment used the
  `gltest` CLI path on Stable Studionet.
- The frontend's MetaMask write path was verified with a throwaway
  genlayer-js account (see evidence), not by the author signing
  with a personal wallet in a browser.
- Not every verdict/category combination has been observed live
  (see evidence for which ones have). Unobserved combinations are
  untested on-chain, not assumed.
- The summary wording of a ruling is stored as context only:
  consensus covers verdict and category, not prose.
