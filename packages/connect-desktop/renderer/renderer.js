"use strict";

const idle = document.getElementById("idle");
const busy = document.getElementById("busy");
const done = document.getElementById("done");
const error = document.getElementById("error");
const statusEl = document.getElementById("status");
const errorMsg = document.getElementById("error-msg");
const doneMsg = document.getElementById("done-msg");
const btnConnect = document.getElementById("btn-connect");
const btnTelegram = document.getElementById("btn-telegram");
const btnCopyCmd = document.getElementById("btn-copy-cmd");
const btnAgain = document.getElementById("btn-again");
const btnRetry = document.getElementById("btn-retry");

let lastResult = null;

function show(section) {
  for (const el of [idle, busy, done, error]) el.classList.add("hidden");
  section.classList.remove("hidden");
}

window.rhConnect.onStatus((msg) => {
  statusEl.textContent = msg;
});

async function startConnect() {
  show(busy);
  statusEl.textContent = "Starting…";
  btnConnect.disabled = true;
  const result = await window.rhConnect.connectRobinhood();
  btnConnect.disabled = false;
  if (!result.ok) {
    errorMsg.textContent = result.error || "Unknown error";
    show(error);
    return;
  }
  lastResult = result;
  if (result.handoff && result.handoff.deepLink) {
    doneMsg.textContent =
      "Tap Open Telegram to finish. The bot will save your token automatically (one-time link, expires soon).";
    btnTelegram.classList.remove("hidden");
  } else {
    doneMsg.textContent =
      "Token copied to clipboard. Paste this into a DM with the Telegram bot (Open Telegram disabled — handoff staging failed).";
    btnTelegram.classList.add("hidden");
  }
  show(done);
}

btnConnect.addEventListener("click", startConnect);
btnRetry.addEventListener("click", startConnect);
btnAgain.addEventListener("click", () => {
  lastResult = null;
  show(idle);
});

btnTelegram.addEventListener("click", async () => {
  const link = lastResult && lastResult.handoff && lastResult.handoff.deepLink;
  if (link) await window.rhConnect.openExternal(link);
});

btnCopyCmd.addEventListener("click", async () => {
  const cmd = (lastResult && lastResult.pasteCommand) || "";
  if (!cmd) return;
  await window.rhConnect.copyText(cmd);
  btnCopyCmd.textContent = "Copied!";
  setTimeout(() => {
    btnCopyCmd.textContent = "Copy /connect_agentic command";
  }, 1600);
});
