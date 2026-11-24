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
let campaign,
  missions = [],
  states = [],
  histories = [],
  caseIndex = 0;
let campaignState = { selected: 0, unlocked: 0 },
  campaignRenderKey = "";
const campaignKey = "ciphercraft.campaign.missing-astronomer.v1";
const keyFor = (data) => `ciphercraft.play.${data.id}.v${data.version}`;

function resolved(index) {
  const data = missions[index],
    progress = states[index];
  return (
    progress &&
    (progress.checked || progress.revealed) &&
    data.letters.every(
      (letter) => progress.guesses[letter] === data.answer[letter],
    )
  );
}
function caseStatus(index) {
  if (resolved(index)) return states[index].revealed ? "Revealed" : "Solved";
  if (index > campaignState.unlocked) return "Locked";
  return Object.keys(states[index].guesses).length || states[index].clues
    ? "In progress"
    : "Ready";
}
function renderCampaign() {
  const statuses = missions.map((_, index) => caseStatus(index));
  const key = JSON.stringify([caseIndex, statuses]);
  if (key !== campaignRenderKey) {
    campaignRenderKey = key;
    $("campaign-cases").replaceChildren(
      ...missions.map((data, index) => {
        const button = document.createElement("button");
        button.className = "secondary campaign-case";
        button.dataset.case = String(index + 1);
        button.disabled = index > campaignState.unlocked;
        if (index === caseIndex) button.setAttribute("aria-current", "step");
        const title = document.createElement("span");
        title.textContent = `${index + 1}. ${data.title}`;
        const status = document.createElement("small");
        status.textContent = statuses[index];
        button.append(title, status);
        button.onclick = () => activate(index, true);
        return button;
      }),
    );
  }
  const solved = statuses.filter((s) => s === "Solved").length;
  const revealed = statuses.filter((s) => s === "Revealed").length;
  $("campaign-progress").textContent =
    `${solved} of ${missions.length} cases solved · ${revealed} revealed`;
  $("campaign-resume").textContent = statuses.every(
    (s) => s === "Solved" || s === "Revealed",
  )
    ? "Revisit final case"
    : "Continue campaign";
  $("campaign-complete").hidden = !missions.every((_, index) =>
    resolved(index),
  );
  $("campaign-ending").textContent =
    `You followed all five messages to the end of The Missing Astronomer: ${solved} cases solved and ${revealed} revealed.`;
}
function activate(index, focus = false) {
  if (
    !Number.isInteger(index) ||
    index < 0 ||
    index > campaignState.unlocked ||
    index >= missions.length
  )
    return;
  caseIndex = index;
  campaignState.selected = index;
  mission = missions[index];
  state = states[index];
  history = histories[index];
  answer = mission.answer;
  counts = mission.counts;
  letters = mission.letters;
  storageKey = keyFor(mission);
  activeLetter = "";
  $("mission-title").textContent = mission.title;
  $("mission-number").textContent =
    `CASE ${String(index + 1).padStart(2, "0")} · ${mission.skill.toUpperCase()}`;
  document.querySelector(".mission-brief").textContent = mission.briefing;
  document.querySelector(".mission-level").textContent = mission.level;
  $("mission-first-move").querySelector("p").textContent =
    mission.firstMove?.description || "";
  $("mission-try-word").textContent = mission.firstMove
    ? `Try ${mission.firstMove.cipher} → ${mission.firstMove.plain}`
    : "Try a word";
  for (const kind of ["reset", "reveal"])
    $("mission-" + kind + "-confirm").hidden = true;
  createBoard();
  render();
  $("mission-note").scrollTop = 0;
  tell(
    resolved(index)
      ? state.revealed
        ? "Welcome back. This note was revealed."
        : "Welcome back. This case is solved."
      : "Start with a short repeated word. Guesses are reversible.",
  );
  if (focus) $("mission-title").focus();
}

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
  states[caseIndex] = state;
  if (resolved(caseIndex))
    campaignState.unlocked = Math.max(
      campaignState.unlocked,
      Math.min(missions.length - 1, caseIndex + 1),
    );
  if (storageAvailable) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
      localStorage.setItem(campaignKey, JSON.stringify(campaignState));
    } catch {
      storageAvailable = false;
    }
  }
  $("mission-storage").textContent = storageAvailable
    ? "Case progress saves on this device. Your cipher tools stay separate."
    : "Device storage is unavailable. You can keep playing, but progress will be lost when this page closes.";
  renderCampaign();
}
function restore(data) {
  const fresh = { guesses: {}, clues: 0, checked: false, revealed: false };
  try {
    const raw = localStorage.getItem(keyFor(data));
    if (!raw || raw.length > 4096) return fresh;
    const stored = JSON.parse(raw);
    if (!stored || typeof stored !== "object") return fresh;
    const used = new Set();
    for (const letter of data.letters) {
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
  return mission.clues;
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
  $("mission-first-move").hidden = filled > 0 || !mission.firstMove;
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
    ? "The full note is shown above. This case counts as revealed, rather than solved. " +
      mission.ending
    : mission.ending;
  $("mission-next").hidden = !complete || caseIndex === missions.length - 1;
  $("mission-next-help").textContent =
    caseIndex === missions.length - 1
      ? "You reached the final case. Replay earlier cases using the case list."
      : `Next: ${missions[caseIndex + 1].title}. Revealing a note also lets you continue the story.`;
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
  $("campaign-resume").onclick = () => {
    const index = missions.findIndex(
      (_, i) => i <= campaignState.unlocked && !resolved(i),
    );
    activate(index < 0 ? missions.length - 1 : index, true);
  };
  $("mission-next").onclick = () => {
    if (resolved(caseIndex)) activate(caseIndex + 1, true);
  };
  $("mission-try-word").onclick = () => {
    if (Object.keys(state.guesses).length) return;
    remember();
    if (!mission.firstMove) return;
    state.guesses = Object.fromEntries(
      [...mission.firstMove.cipher].map((letter, i) => [
        letter,
        mission.firstMove.plain[i],
      ]),
    );
    state.clues = Math.max(1, state.clues);
    render();
    tell(
      "You tried AOL as THE. Every A now reads T, every O reads H, and every L reads E. Try another letter below, or get the next clue.",
    );
    $("guess-" + mission.firstMove.cipher[0]).focus();
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
    tell(
      `Case solved: ${mission.title}. ${caseIndex === missions.length - 1 ? "You reached the end of the mystery." : "The next case is ready."}`,
    );
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
function validateMission(data) {
  if (
    !data ||
    !/^[a-z0-9-]+$/.test(data.id) ||
    !Number.isInteger(data.version) ||
    data.version < 1 ||
    typeof data.ciphertext !== "string" ||
    !data.ciphertext.length ||
    data.ciphertext.length > 500 ||
    typeof data.solution !== "string" ||
    data.ciphertext.length !== data.solution.length ||
    ![data.title, data.briefing, data.level, data.skill, data.ending].every(
      (text) => typeof text === "string" && text.length > 0,
    ) ||
    !Array.isArray(data.clues) ||
    data.clues.length !== 3 ||
    !data.clues.every((text) => typeof text === "string" && text.length > 0)
  )
    throw new Error("Invalid case");
  const answer = {},
    counts = {};
  [...data.ciphertext].forEach((letter, i) => {
    const plain = data.solution[i];
    if (!alphabet.test(letter)) {
      if (plain !== letter || !/[ .,!?'\-]/.test(letter))
        throw new Error("Invalid punctuation");
      return;
    }
    if (!alphabet.test(plain) || (answer[letter] && answer[letter] !== plain))
      throw new Error("Inconsistent case");
    answer[letter] = plain;
    counts[letter] = (counts[letter] || 0) + 1;
  });
  const letters = Object.keys(answer).sort();
  if (!letters.length || new Set(Object.values(answer)).size !== letters.length)
    throw new Error("Invalid alphabet");
  if (
    data.firstMove &&
    (typeof data.firstMove.cipher !== "string" ||
      typeof data.firstMove.plain !== "string" ||
      !data.firstMove.cipher.length ||
      data.firstMove.cipher.length !== data.firstMove.plain.length ||
      !data.ciphertext.includes(data.firstMove.cipher) ||
      ![...data.firstMove.cipher].every(
        (letter, i) => answer[letter] === data.firstMove.plain[i],
      ))
  )
    throw new Error("Invalid first move");
  return { ...data, answer, counts, letters };
}
async function loadJSON(file) {
  const response = await fetch("./missions/" + file);
  if (!response.ok) throw new Error("Case unavailable");
  return response.json();
}
export async function openMission() {
  if (mission || loading) return;
  loading = true;
  $("mission-error").hidden = true;
  $("mission-loading").hidden = false;
  try {
    const manifest = await loadJSON("campaign.json");
    if (
      manifest.id !== "missing-astronomer" ||
      manifest.version !== 1 ||
      typeof manifest.title !== "string" ||
      !Array.isArray(manifest.missions) ||
      manifest.missions.length !== 5 ||
      !manifest.missions.every((file) => /^[a-z0-9-]+\.json$/.test(file))
    )
      throw new Error("Invalid campaign");
    const loaded = (await Promise.all(manifest.missions.map(loadJSON))).map(
      validateMission,
    );
    if (new Set(loaded.map((data) => data.id)).size !== loaded.length)
      throw new Error("Duplicate case");
    campaign = manifest;
    missions = loaded;
    states = missions.map(restore);
    histories = missions.map(() => []);
    try {
      const raw = localStorage.getItem(campaignKey);
      const stored = raw && raw.length <= 1024 ? JSON.parse(raw) : null;
      if (
        stored &&
        Number.isInteger(stored.unlocked) &&
        stored.unlocked >= 0 &&
        stored.unlocked < missions.length
      ) {
        campaignState.unlocked = stored.unlocked;
        campaignState.selected =
          Number.isInteger(stored.selected) &&
          stored.selected >= 0 &&
          stored.selected <= stored.unlocked
            ? stored.selected
            : 0;
      }
    } catch (error) {
      if (!(error instanceof SyntaxError)) storageAvailable = false;
    }
    // Migrate the original standalone case and recover progress if the ledger was lost.
    missions.forEach((data, index) => {
      if (resolved(index))
        campaignState.unlocked = Math.max(
          campaignState.unlocked,
          Math.min(index + 1, missions.length - 1),
        );
      else if (Object.keys(states[index].guesses).length || states[index].clues)
        campaignState.unlocked = Math.max(campaignState.unlocked, index);
    });
    $("campaign-title").textContent = campaign.title;
    $("campaign-header").hidden = false;
    wireActions();
    activate(campaignState.selected);
    $("mission-content").hidden = false;
  } catch {
    mission = null;
    $("mission-content").hidden = true;
    $("campaign-header").hidden = true;
    $("mission-error").hidden = false;
  } finally {
    loading = false;
    $("mission-loading").hidden = true;
  }
}
$("mission-retry").onclick = openMission;
