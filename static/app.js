const $ = (id) => document.getElementById(id);
let worker,
  loadingTimer,
  readingFile = false,
  fileLoadId = 0,
  ready = false,
  busy = false,
  revision = 0,
  request = 0,
  pending,
  fileMode = false,
  filename = "message.txt",
  operation = "Encrypt",
  resultText = "",
  workflow = "crack",
  activeAction = "",
  isSuggestion = false;
const specs = {
  Caesar: ["Shift (0–25)", "Each letter moves by this many places.", "3"],
  Vigenère: ["Keyword", "Use English letters, for example LEMON.", ""],
  Substitution: [
    "Alphabet key",
    "Enter all 26 English letters, each used once.",
    "",
  ],
  "Columnar transposition": [
    "Keyword or column order",
    "For example ZEBRAS or 2,0,1. Removes spaces and pads with X; decryption keeps that padding.",
    "",
  ],
  "Rail Fence": [
    "Rails (2–100)",
    "Encryption follows a zigzag across this many rails. Spaces are removed.",
    "3",
  ],
  Affine: [
    "Multiplier a",
    "Choose 1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, or 25.",
    "5",
  ],
};
function status(text, error = false) {
  $("status").textContent = text;
  $("status").dataset.error = error;
}
function controls() {
  for (const id of ["encrypt", "decrypt", "analyze", "generate", "identify"])
    $(id).disabled = !ready || busy || readingFile;
  $("analyze").hidden = ![
    "Caesar",
    "Vigenère",
    "Rail Fence",
    "Affine",
  ].includes($("cipher").value);
  const labels = {
    identify: ["Identify & crack", "Cracking…", "crack"],
    encrypt: ["Encrypt", "Encrypting…", "Encrypt"],
    decrypt: ["Decrypt", "Decrypting…", "Decrypt"],
    analyze: ["Find key", "Finding key…", "analyze"],
  };
  for (const [id, [normal, working, action]] of Object.entries(labels)) {
    const running = busy && activeAction === action;
    $(id).textContent = running ? working : normal;
    $(id).dataset.busy = running;
  }
  $("result-panel").setAttribute("aria-busy", String(busy));
  $("example").disabled = busy || readingFile;
}
function renderResult() {
  const hasResult = resultText.length > 0;
  if ($("result").textContent !== resultText)
    $("result").textContent = resultText;
  $("result").classList.toggle("ciphertext", operation === "Encrypt");
  $("result-content").hidden = !hasResult;
  $("copy").disabled =
    $("download").disabled =
    $("reuse").disabled =
      !hasResult;
  $("copy").textContent = "Copy text";
  $("empty-result").hidden =
    hasResult ||
    $("identification").childElementCount > 0 ||
    (!$("suggestions").hidden && $("suggestions").childElementCount > 0);
  $("result-heading").textContent = hasResult
    ? isSuggestion
      ? "Suggested decryption"
      : operation === "Encrypt"
        ? "Encrypted message"
        : "Decrypted message"
    : "Result";
  $("other-guesses").hidden =
    !hasResult ||
    !isSuggestion ||
    (!$("suggestions").hidden && $("suggestions").childElementCount > 0);
}
function updateCount() {
  const count = Array.from($("message").value).length;
  $("character-count").textContent =
    count.toLocaleString() + (count === 1 ? " character" : " characters");
  $("example").hidden = workflow !== "crack" || !!$("message").value.trim();
}
function setMode(mode) {
  if (mode !== workflow) revision++;
  workflow = mode;
  const manual = mode === "manual";
  for (const id of ["crack-tab", "manual-tab"]) {
    const selected = id === (manual ? "manual-tab" : "crack-tab");
    $(id).setAttribute("aria-selected", String(selected));
    $(id).tabIndex = selected ? 0 : -1;
  }
  $("input-panel").setAttribute(
    "aria-labelledby",
    manual ? "manual-tab" : "crack-tab",
  );
  $("manual-settings").hidden = $("manual-actions").hidden = !manual;
  $("identify").hidden = manual;
  $("suggestions").hidden = !manual;
  $("workflow-title").textContent = manual
    ? "Encrypt or decrypt."
    : "Crack a message.";
  $("workflow-description").textContent = manual
    ? "Choose a classical cipher and work with a key you know."
    : "Find a likely cipher, discover its key, and uncover the text.";
  $("message-heading").textContent = manual
    ? "Your message"
    : "Your ciphertext";
  $("message").placeholder = manual
    ? "Type or paste your message…"
    : "Paste an encrypted message here…";
  $("message").classList.toggle("plain-input", manual);
  $("input-help").textContent = manual
    ? "Up to 100,000 characters · Find key searches the selected cipher"
    : "100+ English letters · up to 5,000 characters";
  $("empty-help").textContent = manual
    ? "Choose a cipher and key, then encrypt or decrypt your message."
    : "Add an encrypted message, or try the example to see CipherCraft at work.";
  updateCount();
  renderResult();
  controls();
}
function invalidate() {
  revision++;
  resultText = "";
  isSuggestion = false;
  $("suggestions").replaceChildren();
  $("identification").replaceChildren();
  $("manual-link").hidden = true;
  renderResult();
  if (ready && !busy)
    status("Inputs changed. Choose an action to process the current message.");
}
function start() {
  clearTimeout(loadingTimer);
  ready = false;
  busy = false;
  controls();
  $("retry").hidden = true;
  worker?.terminate();
  status("Loading the cipher engine… The first visit may take a moment.");
  worker = new Worker("./worker.js", { type: "module" });
  loadingTimer = setTimeout(
    () =>
      failed("Loading is taking too long. Check your connection and retry."),
    60000,
  );
  worker.onerror = () =>
    failed(
      "The cipher engine could not load. Check your connection and retry.",
    );
  worker.onmessage = ({ data }) => {
    if (data.fatal) return failed(data.fatal);
    if (data.ready) {
      clearTimeout(loadingTimer);
      ready = true;
      controls();
      status("Ready.");
      return;
    }
    busy = false;
    activeAction = "";
    controls();
    if (!pending || data.id !== pending.id || pending.revision !== revision) {
      status(
        "Inputs changed. Choose an action to process the current message.",
      );
      return;
    }
    if (data.error) return status(data.error, true);
    if (pending.action === "crack") {
      showAutomaticResult(data.result);
      return;
    }
    if (pending.action === "generate") {
      $("key").value = data.result;
      invalidate();
      status("Substitution key generated. Keep it to decrypt your message.");
    } else if (pending.action === "analyze") {
      if (!data.result.length) {
        $("suggestions").replaceChildren();
        renderResult();
        status(
          "No key suggestions were found. Try a longer English ciphertext sample.",
          true,
        );
        return;
      }
      showSuggestions(data.result);
      status(
        "Possible keys found. Choose a suggestion to apply it and decrypt.",
      );
    } else {
      resultText = data.result;
      operation = pending.action;
      isSuggestion = false;
      renderResult();
      status(
        `${operation === "Encrypt" ? "Encryption" : "Decryption"} complete.`,
      );
    }
  };
}
function failed(text) {
  clearTimeout(loadingTimer);
  worker?.terminate();
  ready = false;
  busy = false;
  controls();
  status(text, true);
  $("retry").hidden = false;
}
function run(action) {
  if (!ready || busy || readingFile) return;
  busy = true;
  activeAction = action;
  controls();
  if (action === "crack") invalidate();
  status(
    action === "crack"
      ? "Identifying the cipher and searching for a key…"
      : action === "analyze"
        ? "Analyzing possible keys…"
        : "Processing…",
  );
  pending = { id: ++request, revision, action };
  worker.postMessage({
    id: request,
    action,
    text: fileMode ? originalFile : $("message").value,
    cipher: $("cipher").value,
    key:
      $("cipher").value === "Affine"
        ? [$("key").value, $("key-b").value]
        : $("key").value,
    file_mode: fileMode,
  });
}
function applyKey(cipher, key) {
  $("cipher").value = cipher;
  $("cipher").onchange();
  if (Array.isArray(key)) {
    $("key").value = key[0];
    $("key-b").value = key[1];
  } else $("key").value = key;
}
function showAutomaticResult(data) {
  const best = data.candidates[0];
  if (data.status === "suggested") {
    applyKey(best.cipher, best.key);
    resultText = data.plaintext;
    operation = "Decrypt";
    isSuggestion = true;
  } else {
    $("cipher").value = data.identified[0].cipher;
    $("cipher").onchange();
  }
  const area = $("identification");
  area.replaceChildren();
  const heading = document.createElement("h3");
  heading.textContent =
    data.status === "suggested"
      ? `${best.cipher} · ${best.label}`
      : data.status === "unsupported"
        ? `Likely cipher: ${data.identified[0].cipher}`
        : "No convincing decryption found";
  area.append(heading);
  const note = document.createElement("p");
  note.className = "hint";
  note.textContent =
    data.status === "suggested"
      ? "An AI suggestion, ready for your review."
      : data.status === "unsupported"
        ? "Automatic key recovery is not available for this cipher. Enter a known key to decrypt, or choose another cipher manually."
        : "The available searches did not produce a plausible English message. Try a longer sample or a known key. Unsupported ciphers and plain text can also be misidentified.";
  area.append(note);
  $("manual-link").hidden = data.status === "suggested";
  renderResult();
  status(
    data.status === "suggested"
      ? "Suggested decryption ready. Review the recovered message."
      : data.status === "unsupported"
        ? "Cipher identified, but automatic key recovery is not supported."
        : "No convincing decryption found. Try a longer English sample.",
    data.status !== "suggested",
  );
  heading.tabIndex = -1;
  heading.focus();
}
function showSuggestions(results) {
  $("suggestions").hidden = false;
  const area = $("suggestions");
  area.replaceChildren();
  const heading = document.createElement("h3");
  heading.textContent = "Possible keys";
  area.append(heading);
  const note = document.createElement("p");
  note.className = "hint";
  note.textContent =
    "Ranked by our locally trained English language model. These are suggestions, not guaranteed decryptions.";
  area.append(note);
  for (const item of results) {
    const button = document.createElement("button");
    button.className = "secondary";
    button.textContent = `${item.label}\n${item.sample}\nApply key and decrypt`;
    button.onclick = () => {
      if (Array.isArray(item.key)) {
        $("key").value = item.key[0];
        $("key-b").value = item.key[1];
      } else $("key").value = item.key;
      invalidate();
      run("Decrypt");
    };
    area.append(button);
  }
  heading.tabIndex = -1;
  renderResult();
  heading.focus();
}
$("cipher").onchange = () => {
  const cipher = $("cipher").value;
  const [label, help, value] = specs[cipher];
  $("key-label").textContent = label;
  $("key-help").textContent = help;
  $("key").value = value;
  $("key").type = ["Caesar", "Rail Fence", "Affine"].includes(cipher)
    ? "number"
    : "text";
  $("affine-second").hidden = cipher !== "Affine";
  $("generate").hidden = cipher !== "Substitution";
  invalidate();
  controls();
};
for (const id of ["key", "key-b"]) $(id).oninput = invalidate;
$("message").oninput = () => {
  fileMode = false;
  filename = "message.txt";
  $("upload").value = "";
  $("file-info").hidden = true;
  updateCount();
  invalidate();
};
$("upload").onchange = async () => {
  const file = $("upload").files[0];
  if (!file) return;
  invalidate();
  const version = revision;
  const loadId = ++fileLoadId;
  readingFile = true;
  controls();
  try {
    if (file.size > 1048576)
      throw new Error("Choose a text file smaller than 1 MB.");
    const text = new TextDecoder("utf-8", { fatal: true }).decode(
      await file.arrayBuffer(),
    );
    if (revision !== version) return;
    if (text.length > 100000)
      throw new Error("Messages can contain up to 100,000 characters.");
    if (!text.trim())
      throw new Error(
        "This file is empty. Choose a file containing a message.",
      );
    $("message").value = text;
    fileMode = true;
    filename = file.name;
    /* textarea normalizes line endings; retain original for file transforms */ originalFile =
      text;
    $("file-info").textContent = `${file.name} · each line uses the same key`;
    $("file-info").hidden = false;
    updateCount();
    status("File opened. Choose an action to continue.");
  } catch (error) {
    if (revision !== version) return;
    $("upload").value = "";
    status(
      (error instanceof TypeError
        ? "This file is not UTF-8 text."
        : error.message) + " Your previous message has been kept.",
      true,
    );
  } finally {
    if (loadId === fileLoadId) {
      readingFile = false;
      controls();
    }
  }
};
let originalFile = "";
// Keep exact uploaded line endings when sending the file to Python.
for (const action of ["Encrypt", "Decrypt", "analyze"])
  $(action.toLowerCase()).onclick = () => run(action);
