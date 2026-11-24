import { sha256 } from "./sha256.js";

const $ = (id) => document.getElementById(id);
const KEY = "ciphercraft.learn.password-storage.v1";
const DEMO_PASSWORD = "harbor-lantern", ITERATIONS = 600000;
const encoder = new TextEncoder();
const hex = (bytes) => [...new Uint8Array(bytes)].map((n) => n.toString(16).padStart(2, "0")).join("");
const fresh = () => ({ stage: 0, quiz1: "", quiz2: "", passed1: false, passed2: false, verified: false });
let state = fresh(), initialized = false, storage = true, generation = 0, job = "", records = null;
const supported = () => !!crypto?.subtle?.deriveBits && !!crypto?.getRandomValues;
function say(id, text, error = false) { $(id).textContent = text; $(id).dataset.error = String(error); }
function save() {
  if (storage) try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { storage = false; }
  $("pw-storage").textContent = storage
    ? "Only lesson choices and completion save on this device. Guesses, salts and derived values stay in memory and are not uploaded."
    : "Device storage is unavailable. You can keep learning, but progress will be lost when this page closes. Guesses and demo records are not saved.";
}
function restore() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw || raw.length > 2048) return;
    const data = JSON.parse(raw);
    if (!data || typeof data !== "object") return;
    state.quiz1 = ["fast", "decrypt", "short"].includes(data.quiz1) ? data.quiz1 : "";
    state.quiz2 = ["secret", "guesses", "decrypt"].includes(data.quiz2) ? data.quiz2 : "";
    state.passed1 = data.passed1 === true && state.quiz1 === "fast";
    state.passed2 = data.passed2 === true && state.quiz2 === "guesses";
    state.verified = data.verified === true && state.passed1 && state.passed2;
    const max = state.passed1 ? state.passed2 ? 2 : 1 : 0;
    state.stage = Number.isInteger(data.stage) && data.stage >= 0 && data.stage <= max ? data.stage : 0;
  } catch (error) { if (!(error instanceof SyntaxError)) storage = false; }
}
function allowed(stage) { return stage === 0 || (state.passed1 && (stage === 1 || state.passed2)); }
function render() {
  for (let i = 0; i < 3; i++) {
    const active = i === state.stage, tab = $(`pw-step-${i}-tab`);
    tab.disabled = !allowed(i); tab.setAttribute("aria-selected", String(active)); tab.tabIndex = active ? 0 : -1;
    $(`pw-step-${i}`).hidden = !active;
  }
  $("pw-crypto-error").hidden = supported();
  $("pw-next-1").disabled = !state.passed1;
  $("pw-next-2").disabled = !state.passed2;
  for (const id of ["pw-generate", "pw-recreate"]) {
    $(id).disabled = !supported() || !!job;
    $(id).dataset.busy = String(job === "records");
  }
  $("pw-generate").textContent = job === "records" ? "Deriving two records…" : records ? "Generate fresh salts" : "Compare two accounts";
  $("pw-records").hidden = $("pw-quiz-2-group").hidden = $("pw-check-2").hidden = !records;
  $("pw-recreate").hidden = $("pw-recreate-help").hidden = !!records;
  $("pw-stored-record").hidden = !records;
  $("pw-verify").disabled = !records || !supported() || !!job;
  $("pw-verify").textContent = job === "verify" ? "Verifying…" : "Check password";
  $("pw-verify").dataset.busy = String(job === "verify");
  $("pw-complete").hidden = !state.verified;
  $("pw-progress").textContent = `${Number(state.passed1) + Number(state.passed2) + Number(state.verified)} of 3 steps complete${state.verified ? " · Practice lesson completed" : ""}`;
  save();
}
function stage(index, focus = true) {
  if (!allowed(index)) return;
  state.stage = index; say("pw-job-status", ""); render(); if (focus) $("pw-title-" + index).focus();
}
async function derive(password, salt) {
  const material = await crypto.subtle.importKey("raw", encoder.encode(password), "PBKDF2", false, ["deriveBits"]);
  return hex(await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations: ITERATIONS }, material, 256));
}
function showRecords() {
  $("pw-records").replaceChildren(...records.map((record, index) => {
    const card = document.createElement("div");
    const title = document.createElement("h4"); title.textContent = `Account ${index ? "B" : "A"}`; card.append(title);
    for (const [label, value, id] of [["Plain SHA-256 (fast)", record.fast, `pw-fast-${index}`], ["Random salt (stored, not secret)", hex(record.salt), `pw-salt-${index}`], ["PBKDF2 derived value", record.value, `pw-derived-${index}`]]) {
      const p = document.createElement("p"); p.className = "hint"; p.textContent = label;
      const code = document.createElement("code"); code.className = "hash-digest"; code.id = id; code.textContent = value; card.append(p, code);
    }
    return card;
  }));
  $("pw-record-json").textContent = JSON.stringify({ algorithm: "PBKDF2-HMAC-SHA-256", iterations: ITERATIONS, salt: hex(records[0].salt), derivedValue: records[0].value }, null, 2);
  $("pw-record-summary").textContent = "The plain SHA-256 values match because the password bytes match. The sampled PBKDF2 values differ because each account has its own salt.";
}
async function generate() {
  if (job || !supported()) return;
  const token = ++generation; job = "records"; render();
  say("pw-job-status", "Deriving two demo records with fresh random salts. This may take a moment.");
  try {
    const salts = [crypto.getRandomValues(new Uint8Array(16)), crypto.getRandomValues(new Uint8Array(16))];
    const fast = await sha256(encoder.encode(DEMO_PASSWORD));
    const values = await Promise.all(salts.map((salt) => derive(DEMO_PASSWORD, salt)));
    if (token !== generation) return;
    records = salts.map((salt, i) => ({ salt, fast, value: values[i] }));
    say("pw-verify-feedback", ""); showRecords(); say("pw-job-status", "Both records derived locally. Compare the salts and values, then answer the question.");
  } catch { if (token === generation) say("pw-job-status", "The demo records could not be derived. Try again in an up-to-date browser.", true); }
  finally { if (token === generation) { job = ""; render(); } }
}
async function verify() {
  if (job || !records || !supported()) return;
  const guess = $("pw-guess").value;
  if (!guess || guess.length > 128) { say("pw-verify-feedback", "Enter a made-up guess of 1–128 characters.", true); return; }
  const token = ++generation, record = records[0]; job = "verify"; render();
  say("pw-verify-feedback", "Re-deriving the guess with account A’s stored salt and settings…");
  try {
    const value = await derive(guess, record.salt);
    if (token !== generation) return;
    const match = value === record.value;
    say("pw-verify-feedback", match ? "Match. The guess produced the stored derived value. No password was decrypted." : "No match. The same salt and settings produced a different value for this guess. Try the fictional demo password.", !match);
    if (match) state.verified = true;
    render(); if (match) $("pw-complete-title").focus();
  } catch { if (token === generation) say("pw-verify-feedback", "The guess could not be verified. Try again.", true); }
  finally { if (token === generation) { job = ""; render(); } }
}
export function openPasswordLesson() {
  if (initialized) return;
  initialized = true; restore();
  for (let i = 0; i < 3; i++) {
    $(`pw-step-${i}-tab`).onclick = () => stage(i);
    $(`pw-step-${i}-tab`).onkeydown = (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const enabled = [0, 1, 2].filter(allowed), index = enabled.indexOf(state.stage);
      const next = event.key === "Home" ? enabled[0] : event.key === "End" ? enabled.at(-1) : enabled[(index + (event.key === "ArrowRight" ? 1 : enabled.length - 1)) % enabled.length];
      stage(next, false); $(`pw-step-${next}-tab`).focus();
    };
  }
  for (const number of [1, 2]) {
    document.querySelectorAll(`input[name="pw-quiz-${number}"]`).forEach((radio) => radio.onchange = () => {
      state["quiz" + number] = radio.value; state["passed" + number] = false; state.verified = false;
      say("pw-feedback-" + number, "Answer selected. Choose Check answer for feedback."); render();
    });
    $("pw-check-" + number).onclick = () => {
      const chosen = state["quiz" + number];
      if (!chosen) { say("pw-feedback-" + number, "Choose an answer first.", true); return; }
      const correct = chosen === (number === 1 ? "fast" : "guesses") && (number === 1 || !!records);
      state["passed" + number] = correct;
      say("pw-feedback-" + number, correct ? number === 1 ? "Correct. A fast general-purpose hash makes repeated guesses inexpensive." : "Correct. A salt is not secret and cannot rescue a weak password from guessing." : number === 1 ? "Try again. A digest is not decrypted; the issue here is how cheaply guesses can be checked." : "Try again. Salts separate account records, but guesses are still possible.", !correct); render();
    };
  }
  $("pw-next-1").onclick = () => stage(1); $("pw-next-2").onclick = () => stage(2);
  $("pw-generate").onclick = $("pw-recreate").onclick = generate;
  $("pw-verify").onclick = verify;
  $("pw-guess").oninput = () => {
    if (job === "verify") { generation++; job = ""; }
    say("pw-verify-feedback", "Guess changed. Choose Check password to test it."); render();
  };
  $("pw-reset").onclick = () => { $("pw-reset-confirm").hidden = false; $("pw-reset-no").focus(); };
  $("pw-reset-no").onclick = () => { $("pw-reset-confirm").hidden = true; $("pw-reset").focus(); };
  $("pw-reset-yes").onclick = () => {
    generation++; job = ""; records = null; state = fresh(); $("pw-guess").value = "";
    $("pw-records").replaceChildren(); $("pw-record-json").textContent = ""; $("pw-record-summary").textContent = "";
    for (const id of ["pw-feedback-1", "pw-feedback-2", "pw-job-status", "pw-verify-feedback"]) say(id, "");
    document.querySelectorAll('#password-lesson input[type="radio"]').forEach((radio) => { radio.checked = false; });
    $("pw-reset-confirm").hidden = true; render(); $("pw-title-0").focus();
  };
  for (const n of [1, 2]) document.querySelectorAll(`input[name="pw-quiz-${n}"]`).forEach((radio) => { radio.checked = radio.value === state["quiz" + n]; });
  render();
}
