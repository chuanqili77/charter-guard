// Verification for the frontend's contract-call layer (Node, no browser).
//
// Uses the same genlayer-js calls the web app uses (createClient,
// readContract, writeContract, waitForTransactionReceipt), but with a
// throwaway generated account instead of a MetaMask account, so the
// write path can be exercised without a personal wallet. The account
// is generated fresh on every run and discarded afterwards.
//
// Usage:
//   CONTRACT_ADDRESS=0x... node scripts/verify-frontend-call.mjs
//
// It files a proposal with a fresh id, reads it back, and prints the
// contract address, transaction hash, and stored record. It asserts
// only that the write finalised and the record reads back with
// status FILED; it does not run a ruling here (that path is
// covered by the Studionet integration test with live validators).

import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const address = process.env.CONTRACT_ADDRESS;
if (!address) {
  console.error("Set CONTRACT_ADDRESS first.");
  process.exit(1);
}

const account = createAccount();
const client = createClient({ chain: studionet, account });
const id = "node-verify-" + Date.now().toString(36);

const hash = await client.writeContract({
  address,
  functionName: "file_proposal",
  args: [
    id,
    "Node verification proposal",
    "Allocate 5,000 GEN from the treasury to fund a documentation sprint, after a 7-day discussion period and a vote with 70% participation. The author receives no funds.",
    "Article 1 - Spending: no single proposal may allocate more than 50,000 GEN from the treasury in one quarter. Article 2 - Procedure: every proposal must be discussed for at least 7 days and receive votes from at least 60% of voting members before execution.",
    "",
    "",
    "",
  ],
  value: BigInt(0),
});
console.log(JSON.stringify({ contract: address, tx: hash }, null, 2));
const receipt = await client.waitForTransactionReceipt({
  hash,
  status: "FINALIZED",
  interval: 3000,
  retries: 200,
});
console.log("receipt status:", receipt?.status ?? receipt?.status_name ?? "unknown");

const raw = await client.readContract({
  address,
  functionName: "get_proposal",
  args: [id],
});
const record = typeof raw === "string" ? JSON.parse(raw) : raw;
console.log(JSON.stringify(record, null, 2));
if (record.status !== "FILED" || record.proposal_id !== id) {
  throw new Error("Record did not read back as expected.");
}
console.log("FRONTEND_CALL_VERIFIED");
