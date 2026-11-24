// The mission owns its state. It never reads or writes cipher-tool inputs.
const $ = (id) => document.getElementById(id);
const alphabet = /^[A-Z]$/;
let mission,
  loading = false,
  state,
  letters,
  answer,
  counts,
  storageKey;
let history = [],
  activeLetter = "",
  storageAvailable = true;

function snapshot() {
  return {
    guesses: { ...state.guesses },
    clues: state.clues,
    checked: state.checked,
    revealed: state.revealed,
  };
}
function remember() {
  history.push(snapshot());
  if (history.length > 50) history.shift();
}
function correct() {
  return letters.every((letter) => state.guesses[letter] === answer[letter]);
}
function tell(text, error = false) {
  $("mission-status").textContent = text;
  $("mission-status").dataset.error = String(error);
}
function save() {
  if (storageAvailable) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      storageAvailable = false;
    }
  }
  $("mission-storage").textContent = storageAvailable
    ? "Case progress saves on this device. Your cipher tools stay separate."
    : "Device storage is unavailable. You can keep playing, but progress will be lost when this page closes.";
}
function restore() {
  const fresh = { guesses: {}, clues: 0, checked: false, revealed: false };
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw || raw.length > 4096) return fresh;
    const stored = JSON.parse(raw);
    if (!stored || typeof stored !== "object") return fresh;
    const used = new Set();
    for (const letter of letters) {
      const value = stored.guesses?.[letter];
      if (
        typeof value === "string" &&
        alphabet.test(value) &&
        !used.has(value)
      ) {
        fresh.guesses[letter] = value;
        used.add(value);
      }
    }
    fresh.clues = Number.isInteger(stored.clues)
      ? Math.max(0, Math.min(3, stored.clues))
      : 0;
    fresh.checked = stored.checked === true;
    fresh.revealed = stored.revealed === true;
  } catch (error) {
    if (!(error instanceof SyntaxError)) storageAvailable = false;
  }
  return fresh;
}
function clueTexts() {
  const repeated = mission.ciphertext
    .split(/[^A-Z]+/)
    .filter((word) => word === "AOL").length;
  const frequent = [...letters].sort(
    (a, b) => counts[b] - counts[a] || a.localeCompare(b),
  )[0];
  return [
    `AOL appears ${repeated} times as a complete three-letter word. THE is a useful word to try. ${frequent} is the most frequent cipher letter (${counts[frequent]} appearances).`,
    "This note uses a Caesar cipher: the whole alphabet moved by the same number of places. If AOL means THE, each pair must follow the same shift.",
    "A stands for T, O stands for H, and L stands for E. The encryption shift is 7. Use that pattern to work out the remaining letters.",
  ];
}
function render() {
  for (const letter of letters) {
    const input = $("guess-" + letter);
    if (input.value !== (state.guesses[letter] || ""))
      input.value = state.guesses[letter] || "";
    input.removeAttribute("aria-invalid");
  }
  for (const cell of $("mission-note").querySelectorAll("[data-letter]")) {
    cell.querySelector(".mission-guess").textContent =
      state.guesses[cell.dataset.letter] || "·";
    cell.dataset.highlight = String(cell.dataset.letter === activeLetter);
  }
  $("mission-readable").textContent =
    "Your reading: " +
    [...mission.ciphertext]
      .map((letter) =>
        alphabet.test(letter) ? state.guesses[letter] || "_" : letter,
      )
      .join("");
  const filled = Object.keys(state.guesses).length;
  $("mission-first-move").hidden = filled > 0;
  $("mission-progress").textContent =
    `${filled} of ${letters.length} letter guesses filled`;
  $("mission-undo").disabled = !history.length;
  $("mission-clue").disabled = state.clues >= 3;
  $("mission-clue").textContent =
    state.clues >= 3 ? "All clues shown" : "Get a clue";
  $("mission-clues").hidden = state.clues === 0;
  $("mission-clue-list").replaceChildren(
    ...clueTexts()
      .slice(0, state.clues)
      .map((text) => {
        const item = document.createElement("li");
        item.textContent = text;
        return item;
      }),
  );
  const complete = correct() && (state.checked || state.revealed);
  $("mission-complete").hidden = !complete;
  $("mission-complete-title").textContent = state.revealed
    ? "Note revealed"
    : "Case solved";
  $("mission-ending").textContent = state.revealed
    ? "The full note is shown above. Undo the reveal or reset the case to try solving it yourself."
    : mission.ending;
  save();
}
function changeGuess(letter, input) {
  const value = input.value.toUpperCase();
  const previous = state.guesses[letter] || "";
  if (value && !alphabet.test(value)) {
    input.value = previous;
    input.setAttribute("aria-invalid", "true");
    tell("Use one English letter, A to Z, or clear the box.", true);
    return;
  }
  const duplicate = letters.find(
    (other) => other !== letter && state.guesses[other] === value && value,
  );
  if (duplicate) {
    input.value = previous;
    input.setAttribute("aria-invalid", "true");
    tell(
      `${value} is already assigned to cipher ${duplicate}. Clear that guess first to reuse it.`,
      true,
    );
    return;
  }
  if (value === previous) return;
  remember();
  if (value) state.guesses[letter] = value;
  else delete state.guesses[letter];
  state.checked = state.revealed = false;
  render();
  tell(
    value
      ? `Cipher ${letter} now reads ${value}.`
      : `Guess for ${letter} cleared.`,
  );
}
function createBoard() {
  const words = mission.ciphertext.split(" ").map((word) => {
    const group = document.createElement("span");
    group.className = "mission-word";
    for (const letter of word) {
      const cell = document.createElement("span");
      cell.className = "mission-letter";
      const top = document.createElement("span");
      top.className = "mission-cipher";
      top.textContent = letter;
      const bottom = document.createElement("span");
      bottom.className = "mission-guess";
      if (alphabet.test(letter)) cell.dataset.letter = letter;
      else bottom.textContent = letter;
      cell.append(top, bottom);
      group.append(cell);
    }
    return group;
  });
  $("mission-note").replaceChildren(...words);
  $("mission-mappings").replaceChildren(
    ...letters.map((letter) => {
      const group = document.createElement("div");
      group.className = "mission-map";
      const label = document.createElement("label");
      label.htmlFor = "guess-" + letter;
      label.append(letter);
      const count = document.createElement("small");
      count.textContent = counts[letter];
      count.setAttribute("aria-hidden", "true");
      label.append(count);
      const input = document.createElement("input");
      input.id = "guess-" + letter;
      input.maxLength = 1;
      input.autocomplete = "off";
      input.spellcheck = false;
      input.autocapitalize = "characters";
      input.setAttribute(
        "aria-label",
        `Cipher ${letter} becomes (${counts[letter]} appearances)`,
      );
      input.setAttribute("aria-describedby", "mission-map-help mission-status");
      input.addEventListener("input", () => changeGuess(letter, input));
      input.addEventListener("focus", () => {
        activeLetter = letter;
        render();
      });
      input.addEventListener("blur", () => {
        activeLetter = "";
        render();
      });
      group.append(label, input);
      return group;
    }),
  );
}
function wireActions() {
  $("mission-try-word").onclick = () => {
    if (Object.keys(state.guesses).length) return;
    remember();
    state.guesses = { A: "T", O: "H", L: "E" };
    state.clues = Math.max(1, state.clues);
    render();
    tell(
      "You tried AOL as THE. Every A now reads T, every O reads H, and every L reads E. Try another letter below, or get the next clue.",
    );
    $("guess-A").focus();
  };
  $("mission-check").onclick = () => {
    if (state.revealed) {
      tell(
        "This note was revealed. Undo the reveal or reset to try solving it yourself.",
      );
      return;
    }
    const missing = letters.length - Object.keys(state.guesses).length;
    if (missing) {
      tell(
        `${missing} letter guesses are still blank. Keep going or get a clue.`,
      );
      return;
    }
    if (!correct()) {
      tell(
        "The note is not quite right yet. Check repeated words, or get a clue. Your guesses are safe.",
        true,
      );
      return;
    }
    remember();
    state.checked = true;
    render();
    tell("Case solved. You found the meeting place and what to bring.");
    $("mission-complete-title").focus();
  };
  $("mission-undo").onclick = () => {
    if (!history.length) return;
    state = history.pop();
    render();
    tell("Last change undone.");
  };
  $("mission-clue").onclick = () => {
    if (state.clues >= 3) return;
    remember();
    state.clues++;
    render();
    tell(`Clue ${state.clues}: ${clueTexts()[state.clues - 1]}`);
  };
  for (const kind of ["reset", "reveal"]) {
    $("mission-" + kind).onclick = () => {
      $("mission-" + kind + "-confirm").hidden = false;
      $("mission-" + kind + "-no").focus();
    };
    $("mission-" + kind + "-no").onclick = () => {
      $("mission-" + kind + "-confirm").hidden = true;
      $("mission-" + kind).focus();
    };
    $("mission-" + kind + "-yes").onclick = () => {
      remember();
      state =
        kind === "reset"
          ? { guesses: {}, clues: 0, checked: false, revealed: false }
          : {
              ...state,
              guesses: { ...answer },
              checked: false,
              revealed: true,
            };
      $("mission-" + kind + "-confirm").hidden = true;
      render();
      tell(
        kind === "reset"
          ? "Case reset. Undo can restore your progress."
          : "Solution revealed. You can undo this to keep solving.",
      );
      $(
        kind === "reset" ? "guess-" + letters[0] : "mission-complete-title",
      ).focus();
    };
  }
}
export async function openMission() {
  if (mission || loading) return;
  loading = true;
  $("mission-error").hidden = true;
  $("mission-loading").hidden = false;
  try {
    const response = await fetch("./missions/observatory-note.json");
    if (!response.ok) throw new Error("Case unavailable");
    const data = await response.json();
    if (!data.ciphertext || data.ciphertext.length !== data.solution?.length)
      throw new Error("Invalid case");
    answer = {};
    counts = {};
    [...data.ciphertext].forEach((letter, i) => {
      if (!alphabet.test(letter)) return;
      if (answer[letter] && answer[letter] !== data.solution[i])
        throw new Error("Inconsistent case");
      answer[letter] = data.solution[i];
      counts[letter] = (counts[letter] || 0) + 1;
    });
    letters = Object.keys(answer).sort();
    storageKey = `ciphercraft.play.${data.id}.v${data.version}`;
    mission = data;
    state = restore();
    createBoard();
    wireActions();
    render();
    $("mission-content").hidden = false;
    tell(
      correct() && state.checked
        ? "Welcome back. This case is solved."
        : "Start with a short repeated word. Guesses are reversible.",
    );
  } catch {
    mission = null;
    $("mission-error").hidden = false;
  } finally {
    loading = false;
    $("mission-loading").hidden = true;
  }
}
$("mission-retry").onclick = openMission;
