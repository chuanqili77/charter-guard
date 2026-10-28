# MECHANISM.md — How CharterGuard decides

## The problem in one paragraph

A DAO charter is a constitution in plain language: spending caps,
procedure, quorum, a ban on self-dealing. A proposal either
complies with it or it does not, but that question is a judgement
call over text, and today it is answered by whoever runs the vote
or benefits from the outcome. CharterGuard replaces both with
validator consensus over the filed texts, plus live web evidence
when a compliance question depends on a fact.

## What is deterministic, what is judged

Deterministic code owns everything that can be decided exactly:

- Input bounds (lengths, id charset, `https://` sources, duplicate
  -id rejection). Sources are optional; zero sources is valid.
- Proposal identity and lifecycle: `FILED` → `RULED`, and `RULED`
  is terminal. No transition can be forced by an LLM output.
- Storage: records are JSON strings in a `TreeMap`, ids are kept
  in creation order as one newline-joined string under a single
  index key, and the count is a `u32` incremented with
  `u32(int(x) + 1)`. These shapes are the ones verified to work on
  the Studionet validator runtime; `DynArray` storage is not
  assumed to work there.
- No deterministic verdict shortcut: unlike a source-only verdict,
  a charter ruling cannot be forced to `UNCLEAR` when sources fail,
  because the charter and proposal texts are themselves the
  primary evidence. The LLM still judges, with `FETCH_FAILED`
  markers in place of unloaded sources.

The LLM judges exactly one decision: the verdict (`COMPLIANT` /
`VIOLATION` / `UNCLEAR`) and a reason category from a closed list
(`compliant`, `spending_limit`, `process_violation`,
`self_dealing`, `values_conflict`, `insufficient_evidence`,
`ambiguous_text`, `source_unreachable`). Its one-or-two-sentence
summary is stored as context only and never drives a transition.

## The ruling flow

1. `rule_proposal` loads the record and rejects anything not
   `FILED`.
2. The leader function fetches each filed source with
   `gl.nondet.web.render(url, mode="text")`, truncated to 6000
   characters per source. A failed fetch contributes a
   `FETCH_FAILED` marker for that source. When no sources were
   filed, the prompt says so explicitly and the ruling proceeds on
   the texts alone.
3. The leader builds a prompt: a short adjudicator instruction,
   the weighing rules below, the filed title, proposal text, and
   charter text (each sanitised, see below), and the fetched
   source sections. `gl.nondet.exec_prompt` returns JSON, parsed
   strictly: verdict and category must be in their closed lists,
   and the summary must be 10–500 characters after trimming
   (longer summaries are truncated, never rejected).
4. `gl.vm.run_nondet_unsafe` hands the leader result to every
   validator, which re-runs the same ruling independently and
   accepts only if its own verdict and category match the leader's
   exactly. Summary wording is deliberately not compared.
5. Only after consensus returns does deterministic code write
   `RULED`, the verdict, the category, the summary, and an
   incremented assessment count.

Fetched page text is never stored and never compared. Pages change,
and validators may legitimately see slightly different bytes.
Consensus is on the decision, not on the page.

## Weighing rules (prompt, not code)

- The charter text is supreme. The proposal's own claims about
  itself never override it.
- A proposal that violates any single hard rule — a spending
  limit, a procedure or quorum requirement, a ban on self-dealing
  — is `VIOLATION` even if every other part complies.
- A proposal too vague to check against the charter is `UNCLEAR`,
  not `COMPLIANT`: silence is not compliance.
- Sources are consulted only for facts a compliance question
  actually depends on. When every filed source fails to load, the
  ruling still proceeds on the texts, but a compliance question
  whose key fact then cannot be checked is `UNCLEAR` with
  category `source_unreachable` or `insufficient_evidence`, never
  a guess.
- `values_conflict` is only for proposals that contradict the
  charter's stated values without breaking a hard rule; it is not
  a fallback for weak evidence.

## Prompt-boundary sanitisation

Filed texts are data, never instructions. Before they enter the
prompt, any tag whose name (after stripping whitespace, slashes,
and case) is `proposal`, `charter`, `source`, or `title` is
replaced with `[removed]`, as is any `===...===` segment whose
inner text mentions one of them. Only the prompt copy is affected;
the stored record keeps the original text. The replacement is
shorter than any marker it replaces, so sanitisation never expands
the text.

## What consensus does not guarantee

- That a source document is genuine. Validators read what the URL
  serves; a forged page would fool any reader.
- That the summary prose is identical across validators. Only
  verdict and category are compared.
- That every verdict/category combination has been observed live.
  See evidence/EVIDENCE.md for the combinations actually observed.
