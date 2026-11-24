// Hash Lab is independent of the cipher worker and never persists its inputs.
import { sha256 as digest, digestBits } from "./sha256.js";
const $ = (id) => document.getElementById(id);
const encoder = new TextEncoder();
const MAX_FILE_BYTES = 20 * 1024 * 1024;
const MAX_TEXT_LENGTH = 100000;
let initialized = false,
  mode = "text",
  compare = false,
  comparedBefore = false;
let generation = 0,
  busy = false,
  selectedFile = null;
const digests = { text: "", changed: "", file: "" };

function status(text, error = false) {
  $("hash-status").textContent = text;
  $("hash-status").dataset.error = String(error);
}
function supported() {
  return !!globalThis.crypto?.subtle;
}
function controls() {
  for (const id of [
    "hash-text",
    "hash-changed",
    "hash-file",
    "hash-expected",
    "hash-example",
    "hash-compare-toggle",
  ])
    $(id).disabled = !supported();
  $("hash-text-run").disabled = !supported() || busy;
  $("hash-file-run").disabled = !supported() || busy || !selectedFile;
  for (const id of ["hash-text-run", "hash-file-run"]) {
    const active = busy && id === `hash-${mode}-run`;
    $(id).dataset.busy = String(active);
    $(id).textContent = active
      ? "Hashing…"
      : id === "hash-file-run"
        ? "Hash file"
        : compare
          ? "Compare hashes"
          : "Hash text";
  }
  $("hash-content").setAttribute("aria-busy", String(busy));
}
function invalidate(type) {
  generation++;
  busy = false;
  if (type === "text") {
    digests.text = digests.changed = "";
    $("hash-text-results").hidden = true;
    $("hash-bits-details").open = false;
  } else {
    digests.file = "";
    $("hash-file-results").hidden = true;
    $("hash-verification").hidden = true;
  }
  for (const [key, label] of [
    ["text", "Copy hash"],
    ["changed", "Copy changed hash"],
    ["file", "Copy file hash"],
  ])
    $(`hash-${key}-copy`).textContent = label;
  controls();
}
function setMode(next) {
  if (mode !== next) {
    generation++;
    busy = false;
  }
  mode = next;
  for (const candidate of ["text", "file"]) {
    const selected = mode === candidate;
    $(`hash-${candidate}-tab`).setAttribute("aria-selected", String(selected));
    $(`hash-${candidate}-tab`).tabIndex = selected ? 0 : -1;
    $(`hash-${candidate}-panel`).hidden = !selected;
  }
  controls();
  if (supported())
    status(
      mode === "text"
        ? "Hash the text exactly as entered, or compare a change."
        : "Choose a file and optionally paste its expected SHA-256.",
    );
}
function bytesLabel(length) {
  return `${length.toLocaleString()} ${length === 1 ? "byte" : "bytes"}`;
}
function compareBits(original, changed) {
  const a = digestBits(original),
    b = digestBits(changed);
  let count = 0;
  $("hash-bits").replaceChildren(
    ...[...b].map((bit, index) => {
      const cell = document.createElement("span");
      cell.textContent = bit;
      cell.dataset.changed = String(bit !== a[index]);
      if (bit !== a[index]) count++;
      return cell;
    }),
  );
  $("hash-difference").textContent =
    `${count} of 256 output bits changed (${((count / 256) * 100).toFixed(1)}%)`;
  $("hash-difference-help").textContent =
    count === 0
      ? "These inputs produced the same digest. Identical input bytes always produce the same SHA-256."
      : "A small edit can affect many digest bits. This illustrates the avalanche effect; a single example need not change exactly half.";
}
async function hashText() {
  if (busy || !supported()) return;
  const original = $("hash-text").value,
    changed = $("hash-changed").value;
  if (
    original.length > MAX_TEXT_LENGTH ||
    (compare && changed.length > MAX_TEXT_LENGTH)
  ) {
    invalidate("text");
    status("Use at most 100,000 characters in each text box.", true);
    return;
  }
  invalidate("text");
  const token = generation,
    comparing = compare;
  busy = true;
  controls();
  status("Hashing UTF-8 text on this device…");
  try {
    const originalBytes = encoder.encode(original),
      changedBytes = comparing ? encoder.encode(changed) : null;
    const [a, b] = await Promise.all([
      digest(originalBytes),
      comparing ? digest(changedBytes) : Promise.resolve(""),
    ]);
    if (token !== generation) return;
    digests.text = a;
    digests.changed = b;
    $("hash-text-digest").textContent = a;
    $("hash-text-bytes").textContent =
      `${bytesLabel(originalBytes.byteLength)} · UTF-8`;
    $("hash-changed-result").hidden = $("hash-comparison").hidden = !comparing;
    if (comparing) {
      $("hash-changed-digest").textContent = b;
      $("hash-changed-bytes").textContent =
        `${bytesLabel(changedBytes.byteLength)} · UTF-8`;
      compareBits(a, b);
    }
    $("hash-text-results").hidden = false;
    status(
      comparing
        ? "Comparison complete. " + $("hash-difference").textContent
        : "SHA-256 calculated. The digest is 256 bits, written as 64 hexadecimal characters.",
    );
  } catch {
    if (token === generation)
      status(
        "The text could not be hashed. Try again in an up-to-date browser.",
        true,
      );
  } finally {
    if (token === generation) {
      busy = false;
      controls();
    }
  }
}
function expectedValue() {
  const value = $("hash-expected").value.trim().toLowerCase();
  const invalid = value && !/^[a-f0-9]{64}$/.test(value);
  $("hash-expected").setAttribute("aria-invalid", String(!!invalid));
  if (invalid) {
    status(
      "Expected SHA-256 must contain exactly 64 hexadecimal characters (0–9 and a–f).",
      true,
    );
    return null;
  }
  return value;
}
function verifyFile(announce = true) {
  $("hash-verification").hidden = true;
  const expected = expectedValue();
  if (expected === null) return;
  if (!digests.file) {
    if (announce && !busy)
      status(
        selectedFile
          ? "File selected. Choose Hash file."
          : "Choose a file to check.",
      );
    return;
  }
  if (!expected) {
    if (announce)
      status("File hashed. Paste an expected digest to compare it.");
    return;
  }
  const match = expected === digests.file;
  $("hash-verification").textContent = match
    ? "Match — the digest matches the expected value."
    : "Mismatch — the file does not match the expected digest.";
  $("hash-verification").dataset.match = String(match);
  $("hash-verification").hidden = false;
  if (announce)
    status(
      match
        ? "Digest matches. This comparison does not establish the file’s source or safety."
        : "Digest mismatch. Check the file and the expected SHA-256.",
      !match,
    );
}
function chooseFile() {
  invalidate("file");
  selectedFile = $("hash-file").files?.[0] || null;
  if (selectedFile && selectedFile.size > MAX_FILE_BYTES) {
    selectedFile = null;
    $("hash-file").value = "";
    $("hash-file-info").textContent = "No file selected.";
    controls();
    status(
      "Choose a file no larger than 20 MiB. Large files need more memory on your device.",
      true,
    );
    return;
  }
  $("hash-file-info").textContent = selectedFile
    ? `${selectedFile.name} · ${bytesLabel(selectedFile.size)}`
    : "No file selected.";
  controls();
  status(
    selectedFile
      ? "File selected. Choose Hash file; nothing is uploaded."
      : "No file selected.",
  );
}
async function hashFile() {
  if (busy || !supported() || !selectedFile || expectedValue() === null) return;
  invalidate("file");
  const file = selectedFile,
    token = generation;
  busy = true;
  controls();
  status("Reading and hashing the file on this device…");
  try {
    const bytes = await file.arrayBuffer();
    if (token !== generation) return;
    const value = await digest(bytes);
    if (token !== generation) return;
    digests.file = value;
    $("hash-file-digest").textContent = value;
    $("hash-file-bytes").textContent = bytesLabel(file.size);
    $("hash-file-results").hidden = false;
    verifyFile();
  } catch {
    if (token === generation)
      status(
        "This file could not be read or hashed. Choose it again and retry.",
        true,
      );
  } finally {
    if (token === generation) {
      busy = false;
      controls();
    }
  }
}
async function copyDigest(key) {
  const value = digests[key];
  if (!value) return;
  try {
    if (window.Capacitor?.isNativePlatform())
      await window.Capacitor.Plugins.CipherFiles.copyText({ text: value });
    else await navigator.clipboard.writeText(value);
    if (digests[key] === value) status("SHA-256 copied to clipboard.");
  } catch {
    if (digests[key] === value) {
      status(
        "Copy is unavailable. Select the digest to copy it manually.",
        true,
      );
      $(`hash-${key}-digest`).focus();
    }
  }
}
export function openHashLab() {
  $("hash-error").hidden = true;
  $("hash-content").hidden = false;
  if (initialized) return;
  initialized = true;
  for (const candidate of ["text", "file"]) {
    $(`hash-${candidate}-tab`).onclick = () => setMode(candidate);
    $(`hash-${candidate}-tab`).onkeydown = (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key))
        return;
      event.preventDefault();
      const next =
        event.key === "Home"
          ? "text"
          : event.key === "End"
            ? "file"
            : mode === "text"
              ? "file"
              : "text";
      setMode(next);
      $(`hash-${next}-tab`).focus();
    };
  }
  for (const id of ["hash-text", "hash-changed"])
    $(id).oninput = () => {
      invalidate("text");
      status("Text changed. Calculate a fresh hash to use these inputs.");
    };
  $("hash-compare-toggle").onclick = () => {
    compare = !compare;
    if (compare && !comparedBefore) {
      $("hash-changed").value = $("hash-text").value;
      comparedBefore = true;
    }
    $("hash-compare-input").hidden = !compare;
    $("hash-compare-toggle").setAttribute("aria-expanded", String(compare));
    $("hash-compare-toggle").textContent = compare
      ? "Use one text"
      : "Compare a change";
    invalidate("text");
    status(
      compare
        ? "Edit Changed text, then compare the hashes."
        : "Choose Hash text to calculate one digest.",
    );
  };
  $("hash-example").onclick = () => {
    setMode("text");
    compare = comparedBefore = true;
    $("hash-text").value = "Meet at dawn.";
    $("hash-changed").value = "Meet at Dawn.";
    $("hash-compare-input").hidden = false;
    $("hash-compare-toggle").setAttribute("aria-expanded", "true");
    $("hash-compare-toggle").textContent = "Use one text";
    invalidate("text");
    hashText();
  };
  $("hash-text-run").onclick = hashText;
  $("hash-file-run").onclick = hashFile;
  $("hash-file").onchange = chooseFile;
  $("hash-expected").oninput = () => verifyFile();
  for (const key of Object.keys(digests))
    $(`hash-${key}-copy`).onclick = () => copyDigest(key);
  controls();
  if (!supported())
    status(
      "This browser cannot calculate SHA-256 here. Use HTTPS or localhost in an up-to-date browser.",
      true,
    );
}