$("identify").onclick = () => run("crack");
$("generate").onclick = () => run("generate");
$("retry").onclick = start;
$("download").onclick = () => {
  const blob = new Blob([resultText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download =
    filename
      .replace(/\.[^.]*$/, "")
      .replace(/[^\w.-]/g, "_")
      .slice(0, 80) + `_${operation.toLowerCase()}ed.txt`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
$("reuse").onclick = () => {
  const text = resultText;
  $("message").value = text;
  if (fileMode) originalFile = text;
  updateCount();
  invalidate();
  $("message").focus();
  status("Result moved to your message. Choose your next action.");
};
$("crack-tab").onclick = () => setMode("crack");
$("manual-tab").onclick = () => setMode("manual");
for (const id of ["crack-tab", "manual-tab"])
  $(id).onkeydown = (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const manual =
      event.key === "End" || (event.key !== "Home" && workflow === "crack");
    setMode(manual ? "manual" : "crack");
    $(manual ? "manual-tab" : "crack-tab").focus();
  };
$("open-file").onclick = () => $("upload").click();
$("other-guesses").onclick = () => {
  setMode("manual");
  run("analyze");
};
$("manual-link").onclick = () => {
  setMode("manual");
  $("key").focus();
};
$("copy").onclick = async () => {
  const text = resultText;
  try {
    await navigator.clipboard.writeText(text);
    if (resultText !== text) return;
    $("copy").textContent = "Copied";
    status("Copied to clipboard.");
    setTimeout(() => {
      if (resultText === text) $("copy").textContent = "Copy text";
    }, 1500);
  } catch {
    status(
      "Copy is unavailable. Select the result text or use Download .txt.",
      true,
    );
    $("result").focus();
  }
};
$("example").onclick = () => {
  $("message").value =
    "Hyf wer fcaxfmbbhfp tbhcu bjhjv upx eljmm jrmtxm, nimks r tqgucf ttbkfzg plsvxr sfabrv upx bfsbasio ebbupe. Th djlgwxib, mvv dikskbsxf ujavcmfzxr r gwerve vhhv cmgsrup mvv umesjdwis. Zu lxgtsqusu b pbrufv kcfn jxvzol mvv mqufrsg tbu b ehcufv uco dwghrjvbbx upx aztabbx ffisujbbce smvciea. Mvv gqgoc jvlhivkmwfo etg jjuizv: czbbx upx pibal qfnxtgj bvw krjb nbkjt mvv nwkbzoo uscma usxjv mc ijvz.";
  $("message").oninput();
  if (ready && !busy) status("Example loaded. Choose Identify & crack.");
  $("message").focus();
};
setMode("crack");
start();
