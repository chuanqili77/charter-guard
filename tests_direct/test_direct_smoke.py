"""Direct-mode smoke tests for CharterGuard, using the real GenVM.

These tests are separate from tests/test_charter_guard.py: they
require the genlayer-test direct fixtures, which are only available
in the reproducible environment. They make no network call and no
chain transaction: direct mode runs the contract in-process.

Run only with the reproducible environment, from the project root:
    .venv-repro/bin/python -m pytest tests_direct -v
"""

import json


def test_direct_deploy_and_empty_view(direct_deploy):
    contract = direct_deploy("contracts/charter_guard.py")
    assert contract.get_proposal_count() == "0"
    assert contract.get_status("missing") == "NOT_FOUND"
    assert contract.get_proposal("missing") == ""


def test_direct_file_proposal(direct_deploy):
    contract = direct_deploy("contracts/charter_guard.py")
    result = contract.file_proposal(
        "direct-smoke",
        "Q4 community grants round",
        "Allocate 20,000 GEN from the treasury to fund the Q4 community grants round, after the full 7-day discussion period and a vote in which 72% of voting members participated. The author receives no funds.",
        "Article 1 - Spending: no single proposal may allocate more than 50,000 GEN from the treasury in one quarter. Article 2 - Procedure: every proposal must be discussed for at least 7 days and receive votes from at least 60% of voting members before execution.",
        "https://example.org/treasury-balance",
        "",
        "",
    )
    record = json.loads(result)
    assert record["status"] == "FILED"
    assert record["sources"] == ["https://example.org/treasury-balance"]
    assert contract.get_proposal_count() == "1"
    assert contract.get_proposal_id(0) == "direct-smoke"
    assert contract.get_proposal_id(1) == ""
