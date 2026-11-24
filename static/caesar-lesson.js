import { requestCipher } from "./app.js";
const $ = (id) => document.getElementById(id);
const storageKey = "ciphercraft.learn.caesar.v1";
const fresh = () => ({ step: 0, letter: "", word: "", key: null, phrase: "" });
const normal = (value) =>
  value
    .trim()
    .toUpperCase()
    .replace(/[.!?]+$/, "")
    .trim()
    .replace(/\s+/g, " ");
let state = fresh(),
  initialized = false,
  generation = 0,
  busy = false,
  storage = true;
const hints = [
  [
    "Start at Y. The first move lands on Z.",
    "The second move wraps to A. Take one more move.",
  ],
  [
    "Move backward: F → E → D → C. That recovers the first letter.",
    "Move D and W backward by the same three places. Wrapping works backward too.",
  ],
  [
    "Compare the known first letter M with the encrypted first letter T. Count forward from M.",
    "M → N → O → P → Q → R → S → T is seven moves. Decrypt by moving backward seven.",
  ],
];
let hintLevels = [0, 0, 0];
const passed = (i) =>
  i === 0
    ? state.letter === "B"
    : i === 1
      ? state.word === "CAT"
      : state.key === 7 && state.phrase === "MEET ME AT NOON";
const allowed = (i) => i === 0 || (passed(0) && (i === 1 || passed(1)));
function say(id, text, error = false) {
  $(id).textContent = text;
  $(id).dataset.error = String(error);
}
function save() {
  try {
    if (storage) localStorage.setItem(storageKey, JSON.stringify(state));
  } catch {
    storage = false;
  }
  $("cs-storage").textContent = storage
    ? "Caesar practice progress saves on this device. Your other work stays separate."
    : "Device storage is unavailable. You can keep practicing, but progress will be lost when this page closes.";
}
function render() {
  for (let i = 0; i < 3; i++) {
    const active = state.step === i,
      tab = $(`cs-step-${i}-tab`);
    tab.disabled = !allowed(i);
    tab.tabIndex = active ? 0 : -1;
    tab.setAttribute("aria-selected", String(active));
    $(`cs-step-${i}`).hidden = !active;
    $(`cs-check-${i}`).disabled = busy;
    $(`cs-check-${i}`).dataset.busy = String(busy);
  }
  $("cs-next-0").disabled = !passed(0);
  $("cs-next-1").disabled = !passed(1);
  $("cs-trace").hidden = !passed(0);
  $("cs-word-mapping").hidden = !passed(1);
  $("cs-complete").hidden = !passed(2);
  $("cs-progress").textContent =
    `${[0, 1, 2].filter(passed).length} of 3 steps complete`;
  save();
}
function stage(i, focus = true) {
  if (!allowed(i)) return;
  state.step = i;
  render();
  if (focus) $(`cs-title-${i}`).focus();
}
function restore() {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw || raw.length > 1024) return;
    const value = JSON.parse(raw);
    if (!value || typeof value !== "object") return;
    if (value.letter === "B") state.letter = "B";
    if (passed(0) && value.word === "CAT") state.word = "CAT";
    if (passed(1) && value.key === 7 && value.phrase === "MEET ME AT NOON") {
      state.key = 7;
      state.phrase = value.phrase;
    }
    if (
      Number.isInteger(value.step) &&
      value.step >= 0 &&
      value.step <= 2 &&
      allowed(value.step)
    )
      state.step = value.step;
  } catch (error) {
    if (!(error instanceof SyntaxError)) storage = false;
  }
}
async function check(i) {
  if (busy) return;
  const key = i === 2 ? Number($("cs-key").value) : 3;
  if (i === 2 && !/^(?:[0-9]|1[0-9]|2[0-5])$/.test($("cs-key").value)) {
    say("cs-feedback-2", "Use a whole-number shift from 0 to 25.", true);
    return;
  }
  const answer =
    i === 0
      ? $("cs-letter").value.trim().toUpperCase()
      : i === 1
        ? $("cs-word").value.trim().toUpperCase()
        : normal($("cs-phrase").value);
  const current = ++generation;
  busy = true;
  render();
  say(`cs-feedback-${i}`, "Checking with the local cipher engine…");
  try {
    const output = await requestCipher(i === 0 ? "Encrypt" : "Decrypt", {
      cipher: "Caesar",
      text: i === 0 ? "Y" : i === 1 ? "FDW" : "TLLA TL HA UVVU.",
      key,
    });
    if (current !== generation) return;
    const correct =
      i === 2 ? key === 7 && normal(output) === answer : output === answer;
    if (correct) {
      if (i === 0) state.letter = answer;
      else if (i === 1) state.word = answer;
      else {
        state.key = key;
        state.phrase = answer;
      }
    }
    const feedback = correct
      ? [
          "Correct. Y → Z → A → B: three forward moves, wrapping after Z.",
          "Correct. FDW becomes CAT. Decryption reversed every shift by three places.",
          "Correct. Shift 7 recovers MEET ME AT NOON. You used a known word to find the key.",
        ][i]
      : i === 2 && key === 7
        ? "Your key is correct. Recheck the recovered words by moving each letter backward seven places."
        : [
            "Try again. Count three moves starting after Y, and wrap after Z.",
            "Try again. Decryption moves backward, not forward. Start with F and take three backward steps.",
            "Try again. Count the forward distance from known M to encrypted T, then reverse that shift.",
          ][i];
    say(`cs-feedback-${i}`, feedback, !correct);
    render();
    if (correct && i === 2) $("cs-complete-title").focus();
  } catch (error) {
    if (current === generation)
      say(
        `cs-feedback-${i}`,
        error.message ||
          "The cipher engine could not check this answer. Retry, or open Crack a message to restart the engine.",
        true,
      );
  } finally {
    if (current === generation) {
      busy = false;
      render();
    }
  }
}
export function openCaesarLesson(openTools) {
  if (initialized) return;
  initialized = true;
  restore();
  $("cs-letter").value = state.letter;
  $("cs-word").value = state.word;
  $("cs-key").value = state.key ?? "";
  $("cs-phrase").value = state.phrase;
  for (let i = 0; i < 3; i++) {
    $(`cs-step-${i}-tab`).onclick = () => stage(i);
    $(`cs-form-${i}`).onsubmit = (e) => {
      e.preventDefault();
      check(i);
    };
    $(`cs-hint-${i}`).onclick = () => {
      say(`cs-hint-text-${i}`, hints[i][Math.min(hintLevels[i]++, 1)]);
    };
    $(`cs-step-${i}-tab`).onkeydown = (e) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
      e.preventDefault();
      const enabled = [0, 1, 2].filter(allowed),
        idx = enabled.indexOf(state.step);
      const next =
        e.key === "Home"
          ? enabled[0]
          : e.key === "End"
            ? enabled.at(-1)
            : enabled[
                (idx + (e.key === "ArrowRight" ? 1 : enabled.length - 1)) %
                  enabled.length
              ];
      stage(next, false);
      $(`cs-step-${next}-tab`).focus();
    };
  }
  for (const [i, ids] of [
    [0, ["cs-letter"]],
    [1, ["cs-word"]],
    [2, ["cs-key", "cs-phrase"]],
  ])
    for (const id of ids)
      $(id).oninput = () => {
        generation++;
        busy = false;
        if (i === 0) state.letter = "";
        if (i <= 1) state.word = "";
        state.key = null;
        state.phrase = "";
        say(`cs-feedback-${i}`, "Answer changed. Check it when you’re ready.");
        render();
      };
  $("cs-next-0").onclick = () => stage(1);
  $("cs-next-1").onclick = () => stage(2);
  $("cs-open-tools").onclick = openTools;
  $("cs-reset").onclick = () => {
    $("cs-reset-confirm").hidden = false;
    $("cs-reset-no").focus();
  };
  $("cs-reset-no").onclick = () => {
    $("cs-reset-confirm").hidden = true;
    $("cs-reset").focus();
  };
  $("cs-reset-yes").onclick = () => {
    generation++;
    busy = false;
    state = fresh();
    hintLevels = [0, 0, 0];
    for (const id of ["cs-letter", "cs-word", "cs-key", "cs-phrase"])
      $(id).value = "";
    for (let i = 0; i < 3; i++) {
      say(`cs-feedback-${i}`, "");
      say(`cs-hint-text-${i}`, "");
    }
    $("cs-reset-confirm").hidden = true;
    render();
    $("cs-title-0").focus();
  };
  render();
}
