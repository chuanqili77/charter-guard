"""Studionet integration test for CharterGuard (real chain, real validators).

Run ONLY with the reproducible environment, from the project root:
    .venv-repro/bin/gltest --network studionet tests_integration -v -s

Deploys one contract instance on Stable Studionet (61999), files two
demo proposals against the same fictional charter text, and runs
live-validator rulings that compare each proposal against that
charter. No mocked LLM and no mocked web fetch is used. The test
asserts only what the design guarantees: each ruling completes,
the status becomes RULED, and the verdict and category are members
of their closed sets. The actual verdicts are printed as JSON
evidence lines and archived in evidence/, not forced to particular
values here, because live validators judge the texts independently.

The charter is a short fictional text written for this demo (the
"Meridian Collective" charter). Both demos cite it on purpose, so
the chamber record shows one compliant proposal and one violating
proposal side by side:
- demo-grants-q4: allocates 20,000 GEN (inside the 50,000 GEN
  quarterly cap), discussed 10 days, 72% participation, author
  receives nothing. Compliant on every article.
- demo-audit-80k: allocates 80,000 GEN to an independent auditor,
  discussed 10 days, 71% participation, author receives nothing.
  It violates exactly one hard rule -- the Article 1 spending cap
  -- and no other, so the ruling category is unambiguous. A
  proposal violating several rules at once would risk validators
  disagreeing on which category to report; the single-violation
  design keeps the demo decisive.

Neither demo files a source URL: the charter and proposal texts
are the primary evidence, and sources are optional by design.
On-chain source fetching during a ruling is therefore covered by
the stand-in suite, not by a chain demo; see README.md.

Do NOT run this file against another network without reviewing it
first, and do NOT use it for Appeal.
"""

import json
from pathlib import Path

from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus

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
CHARTER = (
    "Article 1 - Spending: no single proposal may allocate more than "
    "50,000 GEN from the treasury in one quarter. Article 2 - Procedure: "
    "every proposal must be discussed for at least 7 days and receive votes "
    "from at least 60% of voting members before execution. Article 3 - "
    "Self-dealing: no proposal may direct treasury funds to its own author "
    "or to an entity the author controls. Article 4 - Membership: only "
    "members in good standing may author proposals; suspended members may "
    "not author proposals."
)


def _receipt_info(receipt):
    info = {}
    for key in ("hash", "transaction_hash", "tx_hash", "status",
                "consensus_status", "execution_result", "result",
                "contract_address", "address"):
        try:
            value = receipt.get(key)
        except Exception:
            value = None
        if value is not None:
            info[key] = str(value)
    info["raw_keys"] = sorted(list(receipt.keys())) if hasattr(receipt, "keys") else []
    return info


def test_studionet_full_flow():
    factory = get_contract_factory(contract_file_path="charter_guard.py")
    deploy_receipt = factory.deploy_contract_tx(
        wait_transaction_status=TransactionStatus.FINALIZED,
    )
    assert tx_execution_succeeded(deploy_receipt), deploy_receipt
    from gltest.utils import extract_contract_address
    address = extract_contract_address(deploy_receipt)
    contract = factory.build_contract(contract_address=address)
    print("\nEVIDENCE_CHARTER_DEPLOY " + json.dumps({
        "contract_address": str(address),
        "deploy_receipt": _receipt_info(deploy_receipt),
    }, sort_keys=True))

    proposals = [
        (
            "demo-grants-q4",
            "Q4 community grants round",
            "Allocate 20,000 GEN from the treasury to fund the Q4 community "
            "grants round. The proposal was discussed for 10 days and "
            "received votes from 72% of voting members. The author "
            "receives no funds and holds no interest in any recipient.",
        ),
        (
            "demo-audit-80k",
            "Annual treasury audit grant",
            "Allocate 80,000 GEN from the treasury to an independent "
            "community auditor for the annual treasury audit. The proposal "
            "was discussed for 10 days and received votes from 71% of "
            "voting members. The author receives no funds.",
        ),
    ]
    for proposal_id, title, text in proposals:
        receipt = contract.file_proposal(
            args=[proposal_id, title, text, CHARTER, "", "", ""]
        ).transact(wait_transaction_status=TransactionStatus.FINALIZED)
        assert tx_execution_succeeded(receipt), receipt
        print("EVIDENCE_CHARTER_FILE " + json.dumps({
            "contract_address": str(address),
            "proposal_id": proposal_id,
            "file_receipt": _receipt_info(receipt),
        }, sort_keys=True))

    out = {"contract_address": str(address), "proposals": {}}
    out["deploy_receipt"] = _receipt_info(deploy_receipt)
    for proposal_id, _, _ in proposals:
        receipt = contract.rule_proposal(
            args=[proposal_id]
        ).transact(wait_transaction_status=TransactionStatus.FINALIZED)
        assert tx_execution_succeeded(receipt), receipt
        print("EVIDENCE_CHARTER_RULE " + json.dumps({
            "contract_address": str(address),
            "proposal_id": proposal_id,
            "rule_receipt": _receipt_info(receipt),
        }, sort_keys=True))
        out["proposals"][proposal_id] = {"rule_receipt": _receipt_info(receipt)}

    records = {}
    for proposal_id, _, _ in proposals:
        status = contract.get_status(args=[proposal_id]).call()
        record = json.loads(contract.get_proposal(args=[proposal_id]).call())
        records[proposal_id] = record
        print("EVIDENCE_CHARTER_RECORD " + json.dumps({
            "contract_address": str(address),
            "proposal_id": proposal_id,
            "status": str(status),
            "record": record,
        }, sort_keys=True))
        assert str(status) == "RULED"
        assert record["status"] == "RULED"
        assert record["verdict"] in VERDICTS
        assert record["category"] in CATEGORIES
        assert record["assessment_count"] == 1
        out["proposals"][proposal_id]["record"] = record

    count = contract.get_proposal_count().call()
    assert int(count) == 2
    assert contract.get_proposal_id(args=[0]).call() == "demo-grants-q4"
    assert contract.get_proposal_id(args=[1]).call() == "demo-audit-80k"
    out["proposal_count"] = int(count)
    path = Path("evidence/studionet_assess.json")
    path.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"Wrote {path}")
