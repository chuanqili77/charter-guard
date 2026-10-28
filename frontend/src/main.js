import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import "./style.css";

const DEFAULT_CONTRACT = import.meta.env.VITE_CONTRACT_ADDRESS || "";
const EXPLORER = "https://explorer-studio.genlayer.com";

const $ = (id) => document.getElementById(id);
const short = (addr) =>
  addr && addr.length > 13
    ? addr.slice(0, 6) + "…" + addr.slice(-4)
    : addr || "";

let account = null;
let client = null;
let contractAddress = localStorage.getItem("cg_contract") || DEFAULT_CONTRACT;
let allProposals = [];
let currentFilter = "ALL";

const CATEGORY_TEXT = {
  compliant: "Every applicable charter rule is satisfied.",
  spending_limit: "A charter spending cap is exceeded.",
  process_violation: "A charter procedure or quorum requirement is broken.",
  self_dealing: "The proposal benefits its own author against the charter.",
  values_conflict: "The proposal contradicts the charter's stated values.",
  insufficient_evidence: "The texts do not settle compliance.",
  ambiguous_text: "The proposal is too vague to check against the charter.",
  source_unreachable: "A key fact cannot be checked; the filed sources failed to load.",
};

const DEMO_CHARTER =
  "Article 1 - Spending: no single proposal may allocate more than 50,000 GEN from the treasury in one quarter. " +
  "Article 2 - Procedure: every proposal must be discussed for at least 7 days and receive votes from at least 60% of voting members before execution. " +
  "Article 3 - Self-dealing: no proposal may direct treasury funds to its own author or to an entity the author controls. " +
  "Article 4 - Membership: only members in good standing may author proposals; suspended members may not author proposals.";

/* ---------- Drifting gold dust ---------- */

function startGoldDust() {
  const canvas = $("golddust");
  if (!canvas) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const ctx = canvas.getContext("2d");
  let w = (canvas.width = window.innerWidth);
  let h = (canvas.height = window.innerHeight);
  const motes = Array.from({ length: 70 }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    r: 0.8 + Math.random() * 2.2,
    vy: -(0.08 + Math.random() * 0.25),
    vx: (Math.random() - 0.5) * 0.12,
    a: 0.15 + Math.random() * 0.45,
  }));
  window.addEventListener("resize", () => {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  });
  (function draw() {
    ctx.clearRect(0, 0, w, h);
    for (const m of motes) {
      m.x += m.vx;
      m.y += m.vy;
      if (m.y < -4) {
        m.y = h + 4;
        m.x = Math.random() * w;
      }
      if (m.x < -4) m.x = w + 4;
      if (m.x > w + 4) m.x = -4;
      ctx.fillStyle = `rgba(176, 138, 62, ${m.a})`;
      ctx.beginPath();
      ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(draw);
  })();
}

/* ---------- Proceedings timeline ---------- */

function setStage(stage) {
  const order = ["sign", "sent", "consensus", "final"];
  document.querySelectorAll(".steps li").forEach((li) => {
    const step = li.dataset.step;
    li.classList.remove("active", "done");
    if (stage === "error") return;
    if (order.indexOf(step) < order.indexOf(stage)) li.classList.add("done");
    if (step === stage) li.classList.add("active");
    if (stage === "final" && step === "final") li.classList.add("done");
  });
}

function setTx(text, kind = "", hash = "") {
  const el = $("tx-status");
  el.className = "tx " + kind;
  el.textContent = text;
  if (hash) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "Copy hash";
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(hash);
        btn.textContent = "Copied";
      } catch {
        btn.textContent = hash;
      }
    });
    el.appendChild(btn);
  }
}

function showError(message) {
  const el = $("error");
  el.textContent = message;
  el.hidden = !message;
}

function readClient() {
  return createClient({ chain: studionet });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}

function verdictStamp(p) {
  if (p.verdict === "COMPLIANT") return `<span class="stamp ok">COMPLIANT ✓</span>`;
  if (p.verdict === "VIOLATION") return `<span class="stamp bad">VIOLATION ✗</span>`;
  if (p.verdict === "UNCLEAR") return `<span class="stamp warn">UNCLEAR ?</span>`;
  return "";
}

