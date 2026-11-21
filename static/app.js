const $ = (id) => document.getElementById(id);
let worker,
  loadingTimer,
  ready = false,
  busy = false,
  revision = 0,
  request = 0,
  pending,
  fileMode = false,
  filename = "message.txt",
  operation = "Encrypt",
  resultText = "";
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
  for (const id of ["encrypt", "decrypt", "analyze", "generate"])
    $(id).disabled = !ready || busy;
  $("analyze").hidden = ![
    "Caesar",
    "Vigenère",
    "Rail Fence",
    "Affine",
  ].includes($("cipher").value);
}
function invalidate() {
  revision++;
  resultText = "";
  $("result").value = "";
  $("download").disabled = true;
  $("reuse").disabled = true;
  $("suggestions").replaceChildren();
  if (ready && !busy)
    status("Inputs changed. Choose Encrypt, Decrypt, or Analyze cipher.");
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
      status(
        "Ready. Enter a message and a key, then choose Encrypt or Decrypt.",
      );
      return;
    }
    busy = false;
    controls();
    if (!pending || data.id !== pending.id || pending.revision !== revision) {
      status(
        "Inputs changed. Choose an action to process the current message.",
      );
      return;
    }
    if (data.error) return status(data.error, true);
    if (pending.action === "generate") {
      $("key").value = data.result;
      invalidate();
      status("Substitution key generated. Keep it to decrypt your message.");
    } else if (pending.action === "analyze") {
      showSuggestions(data.result);
      status(
        "Possible keys found. Choose a suggestion to apply it and decrypt.",
      );
    } else {
      resultText = data.result;
      $("result").value = resultText;
      operation = pending.action;
      $("download").disabled = false;
      $("reuse").disabled = false;
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
  if (!ready || busy) return;
  busy = true;
  controls();
  status(action === "analyze" ? "Analyzing possible keys…" : "Processing…");
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
function showSuggestions(results) {
  const area = $("suggestions");
  area.replaceChildren();
  const heading = document.createElement("h3");
  heading.textContent = "Possible keys";
  area.append(heading);
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
  $("file-info").textContent =
    "Up to 1 MB. Files are processed one line at a time.";
  invalidate();
};
$("upload").onchange = async () => {
  const file = $("upload").files[0];
  if (!file) return;
  fileMode = false;
  invalidate();
  const version = revision;
  try {
    if (file.size > 1048576)
      throw new Error("Choose a text file smaller than 1 MB.");
    const text = new TextDecoder("utf-8", { fatal: true }).decode(
      await file.arrayBuffer(),
    );
    if (revision !== version) return;
    if (text.length > 100000)
      throw new Error("Messages can contain up to 100,000 characters.");
    $("message").value = text;
    fileMode = true;
    filename = file.name;
    /* textarea normalizes line endings; retain original for file transforms */ originalFile =
      text;
    $("file-info").textContent = `${file.name} · each line uses the same key`;
    status("File opened. Choose a key and an action.");
  } catch (error) {
    status(
      error instanceof TypeError
        ? "This file is not UTF-8 text."
        : error.message,
      true,
    );
  }
};
let originalFile = "";
// Keep exact uploaded line endings when sending the file to Python.
for (const action of ["Encrypt", "Decrypt", "analyze"])
  $(action.toLowerCase()).onclick = () => run(action);
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
  invalidate();
  $("message").focus();
  status("Result moved to your message. Choose your next action.");
};
start();
