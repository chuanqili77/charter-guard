"""Example calls for CharterGuard (documentation only).

These are not executed by the test suites. They show the exact
argument shapes for the contract's write methods on Stable
Studionet (chain 61999). Use the demo site, or genlayer-js, or
the gltest CLI path described in DEPLOY.md, to run them for real.
No key is involved in this file.
"""

CONTRACT_ADDRESS = "0x77b8E8289a51eb9DCB8Dd6b9f000F4E31e0b8A82"  # see evidence/EVIDENCE.md
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

# 1. File a proposal the charter permits.
file_proposal_args = [
    "demo-grants-q4",
    "Q4 community grants round",
    "Allocate 20,000 GEN from the treasury to fund the Q4 community "
    "grants round. The proposal was discussed for 10 days and "
    "received votes from 72% of voting members. The author "
    "receives no funds and holds no interest in any recipient.",
    CHARTER,
    "",
    "",
    "",
]

# 2. File a proposal that violates exactly one hard rule: the cap.
file_proposal_args_violation = [
    "demo-audit-80k",
    "Annual treasury audit grant",
    "Allocate 80,000 GEN from the treasury to an independent "
    "community auditor for the annual treasury audit. The proposal "
    "was discussed for 10 days and received votes from 71% of "
    "voting members. The author receives no funds.",
    CHARTER,
    "",
    "",
    "",
]

# 3. Run the validator ruling (text comparison + consensus).
rule_proposal_args = ["demo-grants-q4"]

# 4. Read the ruled record back.
get_proposal_args = ["demo-grants-q4"]
get_status_args = ["demo-grants-q4"]

# 5. Enumerate the chamber record.
get_proposal_count_args = []
get_proposal_id_args = [0]