function verdictBadge(p) {
  if (p.verdict === "COMPLIANT") return `<span class="badge ok">COMPLIANT</span>`;
  if (p.verdict === "VIOLATION") return `<span class="badge bad">VIOLATION</span>`;
  if (p.verdict === "UNCLEAR") return `<span class="badge warn">UNCLEAR</span>`;
  return "";
}

function renderCard(p) {
  const canRule = p.status === "FILED";
  const sources = (p.sources || [])
    .map(
      (u) =>
        `<li><a href="${escapeHtml(u)}" target="_blank" rel="noreferrer">${escapeHtml(
          u
        )}</a></li>`
    )
    .join("");
  return `<article class="proposal-card">
    ${verdictStamp(p)}
    <header><h3>${escapeHtml(p.title)}</h3>
    <span><span class="badge neutral">${escapeHtml(p.status)}</span>${verdictBadge(p)}</span></header>
    <p class="charter-excerpt">${escapeHtml(p.proposal_text)}</p>
    <details><summary>Charter text</summary><p>${escapeHtml(p.charter_text)}</p></details>
    <p class="meta">ID <code>${escapeHtml(p.proposal_id)}</code> · filed by ${short(
      p.filer
    )} · rulings ×${p.assessment_count}</p>
    ${sources ? `<ul class="sources">${sources}</ul>` : `<p class="muted small">No sources filed — ruled on the texts alone.</p>`}
    ${
      p.summary
        ? `<p class="summary"><strong>The chamber's reasoning:</strong> ${escapeHtml(
            p.summary
          )}<br><span class="muted">${escapeHtml(
            CATEGORY_TEXT[p.category] || p.category
          )}</span></p>`
        : ""
    }
    ${
      canRule
        ? `<button class="btn crimson" data-rule="${escapeHtml(
            p.proposal_id
          )}">Rule on this proposal</button>`
        : ""
    }
  </article>`;
}

function renderFiltered() {
  const list = $("proposal-list");
  const shown =
    currentFilter === "ALL"
      ? allProposals
      : currentFilter === "FILED"
        ? allProposals.filter((p) => p.status === "FILED")
        : allProposals.filter((p) => p.verdict === currentFilter);
  if (shown.length === 0) {
    list.innerHTML = "<p class='muted'>No proposals match this filter.</p>";
    return;
  }
  list.innerHTML = shown.map(renderCard).join("");
  list.querySelectorAll("[data-rule]").forEach((btn) => {
    btn.addEventListener("click", () => onRule(btn.dataset.rule));
  });
}

function renderLedger() {
  $("count").textContent = String(allProposals.length);
  $("count-compliant").textContent = String(
    allProposals.filter((p) => p.verdict === "COMPLIANT").length
  );
  $("count-violation").textContent = String(
    allProposals.filter((p) => p.verdict === "VIOLATION").length
  );
  $("count-unclear").textContent = String(
    allProposals.filter((p) => p.verdict === "UNCLEAR").length
  );
  $("hero-count").textContent = String(allProposals.length);
  $("hero-compliant").textContent = String(
    allProposals.filter((p) => p.verdict === "COMPLIANT").length
  );
  $("hero-violation").textContent = String(
    allProposals.filter((p) => p.verdict === "VIOLATION").length
  );
}

async function refreshList() {
  const list = $("proposal-list");
  if (!contractAddress) {
    list.innerHTML =
      "<p class='muted'>Enter a contract address above to open the chamber.</p>";
    return;
  }
  list.innerHTML = "<p class='muted'>Opening the chamber record…</p>";
  try {
    const c = readClient();
    const countRaw = await c.readContract({
      address: contractAddress,
      functionName: "get_proposal_count",
      args: [],
    });
    const count = Number(countRaw);
    if (count === 0) {
      allProposals = [];
      list.innerHTML =
        "<p class='muted'>The record is empty. File the first proposal below.</p>";
      renderLedger();
      return;
    }
    allProposals = [];
    for (let i = count - 1; i >= 0; i--) {
      const id = await c.readContract({
        address: contractAddress,
        functionName: "get_proposal_id",
        args: [i],
      });
      const raw = await c.readContract({
        address: contractAddress,
        functionName: "get_proposal",
        args: [String(id)],
      });
      allProposals.push(typeof raw === "string" ? JSON.parse(raw) : raw);
    }
    renderLedger();
    renderFiltered();
  } catch (err) {
    list.innerHTML = "<p class='muted'>Could not load the chamber record.</p>";
    showError("Load failed: " + (err?.message || err));
  }
}

async function ensureWallet() {
  if (!window.ethereum)
    throw new Error("No wallet found. Install MetaMask and try again.");
  if (!account) {
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });
    account = accounts[0];
    $("wallet-btn").textContent = "Connected: " + short(account);
  }
  client = createClient({ chain: studionet, account });
  await client.connect("studionet");
  return client;
}

async function send(method, args) {
  showError("");
  const c = await ensureWallet();
  setStage("sign");
  setTx("Waiting for signature…");
  const hash = await c.writeContract({
    address: contractAddress,
    functionName: method,
    args,
    value: BigInt(0),
  });
  setStage("sent");
  setTx(`Sent: ${hash}. Waiting for validator consensus…`, "", hash);
  setStage("consensus");
  await c.waitForTransactionReceipt({
    hash,
    status: "FINALIZED",
    interval: 3000,
    retries: 200,
  });
  setStage("final");
  setTx(`Ruled on-chain: ${hash}`, "ok", hash);
}

async function onCreate(ev) {
  ev.preventDefault();
  if (!contractAddress) return showError("Set a contract address first.");
  const id = $("f-id").value.trim();
  const title = $("f-title").value.trim();
  const proposal = $("f-proposal").value.trim();
  const charter = $("f-charter").value.trim();
  const s1 = $("f-s1").value.trim();
  const s2 = $("f-s2").value.trim();
  const s3 = $("f-s3").value.trim();
  try {
    await send("file_proposal", [id, title, proposal, charter, s1, s2, s3]);
    await refreshList();
  } catch (err) {
    setStage("error");
    setTx("");
    showError("Filing failed: " + (err?.message || err));
  }
}

async function onRule(pid) {
  if (!contractAddress) return showError("Set a contract address first.");
  try {
    await send("rule_proposal", [pid]);
    await refreshList();
  } catch (err) {
    setStage("error");
    setTx("");
    showError("Ruling failed: " + (err?.message || err));
  }
}

function bindCounter(inputId, counterId, max) {
  const input = $(inputId);
  const counter = $(counterId);
  if (!input || !counter) return;
  const update = () => {
    counter.textContent = `${input.value.length} / ${max} chars`;
  };
  input.addEventListener("input", update);
  update();
}

$("wallet-btn").addEventListener("click", async () => {
  try {
    await ensureWallet();
  } catch (err) {
    showError(err?.message || err);
  }
});
$("contract-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  contractAddress = $("contract-address").value.trim();
  localStorage.setItem("cg_contract", contractAddress);
  $("explorer-link").href = EXPLORER + "/address/" + contractAddress;
  refreshList();
});
$("create-form").addEventListener("submit", onCreate);
$("refresh-btn").addEventListener("click", refreshList);
$("charter-preset").addEventListener("click", () => {
  $("f-charter").value = DEMO_CHARTER;
  $("f-charter").dispatchEvent(new Event("input"));
});
document.querySelectorAll("[data-filter]").forEach((btn) => {
  btn.addEventListener("click", () => {
    currentFilter = btn.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((b) => {
      b.setAttribute("aria-pressed", b === btn ? "true" : "false");
    });
    renderFiltered();
  });
});
$("demo-btn").addEventListener("click", () => {
  if (DEFAULT_CONTRACT) {
    contractAddress = DEFAULT_CONTRACT;
    localStorage.setItem("cg_contract", contractAddress);
    $("contract-address").value = contractAddress;
    $("explorer-link").href = EXPLORER + "/address/" + contractAddress;
  }
  refreshList();
});

$("contract-address").value = contractAddress;
$("explorer-link").href = contractAddress
  ? EXPLORER + "/address/" + contractAddress
  : EXPLORER;
$("chain-note").textContent =
  "Stable Studionet · Chain ID 61999 · test network only, no real funds";
bindCounter("f-proposal", "c-proposal", 2000);
bindCounter("f-charter", "c-charter", 3000);
startGoldDust();
refreshList();
