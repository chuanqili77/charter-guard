# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""CharterGuard: DAO charter compliance adjudication on GenLayer.

A DAO's charter is its constitution: spending limits, proposal
procedure, quorum rules, a ban on self-dealing, membership rules.
But a charter written in plain language cannot enforce itself, and
today compliance is usually judged by whoever runs the vote, or by
a committee whose members are also the proposal's beneficiaries.
The argument is settled by an interested party, and the losing
side has no neutral record to point at.

CharterGuard moves that argument to a place neither side controls.
Anyone files a governance proposal together with the charter text
it must comply with, plus up to three optional public sources for
any real-time fact the compliance question depends on (a treasury
balance, a token price, a membership registry). GenLayer validators
then compare the proposal against the charter, article by article,
fetching those sources live when a fact needs checking, and the
decision becomes shared on-chain state instead of one more forum
thread.

Why this needs GenLayer
-----------------------
Whether a proposal complies with a charter is a judgement call
over natural language, not a computation, and the facts it may
depend on live on the open web, outside any ordinary contract's
reach. A single backend LLM call is one opinion, and it never
touches the charter the same way twice. CharterGuard puts the
whole job through validator consensus:

1. Deterministic code owns everything that can be decided exactly:
   input bounds, proposal identity, lifecycle transitions, and
   storage. No LLM output can file a proposal, change a filer, or
   move a record to a state the lifecycle forbids.
2. The charter and proposal texts are filed on-chain as data and
   compared in full. Each validator independently fetches any
   filed source URLs live (gl.nondet.web.render, text mode) when
   a compliance question depends on a fact; fetched page text is
   never stored and never compared, because pages change.
   Consensus is on the decision, not on the page.
3. The LLM judges exactly one decision: the verdict (COMPLIANT /
   VIOLATION / UNCLEAR) and a reason category from a closed list.
   Its summary is stored as context only and never drives a
   transition.
4. Equivalence principle: a validator re-runs the same ruling and
   must agree exactly on the two decision fields, verdict and
   category. Summary wording is deliberately not compared, because
   models phrase the same judgement differently. A validator that
   reaches a different verdict or category disagrees, and a
   malformed leader output is rejected, never agreed on.
5. State is written only after consensus, in deterministic code.

How the charter is weighed (prompt rule, not code)
---------------------------------------------------
The charter text is supreme. A proposal that violates any single
hard rule in it -- a spending limit, a procedure or quorum
requirement, a ban on self-dealing -- is VIOLATION even if every
other part complies. A proposal too vague to check against the
charter is UNCLEAR, not COMPLIANT: silence is not compliance. The
proposal's own claims about itself never override the charter
text. Sources are consulted only for facts a compliance question
actually depends on; when every filed source fails to load, the
ruling still proceeds on the charter and proposal texts, but a
compliance question whose key fact cannot then be checked is
UNCLEAR with category source_unreachable or
insufficient_evidence, never a guess.

Lifecycle
---------
FILED -> RULED (verdict COMPLIANT, VIOLATION or UNCLEAR).
RULED is terminal: an amended proposal is filed as a new record
instead of rewriting history, so the chamber record stays an
honest public record of what was proposed and how it was ruled.

Scope and limits (see README.md and MECHANISM.md)
-------------------------------------------------
* Proposal ids are at most 64 characters, [A-Za-z0-9_-]; titles
  are 1-128 characters; proposal texts are 10-2000 characters;
  charter texts are 10-3000 characters; each proposal files 0-3
  source URLs, each at most 500 characters, https only. Sources
  are optional: the charter and proposal texts are themselves the
  primary evidence.
* The verdict judges the filed charter and proposal texts, plus
  the filed sources, only. It does not audit a treasury, verify
  that a source document itself is genuine, or execute the
  proposal: CharterGuard is the adjudication layer, not the DAO's
  treasury. A forged source page would fool any reader, including
  validators.
* Fetched page text is truncated to 6000 characters per source
  before it reaches the prompt, so very long pages are judged on
  their opening sections. Filers should link the specific page
  that carries the fact, not a homepage.
