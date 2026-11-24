import { sha256, digestBits } from "./sha256.js";

const $ = (id) => document.getElementById(id);
const storageKey = "ciphercraft.learn.hash-integrity.v1";
const fresh = () => ({
  step: 0,
  quiz1: "",
  quiz2: "",
  passed1: false,
  passed2: false,
  experiment: false,
  hashed: [],
  found: "",
  reason: "",
  confirmed: false,
});
let unit,
  files = [],
  state = fresh(),
  loading = false,
  availableStorage = true;
let revision = 0,
  experiment = null,
  experimenting = false;
const calculated = new Map(),
  pending = new Set();
const supported = () => !!globalThis.crypto?.subtle;
function feedback(id, text, error = false) {
  $(id).textContent = text;
  $(id).dataset.error = String(error);
}
function save() {
  if (availableStorage) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      availableStorage = false;
    }
  }
  $("learn-storage").textContent = availableStorage
    ? "Lesson progress saves on this device. Lab inputs and campaign progress stay separate."
    : "Device storage is unavailable. You can keep learning, but progress will be lost when this page closes.";
}
function restore() {
  const result = fresh();
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw || raw.length > 4096) return result;
    const value = JSON.parse(raw);
    if (!value || typeof value !== "object") return result;
    result.quiz1 = ["same", "random", "key"].includes(value.quiz1)
      ? value.quiz1
      : "";
    result.quiz2 = ["exact", "varies", "key"].includes(value.quiz2)
      ? value.quiz2
      : "";
    result.experiment = value.experiment === true;
    result.passed1 = value.passed1 === true && result.quiz1 === "same";
    result.passed2 =
      value.passed2 === true && result.quiz2 === "varies" && result.experiment;
    result.hashed = Array.isArray(value.hashed)
      ? files
          .filter((file) => value.hashed.includes(file.id))
          .map((file) => file.id)
      : [];
    result.found = files.some((file) => file.id === value.found)
      ? value.found
      : "";
    result.reason = ["changed", "attacker", "safe"].includes(value.reason)
      ? value.reason
      : "";
    result.confirmed =
      value.confirmed === true &&
      result.found === unit.altered &&
      result.reason === "changed";
    const maxStep = result.passed1 ? (result.passed2 ? 2 : 1) : 0;
    result.step =
      Number.isInteger(value.step) && value.step >= 0 && value.step <= maxStep
        ? value.step
        : 0;
  } catch (error) {
    if (!(error instanceof SyntaxError)) availableStorage = false;
  }
  return result;
}
function complete() {
  return (
    state.passed1 &&
    state.passed2 &&
    calculated.size === files.length &&
    state.confirmed &&
    state.found === unit.altered &&
    state.reason === "changed"
  );
}
function canOpen(index) {
  return index === 0 || (state.passed1 && (index === 1 || state.passed2));
}
function render() {
  for (let index = 0; index < 3; index++) {
    const tab = $(`learn-step-${index}-tab`),
      active = index === state.step;
    tab.disabled = !canOpen(index);
    tab.tabIndex = active ? 0 : -1;
    tab.setAttribute("aria-selected", String(active));
    $(`learn-step-${index}`).hidden = !active;
  }
  $("learn-crypto-error").hidden = supported();
  $("learn-next-1").disabled = !state.passed1;
  $("learn-next-2").disabled = !state.passed2;
  $("learn-experiment").disabled = !supported() || experimenting;
  $("learn-experiment").textContent = experimenting
    ? "Hashing…"
    : "Hash both examples";
  $("learn-experiment").dataset.busy = String(experimenting);
  $("learn-experiment-results").hidden = $("learn-quiz-2").hidden = !experiment;
  if (experiment) {
    $("learn-example-a").textContent = experiment.a;
    $("learn-example-b").textContent = experiment.b;
    $("learn-example-difference").textContent =
      `${experiment.count} of 256 output bits changed. The count varies for different edits; it is not always exactly half.`;
  }
  for (const file of files) {
    const value = calculated.get(file.id),
      button = $("learn-hash-" + file.id);
    button.disabled = !supported() || pending.has(file.id) || !!value;
    button.textContent = pending.has(file.id)
      ? "Hashing…"
      : value
        ? "Hash calculated"
        : "Hash this file";
    button.dataset.busy = String(pending.has(file.id));
    $("learn-actual-" + file.id).textContent = value || "Not calculated yet";
    const comparison = $("learn-match-" + file.id);
    comparison.hidden = !value;
    comparison.dataset.match = String(value === file.expected);
    comparison.textContent =
      value === file.expected
        ? "Matches the trusted record."
        : "Mismatch: these bytes differ from the trusted record.";
  }
  $("learn-check-evidence").disabled = calculated.size !== files.length;
  $("learn-complete").hidden = !complete();
  const passed =
    Number(state.passed1) + Number(state.passed2) + Number(complete());
  $("learn-progress").textContent =
    `${passed} of 3 steps complete${complete() ? " · Practice lesson completed" : ""}`;
  save();
}
function openStep(index, focus = true) {
  if (!canOpen(index)) return;
  state.step = index;
  render();
  if (focus) $("learn-title-" + index).focus();
}
async function runExperiment(announce = true) {
  if (!supported() || experimenting) return;
  const token = revision;
  experimenting = true;
  render();
  try {
    const encoder = new TextEncoder();
    const [a, b] = await Promise.all([
      sha256(encoder.encode("Meet at dawn.")),
      sha256(encoder.encode("Meet at Dawn.")),
    ]);
    if (token !== revision) return;
    const bitsA = digestBits(a),
      bitsB = digestBits(b);
    experiment = {
      a,
      b,
      count: [...bitsA].filter((bit, index) => bit !== bitsB[index]).length,
    };
    state.experiment = true;
    if (announce)
      feedback(
        "learn-experiment-status",
        "Both hashes calculated. Answer the question about what changed.",
      );
  } catch {
    if (token === revision)
      feedback(
        "learn-experiment-status",
        "The example could not be hashed. Try again.",
        true,
      );
  } finally {
    if (token === revision) {
      experimenting = false;
      render();
    }
  }
}
async function hashEvidence(file, announce = true) {
  if (!supported() || pending.has(file.id)) return;
  const token = revision;
  pending.add(file.id);
  render();
  try {
    const value = await sha256(file.bytes);
    if (token !== revision) return;
    calculated.set(file.id, value);
    state.hashed = [...calculated.keys()];
    if (announce)
      feedback(
        "learn-evidence-feedback",
        `${file.name}: ${value === file.expected ? "matches" : "does not match"} the trusted digest.${calculated.size === files.length ? " Now check your findings below." : " Calculate the remaining file hashes."}`,
      );
  } catch {
    if (token === revision)
      feedback(
        "learn-evidence-feedback",
        "This file could not be hashed. Try its button again.",
        true,
      );
  } finally {
    if (token === revision) {
      pending.delete(file.id);
      render();
    }
  }
}
async function download(file) {
  try {
    if (window.Capacitor?.isNativePlatform()) {
      const result = await window.Capacitor.Plugins.CipherFiles.saveText({
        filename: file.name,
        text: new TextDecoder("utf-8", { fatal: true }).decode(file.bytes),
      });
      feedback(
        "learn-evidence-feedback",
        result.cancelled
          ? "Save cancelled."
          : `${file.name} saved. You can open it in Hash Lab.`,
      );
    } else {
      const url = URL.createObjectURL(
        new Blob([file.bytes], { type: "text/plain;charset=utf-8" }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = file.name;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      feedback(
        "learn-evidence-feedback",
        `${file.name} download started. You can open it in Hash Lab.`,
      );
    }
  } catch {
    feedback(
      "learn-evidence-feedback",
      "The file could not be saved. Try again; you can still hash it here.",
      true,
    );
  }
}
function buildEvidence() {
  $("learn-evidence").replaceChildren(
    ...files.map((file) => {
      const article = document.createElement("article");
      article.className = "learn-evidence-file";
      const title = document.createElement("h4");
      title.textContent = file.name;
      const expectedLabel = document.createElement("p");
      expectedLabel.className = "hint";
      expectedLabel.textContent = "Trusted expected SHA-256";
      const expected = document.createElement("code");
      expected.className = "hash-digest";
      expected.textContent = file.expected;
      const actualLabel = document.createElement("p");
      actualLabel.className = "hint";
      actualLabel.textContent = "Calculated SHA-256";
      const actual = document.createElement("code");
      actual.id = "learn-actual-" + file.id;
      actual.className = "hash-digest";
      const comparison = document.createElement("p");
      comparison.id = "learn-match-" + file.id;
      comparison.className = "hint";
      const actions = document.createElement("div");
      actions.className = "actions";
      const button = document.createElement("button");
      button.id = "learn-hash-" + file.id;
      button.textContent = "Hash this file";
      button.setAttribute("aria-label", "Hash " + file.name);
      button.onclick = () => hashEvidence(file);
      const save = document.createElement("button");
      save.className = "text-button";
      save.textContent = "Save file";
      save.setAttribute("aria-label", "Save " + file.name);
      save.onclick = () => download(file);
      actions.append(button, save);
      article.append(
        title,
        expectedLabel,
        expected,
        actualLabel,
        actual,
        comparison,
        actions,
      );
      return article;
    }),
  );
  $("learn-file-choices").replaceChildren(
    ...files.map((file) => {
      const label = document.createElement("label");
      label.className = "learn-choice";
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "learn-found";
      radio.value = file.id;
      label.append(radio, file.name);
      return label;
    }),
  );
}
function restoreAnswers() {
  for (const [name, value] of [
    ["learn-quiz-1", state.quiz1],
    ["learn-quiz-2", state.quiz2],
    ["learn-found", state.found],
    ["learn-reason", state.reason],
  ]) {
    document.querySelectorAll(`input[name="${name}"]`).forEach((radio) => {
      radio.checked = radio.value === value;
    });
  }
}
function wire() {
  for (let index = 0; index < 3; index++) {
    $("learn-step-" + index + "-tab").onclick = () => openStep(index);
    $("learn-step-" + index + "-tab").onkeydown = (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key))
        return;
      event.preventDefault();
      const enabled = [0, 1, 2].filter(canOpen),
        current = enabled.indexOf(state.step);
      const next =
        event.key === "Home"
          ? enabled[0]
          : event.key === "End"
            ? enabled.at(-1)
            : enabled[
                (current +
                  (event.key === "ArrowRight" ? 1 : enabled.length - 1)) %
                  enabled.length
              ];
      openStep(next, false);
      $("learn-step-" + next + "-tab").focus();
    };
  }
  for (const number of [1, 2]) {
    document.querySelectorAll(`input[name="learn-quiz-${number}"]`).forEach(
      (radio) =>
        (radio.onchange = () => {
          state["quiz" + number] = radio.value;
          state["passed" + number] = false;
          state.confirmed = false;
          feedback(
            "learn-feedback-" + number,
            "Answer selected. Choose Check answer for feedback.",
          );
          render();
        }),
    );
    $("learn-check-" + number).onclick = () => {
      const answer = state["quiz" + number];
      if (!answer) {
        feedback("learn-feedback-" + number, "Choose an answer first.", true);
        return;
      }
      const correct =
        answer === (number === 1 ? "same" : "varies") &&
        (number === 1 || !!experiment);
      state["passed" + number] = correct;
      feedback(
        "learn-feedback-" + number,
        correct
          ? number === 1
            ? "Correct. Identical bytes produce the same SHA-256 every time."
            : "Correct. Many bits often change, but the number varies with the edit."
          : number === 1
            ? "Try again. Hashing is deterministic: it uses the input bytes, not a random value or decryption key."
            : "Try again. Our example changed 129 bits, not exactly 128. Different edits can give different counts.",
        !correct,
      );
      render();
    };
  }
  $("learn-next-1").onclick = () => openStep(1);
  $("learn-next-2").onclick = () => openStep(2);
  $("learn-experiment").onclick = () => runExperiment();
  $("learn-hint").onclick = () => {
    $("learn-hint-text").hidden = !$("learn-hint-text").hidden;
    $("learn-hint").setAttribute(
      "aria-expanded",
      String(!$("learn-hint-text").hidden),
    );
    $("learn-hint").textContent = $("learn-hint-text").hidden
      ? "Get a hint"
      : "Hide hint";
  };
  for (const [name, key] of [
    ["learn-found", "found"],
    ["learn-reason", "reason"],
  ])
    document.querySelectorAll(`input[name="${name}"]`).forEach(
      (radio) =>
        (radio.onchange = () => {
          state[key] = radio.value;
          state.confirmed = false;
          render();
        }),
    );
  $("learn-check-evidence").onclick = () => {
    if (calculated.size !== files.length) return;
    if (!state.found || !state.reason) {
      feedback(
        "learn-evidence-feedback",
        "Choose a file and a conclusion before checking.",
        true,
      );
      return;
    }
    state.confirmed =
      state.found === unit.altered && state.reason === "changed";
    feedback(
      "learn-evidence-feedback",
      state.confirmed
        ? "Correct. The beacon order differs from the trusted record, but the hash alone cannot explain the cause."
        : state.found !== unit.altered
          ? "Look again at the calculated digests. Which one does not match its trusted record?"
          : "You found the mismatch. Now reconsider what it proves: a hash cannot tell you who changed a file, why, or whether matching files are safe.",
      !state.confirmed,
    );
    render();
    if (complete()) $("learn-complete-title").focus();
  };
  $("learn-reset").onclick = () => {
    $("learn-reset-confirm").hidden = false;
    $("learn-reset-no").focus();
  };
  $("learn-reset-no").onclick = () => {
    $("learn-reset-confirm").hidden = true;
    $("learn-reset").focus();
  };
  $("learn-reset-yes").onclick = () => {
    revision++;
    state = fresh();
    calculated.clear();
    pending.clear();
    experiment = null;
    experimenting = false;
    for (const id of [
      "learn-feedback-1",
      "learn-feedback-2",
      "learn-experiment-status",
    ])
      feedback(id, "");
    feedback(
      "learn-evidence-feedback",
      "Calculate all three file hashes before checking your findings.",
    );
    $("learn-hint-text").hidden = true;
    $("learn-hint").setAttribute("aria-expanded", "false");
    $("learn-hint").textContent = "Get a hint";
    $("learn-reset-confirm").hidden = true;
    restoreAnswers();
    render();
    $("learn-title-0").focus();
  };
}
export async function openLesson() {
  if (unit || loading) return;
  loading = true;
  $("learn-loading").hidden = false;
  $("learn-error").hidden = true;
  try {
    const response = await fetch("./learn/hash-integrity.json");
    if (!response.ok) throw new Error("Lesson unavailable");
    const data = await response.json();
    if (
      data.id !== "hash-integrity" ||
      data.version !== 1 ||
      !Array.isArray(data.files) ||
      data.files.length !== 3 ||
      !data.files.every(
        (file) =>
          /^[a-z0-9-]+$/.test(file.id) &&
          file.name === file.id + ".txt" &&
          /^[a-f0-9]{64}$/.test(file.expected),
      ) ||
      new Set(data.files.map((file) => file.id)).size !== 3 ||
      !data.files.some((file) => file.id === data.altered)
    )
      throw new Error("Invalid lesson");
    const loaded = await Promise.all(
      data.files.map(async (file) => {
        const result = await fetch("./learn/evidence/" + file.name);
        if (!result.ok) throw new Error("Evidence unavailable");
        const bytes = new Uint8Array(await result.arrayBuffer());
        if (bytes.byteLength > 65536) throw new Error("Invalid evidence size");
        return { ...file, bytes };
      }),
    );
    unit = data;
    files = loaded;
    state = restore();
    buildEvidence();
    wire();
    restoreAnswers();
    // Recompute saved observations from actual bytes; do not trust stored digests.
    const previouslyHashed = [...state.hashed];
    if (supported()) {
      if (state.experiment) await runExperiment(false);
      await Promise.all(
        files
          .filter((file) => previouslyHashed.includes(file.id))
          .map((file) => hashEvidence(file, false)),
      );
    }
    render();
    $("learn-content").hidden = false;
    $("learn-reset").hidden = false;
  } catch {
    unit = null;
    $("learn-content").hidden = true;
    $("learn-error").hidden = false;
  } finally {
    loading = false;
    $("learn-loading").hidden = true;
  }
}