* If no sources are filed, the ruling is made on the texts alone.
  If some sources fail to load, the ruling is judged on the ones
  that did, plus the texts.
* This file is intentionally self-contained for Studio deployment:
  it imports only ``json`` besides the GenLayer SDK, and all pure
  helpers are module-level so they can be unit-tested without a node.
* No chain interaction, payment, or private key is involved in this
  file. Deployment is described in DEPLOY.md; recorded deployments
  are listed in evidence/EVIDENCE.md.
"""

from genlayer import *

import json

MAX_PROPOSAL_ID_CHARS = 64
MAX_TITLE_CHARS = 128
MAX_PROPOSAL_CHARS = 2000
MIN_PROPOSAL_CHARS = 10
MAX_CHARTER_CHARS = 3000
MIN_CHARTER_CHARS = 10
MAX_SOURCE_URL_CHARS = 500
MAX_SOURCES = 3
MAX_FETCH_CHARS = 6000
MAX_SUMMARY_CHARS = 500
MIN_SUMMARY_CHARS = 10

VERDICTS = ("COMPLIANT", "VIOLATION", "UNCLEAR")
CATEGORIES = (
    "compliant",
    "spending_limit",
    "process_violation",
    "self_dealing",
    "values_conflict",
    "insufficient_evidence",
    "ambiguous_text",
    "source_unreachable",
)


def _fail(code, detail=""):
    raise gl.vm.UserError(code + (": " + detail if detail else ""))


def _validate_text(value, label, min_chars, max_chars):
    if not isinstance(value, str) or not value.strip():
        _fail("INVALID_INPUT", label + " must be a non-empty string")
    if len(value) < min_chars or len(value) > max_chars:
        _fail(
            "INVALID_INPUT",
            label
            + " must be "
            + str(min_chars)
            + "-"
            + str(max_chars)
            + " characters",
        )


def _validate_proposal_id(proposal_id):
    if not isinstance(proposal_id, str) or not proposal_id:
        _fail("INVALID_INPUT", "proposal_id must be a non-empty string")
    if len(proposal_id) > MAX_PROPOSAL_ID_CHARS:
        _fail("INVALID_INPUT", "proposal_id is too long")
    for ch in proposal_id:
        if not (ch.isalnum() or ch in ("-", "_")):
            _fail(
                "INVALID_INPUT",
                "proposal_id may only contain letters, digits, - and _",
            )


def _validate_source_url(url, label):
    if not isinstance(url, str) or not url.strip():
        _fail("INVALID_INPUT", label + " must be a non-empty string")
    if len(url) > MAX_SOURCE_URL_CHARS:
        _fail("INVALID_INPUT", label + " is too long")
    if not url.startswith("https://"):
        _fail("INVALID_INPUT", label + " must start with https://")


def _sanitize_prompt_text(text):
    """Remove forged prompt-boundary markers from user-supplied text.

    The filed title, proposal, charter, and source texts are treated
    as data, never as instructions. A closing tag such as
    ``</proposal>`` inside the text must not be able to end the data
    section early, so any tag whose name (after stripping
    whitespace, slashes and case) is ``proposal``, ``charter``,
    ``source`` or ``title`` is replaced with ``[removed]``, as is
    any ``===...===`` segment whose inner text mentions one of
    them. The replacement is shorter than any marker it replaces,
    so sanitisation never expands the text. Only the prompt copy is
    affected; the stored record keeps the original text.
    """
    watched = ("proposal", "charter", "source", "title")
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "<":
            j = text.find(">", i + 1)
            if j != -1:
                raw = text[i + 1 : j].strip().strip("/").strip().lower()
                if raw in watched:
                    out.append("[removed]")
                    i = j + 1
                    continue
            out.append(text[i])
            i += 1
            continue
        if text.startswith("===", i):
            j = text.find("===", i + 3)
            if j != -1:
                inner = text[i + 3 : j].strip().lower()
                if any(word in inner for word in watched):
                    out.append("[removed]")
                    i = j + 3
                    continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _parse_verdict(raw):
    # Accepts the dict returned by response_format="json" or a JSON
    # string. Returns a verdict dict or None. The summary is
    # truncated, never rejected for length: only verdict and
    # category drive consensus, and a long summary must not void
    # an otherwise agreed decision.
    try:
        data = raw if isinstance(raw, dict) else json.loads(raw)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    verdict = data.get("verdict")
    category = data.get("category")
    summary = data.get("summary")
    if verdict not in VERDICTS or category not in CATEGORIES:
        return None
    if not isinstance(summary, str) or len(summary.strip()) < MIN_SUMMARY_CHARS:
        return None
    return {
        "verdict": verdict,
        "category": category,
        "summary": summary.strip()[:MAX_SUMMARY_CHARS],
    }


class CharterGuard(gl.Contract):
    proposals: TreeMap[str, str]
    id_index: TreeMap[str, str]
    proposal_count: u32

    def __init__(self):
        self.proposals = TreeMap()
        self.id_index = TreeMap()
        self.proposal_count = u32(0)

    def _load(self, proposal_id):
        _validate_proposal_id(proposal_id)
        raw = self.proposals.get(proposal_id, "")
        if raw == "":
            _fail("NOT_FOUND", "proposal does not exist")
        return json.loads(raw)

    def _store(self, record):
        self.proposals[record["proposal_id"]] = json.dumps(record, sort_keys=True)
        return json.dumps(record, sort_keys=True)

    @gl.public.write
    def file_proposal(
        self,
        proposal_id,
        title,
        proposal_text,
        charter_text,
        source_url_1,
        source_url_2,
        source_url_3,
    ) -> str:
        _validate_proposal_id(proposal_id)
        _validate_text(title, "title", 1, MAX_TITLE_CHARS)
        _validate_text(
            proposal_text, "proposal_text", MIN_PROPOSAL_CHARS, MAX_PROPOSAL_CHARS
        )
        _validate_text(
            charter_text, "charter_text", MIN_CHARTER_CHARS, MAX_CHARTER_CHARS
        )
        sources = []
        for label, url in (
            ("source_url_1", source_url_1),
            ("source_url_2", source_url_2),
            ("source_url_3", source_url_3),
        ):
            if url == "":
                continue
            _validate_source_url(url, label)
            sources.append(url)
        if self.proposals.get(proposal_id, "") != "":
            _fail("PROPOSAL_EXISTS", "proposal_id already used")
        record = {
            "proposal_id": proposal_id,
            "title": title,
            "proposal_text": proposal_text,
            "charter_text": charter_text,
            "sources": sources,
            "filer": str(gl.message.sender_address),
            "status": "FILED",
            "verdict": "",
            "category": "",
            "summary": "",
            "assessment_count": 0,
        }
        # Proposal ids are kept in creation order as one
        # newline-joined string under a single index key. This
        # avoids int-to-string key conversion and list-index
        # arithmetic on the chain runtime; see get_proposal_id.
        self.id_index["ids"] = self.id_index.get("ids", "") + proposal_id + "\n"
        self.proposal_count = u32(int(self.proposal_count) + 1)
        return self._store(record)

    @gl.public.write
    def rule_proposal(self, proposal_id) -> str:
        record = self._load(proposal_id)
        if record["status"] != "FILED":
            _fail("INVALID_STATUS", "proposal is not awaiting a ruling")
        proposal_text = _sanitize_prompt_text(record["proposal_text"])
        charter_text = _sanitize_prompt_text(record["charter_text"])
        title = _sanitize_prompt_text(record["title"])
        sources = record["sources"]

        def leader_fn():
            sections = []
            for index, url in enumerate(sources):
                try:
                    page = gl.nondet.web.render(url, mode="text")
                    text = page[:MAX_FETCH_CHARS] if page else ""
                except Exception:
                    text = ""
                if text.strip():
                    sections.append(
                        "[Source "
                        + str(index + 1)
                        + ": "
                        + url
                        + "]\n"
                        + text
                    )
                else:
                    sections.append(
                        "[Source "
                        + str(index + 1)
                        + ": "
                        + url
                        + "]\nFETCH_FAILED"
                    )
            if sections:
                sources_block = "\n\n".join(sections)
            else:
                sources_block = (
                    "No sources were filed. Rule on the charter and "
                    "proposal texts alone."
                )
            prompt = (
                "You are a DAO charter compliance adjudicator. "
                "Compare the proposal against the charter article by "
                "article. The charter text is supreme: the proposal's "
                "own claims about itself never override it. A "
                "proposal that violates any single hard rule in the "
                "charter -- a spending limit, a procedure or quorum "
                "requirement, a ban on self-dealing -- is VIOLATION "
                "even if every other part complies. A proposal too "
                "vague to check against the charter is UNCLEAR, not "
                "COMPLIANT: silence is not compliance. Consult the "
                "fetched sources only for facts a compliance question "
                "actually depends on. If every filed source failed to "
                "load, still rule on the texts, but a compliance "
                "question whose key fact then cannot be checked is "
                "UNCLEAR with category source_unreachable or "
                "insufficient_evidence, never a guess. "
                "Return JSON only with keys verdict, category, summary.\n"
                "verdict: COMPLIANT if the proposal complies with "
                "every applicable charter rule; VIOLATION if it "
                "violates any hard charter rule; UNCLEAR if the texts "
                "cannot settle compliance or a key fact cannot be "
                "checked.\n"
                "category: one of compliant, spending_limit, "
                "process_violation, self_dealing, values_conflict, "
                "insufficient_evidence, ambiguous_text, "
                "source_unreachable. Use spending_limit only when a "
                "charter spending cap is exceeded; "
                "process_violation only when a charter procedure or "
                "quorum requirement is skipped or broken; "
                "self_dealing only when the proposal benefits its "
                "own author or a related party in a way the charter "
                "forbids; values_conflict only when the proposal "
                "contradicts the charter's stated values without "
                "breaking a hard rule; ambiguous_text only when the "
                "proposal is too vague to check; source_unreachable "
                "only when a key fact cannot be checked because the "
                "filed sources failed to load.\n"
                "summary: one or two sentences, 10 to 500 "
                "characters, saying which charter rules were checked "
                "and which one decided the verdict.\n"
                "<title>\n" + title + "\n</title>\n"
                "<proposal>\n" + proposal_text + "\n</proposal>\n"
                "<charter>\n" + charter_text + "\n</charter>\n"
                + sources_block
                + "\n"
            )
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            parsed = _parse_verdict(raw)
            if parsed is None:
                raise gl.vm.UserError("LLM_ERROR: verdict could not be parsed")
            return parsed

        def validator_fn(result):
            if not isinstance(result, gl.vm.Return):
                return False
            leader = result.calldata
            if _parse_verdict(leader) is None:
                return False
            try:
                own = leader_fn()
            except Exception:
                return False
            return (
                leader["verdict"] == own["verdict"]
                and leader["category"] == own["category"]
            )

        consensus = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        if _parse_verdict(consensus) is None:
            _fail("CONSENSUS_RESULT_INVALID", "agreed result is not a verdict")
        record["status"] = "RULED"
        record["verdict"] = consensus["verdict"]
        record["category"] = consensus["category"]
        record["summary"] = consensus["summary"]
        record["assessment_count"] += 1
        return self._store(record)

    @gl.public.view
    def get_proposal(self, proposal_id) -> str:
        raw = self.proposals.get(proposal_id, "")
        return raw

    @gl.public.view
    def get_status(self, proposal_id) -> str:
        raw = self.proposals.get(proposal_id, "")
        if raw == "":
            return "NOT_FOUND"
        return json.loads(raw)["status"]

    @gl.public.view
    def get_proposal_count(self) -> str:
        return str(int(self.proposal_count))

    @gl.public.view
    def get_proposal_id(self, index) -> str:
        ids = self.id_index.get("ids", "")
        if ids == "":
            return ""
        parts = ids.split("\n")
        if index < 0 or index >= len(parts) - 1:
            return ""
        return parts[index]
